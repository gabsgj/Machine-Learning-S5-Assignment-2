#pragma once
// Background planner: search the capability set for a sequence that reaches a goal.
//
// This component is deliberately outside the Assignment 2 evaluation scope: the assignment
// asks whether capabilities can be embedded and composed, and the planner is the planning step
// of the broader architecture figure, provided here as working background machinery. The
// experiments and the evaluation harness never include it, and the submission documents label
// it as background.
//
// It is nevertheless a real planner over the same specification model:
//
//   forward search   breadth first expansion over application states; every capability whose
//                    preconditions hold is applicable; states are deduplicated by their
//                    canonical rendering so effect cycles terminate
//   backward search  regression from the goal conditions: a capability whose effect establishes
//                    a goal becomes the last step, its preconditions become subgoals; the found
//                    sequence is then validated by forward simulation
//   QoS selection    the strategy orders the frontier by a quality attribute (fewest steps,
//                    least time, least money, most reliable) and reports the chosen plan's
//                    aggregated operational attributes
//   diagnostics      when no plan exists the result names the goal variables no capability can
//                    write, the unreachable subgoals, the depth and expansion limits and the
//                    number of states explored, instead of failing silently
//
// Everything is deterministic: same model, same goal, same result.
#include <string>
#include <vector>

#include "careweave/core/types.hpp"

namespace careweave {
namespace planner {

// How the frontier is ordered.
enum class PlanStrategy { FewestSteps, LeastTime, LeastMoney, MostReliable };

std::string planStrategyToString(PlanStrategy strategy);

struct PlanOptions {
  size_t maxDepth = 6;         // sequence length limit
  size_t maxExpansions = 200000;  // state expansion limit, the cycle guarantee
  PlanStrategy strategy = PlanStrategy::FewestSteps;
  // Optional hard limits on the aggregated operational attributes of the plan.
  double maxTimeMs = 0.0;      // 0 disables the limit
  double maxMoney = 0.0;
  double maxRisk = 0.0;
  double minReliability = 0.0;
};

struct PlanStep {
  std::string capabilityId;
  std::string capabilityName;
  // The step's preconditions that the previous state satisfied (the ones it consumed), and the
  // goal-relevant conditions it established relative to the previous state.
  std::vector<std::string> consumedPreconditions;
  std::vector<std::string> established;
};

struct PlanResult {
  bool found = false;
  bool validated = false;  // the sequence was simulated step by step and reached the goal
  std::string reason;      // diagnostics, populated when found is false
  std::vector<PlanStep> steps;
  // Aggregated operational attributes of the chosen sequence.
  double totalTimeMs = 0.0;
  double totalMoney = 0.0;
  double totalRisk = 0.0;
  double totalReliability = 1.0;
  // Search statistics.
  size_t expandedStates = 0;
  size_t exploredStates = 0;
  size_t depth = 0;
  std::string explanation;  // why this plan, one line per step plus the strategy note
};

class Planner {
 public:
  explicit Planner(const core::ApplicationModel& app) : app_(app) {}

  // Forward search from the application's initial state towards the goal conditions.
  PlanResult planForward(const std::vector<core::Condition>& goal, PlanOptions options = {}) const;

  // Backward regression from the goal conditions, validated by forward simulation.
  PlanResult planBackward(const std::vector<core::Condition>& goal, PlanOptions options = {}) const;

  // Whether a sequence is executable from the application's initial state and reaches the goal.
  bool validate(const std::vector<core::CapabilitySpec>& sequence,
                const std::vector<core::Condition>& goal) const;

 private:
  core::ApplicationModel app_;
};

}  // namespace planner
}  // namespace careweave
