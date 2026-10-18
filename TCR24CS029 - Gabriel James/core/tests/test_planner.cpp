// Planner tests: the background planner is exercised like every other component: forward search
// on a precondition chain, the empty plan, the strategy orderings, cycle protection with
// diagnostics, backward regression with forward validation, depth limit reporting, operational
// limits and the sequence validator.
#include <sstream>
#include <string>
#include <vector>

#include "careweave/core/types.hpp"
#include "careweave/planner/planner.hpp"
#include "careweave/test/framework.hpp"

using careweave::core::ApplicationModel;
using careweave::core::CapabilitySpec;
using careweave::core::CapabilityType;
using careweave::core::Condition;
using careweave::core::ConditionOp;
using careweave::core::Effect;
using careweave::core::EffectOp;
using careweave::core::Value;
using careweave::planner::PlanOptions;
using careweave::planner::PlanResult;
using careweave::planner::PlanStrategy;
using careweave::planner::Planner;

namespace {

Condition cond(const std::string& var, ConditionOp op, Value v) {
  Condition c;
  c.variable = var;
  c.op = op;
  c.value = std::move(v);
  return c;
}

Effect eff(const std::string& var, EffectOp op, Value v) {
  Effect e;
  e.variable = var;
  e.op = op;
  e.value = std::move(v);
  return e;
}

CapabilitySpec cap(const std::string& id, const std::string& name,
                   std::vector<Condition> preconditions, std::vector<Effect> effects,
                   double timeMs = 10.0, double money = 0.0, double reliability = 1.0) {
  CapabilitySpec s;
  s.id = id;
  s.name = name;
  s.type = CapabilityType::API;
  s.mechanism.kind = CapabilityType::API;
  s.preconditions = std::move(preconditions);
  s.effects = std::move(effects);
  s.operational.cost.timeMs = timeMs;
  s.operational.cost.money = money;
  s.operational.reliability = reliability;
  return s;
}

// C1 -> C2 -> C3 chain on Order.exists, Payment.status, Receipt.issued.
ApplicationModel chainApp() {
  ApplicationModel app;
  app.moduleId = "planner-chain";
  app.initialState["Order.exists"] = Value(false);
  app.initialState["Payment.status"] = Value("none");
  app.initialState["Receipt.issued"] = Value(false);
  app.capabilities = {
      cap("C1", "CreateOrder", {}, {eff("Order.exists", EffectOp::SET, Value(true))}, 120.0),
      cap("C2", "MakePayment", {cond("Order.exists", ConditionOp::EQ, Value(true))},
          {eff("Payment.status", EffectOp::SET, Value("paid"))}, 200.0, 0.5),
      cap("C3", "IssueReceipt", {cond("Payment.status", ConditionOp::EQ, Value("paid"))},
          {eff("Receipt.issued", EffectOp::SET, Value(true))}, 30.0),
  };
  return app;
}

bool contains(const std::string& text, const std::string& needle) {
  return text.find(needle) != std::string::npos;
}

}  // namespace

CW_TEST_CASE(forward_plan_orders_the_precondition_chain) {
  const ApplicationModel app = chainApp();
  const Planner planner(app);
  const PlanResult result = planner.planForward({cond("Receipt.issued", ConditionOp::EQ,
                                                      Value(true))});
  CW_CHECK(result.found);
  CW_CHECK(result.validated);
  CW_CHECK(result.depth == 3);
  CW_CHECK(result.steps.size() == 3);
  CW_CHECK(result.steps[0].capabilityId == "C1");
  CW_CHECK(result.steps[1].capabilityId == "C2");
  CW_CHECK(result.steps[2].capabilityId == "C3");
  // The second step consumed the condition the first established, and the third the second.
  CW_CHECK(!result.steps[1].consumedPreconditions.empty());
  CW_CHECK(contains(result.steps[1].consumedPreconditions[0], "Order.exists"));
  CW_CHECK(contains(result.steps[2].consumedPreconditions[0], "Payment.status"));
  CW_CHECK(!result.steps[2].established.empty());
  CW_CHECK(contains(result.steps[2].established[0], "Receipt.issued"));
  CW_CHECK_NEAR(result.totalTimeMs, 350.0, 1e-9);
  CW_CHECK_NEAR(result.totalMoney, 0.5, 1e-9);
  CW_CHECK(contains(result.explanation, "Forward search"));
  CW_CHECK(contains(result.explanation, "consumes"));
}

CW_TEST_CASE(goal_already_holding_yields_the_empty_plan) {
  ApplicationModel app;
  app.initialState["Door.open"] = Value(true);
  app.capabilities = {cap("C1", "CloseDoor", {cond("Door.open", ConditionOp::EQ, Value(true))},
                          {eff("Door.open", EffectOp::SET, Value(false))})};
  const Planner planner(app);
  const PlanResult result =
      planner.planForward({cond("Door.open", ConditionOp::EQ, Value(true))});
  CW_CHECK(result.found);
  CW_CHECK(result.validated);
  CW_CHECK(result.steps.empty());
  CW_CHECK(result.depth == 0);
  CW_CHECK(contains(result.explanation, "already holds"));
}

CW_TEST_CASE(strategy_ordering_selects_the_matching_alternative) {
  ApplicationModel app;
  app.initialState["Goal.reached"] = Value(false);
  app.capabilities = {
      cap("SLOW-CHEAP", "SlowCheap", {}, {eff("Goal.reached", EffectOp::SET, Value(true))},
          1000.0, 0.0, 0.9),
      cap("FAST-COSTLY", "FastCostly", {}, {eff("Goal.reached", EffectOp::SET, Value(true))},
          50.0, 5.0, 0.99),
  };
  const Planner planner(app);
  const std::vector<Condition> goal = {cond("Goal.reached", ConditionOp::EQ, Value(true))};

  PlanOptions fewest;
  fewest.strategy = PlanStrategy::FewestSteps;
  const PlanResult byFewestSteps = planner.planForward(goal, fewest);
  CW_CHECK(byFewestSteps.found);
  CW_CHECK(byFewestSteps.depth == 1);
  // Same length and same resulting state: the tie goes to the first declared capability.
  CW_CHECK(byFewestSteps.steps[0].capabilityId == "SLOW-CHEAP");

  PlanOptions time;
  time.strategy = PlanStrategy::LeastTime;
  const PlanResult byLeastTime = planner.planForward(goal, time);
  CW_CHECK(byLeastTime.found);
  CW_CHECK(byLeastTime.steps[0].capabilityId == "FAST-COSTLY");
  CW_CHECK_NEAR(byLeastTime.totalTimeMs, 50.0, 1e-9);

  PlanOptions money;
  money.strategy = PlanStrategy::LeastMoney;
  const PlanResult byLeastMoney = planner.planForward(goal, money);
  CW_CHECK(byLeastMoney.found);
  CW_CHECK(byLeastMoney.steps[0].capabilityId == "SLOW-CHEAP");
  CW_CHECK_NEAR(byLeastMoney.totalMoney, 0.0, 1e-9);

  PlanOptions reliable;
  reliable.strategy = PlanStrategy::MostReliable;
  const PlanResult byReliability = planner.planForward(goal, reliable);
  CW_CHECK(byReliability.found);
  CW_CHECK(byReliability.steps[0].capabilityId == "FAST-COSTLY");
  CW_CHECK_NEAR(byReliability.totalReliability, 0.99, 1e-9);
}

CW_TEST_CASE(cycles_terminate_and_unreachable_goals_are_diagnosed) {
  ApplicationModel app;
  app.initialState["Flag.up"] = Value(true);
  app.capabilities = {
      cap("DROP", "DropFlag", {cond("Flag.up", ConditionOp::EQ, Value(true))},
          {eff("Flag.up", EffectOp::SET, Value(false))}),
      cap("RAISE", "RaiseFlag", {cond("Flag.up", ConditionOp::EQ, Value(false))},
          {eff("Flag.up", EffectOp::SET, Value(true))}),
  };
  const Planner planner(app);
  const PlanResult result =
      planner.planForward({cond("R.missing", ConditionOp::EQ, Value(true))});
  CW_CHECK(!result.found);
  CW_CHECK(contains(result.reason, "no capability writes R.missing"));
  // The two state cycle is fully explored and capped far below any runaway bound.
  CW_CHECK(result.expandedStates < 10);
  CW_CHECK(result.exploredStates <= 2);

  // The same model terminates in backward regression too.
  const PlanResult backward =
      planner.planBackward({cond("R.missing", ConditionOp::EQ, Value(true))});
  CW_CHECK(!backward.found);
  CW_CHECK(!backward.reason.empty());
  CW_CHECK(backward.expandedStates < 100);
}

CW_TEST_CASE(backward_regression_returns_a_validated_sequence) {
  const ApplicationModel app = chainApp();
  const Planner planner(app);
  const PlanResult result = planner.planBackward(
      {cond("Receipt.issued", ConditionOp::EQ, Value(true)), cond("Payment.status",
                                                                  ConditionOp::EQ,
                                                                  Value("paid"))});
  CW_CHECK(result.found);
  CW_CHECK(result.validated);
  CW_CHECK(result.steps.size() == 3);
  CW_CHECK(result.steps[0].capabilityId == "C1");
  CW_CHECK(result.steps[1].capabilityId == "C2");
  CW_CHECK(result.steps[2].capabilityId == "C3");
  CW_CHECK(contains(result.explanation, "Backward regression"));
  CW_CHECK_NEAR(result.totalTimeMs, 350.0, 1e-9);
}

CW_TEST_CASE(depth_limit_is_reported) {
  const ApplicationModel app = chainApp();
  const Planner planner(app);
  PlanOptions options;
  options.maxDepth = 2;
  const PlanResult result =
      planner.planForward({cond("Receipt.issued", ConditionOp::EQ, Value(true))}, options);
  CW_CHECK(!result.found);
  CW_CHECK(contains(result.reason, "depth limit of 2"));
}

CW_TEST_CASE(operational_limits_filter_the_search) {
  ApplicationModel app;
  app.initialState["X.done"] = Value(false);
  app.capabilities = {
      cap("CHEAP", "Cheap", {}, {eff("X.done", EffectOp::SET, Value(true))}, 100.0, 0.5),
      cap("COSTLY", "Costly", {}, {eff("X.done", EffectOp::SET, Value(true))}, 5.0, 10.0),
  };
  const Planner planner(app);
  const std::vector<Condition> goal = {cond("X.done", ConditionOp::EQ, Value(true))};

  PlanOptions money;
  money.strategy = PlanStrategy::LeastMoney;
  money.maxMoney = 1.0;
  const PlanResult cheap = planner.planForward(goal, money);
  CW_CHECK(cheap.found);
  CW_CHECK(cheap.steps[0].capabilityId == "CHEAP");

  PlanOptions tooTight;
  tooTight.maxTimeMs = 1.0;
  const PlanResult blocked = planner.planForward(goal, tooTight);
  CW_CHECK(!blocked.found);

  PlanOptions reliability;
  reliability.minReliability = 0.95;
  app.capabilities[0].operational.reliability = 0.7;
  app.capabilities[1].operational.reliability = 0.99;
  const Planner strict(app);
  const PlanResult reliable = strict.planForward(goal, reliability);
  CW_CHECK(reliable.found);
  CW_CHECK(reliable.steps[0].capabilityId == "COSTLY");
}

CW_TEST_CASE(sequence_validation_checks_order_and_goal) {
  const ApplicationModel app = chainApp();
  const Planner planner(app);
  const std::vector<CapabilitySpec> correct = {app.capabilities[0], app.capabilities[1],
                                               app.capabilities[2]};
  const std::vector<CapabilitySpec> wrong = {app.capabilities[1], app.capabilities[0]};
  const std::vector<Condition> goal = {cond("Receipt.issued", ConditionOp::EQ, Value(true))};
  CW_CHECK(planner.validate(correct, goal));
  CW_CHECK(!planner.validate(wrong, goal));
  CW_CHECK(!planner.validate({}, goal));
}

int main() { return careweave::testing::runAll("test_planner"); }
