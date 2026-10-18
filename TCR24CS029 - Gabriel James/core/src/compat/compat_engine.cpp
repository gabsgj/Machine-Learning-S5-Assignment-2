#include "careweave/compat/compat_engine.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <sstream>

#include "nlohmann/json.hpp"

namespace careweave {
namespace compat {

namespace {

void addCheck(CompatibilityReport& report, const std::string& name, Outcome outcome,
              const std::string& detail) {
  CheckResult c;
  c.name = name;
  c.outcome = outcome;
  c.detail = detail;
  report.checks.push_back(std::move(c));
}

bool outcomeIsFail(const CheckResult& c) { return c.outcome == Outcome::FAIL; }

std::string format(double v) {
  std::ostringstream os;
  os << std::setprecision(6) << v;
  return os.str();
}

std::string joinList(const std::vector<std::string>& items) {
  std::string out;
  for (size_t i = 0; i < items.size(); ++i) {
    if (i) out += ", ";
    out += items[i];
  }
  return out;
}

// Types are compatible when they agree, or when either side does not commit to one.
bool typesCompatible(const std::string& provided, const std::string& required) {
  if (provided.empty() || required.empty()) return true;
  if (provided == "any" || required == "any") return true;
  return provided == required;
}

}  // namespace

std::string verdictToString(Verdict v) {
  switch (v) {
    case Verdict::COMPATIBLE: return "compatible";
    case Verdict::UNCERTAIN: return "uncertain";
    case Verdict::INCOMPATIBLE: return "incompatible";
  }
  return "uncertain";
}

std::string outcomeToString(Outcome o) {
  switch (o) {
    case Outcome::PASS: return "pass";
    case Outcome::FAIL: return "fail";
    case Outcome::SKIP: return "skip";
    case Outcome::UNKNOWN: return "unknown";
  }
  return "skip";
}

bool CompatibilityReport::hasFailed() const {
  return std::any_of(checks.begin(), checks.end(), outcomeIsFail);
}

CompatEngine::CompatEngine(const core::ApplicationModel& app, Context context)
    : app_(app), context_(std::move(context)) {}

CompatibilityReport CompatEngine::check(const core::CapabilitySpec& earlier,
                                        const core::CapabilitySpec& later) const {
  CompatibilityReport report;
  report.earlierId = earlier.id;
  report.laterId = later.id;

  // 1. Symbolic condition check: E_i |= P_j over the abstract domain, starting from S_I.
  report.entailment = entails(core::AppState::fromMap(app_.initialState), earlier.effects,
                              later.preconditions);
  if (report.entailment.overall == Entailment::ENTAILED) {
    const std::string detail =
        later.preconditions.empty()
            ? "later capability has no preconditions"
            : "all " + std::to_string(later.preconditions.size()) +
                  " preconditions established by earlier effects";
    addCheck(report, "precondition-entailment", Outcome::PASS, detail);
  } else if (report.entailment.overall == Entailment::CONFLICT) {
    for (const auto& item : report.entailment.items) {
      if (item.result == Entailment::CONFLICT) {
        report.rejections.push_back("effects of " + earlier.id + " contradict precondition " +
                                    item.precondition + " of " + later.id + " (" +
                                    item.explanation + ")");
      }
    }
    addCheck(report, "precondition-entailment", Outcome::FAIL,
             std::to_string(report.entailment.conflicts) + " conflicting precondition(s) against " +
                 earlier.id + " effects");
  } else {
    addCheck(report, "precondition-entailment", Outcome::UNKNOWN,
             "cannot prove every precondition from " + earlier.id +
                 " effects alone; a state dependent or earlier written value is involved");
  }

  // 2. Input-output binding.
  checkInputOutput(earlier, later, report);

  // 3. Operational attributes: the five quality attributes, reliability, availability,
  // resources and roles.
  checkOperational(earlier, later, report);

  // 4. Model constraints that must survive the composite.
  checkAssumptions(earlier, later, report);

  // 5. Continuous view.
  computeScores(earlier, later, report);

  // Verdict: any hard failure makes the pair incompatible; a clean but not fully proven pair is
  // uncertain; only a fully entailed pair with every check passing is compatible.
  const bool anyUnknown =
      std::any_of(report.checks.begin(), report.checks.end(),
                  [](const CheckResult& c) { return c.outcome == Outcome::UNKNOWN; });
  if (report.hasFailed()) {
    report.verdict = Verdict::INCOMPATIBLE;
  } else if (report.entailment.overall == Entailment::ENTAILED && !anyUnknown) {
    report.verdict = Verdict::COMPATIBLE;
  } else {
    report.verdict = Verdict::UNCERTAIN;
  }
  return report;
}

void CompatEngine::checkInputOutput(const core::CapabilitySpec& earlier,
                                    const core::CapabilitySpec& later,
                                    CompatibilityReport& report) const {
  int bound = 0, missing = 0, mismatched = 0;
  std::vector<std::string> unknownNames;
  std::vector<std::string> mismatchDetails;
  for (const auto& in : later.inputs) {
    // An optional input needs no binding; only mandatory inputs must be established.
    if (!in.required) continue;
    const core::OutputSpec* match = nullptr;
    for (const auto& out : earlier.outputs) {
      if (out.name == in.name) {
        match = &out;
        break;
      }
    }
    if (match != nullptr) {
      ++bound;
      if (!typesCompatible(match->type, in.type)) {
        ++mismatched;
        mismatchDetails.push_back(in.name + " output type " + match->type + " against required " +
                                  in.type);
      }
      continue;
    }
    // The value may arrive through a state variable the earlier effects write.
    const bool writtenByEffects =
        std::any_of(earlier.effects.begin(), earlier.effects.end(),
                    [&](const core::Effect& e) { return e.variable == in.name; });
    if (writtenByEffects) {
      ++bound;
      continue;
    }
    if (app_.initialState.count(in.name) != 0) {
      ++bound;
      continue;
    }
    ++missing;
    unknownNames.push_back(in.name);
  }
  if (later.inputs.empty()) {
    addCheck(report, "input-output", Outcome::PASS, "later capability declares no inputs");
    return;
  }
  if (mismatched > 0) {
    for (const auto& d : mismatchDetails) {
      report.rejections.push_back("input-output type mismatch: " + d);
    }
    addCheck(report, "input-output", Outcome::FAIL,
             std::to_string(mismatched) + " input type mismatch(es)");
    return;
  }
  if (missing > 0) {
    addCheck(report, "input-output", Outcome::UNKNOWN,
             "inputs not bound by " + earlier.id + " outputs, effects or the initial state: " +
                 joinList(unknownNames) + "; an earlier capability in the pipeline can bind them");
    return;
  }
  addCheck(report, "input-output", Outcome::PASS,
           std::to_string(bound) + " of " + std::to_string(later.inputs.size()) +
               " inputs bound");
}

void CompatEngine::checkOperational(const core::CapabilitySpec& earlier,
                                    const core::CapabilitySpec& later,
                                    CompatibilityReport& report) const {
  const core::QualityAttributes composed =
      earlier.operational.cost.sequentialSum(later.operational.cost);

  auto numericCap = [&](const std::string& name, double value, double cap) {
    if (cap <= 0.0) {
      addCheck(report, name, Outcome::SKIP, "no cap supplied for this context");
      return;
    }
    if (value <= cap) {
      addCheck(report, name, Outcome::PASS, format(value) + " within cap " + format(cap));
    } else {
      addCheck(report, name, Outcome::FAIL, format(value) + " exceeds cap " + format(cap));
      report.rejections.push_back(name + ": composed value " + format(value) +
                                  " exceeds the context cap " + format(cap));
    }
  };
  numericCap("cost-time", composed.timeMs, context_.maxTimeMs);
  numericCap("cost-money", composed.money, context_.maxMoney);
  numericCap("cost-energy", composed.energy, context_.maxEnergy);
  numericCap("cost-resource", composed.resource, context_.maxResource);
  numericCap("risk", composed.risk, context_.maxRisk);

  if (context_.minReliability <= 0.0) {
    addCheck(report, "reliability", Outcome::SKIP, "no reliability floor supplied");
  } else {
    const double composedReliability = earlier.operational.reliability * later.operational.reliability;
    if (composedReliability >= context_.minReliability) {
      addCheck(report, "reliability", Outcome::PASS,
               format(composedReliability) + " at or above floor " +
                   format(context_.minReliability));
    } else {
      addCheck(report, "reliability", Outcome::FAIL,
               format(composedReliability) + " below floor " + format(context_.minReliability));
      report.rejections.push_back("reliability: composed " + format(composedReliability) +
                                  " below the context floor " + format(context_.minReliability));
    }
  }

  // Static availability flag first, then windows when a time point was supplied. The static flag
  // withdraws a capability only when no window is declared: a windowed capability is scheduled
  // (A_i(t) form), so `always: false` plus windows means "open inside the windows".
  auto withdrawn = [](const core::OperationalSpec& ops) {
    return !ops.available && !(ops.windowed && !ops.windows.empty());
  };
  if (withdrawn(earlier.operational) || withdrawn(later.operational)) {
    const std::string who = withdrawn(earlier.operational) ? earlier.id : later.id;
    addCheck(report, "availability", Outcome::FAIL, who + " is marked unavailable");
    report.rejections.push_back("availability: " + who + " is marked unavailable");
  } else if (context_.weekday.empty()) {
    addCheck(report, "availability", Outcome::SKIP,
             "no weekday supplied; window evaluation A(t) skipped");
  } else {
    const bool earlierOpen =
        earlier.operational.availableAt(context_.weekday, context_.minutesAfterMidnight);
    const bool laterOpen =
        later.operational.availableAt(context_.weekday, context_.minutesAfterMidnight);
    if (earlierOpen && laterOpen) {
      addCheck(report, "availability", Outcome::PASS,
               "both open at " + context_.weekday + " minute " +
                   std::to_string(context_.minutesAfterMidnight));
    } else {
      const std::string who = !earlierOpen ? earlier.id : later.id;
      addCheck(report, "availability", Outcome::FAIL,
               who + " closed at " + context_.weekday + " minute " +
                   std::to_string(context_.minutesAfterMidnight));
      report.rejections.push_back("availability: " + who + " is outside its A(t) window at " +
                                  context_.weekday + " minute " +
                                  std::to_string(context_.minutesAfterMidnight));
    }
  }

  if (!context_.enforceResources) {
    addCheck(report, "resources", Outcome::SKIP, "no resource inventory supplied");
  } else {
    std::vector<std::string> required = earlier.resources;
    for (const auto& r : later.resources) required.push_back(r);
    std::vector<std::string> missingResources;
    for (const auto& r : required) {
      if (std::find(context_.availableResources.begin(), context_.availableResources.end(), r) ==
          context_.availableResources.end()) {
        missingResources.push_back(r);
      }
    }
    if (missingResources.empty()) {
      addCheck(report, "resources", Outcome::PASS,
               required.empty() ? "no resource requirements" : "all required resources present");
    } else {
      addCheck(report, "resources", Outcome::FAIL,
               "missing resources: " + joinList(missingResources));
      report.rejections.push_back("resources: missing " + joinList(missingResources));
    }
  }

  if (!context_.enforceRoles) {
    addCheck(report, "roles", Outcome::SKIP, "no role inventory supplied");
  } else {
    std::vector<std::string> required = earlier.roles;
    for (const auto& r : later.roles) required.push_back(r);
    std::vector<std::string> missingRoles;
    for (const auto& r : required) {
      if (std::find(context_.grantedRoles.begin(), context_.grantedRoles.end(), r) ==
          context_.grantedRoles.end()) {
        missingRoles.push_back(r);
      }
    }
    if (missingRoles.empty()) {
      addCheck(report, "roles", Outcome::PASS,
               required.empty() ? "no role requirements" : "all required roles granted");
    } else {
      addCheck(report, "roles", Outcome::FAIL, "missing roles: " + joinList(missingRoles));
      report.rejections.push_back("roles: missing " + joinList(missingRoles));
    }
  }
}

void CompatEngine::checkAssumptions(const core::CapabilitySpec& earlier,
                                    const core::CapabilitySpec& later,
                                    CompatibilityReport& report) const {
  if (context_.assumptions.empty()) {
    addCheck(report, "constraints", Outcome::SKIP, "no model constraints supplied");
    return;
  }
  std::vector<std::string> violated;
  std::vector<std::string> unevaluable;
  for (const std::string& phase :
       {std::string("after earlier effects"), std::string("after later effects")}) {
    core::AppState state = core::AppState::fromMap(app_.initialState);
    core::applyEffects(earlier.effects, state);  // both phases include the earlier effects
    if (phase == "after later effects") core::applyEffects(later.effects, state);
    for (const auto& assumption : context_.assumptions) {
      if (!state.has(assumption.variable)) {
        unevaluable.push_back(assumption.toString() + " (" + phase + ")");
        continue;
      }
      if (!core::satisfies(assumption, state)) {
        violated.push_back(assumption.toString() + " (" + phase + ")");
      }
    }
  }
  if (!violated.empty()) {
    addCheck(report, "constraints", Outcome::FAIL, "violated: " + joinList(violated));
    report.rejections.push_back("constraints: " + joinList(violated));
  } else if (!unevaluable.empty()) {
    addCheck(report, "constraints", Outcome::UNKNOWN,
             "not evaluable on the application state: " + joinList(unevaluable));
  } else {
    addCheck(report, "constraints", Outcome::PASS,
             std::to_string(context_.assumptions.size()) + " constraint(s) hold");
  }
}

void CompatEngine::computeScores(const core::CapabilitySpec& earlier,
                                 const core::CapabilitySpec& later,
                                 CompatibilityReport& report) const {
  report.scores.coverage = encoder_.variableCoverage(earlier, later);
  report.scores.signedCosine =
      embedding::VectorMath::cosine(encoder_.signedEffectVector(earlier),
                                    encoder_.signedPreconditionVector(later));
  report.scores.vectorScore =
      report.scores.coverage * 0.5 * (1.0 + report.scores.signedCosine);
  const embedding::EncodedCapability ea = encoder_.encodeCapabilityDetailed(earlier);
  const embedding::EncodedCapability eb = encoder_.encodeCapabilityDetailed(later);
  report.scores.functionalSimilarity =
      embedding::VectorMath::cosine(ea.functionalView(), eb.functionalView());
  report.scores.implementationSimilarity =
      embedding::VectorMath::cosine(ea.implementationView(), eb.implementationView());
}

std::string CompatibilityReport::render() const {
  std::ostringstream os;
  os << "compatibility " << earlierId << " -> " << laterId << ": " << verdictToString(verdict)
     << "\n";
  os << "  scores: vector " << format(scores.vectorScore) << " (coverage "
     << format(scores.coverage) << ", signed cosine " << format(scores.signedCosine)
     << "), functional similarity " << format(scores.functionalSimilarity)
     << ", implementation similarity " << format(scores.implementationSimilarity) << "\n";
  os << "  entailment: " << entailment.render() << "\n";
  for (const auto& c : checks) {
    os << "  [" << outcomeToString(c.outcome) << "] " << c.name << ": " << c.detail << "\n";
  }
  if (!rejections.empty()) {
    os << "  rejections:\n";
    for (const auto& r : rejections) os << "    - " << r << "\n";
  }
  return os.str();
}

std::string CompatibilityReport::toJsonString() const {
  nlohmann::json j;
  j["earlier"] = earlierId;
  j["later"] = laterId;
  j["verdict"] = verdictToString(verdict);
  j["scores"] = {{"vectorScore", scores.vectorScore},
                 {"coverage", scores.coverage},
                 {"signedCosine", scores.signedCosine},
                 {"functionalSimilarity", scores.functionalSimilarity},
                 {"implementationSimilarity", scores.implementationSimilarity}};
  j["entailment"] = {{"overall", entailmentToString(entailment.overall)},
                     {"entailed", entailment.entailed},
                     {"possible", entailment.possible},
                     {"conflicts", entailment.conflicts},
                     {"unknown", entailment.unknown},
                     {"items", nlohmann::json::array()}};
  for (const auto& item : entailment.items) {
    j["entailment"]["items"].push_back({{"precondition", item.precondition},
                                        {"result", entailmentToString(item.result)},
                                        {"explanation", item.explanation}});
  }
  j["checks"] = nlohmann::json::array();
  for (const auto& c : checks) {
    j["checks"].push_back(
        {{"name", c.name}, {"outcome", outcomeToString(c.outcome)}, {"detail", c.detail}});
  }
  j["rejections"] = rejections;
  return j.dump(2);
}

}  // namespace compat
}  // namespace careweave
