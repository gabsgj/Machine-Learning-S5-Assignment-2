// Evaluation harness: the nine criteria of the assignment specification, each measured.
//
// The specification asks to evaluate the embedding against nine questions. This program answers
// each of them with a measurement on the real components (encoder, mapper, compatibility engine,
// composer, corpus and labeled dataset) and records the result and the conclusion:
//
//   1. capability representation: can different capabilities be represented distinctly?
//   2. state relationship: does the representation capture the relation between capabilities and
//      states?
//   3. precondition-effect compatibility: are composable capabilities distinguished from
//      incompatible ones?
//   4. input-output compatibility: can dependencies between capabilities be represented?
//   5. composition: can complex capabilities be represented from smaller ones?
//   6. goal relevance: can the relation between capabilities and goals be identified?
//   7. operational properties: are cost, reliability, availability and constraints represented?
//   8. consistency: does the representation behave consistently across different problems?
//   9. efficiency: what are the computational and storage requirements?
//
// Every number printed and written to experiments/out/evaluation.{json,csv,md} comes from this
// run. When a measured claim stops holding, the harness fails instead of reporting the stale
// value.

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <map>
#include <string>
#include <vector>

#include "careweave/compat/compat_engine.hpp"
#include "careweave/composer/composer.hpp"
#include "careweave/embedding/encoders.hpp"
#include "careweave/mapper/mapper.hpp"
#include "experiment_support.hpp"
#include "nlohmann/json.hpp"

namespace exp = careweave::experiments;
namespace compat = careweave::compat;
namespace composer = careweave::composer;
namespace embedding = careweave::embedding;
namespace mapper = careweave::mapper;
namespace core = careweave::core;
using nlohmann::json;
using exp::fmt;
using exp::require;

namespace {

const compat::CheckResult* findCheck(const compat::CompatibilityReport& report,
                                     const std::string& name) {
  for (const compat::CheckResult& check : report.checks) {
    if (check.name == name) return &check;
  }
  return nullptr;
}

int failCount(const compat::CompatibilityReport& report) {
  int failures = 0;
  for (const compat::CheckResult& check : report.checks) {
    if (check.outcome == compat::Outcome::FAIL) ++failures;
  }
  return failures;
}

std::vector<exp::fs::path> pathsFrom(const exp::fs::path& root, const json& relativePaths) {
  std::vector<exp::fs::path> sheets;
  for (const auto& entry : relativePaths) sheets.push_back(root / entry.get<std::string>());
  return sheets;
}

std::vector<std::string> idsOf(const json& values) {
  std::vector<std::string> ids;
  for (const auto& entry : values) ids.push_back(entry.get<std::string>());
  return ids;
}

bool contains(const std::vector<std::string>& values, const std::string& value) {
  return std::find(values.begin(), values.end(), value) != values.end();
}

// One numeric attribute toggle: the pass counterpart has the cap (or floor) exactly at the
// composed value, the fail counterpart just past it; the claim is that exactly the named check
// flips and the pair turns incompatible.
template <typename SetBoundary>
bool numericToggleHolds(const core::ApplicationModel& app, const core::CapabilitySpec& earlier,
                        const core::CapabilitySpec& later, const std::string& attribute,
                        double passValue, double failValue, SetBoundary setBoundary) {
  compat::Context passContext;
  setBoundary(passContext, passValue);
  compat::Context failContext;
  setBoundary(failContext, failValue);
  const compat::CompatibilityReport pass = compat::CompatEngine(app, passContext).check(earlier, later);
  const compat::CompatibilityReport fail = compat::CompatEngine(app, failContext).check(earlier, later);
  const compat::CheckResult* passCheck = findCheck(pass, attribute);
  const compat::CheckResult* failCheck = findCheck(fail, attribute);
  const bool passOk = passCheck != nullptr && passCheck->outcome == compat::Outcome::PASS &&
                      failCount(pass) == 0;
  const bool failOk = failCheck != nullptr && failCheck->outcome == compat::Outcome::FAIL &&
                      failCount(fail) == 1 && fail.verdict == compat::Verdict::INCOMPATIBLE;
  return passOk && failOk;
}

template <typename Callable>
double microsPerCall(Callable&& call, size_t iterations, volatile double& sink) {
  const auto start = std::chrono::steady_clock::now();
  for (size_t i = 0; i < iterations; ++i) sink += call(i);
  const auto end = std::chrono::steady_clock::now();
  const double total = static_cast<double>(
      std::chrono::duration_cast<std::chrono::microseconds>(end - start).count());
  return total / static_cast<double>(iterations);
}

struct Criterion {
  int number = 0;
  std::string property;
  std::string measurement;
  std::string value;
  std::string conclusion;
};

}  // namespace

int main(int argc, char** argv) {
  const std::vector<std::string> args(argv + 1, argv + argc);
  const exp::fs::path out = exp::outDir(args);
  const exp::fs::path root = exp::rootDir();

  const embedding::Encoder encoder;
  const mapper::Mapper mapperTool;
  const composer::Composer composerTool;

  const core::ApplicationModel pattern =
      exp::loadApplication(root / "experiments" / "specs" / "order_pattern.yaml");
  const core::ApplicationModel decoys =
      exp::loadApplication(root / "experiments" / "specs" / "irrelevant_decoys.yaml");
  const core::CapabilitySpec& createOrder = exp::findCapability(pattern, "PAT-CreateOrder");
  const core::CapabilitySpec& makePayment = exp::findCapability(pattern, "PAT-MakePayment");
  const core::CapabilitySpec& cancelCart = exp::findCapability(pattern, "PAT-CancelCart");
  const core::CapabilitySpec& decMaintenance = exp::findCapability(decoys, "DEC-ScheduleMaintenance");
  const core::CapabilitySpec& decEscalate = exp::findCapability(decoys, "DEC-EscalateTicket");
  const compat::CompatEngine patternEngine(pattern);

  const std::vector<exp::fs::path> applicationSheets = {
      root / "specs" / "app" / "hospital_clinic_visit.yaml",
      root / "specs" / "app" / "hospital_alias_resolution.yaml",
      root / "specs" / "app" / "ecommerce_purchase.yaml",
      root / "specs" / "app" / "document_processing.yaml",
      root / "specs" / "app" / "compliance_audit.yaml",
  };
  const std::vector<core::CapabilitySpec> corpus = exp::loadCapabilities(applicationSheets);
  require(corpus.size() == 53, "the corpus must hold the 53 shipped capabilities");

  // The labeled dataset, replayed through the real components; the counters feed the
  // compatibility, input-output and consistency criteria.
  struct DatasetReplay {
    size_t required = 0, requiredOk = 0;
    size_t negatives = 0, negativesOk = 0;
    size_t fullPool = 0, fullPoolOk = 0;
    size_t ambiguity = 0, ambiguityOk = 0;
    size_t compatPairs = 0, compatOk = 0;
    size_t boundRows = 0, totalRows = 0;
    size_t ioPass = 0, ioUnknown = 0, ioFail = 0;
    std::vector<double> discScores;
    std::vector<int> discLabels;
  } replay;

  std::vector<std::pair<std::string, json>> problems;
  for (const std::string& problemId : {"hospital_alias", "ecommerce_purchase",
                                       "document_processing"}) {
    std::ifstream stream(root / "dataset" / problemId / "problem.json");
    require(stream.good(), "cannot open dataset/" + problemId + "/problem.json");
    json document;
    stream >> document;
    problems.emplace_back(problemId, std::move(document));
  }

  std::map<std::string, core::ApplicationModel> appCache;
  const auto appFor = [&](const std::string& relative) -> const core::ApplicationModel& {
    auto it = appCache.find(relative);
    if (it == appCache.end()) {
      it = appCache.emplace(relative, exp::loadApplication(root / relative)).first;
    }
    return it->second;
  };

  for (const auto& problemEntry : problems) {
    const std::string& problemId = problemEntry.first;
    const json& problem = problemEntry.second;

    for (const json& c : problem["required_mappings"]) {
      ++replay.required;
      const core::ApplicationModel& requirementSheet =
          appFor(c["requirement_spec"].get<std::string>());
      require(requirementSheet.capabilities.size() == 1,
              problemId + ": the requirement sheet must declare one capability");
      const std::vector<core::CapabilitySpec> candidates =
          exp::loadCapabilities(pathsFrom(root, c["candidate_specs"]));
      const std::vector<mapper::MatchResult> ranked =
          mapperTool.rank(requirementSheet.capabilities.front(), candidates);
      const mapper::Mapper::Selection selection = mapperTool.select(ranked);
      const std::vector<std::string> expected = idsOf(c["expected_capability_ids"]);
      bool ok = selection.bestIndex >= 0 &&
                contains(expected,
                         ranked[static_cast<size_t>(selection.bestIndex)].candidateId);
      if (c["expectation"].get<std::string>() == "resolved_by_kind") {
        ok = ok && selection.kindTieBreak;
      } else {
        ok = ok && !selection.ambiguous;
      }
      if (ok) ++replay.requiredOk;
      if (!ranked.empty()) {
        for (const mapper::FieldMatch& field : ranked[0].inputs) {
          ++replay.totalRows;
          if (field.assigned) ++replay.boundRows;
        }
      }
    }

    for (const json& c : problem["negative_cases"]) {
      ++replay.negatives;
      const core::ApplicationModel& requirementSheet =
          appFor(c["requirement_spec"].get<std::string>());
      const std::vector<core::CapabilitySpec> candidates =
          exp::loadCapabilities(pathsFrom(root, c["candidate_specs"]));
      const std::vector<mapper::MatchResult> ranked =
          mapperTool.rank(requirementSheet.capabilities.front(), candidates);
      const mapper::Mapper::Selection selection = mapperTool.select(ranked);
      if (selection.bestIndex < 0) ++replay.negativesOk;
    }

    for (const json& c : problem["full_pool_cases"]) {
      ++replay.fullPool;
      const core::ApplicationModel& requirementSheet =
          appFor(c["requirement_spec"].get<std::string>());
      const std::vector<core::CapabilitySpec> pool =
          exp::loadCapabilities(pathsFrom(root, problem["pool"]));
      const std::vector<mapper::MatchResult> ranked =
          mapperTool.rank(requirementSheet.capabilities.front(), pool);
      const std::vector<std::string> expected = idsOf(c["expected_capability_ids"]);
      const mapper::Mapper::Selection selection = mapperTool.select(ranked);
      bool ok = !ranked.empty() && contains(expected, ranked[0].candidateId);
      const std::string expectation = c["expectation"].get<std::string>();
      if (expectation == "top1") {
        ok = ok && !selection.ambiguous;
      } else {
        ok = ok && selection.ambiguous;
      }
      if (ok) ++replay.fullPoolOk;
    }

    for (const json& c : problem["ambiguity_cases"]) {
      ++replay.ambiguity;
      const core::ApplicationModel& requirementSheet =
          appFor(c["requirement_spec"].get<std::string>());
      std::vector<core::CapabilitySpec> candidates =
          exp::loadCapabilities(pathsFrom(root, c["candidate_specs"]));
      const json& inject = c["inject"];
      const std::string cloneId = inject["clone_capability_id"].get<std::string>();
      const auto base = std::find_if(candidates.begin(), candidates.end(),
                                     [&](const core::CapabilitySpec& s) { return s.id == cloneId; });
      require(base != candidates.end(), problemId + ": the twin base must exist");
      core::CapabilitySpec twin = *base;
      twin.id = inject["new_capability_id"].get<std::string>();
      twin.name = inject["new_name"].get<std::string>();
      candidates.push_back(twin);
      const std::vector<mapper::MatchResult> ranked =
          mapperTool.rank(requirementSheet.capabilities.front(), candidates);
      const mapper::Mapper::Selection selection = mapperTool.select(ranked);
      const std::vector<std::string> acceptable = idsOf(c["acceptable_capability_ids"]);
      if (selection.ambiguous && !ranked.empty() && contains(acceptable, ranked[0].candidateId)) {
        ++replay.ambiguityOk;
      }
    }

    for (const json& c : problem["compatibility_cases"]) {
      const core::ApplicationModel& app = appFor(c["app"].get<std::string>());
      const compat::CompatEngine engine(app);
      const std::vector<std::string> sequence = idsOf(c["sequence"]);
      require(sequence.size() >= 2, problemId + ": a compatibility case needs two steps");
      const core::CapabilitySpec& earlier = exp::findCapability(app, sequence[0]);
      const core::CapabilitySpec& later = exp::findCapability(app, sequence[1]);
      const compat::CompatibilityReport report = engine.check(earlier, later);
      ++replay.compatPairs;
      const std::string expectation = c["expectation"].get<std::string>();
      if (expectation == compat::verdictToString(report.verdict)) ++replay.compatOk;
      const std::string label = problemId + "/" + c.value("case_id", std::string());
      require(expectation == compat::verdictToString(report.verdict),
              label + ": the frozen verdict changed to " +
                  compat::verdictToString(report.verdict));
      if (expectation == "compatible" || expectation == "incompatible") {
        replay.discScores.push_back(report.scores.vectorScore);
        replay.discLabels.push_back(expectation == "compatible" ? 1 : 0);
      }
      const compat::CheckResult* io = findCheck(report, "input-output");
      require(io != nullptr, label + ": the report must carry the input-output check");
      if (io->outcome == compat::Outcome::PASS) ++replay.ioPass;
      else if (io->outcome == compat::Outcome::UNKNOWN) ++replay.ioUnknown;
      else if (io->outcome == compat::Outcome::FAIL) ++replay.ioFail;
    }
  }
  require(replay.compatPairs == 17, "the dataset must hold the seventeen labeled pairs");
  require(replay.boundRows > 0, "the required mappings must expose input bindings");

  // ---- 1. Capability representation: distinctness ----
  std::vector<embedding::EncodedCapability> encodedCorpus;
  encodedCorpus.reserve(corpus.size());
  for (const core::CapabilitySpec& capability : corpus) {
    encodedCorpus.push_back(encoder.encodeCapabilityDetailed(capability));
  }
  size_t duplicatePairs = 0;
  double nearestSum = 0.0, nearestMax = 0.0;
  std::string nearestMaxPair;
  for (size_t i = 0; i < encodedCorpus.size(); ++i) {
    double best = -1.0;
    size_t bestJ = i;
    for (size_t j = 0; j < encodedCorpus.size(); ++j) {
      if (i == j) continue;
      const double cosine =
          embedding::VectorMath::cosine(encodedCorpus[i].vector, encodedCorpus[j].vector);
      if (cosine > best) {
        best = cosine;
        bestJ = j;
      }
      if (j > i && cosine >= 1.0 - 1e-12) ++duplicatePairs;
    }
    nearestSum += best;
    if (best > nearestMax) {
      nearestMax = best;
      nearestMaxPair = encodedCorpus[i].id + " / " + encodedCorpus[bestJ].id;
    }
  }
  const double nearestMean = nearestSum / static_cast<double>(encodedCorpus.size());
  require(duplicatePairs == 0, "no two capabilities may share one vector");
  require(nearestMax < 0.9999,
          "every capability must stay clear of its nearest neighbour, max " + fmt(nearestMax));
  Criterion c1;
  c1.number = 1;
  c1.property = "Capability representation";
  c1.measurement = "nearest-neighbour full-vector cosine over the 53 capability corpus (53 by "
                   "52 pairs)";
  c1.value = "duplicate vectors 0; nearest neighbour mean " + fmt(nearestMean) + ", max " +
             fmt(nearestMax) + " (" + nearestMaxPair + ")";
  c1.conclusion = "Yes: every capability has its own vector and even the closest pair keeps a "
                  "visible distance.";

  // ---- 2. State relationship ----
  core::AppState s0 = core::AppState::fromMap(pattern.initialState);
  core::AppState s1 = s0;
  core::applyEffects(createOrder.effects, s1);
  core::AppState s2 = s1;
  core::applyEffects(makePayment.effects, s2);
  const embedding::Vector core0 = encoder.stateCore(s0);
  const embedding::Vector core1 = encoder.stateCore(s1);
  const embedding::Vector core2 = encoder.stateCore(s2);
  const double stateMove = 1.0 - embedding::VectorMath::cosine(core0, core1);
  require(stateMove > 0.0, "applying the create effects must move the state encoding");
  require(core1 == core2,
          "a capability without effects must leave the state encoding bitwise unchanged");
  // The relationship between a capability and states is shown through the shared condition
  // space: the precondition of the payment, expressed as the desired condition, must align
  // closer with the state that satisfies it, and the precondition of the cancel the other way
  // round. (The signed precondition vector is a different, struct-block sized projection used by
  // the compatibility score; the state comparison runs in the 64 dimensional condition space, so
  // it uses goalCore and stateCore, which live in that space.)
  core::Goal paymentGoal;
  paymentGoal.conditions = makePayment.preconditions;
  core::Goal cancelGoal;
  cancelGoal.conditions = cancelCart.preconditions;
  const embedding::Vector paymentCondition = encoder.goalCore(paymentGoal);
  const embedding::Vector cancelCondition = encoder.goalCore(cancelGoal);
  const double preconditionAlignmentBefore =
      embedding::VectorMath::cosine(paymentCondition, core0);
  const double preconditionAlignmentAfter =
      embedding::VectorMath::cosine(paymentCondition, core1);
  const double antiAlignmentBefore = embedding::VectorMath::cosine(cancelCondition, core0);
  const double antiAlignmentAfter = embedding::VectorMath::cosine(cancelCondition, core1);
  require(preconditionAlignmentAfter > preconditionAlignmentBefore,
          "the payment precondition must align closer with the state that satisfies it: " +
              fmt(preconditionAlignmentBefore) + " -> " + fmt(preconditionAlignmentAfter));
  require(antiAlignmentBefore > antiAlignmentAfter,
          "the cancel precondition must align closer with the state before the order exists: " +
              fmt(antiAlignmentBefore) + " -> " + fmt(antiAlignmentAfter));
  Criterion c2;
  c2.number = 2;
  c2.property = "State relationship";
  c2.measurement = "state core movement when effects apply (and no movement for a capability "
                   "without effects); alignment of the precondition's desired-condition form "
                   "with the state before and after";
  c2.value = "movement 1-cos " + fmt(stateMove) + " for create, bitwise unchanged for payment; "
             "payment precondition alignment " + fmt(preconditionAlignmentBefore) + " -> " +
             fmt(preconditionAlignmentAfter) + "; cancel precondition " +
             fmt(antiAlignmentBefore) + " -> " + fmt(antiAlignmentAfter);
  c2.conclusion = "Yes: capabilities and states share one condition space, so a precondition "
                  "aligns with exactly the states that satisfy it.";

  // ---- 3. Precondition-effect compatibility ----
  const compat::CompatibilityReport report12 = patternEngine.check(createOrder, makePayment);
  const compat::CompatibilityReport report13 = patternEngine.check(createOrder, cancelCart);
  require(report12.verdict == compat::Verdict::COMPATIBLE,
          "the assignment pattern requires C_1 -> C_2 to be compatible");
  require(report13.verdict == compat::Verdict::INCOMPATIBLE,
          "the assignment pattern requires C_1 -> C_3 to be incompatible");
  require(report12.scores.signedCosine > 0.9 && report13.scores.signedCosine < -0.9,
          "the signed effect-precondition cosine must separate alignment from contradiction");
  const double discAuc = exp::rocAuc(replay.discScores, replay.discLabels);
  require(replay.discLabels.size() == 6, "the decidable discrimination holds six labeled pairs");
  require(discAuc >= 0.99, "the vector compatibility score must separate the decidable pairs");
  Criterion c3;
  c3.number = 3;
  c3.property = "Precondition-effect compatibility";
  c3.measurement = "pattern pair verdicts and scores; the 17 frozen dataset verdicts; vector "
                   "score AUC over the six decidable pairs";
  c3.value = "C_1 -> C_2 compatible (vector score " + fmt(report12.scores.vectorScore) +
             ", signed cosine " + fmt(report12.scores.signedCosine) +
             "); C_1 -> C_3 incompatible (vector score " + fmt(report13.scores.vectorScore) +
             ", signed cosine " + fmt(report13.scores.signedCosine) + "); dataset verdicts " +
             std::to_string(replay.compatOk) + " of " + std::to_string(replay.compatPairs) +
             " reproduced; decidable AUC " + fmt(discAuc);
  c3.conclusion = "Yes: composable pairs are separated from contradictory ones, and the signed "
                  "effects read as alignment and contradiction rather than as distance.";

  // ---- 4. Input-output compatibility ----
  const composer::Composer::Composition comp12 = composerTool.compose({createOrder, makePayment});
  require(comp12.spec.inputs.size() == 1 && comp12.spec.inputs[0].name == "customer_id",
          "the composite must expose exactly the unbound caller input customer_id");
  require(replay.ioFail == 0, "no dataset pair may fail the input-output check");
  require(replay.boundRows == replay.totalRows,
          "every required mapping field must find an assignment");
  Criterion c4;
  c4.number = 4;
  c4.property = "Input-output compatibility";
  c4.measurement = "field assignment rows over the six required mappings; input-output check "
                   "outcomes over the 17 dataset pairs; the composite interface";
  c4.value = "bound " + std::to_string(replay.boundRows) + " of " +
             std::to_string(replay.totalRows) + " field rows; input-output check " +
             std::to_string(replay.ioPass) + " pass, " + std::to_string(replay.ioUnknown) +
             " unknown, " + std::to_string(replay.ioFail) + " fail; composite exposes [" +
             comp12.spec.inputs[0].name + "]";
  c4.conclusion = "Yes: dependencies are represented through named bindings, and what a caller "
                  "must still supply is exactly what stays unbound.";

  // ---- 5. Composition ----
  require(std::fabs(comp12.spec.operational.cost.timeMs - 320.0) < 1e-9 &&
              std::fabs(comp12.spec.operational.cost.money - 0.5) < 1e-9,
          "the composite quality law must add time and money");
  require(std::fabs(comp12.spec.operational.cost.risk - (1.0 - 0.99 * 0.97)) < 1e-9,
          "the composite risk must accumulate as 1-(1-r1)(1-r2)");
  require(std::fabs(comp12.spec.operational.reliability - 0.99 * 0.98) < 1e-9,
          "the composite reliability must multiply");
  const composer::Composer::Composition comp123 =
      composerTool.compose({createOrder, makePayment, cancelCart});
  const compat::CompatibilityReport self12 = patternEngine.check(comp12.spec, comp12.spec);
  const compat::CompatibilityReport self123 = patternEngine.check(comp123.spec, comp123.spec);
  require(self12.verdict != compat::Verdict::INCOMPATIBLE, "the valid composite must be consistent");
  require(self123.verdict == compat::Verdict::INCOMPATIBLE,
          "the contradictory sequence must be detected by its own composite self check");
  const core::CapabilitySpec leftComposition = composerTool.composeTwo(comp12.spec, cancelCart);
  const core::CapabilitySpec rightComposition =
      composerTool.composeTwo(createOrder, composerTool.composeTwo(makePayment, cancelCart));
  const double associativity = embedding::VectorMath::cosine(
      encoder.encodeCapability(leftComposition), encoder.encodeCapability(rightComposition));
  require(associativity > 0.99, "both bracketings must re-encode to nearly the same vector");
  Criterion c5;
  c5.number = 5;
  c5.property = "Composition";
  c5.measurement = "compose the pattern members; quality laws; associativity of both "
                   "bracketings; composite self check of the valid and the contradictory order";
  c5.value = "interface [" + comp12.spec.inputs[0].name + "]; net delta Order.exists; time 320 "
             "ms, money 0.5, risk " + fmt(comp12.spec.operational.cost.risk) + ", reliability " +
             fmt(comp12.spec.operational.reliability) + "; associativity cosine " +
             fmt(associativity) + "; self checks: two-member not incompatible, three-member "
             "incompatible";
  c5.conclusion = "Yes: composites keep the caller interface, the net delta, the quality laws "
                  "and the contradiction structure of their members.";

  // ---- 6. Goal relevance ----
  size_t goalConditions = 0, goalCovered = 0;
  double weakestGoalAlignment = 1.0;
  std::string weakestGoalApp;
  for (const exp::fs::path& sheet : applicationSheets) {
    const core::ApplicationModel app = exp::loadApplication(sheet);
    core::Goal goal;
    goal.conditions = app.goal;
    require(!goal.conditions.empty(), sheet.string() + ": the application must declare a goal");
    for (const core::Condition& condition : goal.conditions) {
      ++goalConditions;
      const bool writable = std::any_of(
          app.capabilities.begin(), app.capabilities.end(),
          [&](const core::CapabilitySpec& capability) {
            return std::any_of(capability.effects.begin(), capability.effects.end(),
                               [&](const core::Effect& effect) {
                                 return effect.variable == condition.variable;
                               });
          });
      if (writable) ++goalCovered;
      require(writable, sheet.string() + ": goal variable " + condition.variable +
                            " must be writable by at least one capability");
    }
    const embedding::Vector goalVector = encoder.goalCore(goal);
    double bestAlignment = 0.0;
    for (const core::CapabilitySpec& capability : app.capabilities) {
      // The effects expressed as desired conditions, so the comparison runs inside the single
      // 64 dimensional condition space that both the goal representation and the capability
      // effects share.
      core::Goal effectGoal;
      for (const core::Effect& effect : capability.effects) {
        core::Condition condition;
        condition.variable = effect.variable;
        condition.op = core::ConditionOp::EQ;
        condition.value = effect.value;
        effectGoal.conditions.push_back(condition);
      }
      if (effectGoal.conditions.empty()) continue;
      bestAlignment = std::max(bestAlignment,
                               embedding::VectorMath::cosine(goalVector,
                                                             encoder.goalCore(effectGoal)));
    }
    require(bestAlignment > 0.0,
            sheet.string() + ": some capability must align with the goal");
    if (bestAlignment < weakestGoalAlignment) {
      weakestGoalAlignment = bestAlignment;
      weakestGoalApp = sheet.filename().string();
    }
  }
  require(goalCovered == goalConditions, "every goal condition must be covered");
  Criterion c6;
  c6.number = 6;
  c6.property = "Goal relevance";
  c6.measurement = "goal conditions writable by at least one capability across the five "
                   "applications; best goal-to-effect alignment per application (both in the "
                   "shared condition space)";
  c6.value = "writable " + std::to_string(goalCovered) + " of " +
             std::to_string(goalConditions) + " goal conditions; weakest best alignment " +
             fmt(weakestGoalAlignment) + " (" + weakestGoalApp + ")";
  c6.conclusion = "Yes: a goal is expressed in the same condition space as the capabilities, "
                  "and every goal condition is reachable by a named effect.";

  // ---- 7. Operational properties ----
  const core::QualityAttributes composedA =
      createOrder.operational.cost.sequentialSum(makePayment.operational.cost);
  const core::QualityAttributes composedB =
      decMaintenance.operational.cost.sequentialSum(decEscalate.operational.cost);
  const double composedReliabilityB =
      decMaintenance.operational.reliability * decEscalate.operational.reliability;
  size_t numericToggles = 0;
  if (numericToggleHolds(pattern, createOrder, makePayment, "cost-time", composedA.timeMs,
                         composedA.timeMs * 0.999,
                         [](compat::Context& c, double v) { c.maxTimeMs = v; })) {
    ++numericToggles;
  }
  if (numericToggleHolds(pattern, createOrder, makePayment, "cost-money", composedA.money,
                         composedA.money * 0.999,
                         [](compat::Context& c, double v) { c.maxMoney = v; })) {
    ++numericToggles;
  }
  if (numericToggleHolds(pattern, createOrder, makePayment, "cost-energy", composedA.energy,
                         composedA.energy * 0.999,
                         [](compat::Context& c, double v) { c.maxEnergy = v; })) {
    ++numericToggles;
  }
  if (numericToggleHolds(decoys, decMaintenance, decEscalate, "cost-resource", composedB.resource,
                         composedB.resource * 0.999,
                         [](compat::Context& c, double v) { c.maxResource = v; })) {
    ++numericToggles;
  }
  if (numericToggleHolds(decoys, decMaintenance, decEscalate, "risk", composedB.risk,
                         composedB.risk * 0.999,
                         [](compat::Context& c, double v) { c.maxRisk = v; })) {
    ++numericToggles;
  }
  if (numericToggleHolds(decoys, decMaintenance, decEscalate, "reliability", composedReliabilityB,
                         composedReliabilityB * 1.001,
                         [](compat::Context& c, double v) { c.minReliability = v; })) {
    ++numericToggles;
  }
  require(numericToggles == 6, "all six numeric attributes must toggle exactly their own check");

  const auto availabilityOutcome = [&](const std::string& weekday, int minute) {
    compat::Context context;
    context.weekday = weekday;
    context.minutesAfterMidnight = minute;
    const compat::CompatibilityReport report =
        compat::CompatEngine(decoys, context).check(decMaintenance, decEscalate);
    const compat::CheckResult* check = findCheck(report, "availability");
    return check != nullptr ? check->outcome : compat::Outcome::SKIP;
  };
  require(availabilityOutcome("mon", 480) == compat::Outcome::PASS &&
              availabilityOutcome("mon", 1019) == compat::Outcome::PASS &&
              availabilityOutcome("mon", 200) == compat::Outcome::FAIL &&
              availabilityOutcome("mon", 1020) == compat::Outcome::FAIL &&
              availabilityOutcome("sat", 480) == compat::Outcome::FAIL &&
              availabilityOutcome("", 0) == compat::Outcome::SKIP,
          "the window arithmetic must hold at every boundary point");

  const auto inventoryOutcome = [&](const std::string& check, bool enforce,
                                    const std::vector<std::string>& inventory) {
    compat::Context context;
    if (check == "resources") {
      context.enforceResources = enforce;
      context.availableResources = inventory;
    } else {
      context.enforceRoles = enforce;
      context.grantedRoles = inventory;
    }
    const compat::CompatibilityReport report =
        compat::CompatEngine(decoys, context).check(decMaintenance, decEscalate);
    const compat::CheckResult* result = findCheck(report, check);
    return result != nullptr ? result->outcome : compat::Outcome::SKIP;
  };
  require(inventoryOutcome("resources", true, {"decoy_db"}) == compat::Outcome::PASS &&
              inventoryOutcome("resources", true, {}) == compat::Outcome::FAIL &&
              inventoryOutcome("resources", false, {}) == compat::Outcome::SKIP &&
              inventoryOutcome("roles", true, {"service"}) == compat::Outcome::PASS &&
              inventoryOutcome("roles", true, {"customer"}) == compat::Outcome::FAIL &&
              inventoryOutcome("roles", false, {}) == compat::Outcome::SKIP,
          "the inventory gates must behave as documented");
  Criterion c7;
  c7.number = 7;
  c7.property = "Operational properties";
  c7.measurement = "six numeric attribute toggles (cap at the composed value against just past "
                   "it); availability window arithmetic at five points plus the omitted control; "
                   "resource and role inventories enforced and gated";
  c7.value = "numeric toggles " + std::to_string(numericToggles) + " of 6; window opens at 480, "
             "open at 1019, closed at 200 and at 1020 (half open), closed on the weekend, "
             "skipped without a time point; inventories pass when covering and fail when "
             "missing, enforce flags gate both";
  c7.conclusion = "Yes: cost, risk, reliability, availability windows, resources and roles are "
                  "represented and checked as first class context.";

  // ---- 8. Consistency ----
  const size_t labelChecks =
      replay.required + replay.negatives + replay.fullPool + replay.ambiguity + replay.compatPairs;
  const size_t labelOk = replay.requiredOk + replay.negativesOk + replay.fullPoolOk +
                         replay.ambiguityOk + replay.compatOk;
  require(labelOk == labelChecks, "every dataset label must be reproduced");
  size_t deterministicVectors = 0;
  for (size_t i = 0; i < corpus.size(); ++i) {
    const embedding::EncodedCapability again = encoder.encodeCapabilityDetailed(corpus[i]);
    if (again.vector == encodedCorpus[i].vector) ++deterministicVectors;
  }
  require(deterministicVectors == corpus.size(),
          "repeated encoding must be bitwise identical for every capability");
  const core::ApplicationModel requirementModel =
      exp::loadApplication(root / "specs" / "app" / "requirements" / "register_pat.yaml");
  const core::CapabilitySpec& requirementCap =
      exp::findCapability(requirementModel, "REQ-RegisterPat");
  const std::vector<mapper::MatchResult> rankedOnce = mapperTool.rank(requirementCap, corpus);
  const std::vector<mapper::MatchResult> rankedTwice = mapperTool.rank(requirementCap, corpus);
  require(rankedOnce.size() == rankedTwice.size() && rankedOnce[0].total == rankedTwice[0].total,
          "repeated scoring must be bitwise identical");
  const compat::CompatibilityReport reportAgain = patternEngine.check(createOrder, makePayment);
  require(reportAgain.verdict == report12.verdict, "repeated checks must agree");
  Criterion c8;
  c8.number = 8;
  c8.property = "Consistency";
  c8.measurement = "replay of every dataset label through the real components; repeated "
                   "encoding, scoring and checking for bitwise reproducibility";
  c8.value = "label checks reproduced " + std::to_string(labelOk) + " of " +
             std::to_string(labelChecks) + " (required, negative, full pool, ambiguity and "
             "compatibility cases); vectors bitwise identical " +
             std::to_string(deterministicVectors) + " of " + std::to_string(corpus.size()) +
             "; repeated scoring and checking identical";
  c8.conclusion = "Yes: the same specification always produces the same numbers, and the labeled "
                  "behaviour holds across the three problem domains.";

  // ---- 9. Efficiency ----
  volatile double sink = 0.0;
  const double encodeMicros = microsPerCall(
      [&](size_t rep) {
        return encoder.encodeCapability(corpus[rep % corpus.size()])[rep % 7];
      },
      5000, sink);
  const double rankMicros = microsPerCall(
      [&](size_t) { return mapperTool.rank(requirementCap, corpus)[0].total; }, 100, sink);
  const double checkMicros = microsPerCall(
      [&](size_t) {
        return static_cast<double>(patternEngine.check(createOrder, makePayment).checks.size());
      },
      500, sink);
  require(encodeMicros < 2000.0, "encoding one capability must stay in the microsecond range");
  require(rankMicros < 50000.0, "ranking a requirement against 53 candidates must stay fast");
  require(checkMicros < 2000.0, "one compatibility check must stay in the microsecond range");
  const size_t vectorDims = encoder.encodeCapability(createOrder).size();
  const size_t vectorBytes = vectorDims * sizeof(double);
  const size_t stateDims = encoder.encodeState(s0).size();
  const size_t corpusBytes = vectorBytes * corpus.size();
  Criterion c9;
  c9.number = 9;
  c9.property = "Efficiency";
  c9.measurement = "wall clock means over repeated runs (5000 encodings, 100 rankings against "
                   "the 53 candidate pool, 500 compatibility checks) and the storage arithmetic "
                   "of the vectors";
  c9.value = "encode " + fmt(encodeMicros, 1) + " us per capability; rank 53 " +
             fmt(rankMicros, 1) + " us per requirement; check " + fmt(checkMicros, 1) +
             " us per pair; " + std::to_string(vectorDims) + " doubles (" +
             std::to_string(vectorBytes) + " bytes) per capability, " +
             std::to_string(corpusBytes) + " bytes for the corpus; state vectors " +
             std::to_string(stateDims) + " doubles; lexicon " +
             std::to_string(embedding::Lexicon::instance().termCount()) + " terms";
  c9.conclusion = "Everything runs offline in microseconds per operation with kilobyte sized "
                  "vectors, so the representation fits the interactive tooling above it.";

  const std::vector<Criterion> criteria = {c1, c2, c3, c4, c5, c6, c7, c8, c9};

  // ---- Report ----
  std::vector<std::vector<std::string>> rows;
  rows.push_back({"#", "property", "measured value", "conclusion"});
  for (const Criterion& criterion : criteria) {
    rows.push_back({std::to_string(criterion.number), criterion.property, criterion.value,
                    criterion.conclusion});
  }
  std::printf("evaluation: the nine criteria\n%s", exp::markdownTable(rows).c_str());
  std::printf("measurement detail\n");
  for (const Criterion& criterion : criteria) {
    std::printf("  %d. %s: %s\n", criterion.number, criterion.property.c_str(),
                criterion.measurement.c_str());
  }

  json result;
  result["evaluation"] = "nine criteria";
  result["criteria"] = json::array();
  for (const Criterion& criterion : criteria) {
    result["criteria"].push_back({{"number", criterion.number},
                                  {"property", criterion.property},
                                  {"measurement", criterion.measurement},
                                  {"value", criterion.value},
                                  {"conclusion", criterion.conclusion}});
  }
  result["raw"]["nearest_neighbour_mean"] = nearestMean;
  result["raw"]["nearest_neighbour_max"] = nearestMax;
  result["raw"]["state_move"] = stateMove;
  result["raw"]["discrimination_auc"] = discAuc;
  result["raw"]["associativity_cosine"] = associativity;
  result["raw"]["encode_micros"] = encodeMicros;
  result["raw"]["rank_micros"] = rankMicros;
  result["raw"]["check_micros"] = checkMicros;
  result["raw"]["label_checks"] = labelChecks;
  result["raw"]["label_ok"] = labelOk;
  exp::writeFile(out / "evaluation.json", result.dump(2) + "\n");

  std::string csv = "number,property,value,conclusion\n";
  for (const Criterion& criterion : criteria) {
    csv += std::to_string(criterion.number) + "," + exp::csvField(criterion.property) + "," +
           exp::csvField(criterion.value) + "," + exp::csvField(criterion.conclusion) + "\n";
  }
  exp::writeFile(out / "evaluation.csv", csv);

  std::string markdown = "# Evaluation: the nine criteria\n\n";
  markdown += exp::markdownTable(rows);
  markdown += "\n## Measurement detail\n\n";
  for (const Criterion& criterion : criteria) {
    markdown += "- " + std::to_string(criterion.number) + ". **" + criterion.property + "**: " +
                criterion.measurement + ".\n";
  }
  exp::writeFile(out / "evaluation.md", markdown);

  std::printf("results written to %s\n", out.string().c_str());
  return 0;
}
