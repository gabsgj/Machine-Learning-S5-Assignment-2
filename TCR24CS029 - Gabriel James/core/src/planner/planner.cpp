// Background planner implementation: forward search, backward regression, QoS ordering,
// cycle protection and diagnostics. See the header for the scope note: the planner is not part
// of the Assignment 2 evaluation.
#include "careweave/planner/planner.hpp"

#include <algorithm>
#include <deque>
#include <map>
#include <queue>
#include <set>
#include <sstream>

namespace careweave {
namespace planner {

std::string planStrategyToString(PlanStrategy strategy) {
  switch (strategy) {
    case PlanStrategy::FewestSteps:
      return "fewest-steps";
    case PlanStrategy::LeastTime:
      return "least-time";
    case PlanStrategy::LeastMoney:
      return "least-money";
    case PlanStrategy::MostReliable:
      return "most-reliable";
  }
  return "unknown";
}

namespace {

bool goalSatisfied(const std::vector<core::Condition>& goal, const core::AppState& state) {
  for (const core::Condition& condition : goal) {
    if (!core::satisfies(condition, state)) return false;
  }
  return true;
}

bool preconditionsHold(const core::CapabilitySpec& capability, const core::AppState& state) {
  for (const core::Condition& condition : capability.preconditions) {
    if (!core::satisfies(condition, state)) return false;
  }
  return true;
}

std::string joined(const std::vector<std::string>& values, const std::string& separator) {
  std::string out;
  for (const std::string& value : values) out += (out.empty() ? "" : separator) + value;
  return out;
}

std::vector<std::string> conditionTexts(const std::vector<core::Condition>& conditions) {
  std::vector<std::string> texts;
  for (const core::Condition& condition : conditions) texts.push_back(condition.toString());
  return texts;
}

// A capability establishes an equality goal when a SET or DELETE effect writes the variable to
// the requested value.
bool establishes(const core::CapabilitySpec& capability, const core::Condition& condition) {
  for (const core::Effect& effect : capability.effects) {
    if (effect.variable != condition.variable) continue;
    if (condition.op != core::ConditionOp::EQ) return false;
    if (effect.op == core::EffectOp::SET && effect.value == condition.value) return true;
  }
  return false;
}

struct Quality {
  core::QualityAttributes cost;
  double reliability = 1.0;
};

void accumulate(Quality& quality, const core::CapabilitySpec& capability) {
  quality.cost = quality.cost.sequentialSum(capability.operational.cost);
  quality.reliability *= capability.operational.reliability;
}

bool withinLimits(const Quality& quality, const PlanOptions& options) {
  const core::QualityAttributes& cost = quality.cost;
  if (options.maxTimeMs > 0.0 && cost.timeMs > options.maxTimeMs) return false;
  if (options.maxMoney > 0.0 && cost.money > options.maxMoney) return false;
  if (options.maxRisk > 0.0 && cost.risk > options.maxRisk) return false;
  if (options.minReliability > 0.0 && quality.reliability < options.minReliability) return false;
  return true;
}

double scalarCost(PlanStrategy strategy, const Quality& quality, size_t depth) {
  switch (strategy) {
    case PlanStrategy::FewestSteps:
      return static_cast<double>(depth);
    case PlanStrategy::LeastTime:
      return quality.cost.timeMs;
    case PlanStrategy::LeastMoney:
      return quality.cost.money;
    case PlanStrategy::MostReliable:
      return (1.0 - quality.reliability) * 1000.0;
  }
  return static_cast<double>(depth);
}

std::string strategyNote(PlanStrategy strategy) {
  switch (strategy) {
    case PlanStrategy::FewestSteps:
      return "the frontier was ordered by sequence length";
    case PlanStrategy::LeastTime:
      return "the frontier was ordered by aggregated execution time";
    case PlanStrategy::LeastMoney:
      return "the frontier was ordered by aggregated monetary cost";
    case PlanStrategy::MostReliable:
      return "the frontier was ordered by aggregated reliability (highest first)";
  }
  return std::string();
}

// Goal variables that no capability can ever write, used by the diagnostics.
std::vector<std::string> unwritableGoalVariables(const core::ApplicationModel& app,
                                                 const std::vector<core::Condition>& goal) {
  std::set<std::string> writable;
  for (const core::CapabilitySpec& capability : app.capabilities) {
    for (const core::Effect& effect : capability.effects) writable.insert(effect.variable);
  }
  std::vector<std::string> missing;
  for (const core::Condition& condition : goal) {
    if (writable.count(condition.variable) == 0) missing.push_back(condition.variable);
  }
  return missing;
}

std::vector<PlanStep> stepsFromIndices(const core::ApplicationModel& app,
                                       const std::vector<size_t>& indices,
                                       const core::AppState& initial,
                                       const std::vector<core::Condition>& goal) {
  std::vector<PlanStep> steps;
  core::AppState state = initial;
  for (size_t index : indices) {
    const core::CapabilitySpec& capability = app.capabilities[index];
    PlanStep step;
    step.capabilityId = capability.id;
    step.capabilityName = capability.name;
    for (const core::Condition& condition : capability.preconditions) {
      if (core::satisfies(condition, state)) step.consumedPreconditions.push_back(condition.toString());
    }
    core::AppState before = state;
    core::applyEffects(capability.effects, state);
    for (const core::Condition& condition : goal) {
      if (!core::satisfies(condition, before) && core::satisfies(condition, state)) {
        step.established.push_back(condition.toString());
      }
    }
    steps.push_back(std::move(step));
  }
  return steps;
}

Quality qualityOf(const core::ApplicationModel& app, const std::vector<size_t>& indices) {
  Quality quality;
  for (size_t index : indices) accumulate(quality, app.capabilities[index]);
  return quality;
}

std::string buildExplanation(const std::vector<size_t>& indices,
                             const std::vector<PlanStep>& steps, PlanStrategy strategy,
                             size_t expanded, size_t explored) {
  std::ostringstream out;
  if (indices.empty()) {
    out << "The goal already holds in the initial state, so the empty sequence solves it.\n";
  } else {
    out << "Strategy " << planStrategyToString(strategy) << ": " << strategyNote(strategy)
        << ".\n";
    for (size_t i = 0; i < steps.size(); ++i) {
      out << (i + 1) << ". " << steps[i].capabilityId << " (" << steps[i].capabilityName << ")";
      if (!steps[i].consumedPreconditions.empty()) {
        out << "; consumes " << joined(steps[i].consumedPreconditions, " and ");
      }
      if (!steps[i].established.empty()) {
        out << "; establishes " << joined(steps[i].established, " and ");
      }
      out << ".\n";
    }
  }
  out << "Search: " << expanded << " state expansions over " << explored << " explored states.";
  return out.str();
}

PlanResult makeResult(const core::ApplicationModel& app, const std::vector<size_t>& indices,
                      const std::vector<core::Condition>& goal, PlanOptions options,
                      size_t expanded, size_t explored, const std::string& method) {
  PlanResult result;
  result.steps = stepsFromIndices(app, indices, core::AppState::fromMap(app.initialState), goal);
  const Quality quality = qualityOf(app, indices);
  result.totalTimeMs = quality.cost.timeMs;
  result.totalMoney = quality.cost.money;
  result.totalRisk = quality.cost.risk;
  result.totalReliability = quality.reliability;
  result.expandedStates = expanded;
  result.exploredStates = explored;
  result.depth = indices.size();
  result.found = true;
  result.validated = true;
  result.explanation = method + "\n" +
                       buildExplanation(indices, result.steps, options.strategy, expanded,
                                        explored);
  return result;
}

}  // namespace

bool Planner::validate(const std::vector<core::CapabilitySpec>& sequence,
                       const std::vector<core::Condition>& goal) const {
  core::AppState state = core::AppState::fromMap(app_.initialState);
  for (const core::CapabilitySpec& capability : sequence) {
    if (!preconditionsHold(capability, state)) return false;
    core::applyEffects(capability.effects, state);
  }
  return goalSatisfied(goal, state);
}

PlanResult Planner::planForward(const std::vector<core::Condition>& goal,
                                PlanOptions options) const {
  const core::AppState initial = core::AppState::fromMap(app_.initialState);
  size_t explored = 0;
  if (goalSatisfied(goal, initial)) {
    return makeResult(app_, {}, goal, options, 0, 1, "Forward search found the goal initially.");
  }

  struct Node {
    core::AppState state;
    std::vector<size_t> indices;
    Quality quality;
    double key = 0.0;
  };
  struct FrontierItem {
    double key = 0.0;
    size_t sequence = 0;
    Node node;
  };
  const auto worse = [](const FrontierItem& a, const FrontierItem& b) {
    if (a.key != b.key) return a.key > b.key;  // min-heap on the strategy key
    return a.sequence > b.sequence;            // deterministic first-in-first-out on ties
  };
  std::priority_queue<FrontierItem, std::vector<FrontierItem>, decltype(worse)> frontier(worse);

  std::map<std::string, double> bestKey;
  size_t sequence = 0;
  const auto push = [&](const Node& node, double key) {
    const std::string stateKeyValue = node.state.toString();
    const auto it = bestKey.find(stateKeyValue);
    const double currentBest = it == bestKey.end() ? -1.0 : it->second;
    if (it != bestKey.end() && currentBest <= key) return false;
    bestKey[stateKeyValue] = key;
    ++sequence;
    frontier.push(FrontierItem{key, sequence, node});
    return true;
  };
  {
    Node start;
    start.state = initial;
    push(start, scalarCost(options.strategy, start.quality, 0));
  }
  explored = 1;

  size_t expanded = 0;
  bool depthLimited = false;
  while (!frontier.empty()) {
    Node current = frontier.top().node;
    frontier.pop();
    ++expanded;
    if (goalSatisfied(goal, current.state)) {
      return makeResult(app_, current.indices, goal, options, expanded - 1, explored,
                        "Forward search solved the goal.");
    }
    if (expanded > options.maxExpansions) {
      PlanResult result;
      result.reason = "no plan: the expansion limit of " + std::to_string(options.maxExpansions) +
                      " states was reached after exploring " + std::to_string(explored) +
                      " states";
      const std::vector<std::string> unwritable = unwritableGoalVariables(app_, goal);
      if (!unwritable.empty()) {
        result.reason += "; no capability writes " + joined(unwritable, ", ");
      }
      result.expandedStates = expanded - 1;
      result.exploredStates = explored;
      return result;
    }
    if (current.indices.size() >= options.maxDepth) {
      depthLimited = true;
      continue;
    }
    for (size_t index = 0; index < app_.capabilities.size(); ++index) {
      const core::CapabilitySpec& capability = app_.capabilities[index];
      if (!preconditionsHold(capability, current.state)) continue;
      Node next;
      next.state = current.state;
      core::applyEffects(capability.effects, next.state);
      if (next.state.toString() == current.state.toString()) continue;  // no-op, cycle guard
      next.quality = current.quality;
      accumulate(next.quality, capability);
      if (!withinLimits(next.quality, options)) continue;
      next.indices = current.indices;
      next.indices.push_back(index);
      const double key = scalarCost(options.strategy, next.quality, next.indices.size());
      if (!push(next, key)) continue;
      ++explored;
    }
  }

  PlanResult result;
  result.reason = "no plan: the reachable state space is exhausted after " +
                  std::to_string(expanded) + " expansions over " + std::to_string(explored) +
                  " states";
  if (depthLimited) {
    result.reason += "; the depth limit of " + std::to_string(options.maxDepth) +
                     " was reached by at least one state";
  }
  const std::vector<std::string> unwritable = unwritableGoalVariables(app_, goal);
  if (!unwritable.empty()) {
    result.reason += "; no capability writes " + joined(unwritable, ", ");
  }
  result.expandedStates = expanded;
  result.exploredStates = explored;
  return result;
}

PlanResult Planner::planBackward(const std::vector<core::Condition>& goal,
                                 PlanOptions options) const {
  const core::AppState initial = core::AppState::fromMap(app_.initialState);
  size_t explored = 1;
  if (goalSatisfied(goal, initial)) {
    return makeResult(app_, {}, goal, options, 0, explored,
                      "Backward regression found the goal already holding.");
  }

  struct Regression {
    std::vector<core::Condition> unresolved;
    std::vector<size_t> applied;  // capabilities chosen so far, first step first
    size_t searchDepth = 0;
  };
  const auto unresolvedKey = [](const std::vector<core::Condition>& conditions) {
    std::vector<std::string> texts = conditionTexts(conditions);
    std::sort(texts.begin(), texts.end());
    return joined(texts, "|");
  };

  std::deque<Regression> frontier;
  Regression start;
  start.unresolved = goal;
  frontier.push_back(start);
  std::set<std::string> visited;
  visited.insert(unresolvedKey(start.unresolved));

  size_t expanded = 0;
  while (!frontier.empty()) {
    Regression current = frontier.front();
    frontier.pop_front();
    ++expanded;
    if (expanded > options.maxExpansions) {
      PlanResult result;
      result.reason = "no plan: the backward expansion limit of " +
                      std::to_string(options.maxExpansions) + " was reached after exploring " +
                      std::to_string(explored) + " subgoal sets";
      result.expandedStates = expanded - 1;
      result.exploredStates = explored;
      return result;
    }
    for (size_t index = 0; index < app_.capabilities.size(); ++index) {
      const core::CapabilitySpec& capability = app_.capabilities[index];
      size_t resolved = current.unresolved.size() + 1;
      for (size_t j = 0; j < current.unresolved.size(); ++j) {
        if (establishes(capability, current.unresolved[j])) {
          resolved = j;
          break;
        }
      }
      if (resolved >= current.unresolved.size()) continue;
      Regression next;
      next.applied = current.applied;
      next.applied.push_back(index);
      next.searchDepth = current.searchDepth + 1;
      for (size_t j = 0; j < current.unresolved.size(); ++j) {
        if (j != resolved) next.unresolved.push_back(current.unresolved[j]);
      }
      for (const core::Condition& precondition : capability.preconditions) {
        const bool already = std::any_of(
            next.unresolved.begin(), next.unresolved.end(),
            [&](const core::Condition& c) { return c.toString() == precondition.toString(); });
        if (!already) next.unresolved.push_back(precondition);
      }
      if (next.unresolved.empty() ||
          next.searchDepth < options.maxDepth) {  // subgoals must still be reachable in depth
        const std::string key = unresolvedKey(next.unresolved);
        if (visited.insert(key).second) {
          ++explored;
          frontier.push_back(next);
        }
      }
      if (next.unresolved.empty()) {
        // The regression reached the initial assumptions; the sequence is the reverse of the
        // chosen order, and it is validated by forward simulation before being trusted.
        std::reverse(next.applied.begin(), next.applied.end());
        const std::vector<PlanStep> steps =
            stepsFromIndices(app_, next.applied, initial, goal);
        core::AppState state = initial;
        bool executable = true;
        for (size_t stepIndex : next.applied) {
          const core::CapabilitySpec& candidate = app_.capabilities[stepIndex];
          if (!preconditionsHold(candidate, state)) {
            executable = false;
            break;
          }
          core::applyEffects(candidate.effects, state);
        }
        if (executable && goalSatisfied(goal, state) &&
            next.applied.size() <= options.maxDepth &&
            withinLimits(qualityOf(app_, next.applied), options)) {
          PlanResult result = makeResult(app_, next.applied, goal, options, expanded, explored,
                                         "Backward regression from the goal, validated by "
                                         "forward simulation.");
          result.explanation += " Regression: " + std::to_string(next.applied.size()) +
                                " steps, resolved " + std::to_string(steps.size()) +
                                " subgoal sets.";
          return result;
        }
      }
    }
  }

  PlanResult result;
  result.reason = "no plan: backward regression exhausted " + std::to_string(explored) +
                  " subgoal sets without a validatable sequence";
  const std::vector<std::string> unwritable = unwritableGoalVariables(app_, goal);
  if (!unwritable.empty()) {
    result.reason += "; no capability writes " + joined(unwritable, ", ");
  }
  result.expandedStates = expanded;
  result.exploredStates = explored;
  return result;
}

}  // namespace planner
}  // namespace careweave
