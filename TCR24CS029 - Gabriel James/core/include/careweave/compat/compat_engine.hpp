#pragma once
// Explainable pairwise compatibility between two capabilities.
//
// The engine answers the question the specification places at the centre of the assignment:
// given an earlier capability and a later one, can an execution path run them back to back?
// It combines two independent verdicts so they can also be compared against each other:
//
//   symbolic   effects E_i against preconditions P_j through the abstract domain (entailment),
//              input-output binding, and the operational constraints of the context
//              (cost attributes, reliability, availability windows, resources, roles)
//   vector     the continuous compatibility score
//              coverage(pre_j, eff_i) * 0.5 * (1 + cos(signedEff_i, signedPre_j))
//
// Every check is recorded with its outcome and a human readable explanation, so the report can
// be rendered in the CLI, in the dashboard mapping studio and in the experiment tables. This is
// the "similarity is not composability" requirement: functional similarity of two capabilities
// is reported separately from the composability verdict, and the two never collapse into one
// number.
#include <string>
#include <vector>

#include "careweave/compat/conditions.hpp"
#include "careweave/core/types.hpp"
#include "careweave/embedding/encoders.hpp"

namespace careweave {
namespace compat {

enum class Verdict { COMPATIBLE, UNCERTAIN, INCOMPATIBLE };
std::string verdictToString(Verdict v);

// Outcome of one named check inside a report.
enum class Outcome { PASS, FAIL, SKIP, UNKNOWN };
std::string outcomeToString(Outcome o);

// Runtime context for the operational checks. Zero values disable the corresponding numeric
// check; empty weekday disables the availability window check; the two enforce flags gate the
// resource and role checks because an empty set would otherwise mean "nothing is available".
struct Context {
  double maxTimeMs = 0.0;   // composed C_time cap
  double maxMoney = 0.0;    // composed C_money cap
  double maxEnergy = 0.0;   // composed C_energy cap
  double maxResource = 0.0; // composed C_resource cap
  double maxRisk = 0.0;     // composed risk cap, 1-(1-r1)(1-r2)
  double minReliability = 0.0;  // composed reliability floor, Rel_i * Rel_j
  std::string weekday;          // mon..sun
  int minutesAfterMidnight = 0;
  bool enforceResources = false;
  std::vector<std::string> availableResources;
  bool enforceRoles = false;
  std::vector<std::string> grantedRoles;
  // Model level constraints (K) that must still hold after the two capabilities ran. Each is a
  // typed condition over the application state; empty means "not checked".
  std::vector<core::Condition> assumptions;
};

struct CheckResult {
  std::string name;
  Outcome outcome = Outcome::SKIP;
  std::string detail;
};

struct CompatibilityScores {
  // The vector compatibility score defined in the embedding design document.
  double vectorScore = 0.0;
  // How much of the later precondition space the earlier effects can write at all (mean of the
  // best per-variable identity cosines in [0,1]).
  double coverage = 0.0;
  // cos(signedEff_i, signedPre_j) in [-1,1]; positive means the effects point towards the
  // preconditions, negative means they point away (Order.exists = true against = false).
  double signedCosine = 0.0;
  // Cosine of the functional views: similarity without any claim of composability.
  double functionalSimilarity = 0.0;
  // Cosine of the implementation views: mechanism, resources, quality block.
  double implementationSimilarity = 0.0;
};

struct CompatibilityReport {
  std::string earlierId;
  std::string laterId;
  Verdict verdict = Verdict::UNCERTAIN;
  EntailmentReport entailment;
  std::vector<CheckResult> checks;
  std::vector<std::string> rejections;
  CompatibilityScores scores;
  bool hasFailed() const;
  std::string render() const;
  std::string toJsonString() const;
};

class CompatEngine {
 public:
  CompatEngine(const core::ApplicationModel& app, Context context);
  explicit CompatEngine(const core::ApplicationModel& app) : CompatEngine(app, Context()) {}

  CompatibilityReport check(const core::CapabilitySpec& earlier,
                            const core::CapabilitySpec& later) const;

  const Context& context() const { return context_; }
  const core::ApplicationModel& application() const { return app_; }

 private:
  void checkInputOutput(const core::CapabilitySpec& earlier, const core::CapabilitySpec& later,
                        CompatibilityReport& report) const;
  void checkOperational(const core::CapabilitySpec& earlier, const core::CapabilitySpec& later,
                        CompatibilityReport& report) const;
  void checkAssumptions(const core::CapabilitySpec& earlier, const core::CapabilitySpec& later,
                        CompatibilityReport& report) const;
  void computeScores(const core::CapabilitySpec& earlier, const core::CapabilitySpec& later,
                     CompatibilityReport& report) const;

  core::ApplicationModel app_;
  Context context_;
  embedding::Encoder encoder_;
};

}  // namespace compat
}  // namespace careweave
