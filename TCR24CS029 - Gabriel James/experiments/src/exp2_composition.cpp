// Experiment 2: capability composition.
//
// The assignment pattern C_1 CreateOrder -> C_2 MakePayment -> C_3 CancelCart is composed through
// the real composer. The experiment investigates how the vector of the composite relates to the
// member vectors, reports the two views the composer keeps separate (algebraic superposition and
// re-encoded specification) and measures the composition laws: net state delta, aggregated
// quality attributes, reliability, associativity, and the detection of an invalid ordering.
//
// Assertions: the composite interface (what the caller must supply), the net delta, the quality
// law (time adds, money adds, risk accumulates as 1-(1-r1)(1-r2), reliability multiplies), the
// self consistency of the valid composition, the provable contradiction of the invalid one, and
// associativity on both bracketings.

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

#include "careweave/compat/compat_engine.hpp"
#include "careweave/composer/composer.hpp"
#include "careweave/embedding/vector.hpp"
#include "experiment_support.hpp"
#include "nlohmann/json.hpp"

namespace exp = careweave::experiments;
namespace compat = careweave::compat;
namespace composer = careweave::composer;
namespace embedding = careweave::embedding;
namespace core = careweave::core;
using nlohmann::json;
using exp::fmt;
using exp::require;

namespace {

bool closeEnough(double a, double b, double eps = 1e-9) { return std::fabs(a - b) <= eps; }

std::string effectsText(const std::vector<core::Effect>& effects) {
  std::string out;
  for (const core::Effect& e : effects) out += (out.empty() ? "" : "; ") + e.toString();
  return out;
}

std::string preconditionsText(const std::vector<core::Condition>& preconditions) {
  std::string out;
  for (const core::Condition& p : preconditions) {
    out += (out.empty() ? "" : "; ") + p.toString();
  }
  return out;
}

std::string outputsText(const core::CapabilitySpec& spec) {
  std::string out;
  for (const auto& output : spec.outputs) out += (out.empty() ? "" : ", ") + output.name;
  return out;
}

std::string inputsText(const core::CapabilitySpec& spec) {
  std::string out;
  for (const auto& input : spec.inputs) out += (out.empty() ? "" : ", ") + input.name;
  return out;
}

json specSummary(const core::CapabilitySpec& spec) {
  json out;
  out["id"] = spec.id;
  out["inputs"] = inputsText(spec);
  out["outputs"] = outputsText(spec);
  out["preconditions"] = preconditionsText(spec.preconditions);
  out["effects"] = effectsText(spec.effects);
  out["time_ms"] = spec.operational.cost.timeMs;
  out["money"] = spec.operational.cost.money;
  out["risk"] = spec.operational.cost.risk;
  out["reliability"] = spec.operational.reliability;
  return out;
}

}  // namespace

int main(int argc, char** argv) {
  const std::vector<std::string> args(argv + 1, argv + argc);
  const exp::fs::path out = exp::outDir(args);
  const exp::fs::path root = exp::rootDir();

  const core::ApplicationModel pattern =
      exp::loadApplication(root / "experiments" / "specs" / "order_pattern.yaml");
  const core::CapabilitySpec& c1 = exp::findCapability(pattern, "PAT-CreateOrder");
  const core::CapabilitySpec& c2 = exp::findCapability(pattern, "PAT-MakePayment");
  const core::CapabilitySpec& c3 = exp::findCapability(pattern, "PAT-CancelCart");

  composer::Composer composerTool;
  embedding::Encoder encoder;

  // ---- The valid composition C_1 o C_2 ----
  const composer::Composer::Composition comp12 = composerTool.compose({c1, c2});
  require(comp12.spec.inputs.size() == 1 && comp12.spec.inputs[0].name == "customer_id",
          "C_1 o C_2 must expose exactly the unbound caller input customer_id, got: " +
              inputsText(comp12.spec));
  require(comp12.spec.outputs.size() == 2,
          "C_1 o C_2 must expose the union of member outputs");
  require(comp12.spec.effects.size() == 1 && comp12.spec.effects[0].variable == "Order.exists",
          "the net delta of C_1 o C_2 is Order.exists = true, got: " +
              effectsText(comp12.spec.effects));
  require(comp12.spec.preconditions.size() == 1 &&
              comp12.spec.preconditions[0].variable == "Order.exists",
          "the composite keeps the conservative union of member preconditions (C_2 requires the "
          "order, C_1 establishes it; the union documents both), got: " +
              preconditionsText(comp12.spec.preconditions));

  // Quality laws: time and money add, risk accumulates, reliability multiplies.
  require(closeEnough(comp12.spec.operational.cost.timeMs, 320.0),
          "time must add: got " + fmt(comp12.spec.operational.cost.timeMs, 1));
  require(closeEnough(comp12.spec.operational.cost.money, 0.5),
          "money must add: got " + fmt(comp12.spec.operational.cost.money));
  require(closeEnough(comp12.spec.operational.cost.risk, 1.0 - (1.0 - 0.01) * (1.0 - 0.03)),
          "risk must accumulate as 1-(1-r1)(1-r2): got " +
              fmt(comp12.spec.operational.cost.risk));
  require(closeEnough(comp12.spec.operational.reliability, 0.99 * 0.98),
          "reliability must multiply: got " + fmt(comp12.spec.operational.reliability));

  // ---- The full sequence C_1 o C_2 o C_3 with its contradictory precondition ----
  const composer::Composer::Composition comp123 = composerTool.compose({c1, c2, c3});
  require(comp123.spec.preconditions.size() == 2,
          "the three member composite must carry both order preconditions, got: " +
              preconditionsText(comp123.spec.preconditions));
  require(closeEnough(comp123.spec.operational.cost.timeMs, 410.0),
          "the full sequence time is 410 ms");
  require(closeEnough(comp123.spec.operational.reliability, 0.99 * 0.98 * 0.99),
          "the full sequence reliability is the product");

  // Sequence validity: adjacent pairs through the compatibility engine plus the composite's own
  // consistency, because a pairwise uncertain step may hide a contradiction only the
  // accumulated effect fold exposes.
  const compat::CompatEngine engine(pattern);
  const compat::CompatibilityReport adjacent12 = engine.check(c1, c2);
  const compat::CompatibilityReport adjacent23 = engine.check(c2, c3);
  const compat::CompatibilityReport self12 = engine.check(comp12.spec, comp12.spec);
  const compat::CompatibilityReport self123 = engine.check(comp123.spec, comp123.spec);
  require(adjacent12.verdict == compat::Verdict::COMPATIBLE, "C_1 -> C_2 must be compatible");
  require(adjacent23.verdict == compat::Verdict::UNCERTAIN,
          "C_2 -> C_3 stays honestly uncertain (the payment writes no state)");
  require(self12.verdict != compat::Verdict::INCOMPATIBLE,
          "C_1 o C_2 must be self consistent:\n" + self12.render());
  require(self123.verdict == compat::Verdict::INCOMPATIBLE,
          "C_1 o C_2 o C_3 must be provably contradictory: the sequence establishes the order "
          "while C_3 requires it not to exist:\n" + self123.render());

  // ---- Associativity: (C_1 o C_2) o C_3  vs  C_1 o (C_2 o C_3) ----
  const core::CapabilitySpec left = composerTool.composeTwo(comp12.spec, c3);
  const core::CapabilitySpec right = composerTool.composeTwo(c1, composerTool.composeTwo(c2, c3));
  require(effectsText(left.effects) == effectsText(right.effects),
          "associativity of the effect fold: " + effectsText(left.effects) + " vs " +
              effectsText(right.effects));
  require(preconditionsText(left.preconditions) == preconditionsText(right.preconditions),
          "associativity of the precondition union");
  require(closeEnough(left.operational.cost.timeMs, right.operational.cost.timeMs) &&
              closeEnough(left.operational.cost.money, right.operational.cost.money) &&
              closeEnough(left.operational.cost.risk, right.operational.cost.risk) &&
              closeEnough(left.operational.reliability, right.operational.reliability),
          "associativity of the quality law");
  const embedding::Vector leftVector = encoder.encodeCapability(left);
  const embedding::Vector rightVector = encoder.encodeCapability(right);
  const double associativityCosine = embedding::VectorMath::cosine(leftVector, rightVector);
  require(associativityCosine > 0.99,
          "the two bracketings must re-encode to nearly the same vector, cosine " +
              fmt(associativityCosine));

  // ---- Vector relations of the composite ----
  const embedding::Vector v1 = encoder.encodeCapability(c1);
  const embedding::Vector v2 = encoder.encodeCapability(c2);
  const embedding::Vector v3 = encoder.encodeCapability(c3);
  const double toC1 = embedding::VectorMath::cosine(comp12.algebraic, v1);
  const double toC2 = embedding::VectorMath::cosine(comp12.algebraic, v2);
  const double toC3 = embedding::VectorMath::cosine(comp12.algebraic, v3);
  require(toC1 > 0.0 && toC2 > 0.0,
          "the composite vector must relate positively to both members");
  require(comp12.algebraicVsReencoded > 0.5,
          "the algebraic superposition and the re-encoded composite must stay close, cosine " +
              fmt(comp12.algebraicVsReencoded));

  // The composite sits between members: it must not coincide with either.
  require(toC1 < 1.0 && toC2 < 1.0, "the composite must not collapse onto a single member");

  // ---- Report ----
  std::vector<std::vector<std::string>> relationRows;
  relationRows.push_back({"relation", "cosine"});
  relationRows.push_back({"composite vs C_1", fmt(toC1)});
  relationRows.push_back({"composite vs C_2", fmt(toC2)});
  relationRows.push_back({"composite vs C_3 (not a member)", fmt(toC3)});
  relationRows.push_back({"algebraic vs re-encoded composite", fmt(comp12.algebraicVsReencoded)});
  relationRows.push_back({"(C_1 o C_2) o C_3 vs C_1 o (C_2 o C_3)", fmt(associativityCosine)});

  std::vector<std::vector<std::string>> lawRows;
  lawRows.push_back({"quantity", "C_1", "C_2", "C_3", "C_1 o C_2", "whole sequence"});
  lawRows.push_back({"time_ms", "120", "200", "90", fmt(comp12.spec.operational.cost.timeMs, 1),
                     fmt(comp123.spec.operational.cost.timeMs, 1)});
  lawRows.push_back({"money", "0", "0.5", "0", fmt(comp12.spec.operational.cost.money),
                     fmt(comp123.spec.operational.cost.money)});
  lawRows.push_back({"risk", "0.01", "0.03", "0.01", fmt(comp12.spec.operational.cost.risk),
                     fmt(comp123.spec.operational.cost.risk)});
  lawRows.push_back({"reliability", "0.99", "0.98", "0.99",
                     fmt(comp12.spec.operational.reliability),
                     fmt(comp123.spec.operational.reliability)});

  std::vector<std::vector<std::string>> sequenceRows;
  sequenceRows.push_back({"step", "verdict", "note"});
  sequenceRows.push_back({"C_1 -> C_2", compat::verdictToString(adjacent12.verdict),
                          "order established, payment binds"});
  sequenceRows.push_back({"C_2 -> C_3", compat::verdictToString(adjacent23.verdict),
                          "payment writes no state; honest uncertainty"});
  sequenceRows.push_back({"composite C_1 o C_2 self check",
                          compat::verdictToString(self12.verdict), "run as one capability"});
  sequenceRows.push_back({"composite C_1 o C_2 o C_3 self check",
                          compat::verdictToString(self123.verdict),
                          "cancel requires the absence the create established"});

  std::printf("experiment 2: capability composition\n");
  std::printf("vector relations of C_1 o C_2\n%s", exp::markdownTable(relationRows).c_str());
  std::printf("composition laws\n%s", exp::markdownTable(lawRows).c_str());
  std::printf("sequence validity\n%s", exp::markdownTable(sequenceRows).c_str());
  std::printf("composite interface: inputs [%s], outputs [%s], net delta [%s]\n",
              inputsText(comp12.spec).c_str(), outputsText(comp12.spec).c_str(),
              effectsText(comp12.spec.effects).c_str());

  // ---- Outputs ----
  json result;
  result["experiment"] = "exp2_composition";
  result["pattern"]["sheet"] = "experiments/specs/order_pattern.yaml";
  result["composite_two"] = specSummary(comp12.spec);
  result["composite_three"] = specSummary(comp123.spec);
  result["relations"]["to_c1"] = toC1;
  result["relations"]["to_c2"] = toC2;
  result["relations"]["to_c3"] = toC3;
  result["relations"]["algebraic_vs_reencoded"] = comp12.algebraicVsReencoded;
  result["relations"]["associativity_cosine"] = associativityCosine;
  result["validity"]["adjacent_c1_c2"] = compat::verdictToString(adjacent12.verdict);
  result["validity"]["adjacent_c2_c3"] = compat::verdictToString(adjacent23.verdict);
  result["validity"]["self_check_two"] = compat::verdictToString(self12.verdict);
  result["validity"]["self_check_three"] = compat::verdictToString(self123.verdict);
  exp::writeFile(out / "exp2_composition.json", result.dump(2) + "\n");

  std::string csv = "relation,cosine\n";
  csv += "composite_vs_c1," + fmt(toC1) + "\n";
  csv += "composite_vs_c2," + fmt(toC2) + "\n";
  csv += "composite_vs_c3," + fmt(toC3) + "\n";
  csv += "algebraic_vs_reencoded," + fmt(comp12.algebraicVsReencoded) + "\n";
  csv += "associativity," + fmt(associativityCosine) + "\n";
  exp::writeFile(out / "exp2_composition.csv", csv);

  std::string markdown = "# Experiment 2: capability composition\n\n";
  markdown += "The composite interface: inputs [" + inputsText(comp12.spec) + "], outputs [" +
              outputsText(comp12.spec) + "], net delta [" + effectsText(comp12.spec.effects) +
              "].\n\n";
  markdown += "## Vector relations of C_1 o C_2\n\n" + exp::markdownTable(relationRows);
  markdown += "\n## Composition laws\n\n" + exp::markdownTable(lawRows);
  markdown += "\n## Sequence validity\n\n" + exp::markdownTable(sequenceRows);
  markdown += "\nThe composite relates positively to both members without collapsing onto "
              "either; the algebraic superposition and the re-encoded specification agree; both "
              "bracketings of the sequence agree on the effect fold, the precondition union, the "
              "quality law and the re-encoded vector (cosine " + fmt(associativityCosine) +
              "). The invalid ordering is detected by the composite self check: the sequence "
              "requires the order not to exist while its net effect establishes it.\n";
  exp::writeFile(out / "exp2_composition.md", markdown);

  std::printf("results written to %s\n", out.string().c_str());
  return 0;
}
