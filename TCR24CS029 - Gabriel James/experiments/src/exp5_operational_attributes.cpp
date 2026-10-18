// Experiment 5: operational attributes and context gates.
//
// Composability depends on more than the state logic: the assignment defines the quality vector
// (time, money, energy, resource, risk, reliability), the availability schedule A_i(t), the
// resource inventory and the role requirements as part of the capability specification, and
// documents/01 defines the composition laws they obey. This experiment exercises every one of
// those quantities through the real compatibility engine:
//
//   numeric attributes   each composed quantity with a context cap at the composed value (the
//                        check passes) and just below it (exactly that check fails and the pair
//                        becomes incompatible)
//   availability         the windowed A_i(t) form around its boundaries: inside the window, one
//                        minute before the close, exactly at the closing minute, outside the
//                        weekday window, and with the time point omitted (evaluation skipped)
//   resources and roles  an inventory that covers the requirements passes, a missing entry fails
//                        the pair, and the enforce flags gate the checks as documented
//   mapper weights       a sweep of the conditions weight from 0 to 1 (name and fields split the
//                        rest) over the requirement that resolves through vocabulary aliasing,
//                        asserting the intended capability stays on top and recording where the
//                        ambiguity margin is reached and the delivery kind tie break takes over
//
// Assertions: the pass and fail counterpart of every toggle, exactly one failing check per
// rejection, the verdict transition into INCOMPATIBLE, the window boundary arithmetic, and the
// stability of the mapping under the weight sweep.

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

#include "careweave/compat/compat_engine.hpp"
#include "careweave/mapper/mapper.hpp"
#include "experiment_support.hpp"
#include "nlohmann/json.hpp"

namespace exp = careweave::experiments;
namespace compat = careweave::compat;
namespace core = careweave::core;
namespace mapper = careweave::mapper;
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

compat::Outcome outcomeOf(const compat::CompatibilityReport& report, const std::string& name) {
  const compat::CheckResult* check = findCheck(report, name);
  require(check != nullptr, "the report must contain the check " + name);
  return check->outcome;
}

int failCount(const compat::CompatibilityReport& report) {
  int failures = 0;
  for (const compat::CheckResult& check : report.checks) {
    if (check.outcome == compat::Outcome::FAIL) ++failures;
  }
  return failures;
}

void expectOneFailure(const compat::CompatibilityReport& report, const std::string& name,
                      const std::string& label) {
  require(outcomeOf(report, name) == compat::Outcome::FAIL,
          label + ": the check " + name + " must fail");
  require(failCount(report) == 1,
          label + ": exactly one check may fail, found " + std::to_string(failCount(report)));
  require(report.verdict == compat::Verdict::INCOMPATIBLE,
          label + ": a failed check must make the pair incompatible");
}

void expectClean(const compat::CompatibilityReport& report, const std::string& name,
                 compat::Outcome expectedOutcome, compat::Verdict expectedVerdict,
                 const std::string& label) {
  require(outcomeOf(report, name) == expectedOutcome,
          label + ": check " + name + " must be " + compat::outcomeToString(expectedOutcome));
  require(failCount(report) == 0, label + ": no check may fail");
  require(report.verdict == expectedVerdict,
          label + ": expected verdict " + compat::verdictToString(expectedVerdict) + ", got " +
              compat::verdictToString(report.verdict));
}

struct NumericCase {
  std::string attribute;
  std::string pair;
  double composed = 0.0;
  double passValue = 0.0;
  double failValue = 0.0;
  compat::CompatibilityReport pass;
  compat::CompatibilityReport fail;
};

// Runs the pass counterpart (cap at the composed value or floor exactly at it) and the fail
// counterpart (cap just below, floor just above) of one numeric attribute.
template <typename SetBoundary>
NumericCase runNumericCase(const core::ApplicationModel& app, const core::CapabilitySpec& earlier,
                           const core::CapabilitySpec& later, const std::string& attribute,
                           const std::string& pair, double composed, double passValue,
                           double failValue, SetBoundary setBoundary) {
  compat::Context passContext;
  setBoundary(passContext, passValue);
  compat::Context failContext;
  setBoundary(failContext, failValue);
  NumericCase testCase;
  testCase.attribute = attribute;
  testCase.pair = pair;
  testCase.composed = composed;
  testCase.passValue = passValue;
  testCase.failValue = failValue;
  testCase.pass = compat::CompatEngine(app, passContext).check(earlier, later);
  testCase.fail = compat::CompatEngine(app, failContext).check(earlier, later);
  return testCase;
}

}  // namespace

int main(int argc, char** argv) {
  const std::vector<std::string> args(argv + 1, argv + argc);
  const exp::fs::path out = exp::outDir(args);
  const exp::fs::path root = exp::rootDir();

  const core::ApplicationModel pattern =
      exp::loadApplication(root / "experiments" / "specs" / "order_pattern.yaml");
  const core::ApplicationModel decoys =
      exp::loadApplication(root / "experiments" / "specs" / "irrelevant_decoys.yaml");
  const core::ApplicationModel alias =
      exp::loadApplication(root / "specs" / "app" / "hospital_alias_resolution.yaml");
  const core::ApplicationModel requirement =
      exp::loadApplication(root / "specs" / "app" / "requirements" / "register_pat.yaml");

  const core::CapabilitySpec& patCreate = exp::findCapability(pattern, "PAT-CreateOrder");
  const core::CapabilitySpec& patPay = exp::findCapability(pattern, "PAT-MakePayment");
  const core::CapabilitySpec& decMaintenance = exp::findCapability(decoys, "DEC-ScheduleMaintenance");
  const core::CapabilitySpec& decEscalate = exp::findCapability(decoys, "DEC-EscalateTicket");
  const core::CapabilitySpec& required = exp::findCapability(requirement, "REQ-RegisterPat");
  const core::CapabilitySpec& patReg = exp::findCapability(alias, "AR-PatReg");
  const core::CapabilitySpec& patRegForm = exp::findCapability(alias, "AR-PatRegForm");

  const std::string pairA = patCreate.id + " -> " + patPay.id;
  const std::string pairB = decMaintenance.id + " -> " + decEscalate.id;
  const core::QualityAttributes composedA =
      patCreate.operational.cost.sequentialSum(patPay.operational.cost);
  const core::QualityAttributes composedB =
      decMaintenance.operational.cost.sequentialSum(decEscalate.operational.cost);
  const double composedReliabilityB =
      decMaintenance.operational.reliability * decEscalate.operational.reliability;

  // ---- Numeric quality attributes ----
  std::vector<NumericCase> numeric;
  numeric.push_back(runNumericCase(
      pattern, patCreate, patPay, "cost-time", pairA, composedA.timeMs, composedA.timeMs,
      composedA.timeMs * 0.999,
      [](compat::Context& context, double v) { context.maxTimeMs = v; }));
  numeric.push_back(runNumericCase(
      pattern, patCreate, patPay, "cost-money", pairA, composedA.money, composedA.money,
      composedA.money * 0.999,
      [](compat::Context& context, double v) { context.maxMoney = v; }));
  numeric.push_back(runNumericCase(
      pattern, patCreate, patPay, "cost-energy", pairA, composedA.energy, composedA.energy,
      composedA.energy * 0.999,
      [](compat::Context& context, double v) { context.maxEnergy = v; }));
  numeric.push_back(runNumericCase(
      decoys, decMaintenance, decEscalate, "cost-resource", pairB, composedB.resource,
      composedB.resource, composedB.resource * 0.999,
      [](compat::Context& context, double v) { context.maxResource = v; }));
  numeric.push_back(runNumericCase(
      decoys, decMaintenance, decEscalate, "risk", pairB, composedB.risk, composedB.risk,
      composedB.risk * 0.999,
      [](compat::Context& context, double v) { context.maxRisk = v; }));
  numeric.push_back(runNumericCase(
      decoys, decMaintenance, decEscalate, "reliability", pairB, composedReliabilityB,
      composedReliabilityB, composedReliabilityB * 1.001,
      [](compat::Context& context, double v) { context.minReliability = v; }));

  for (const NumericCase& testCase : numeric) {
    const compat::Verdict passVerdict =
        testCase.pair == pairA ? compat::Verdict::COMPATIBLE : compat::Verdict::UNCERTAIN;
    expectClean(testCase.pass, testCase.attribute, compat::Outcome::PASS, passVerdict,
                testCase.attribute + " at the composed value");
    expectOneFailure(testCase.fail, testCase.attribute, testCase.attribute + " below the boundary");
  }

  std::vector<std::vector<std::string>> numericRows;
  numericRows.push_back({"attribute", "pair", "composed", "pass boundary", "fail boundary",
                         "pass verdict", "fail verdict"});
  for (const NumericCase& testCase : numeric) {
    numericRows.push_back({testCase.attribute, testCase.pair, fmt(testCase.composed, 6),
                           fmt(testCase.passValue, 6), fmt(testCase.failValue, 6),
                           compat::verdictToString(testCase.pass.verdict),
                           compat::verdictToString(testCase.fail.verdict)});
  }

  // ---- Availability windows (the A_i(t) form) ----
  struct AvailabilityCase {
    std::string weekday;
    int minute = 0;
    compat::Outcome expected = compat::Outcome::PASS;
    compat::Verdict expectedVerdict = compat::Verdict::UNCERTAIN;
    std::string note;
  };
  const std::vector<AvailabilityCase> availabilityCases = {
      {"", 0, compat::Outcome::SKIP, compat::Verdict::UNCERTAIN,
       "no time point supplied; window evaluation skipped"},
      {"mon", 480, compat::Outcome::PASS, compat::Verdict::UNCERTAIN, "opens at 08:00"},
      {"mon", 200, compat::Outcome::FAIL, compat::Verdict::INCOMPATIBLE, "before the window"},
      {"mon", 1019, compat::Outcome::PASS, compat::Verdict::UNCERTAIN, "one minute before close"},
      {"mon", 1020, compat::Outcome::FAIL, compat::Verdict::INCOMPATIBLE,
       "the closing minute is outside (half open interval)"},
      {"sat", 480, compat::Outcome::FAIL, compat::Verdict::INCOMPATIBLE, "weekend"},
  };

  std::vector<std::vector<std::string>> availabilityRows;
  availabilityRows.push_back({"weekday", "minute", "availability", "verdict", "note"});
  json availabilityJson = json::array();
  for (const AvailabilityCase& testCase : availabilityCases) {
    compat::Context context;
    context.weekday = testCase.weekday;
    context.minutesAfterMidnight = testCase.minute;
    const compat::CompatibilityReport report =
        compat::CompatEngine(decoys, context).check(decMaintenance, decEscalate);
    const std::string label = "availability " + (testCase.weekday.empty() ? std::string("omitted")
                                                                          : testCase.weekday) +
                              " minute " + std::to_string(testCase.minute);
    if (testCase.expected == compat::Outcome::FAIL) {
      expectOneFailure(report, "availability", label);
    } else {
      expectClean(report, "availability", testCase.expected, testCase.expectedVerdict, label);
    }
    availabilityRows.push_back({testCase.weekday.empty() ? "(omitted)" : testCase.weekday,
                                std::to_string(testCase.minute),
                                compat::outcomeToString(testCase.expected),
                                compat::verdictToString(report.verdict), testCase.note});
    availabilityJson.push_back({{"weekday", testCase.weekday},
                                {"minute", testCase.minute},
                                {"outcome", compat::outcomeToString(testCase.expected)},
                                {"verdict", compat::verdictToString(report.verdict)},
                                {"note", testCase.note}});
  }

  // ---- Resource inventory and roles ----
  struct InventoryCase {
    bool enforce = false;
    std::vector<std::string> inventory;
    compat::Outcome expected = compat::Outcome::PASS;
    compat::Verdict expectedVerdict = compat::Verdict::UNCERTAIN;
  };
  const std::vector<InventoryCase> resourceCases = {
      {true, {"decoy_db"}, compat::Outcome::PASS, compat::Verdict::UNCERTAIN},
      {true, {}, compat::Outcome::FAIL, compat::Verdict::INCOMPATIBLE},
      {false, {}, compat::Outcome::SKIP, compat::Verdict::UNCERTAIN},
      {false, {"decoy_db"}, compat::Outcome::SKIP, compat::Verdict::UNCERTAIN},
  };
  const std::vector<InventoryCase> roleCases = {
      {true, {"service"}, compat::Outcome::PASS, compat::Verdict::UNCERTAIN},
      {true, {"service", "admin"}, compat::Outcome::PASS, compat::Verdict::UNCERTAIN},
      {true, {"customer"}, compat::Outcome::FAIL, compat::Verdict::INCOMPATIBLE},
      {false, {}, compat::Outcome::SKIP, compat::Verdict::UNCERTAIN},
  };

  std::vector<std::vector<std::string>> inventoryRows;
  inventoryRows.push_back({"check", "enforced", "inventory", "outcome", "verdict"});
  json inventoryJson = json::array();
  auto runInventory = [&](const std::string& check, const InventoryCase& testCase) {
    compat::Context context;
    std::string inventoryText;
    for (const std::string& entry : testCase.inventory) {
      inventoryText += (inventoryText.empty() ? "" : ", ") + entry;
    }
    if (check == "resources") {
      context.enforceResources = testCase.enforce;
      context.availableResources = testCase.inventory;
    } else {
      context.enforceRoles = testCase.enforce;
      context.grantedRoles = testCase.inventory;
    }
    const compat::CompatibilityReport report =
        compat::CompatEngine(decoys, context).check(decMaintenance, decEscalate);
    const std::string label = check + (testCase.enforce ? " enforced" : " not enforced") +
                              " with [" + inventoryText + "]";
    if (testCase.expected == compat::Outcome::FAIL) {
      expectOneFailure(report, check, label);
    } else {
      expectClean(report, check, testCase.expected, testCase.expectedVerdict, label);
    }
    inventoryRows.push_back({check, testCase.enforce ? "yes" : "no",
                             inventoryText.empty() ? "(empty)" : inventoryText,
                             compat::outcomeToString(testCase.expected),
                             compat::verdictToString(report.verdict)});
    inventoryJson.push_back({{"check", check},
                             {"enforced", testCase.enforce},
                             {"inventory", testCase.inventory},
                             {"outcome", compat::outcomeToString(testCase.expected)},
                             {"verdict", compat::verdictToString(report.verdict)}});
  };
  for (const InventoryCase& testCase : resourceCases) runInventory("resources", testCase);
  for (const InventoryCase& testCase : roleCases) runInventory("roles", testCase);

  // ---- Mapper weight sweep ----
  // The three views are combined with weights; the sweep moves the conditions weight from 0 to 1
  // (name and fields split the remainder) and watches the decision that vocabulary aliasing
  // resolves (Pat_reg through pat_no, pat_name, pat_reg against the form variant).
  std::vector<std::vector<std::string>> sweepRows;
  sweepRows.push_back({"conditions weight", "name weight", "fields weight", "Pat_reg total",
                       "form total", "margin", "ambiguous", "kind tie break", "selected"});
  json sweepJson = json::array();
  double smallestPositiveMargin = 1.0;
  for (int step = 0; step <= 20; ++step) {
    const double conditionsWeight = step / 20.0;
    const double nameWeight = (1.0 - conditionsWeight) / 2.0;
    const double fieldsWeight = (1.0 - conditionsWeight) / 2.0;
    const mapper::Mapper swapper(mapper::Weights{nameWeight, fieldsWeight, conditionsWeight});
    const std::vector<mapper::MatchResult> ranked = swapper.rank(required, {patReg, patRegForm});
    require(ranked.size() == 2, "the sweep ranks the two alias candidates");
    const double margin = ranked[0].total - ranked[1].total;
    // At conditions weight 1 the specification views coincide and the totals tie; the stability
    // of the sort decides the display order there, so the identity assertion only applies to a
    // strictly positive margin.
    if (margin > 1e-9) {
      require(ranked[0].candidateId == "AR-PatReg",
              "Pat_reg must stay on top at conditions weight " + fmt(conditionsWeight, 2));
    }
    require(margin >= 0.0, "the margin must never become negative");
    if (conditionsWeight < 1.0) {
      require(margin > 0.0, "below weight 1 the margin must be strictly positive");
      smallestPositiveMargin = std::min(smallestPositiveMargin, margin);
    } else {
      require(margin <= 0.001,
              "at conditions weight 1 the specification views coincide and the totals tie");
    }
    const mapper::Mapper::Selection selection = swapper.select(ranked);
    require(selection.bestIndex >= 0 &&
                ranked[static_cast<size_t>(selection.bestIndex)].candidateId == "AR-PatReg",
            "the selection must land on AR-PatReg at conditions weight " + fmt(conditionsWeight, 2));
    if (margin < 0.05) {
      require(selection.kindTieBreak && !selection.ambiguous,
              "a near tie must be reported and decided by the delivery kind");
    }
    sweepRows.push_back({fmt(conditionsWeight, 2), fmt(nameWeight, 2), fmt(fieldsWeight, 2),
                         fmt(ranked[0].total), fmt(ranked[1].total), fmt(margin),
                         selection.ambiguous ? "yes" : "no",
                         selection.kindTieBreak ? "yes" : "no",
                         ranked[static_cast<size_t>(selection.bestIndex)].candidateId});
    sweepJson.push_back({{"conditions_weight", conditionsWeight},
                         {"name_weight", nameWeight},
                         {"fields_weight", fieldsWeight},
                         {"pat_reg_total", ranked[0].total},
                         {"form_total", ranked[1].total},
                         {"margin", margin},
                         {"ambiguous", selection.ambiguous},
                         {"kind_tie_break", selection.kindTieBreak},
                         {"selected", ranked[static_cast<size_t>(selection.bestIndex)].candidateId}});
  }

  // The default weights are the documented operating point; the CLI calibration quotes exactly
  // this margin.
  const mapper::Mapper defaultMapper;
  const std::vector<mapper::MatchResult> defaultRanked = defaultMapper.rank(required, {patReg, patRegForm});
  const double defaultMargin = defaultRanked[0].total - defaultRanked[1].total;
  const mapper::Mapper::Selection defaultSelection = defaultMapper.select(defaultRanked);
  require(std::fabs(defaultMargin - 0.0492) <= 5e-4,
          "the default weight margin is the calibrated 0.0492, got " + fmt(defaultMargin));
  require(defaultSelection.bestIndex >= 0 &&
              defaultRanked[static_cast<size_t>(defaultSelection.bestIndex)].candidateId ==
                  "AR-PatReg" &&
              defaultSelection.kindTieBreak && !defaultSelection.ambiguous,
          "at the default weights the delivery kind resolves the near tie to Pat_reg");

  // ---- Report ----
  std::printf("experiment 5: operational attributes and context gates\n");
  std::printf("numeric quality attributes\n%s", exp::markdownTable(numericRows).c_str());
  std::printf("availability windows\n%s", exp::markdownTable(availabilityRows).c_str());
  std::printf("resources and roles\n%s", exp::markdownTable(inventoryRows).c_str());
  std::printf("mapper weight sweep\n%s", exp::markdownTable(sweepRows).c_str());
  std::printf("default weights: margin %s, kind tie break %s, selected %s\n",
              fmt(defaultMargin).c_str(), defaultSelection.kindTieBreak ? "yes" : "no",
              defaultRanked[static_cast<size_t>(defaultSelection.bestIndex)].candidateId.c_str());
  std::printf("smallest positive sweep margin %s\n", fmt(smallestPositiveMargin).c_str());

  // ---- Outputs ----
  json result;
  result["experiment"] = "exp5_operational_attributes";
  result["numeric_toggles"] = json::array();
  for (const NumericCase& testCase : numeric) {
    result["numeric_toggles"].push_back(
        {{"attribute", testCase.attribute},
         {"pair", testCase.pair},
         {"composed", testCase.composed},
         {"pass_boundary", testCase.passValue},
         {"fail_boundary", testCase.failValue},
         {"pass_verdict", compat::verdictToString(testCase.pass.verdict)},
         {"fail_verdict", compat::verdictToString(testCase.fail.verdict)}});
  }
  result["availability"] = availabilityJson;
  result["resources_and_roles"] = inventoryJson;
  result["weight_sweep"] = sweepJson;
  result["smallest_positive_sweep_margin"] = smallestPositiveMargin;
  result["default_weights"] = {{"margin", defaultMargin},
                               {"kind_tie_break", defaultSelection.kindTieBreak},
                               {"selected", defaultRanked[static_cast<size_t>(defaultSelection.bestIndex)].candidateId}};
  exp::writeFile(out / "exp5_operational_attributes.json", result.dump(2) + "\n");

  std::string csv = "section,case,value,outcome,verdict\n";
  for (const NumericCase& testCase : numeric) {
    csv += exp::csvField(testCase.attribute) + ",pass," + fmt(testCase.composed) + "," +
           exp::csvField(compat::outcomeToString(outcomeOf(testCase.pass, testCase.attribute))) +
           "," + exp::csvField(compat::verdictToString(testCase.pass.verdict)) + "\n";
    csv += exp::csvField(testCase.attribute) + ",fail," + fmt(testCase.composed) + "," +
           exp::csvField(compat::outcomeToString(outcomeOf(testCase.fail, testCase.attribute))) +
           "," + exp::csvField(compat::verdictToString(testCase.fail.verdict)) + "\n";
  }
  for (const AvailabilityCase& testCase : availabilityCases) {
    csv += "availability," + exp::csvField(testCase.weekday.empty() ? "(omitted)" : testCase.weekday) +
           "@" + std::to_string(testCase.minute) + ",," +
           exp::csvField(compat::outcomeToString(testCase.expected)) + "," +
           exp::csvField(compat::verdictToString(testCase.expectedVerdict)) + "\n";
  }
  for (const InventoryCase& testCase : resourceCases) {
    csv += "resources," + std::string(testCase.enforce ? "enforced" : "not enforced") + ",," +
           exp::csvField(compat::outcomeToString(testCase.expected)) + "," +
           exp::csvField(compat::verdictToString(testCase.expectedVerdict)) + "\n";
  }
  for (const InventoryCase& testCase : roleCases) {
    csv += "roles," + std::string(testCase.enforce ? "enforced" : "not enforced") + ",," +
           exp::csvField(compat::outcomeToString(testCase.expected)) + "," +
           exp::csvField(compat::verdictToString(testCase.expectedVerdict)) + "\n";
  }
  for (int step = 0; step <= 20; ++step) {
    const double conditionsWeight = step / 20.0;
    const mapper::Mapper swapper(mapper::Weights{(1.0 - conditionsWeight) / 2.0,
                                                 (1.0 - conditionsWeight) / 2.0, conditionsWeight});
    const std::vector<mapper::MatchResult> ranked = swapper.rank(required, {patReg, patRegForm});
    csv += "weight_sweep,conditions=" + fmt(conditionsWeight, 2) + "," + fmt(ranked[0].total) + "," +
           exp::csvField(ranked[0].candidateId) + "," + fmt(ranked[0].total - ranked[1].total) + "\n";
  }
  exp::writeFile(out / "exp5_operational_attributes.csv", csv);

  std::string markdown = "# Experiment 5: operational attributes and context gates\n\n";
  markdown += "## Numeric quality attributes\n\n" + exp::markdownTable(numericRows);
  markdown += "\n## Availability windows\n\n" + exp::markdownTable(availabilityRows);
  markdown += "\n## Resources and roles\n\n" + exp::markdownTable(inventoryRows);
  markdown += "\n## Mapper weight sweep\n\n" + exp::markdownTable(sweepRows);
  markdown += "\nEvery composed quantity has a passing and a rejecting counterpart through the "
              "real engine: a cap exactly at the composed value passes, a cap just below it fails "
              "exactly that check and turns the pair incompatible, and the reliability floor "
              "behaves symmetrically. The windowed availability form is exercised at its "
              "boundaries, including the half open closing minute. An inventory that covers the "
              "requirements passes, a missing entry fails the pair, and the enforce flags gate "
              "the checks so an absent inventory never rejects on its own. The weight sweep keeps "
              "the intended capability on top for every combination; below the ambiguity margin "
              "the delivery kind resolves the near tie, and at the default weights the margin is " +
              fmt(defaultMargin) + ", the same value the CLI reports.\n";
  exp::writeFile(out / "exp5_operational_attributes.md", markdown);

  std::printf("results written to %s\n", out.string().c_str());
  return 0;
}
