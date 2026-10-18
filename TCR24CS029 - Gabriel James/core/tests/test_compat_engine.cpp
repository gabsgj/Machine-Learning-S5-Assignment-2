// Compatibility engine tests: the specification pattern (CreateOrder -> MakePayment entailed,
// CreateOrder -> CancelCart conflict), input-output binding, the five operational attributes,
// reliability, availability windows, resources, roles, constraints and the explainable report.
#include <sstream>

#include "careweave/compat/compat_engine.hpp"
#include "careweave/core/types.hpp"
#include "careweave/test/framework.hpp"

using careweave::compat::CompatEngine;
using careweave::compat::CompatibilityReport;
using careweave::compat::Context;
using careweave::compat::Entailment;
using careweave::compat::Outcome;
using careweave::compat::Verdict;
using careweave::core::AppState;
using careweave::core::ApplicationModel;
using careweave::core::AvailabilityWindow;
using careweave::core::CapabilitySpec;
using careweave::core::CapabilityType;
using careweave::core::Condition;
using careweave::core::ConditionOp;
using careweave::core::Effect;
using careweave::core::EffectOp;
using careweave::core::InputSpec;
using careweave::core::OutputSpec;
using careweave::core::Value;

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

CapabilitySpec createOrder() {
  CapabilitySpec s;
  s.id = "C1";
  s.name = "CreateOrder";
  s.type = CapabilityType::API;
  s.mechanism.kind = CapabilityType::API;
  s.mechanism.method = "POST";
  s.mechanism.endpoint = "/orders";
  s.effects = {eff("Order.exists", EffectOp::SET, Value(true))};
  return s;
}

CapabilitySpec makePayment() {
  CapabilitySpec s;
  s.id = "C2";
  s.name = "MakePayment";
  s.type = CapabilityType::API;
  s.mechanism.kind = CapabilityType::API;
  s.mechanism.method = "POST";
  s.mechanism.endpoint = "/payments";
  s.preconditions = {cond("Order.exists", ConditionOp::EQ, Value(true))};
  s.effects = {eff("Payment.status", EffectOp::SET, Value("paid"))};
  return s;
}

CapabilitySpec cancelCart() {
  CapabilitySpec s;
  s.id = "C3";
  s.name = "CancelCart";
  s.type = CapabilityType::GUI;
  s.mechanism.kind = CapabilityType::GUI;
  s.mechanism.action = "cancel";
  s.preconditions = {cond("Order.exists", ConditionOp::EQ, Value(false))};
  return s;
}

ApplicationModel storeApp() {
  ApplicationModel app;
  app.moduleId = "store";
  app.version = "1.0";
  app.domain = "ecommerce";
  app.initialState["Order.exists"] = Value(false);
  app.initialState["Payment.status"] = Value("none");
  app.capabilities = {createOrder(), makePayment(), cancelCart()};
  return app;
}

const careweave::compat::CheckResult* findCheck(const CompatibilityReport& r,
                                                const std::string& name) {
  for (const auto& c : r.checks) {
    if (c.name == name) return &c;
  }
  return nullptr;
}

}  // namespace

CW_TEST_CASE(specification_pattern_positive_and_negative) {
  const ApplicationModel app = storeApp();
  const CompatEngine engine(app);
  const CompatibilityReport positive = engine.check(createOrder(), makePayment());
  CW_CHECK(positive.verdict == Verdict::COMPATIBLE);
  CW_CHECK(positive.entailment.overall == Entailment::ENTAILED);
  // The effect writes the exact variable the precondition reads, so coverage is full.
  CW_CHECK_NEAR(positive.scores.coverage, 1.0, 1e-9);
  // Effects and preconditions agree, so the signed cosine is at its maximum.
  CW_CHECK(positive.scores.signedCosine > 0.99);
  CW_CHECK(positive.scores.vectorScore > 0.99);
  CW_CHECK(!positive.hasFailed());

  const CompatibilityReport negative = engine.check(createOrder(), cancelCart());
  CW_CHECK(negative.verdict == Verdict::INCOMPATIBLE);
  CW_CHECK(negative.entailment.overall == Entailment::CONFLICT);
  CW_CHECK(!negative.rejections.empty());
  // Order.exists = true against Order.exists = false sits on the opposite side of the condition
  // space, so the signed cosine is strongly negative and the score collapses.
  CW_CHECK(negative.scores.signedCosine < -0.99);
  CW_CHECK(negative.scores.vectorScore < 0.01);
}

CW_TEST_CASE(entailment_and_io_are_independent_of_similarity) {
  const ApplicationModel app = storeApp();
  const CompatEngine engine(app);
  CapabilitySpec refund = makePayment();
  refund.id = "P2";
  refund.name = "RefundPayment";
  refund.mechanism.endpoint = "/payments/refund";
  refund.preconditions = {cond("Payment.status", ConditionOp::EQ, Value("refunded"))};
  refund.effects = {eff("Payment.status", EffectOp::SET, Value("refunded"))};

  // Refund customers have paid; the initial state has not, and CreateOrder does not pay, so the
  // precondition cannot be proven from CreateOrder effects alone.
  const CompatibilityReport unproven = engine.check(createOrder(), refund);
  CW_CHECK(unproven.verdict == Verdict::UNCERTAIN);
  CW_CHECK(unproven.entailment.overall == Entailment::POSSIBLE);
  CW_CHECK(unproven.entailment.unknown == 1);
  CW_CHECK(!unproven.hasFailed());

  // MakePayment and RefundPayment are neighbours in the same functional family (same target
  // variable, same mechanism family, overlapping text) yet compose into a contradiction, which is
  // exactly the "similarity is not composability" case: the verdict comes from the conditions,
  // not from the similarity score.
  const CompatibilityReport clashing = engine.check(makePayment(), refund);
  CW_CHECK(clashing.verdict == Verdict::INCOMPATIBLE);
  CW_CHECK(clashing.entailment.overall == Entailment::CONFLICT);
  CW_CHECK(clashing.scores.functionalSimilarity > 0.0);
  CW_CHECK(findCheck(clashing, "precondition-entailment")->outcome == Outcome::FAIL);
}

CW_TEST_CASE(io_type_mismatch_fails_and_missing_input_is_uncertain) {
  const ApplicationModel app = storeApp();
  const CompatEngine engine(app);

  CapabilitySpec c1 = createOrder();
  OutputSpec out;
  out.name = "order_id";
  out.type = "integer";
  c1.outputs = {out};

  CapabilitySpec c2 = makePayment();
  InputSpec in;
  in.name = "order_id";
  in.type = "integer";
  c2.inputs = {in};
  CompatibilityReport ok = engine.check(c1, c2);
  CW_CHECK(ok.verdict == Verdict::COMPATIBLE);
  const auto* io = findCheck(ok, "input-output");
  CW_CHECK(io != nullptr && io->outcome == Outcome::PASS);

  CapabilitySpec c3 = c2;
  c3.inputs[0].type = "string";
  CompatibilityReport bad = engine.check(c1, c3);
  CW_CHECK(bad.verdict == Verdict::INCOMPATIBLE);
  CW_CHECK(findCheck(bad, "input-output")->outcome == Outcome::FAIL);

  CapabilitySpec c4 = c2;
  c4.inputs[0].name = "patient_id";
  CompatibilityReport missing = engine.check(c1, c4);
  CW_CHECK(missing.verdict == Verdict::UNCERTAIN);
  CW_CHECK(findCheck(missing, "input-output")->outcome == Outcome::UNKNOWN);
  CW_CHECK(!missing.hasFailed());
}

CW_TEST_CASE(cost_and_risk_caps_reject_the_composition) {
  ApplicationModel app = storeApp();
  CapabilitySpec c1 = createOrder();
  CapabilitySpec c2 = makePayment();
  c1.operational.cost.money = 3.0;
  c2.operational.cost.money = 4.0;
  c1.operational.cost.timeMs = 10.0;
  c2.operational.cost.timeMs = 20.0;
  c1.operational.cost.energy = 1.0;
  c2.operational.cost.energy = 1.5;
  c1.operational.cost.resource = 0.5;
  c2.operational.cost.resource = 0.5;
  c1.operational.cost.risk = 0.1;
  c2.operational.cost.risk = 0.2;
  app.capabilities = {c1, c2};

  Context within;
  within.maxMoney = 10.0;
  within.maxTimeMs = 100.0;
  within.maxEnergy = 4.0;
  within.maxResource = 1.5;
  within.maxRisk = 0.4;
  CompatEngine ok(app, within);
  const CompatibilityReport pass = ok.check(c1, c2);
  CW_CHECK(pass.verdict == Verdict::COMPATIBLE);
  CW_CHECK(findCheck(pass, "cost-money")->outcome == Outcome::PASS);
  CW_CHECK(findCheck(pass, "risk")->outcome == Outcome::PASS);

  Context over;
  over.maxMoney = 5.0;
  CompatEngine rejects(app, over);
  const CompatibilityReport fail = rejects.check(c1, c2);
  CW_CHECK(fail.verdict == Verdict::INCOMPATIBLE);
  const auto* money = findCheck(fail, "cost-money");
  CW_CHECK(money != nullptr && money->outcome == Outcome::FAIL);
  CW_CHECK(money->detail.find("7") != std::string::npos);
  // The composed risk is 1-(1-0.1)(1-0.2) = 0.28.
  CW_CHECK(findCheck(fail, "cost-time")->outcome == Outcome::SKIP);
}

CW_TEST_CASE(reliability_floor_and_availability_window) {
  ApplicationModel app = storeApp();
  CapabilitySpec c1 = createOrder();
  CapabilitySpec c2 = makePayment();
  c1.operational.reliability = 0.9;
  c2.operational.reliability = 0.8;
  AvailabilityWindow window;
  window.days = {"mon", "tue", "wed", "thu", "fri"};
  window.fromMinutes = 9 * 60;
  window.toMinutes = 17 * 60;
  c2.operational.windowed = true;
  c2.operational.windows = {window};
  app.capabilities = {c1, c2};

  Context ctx;
  ctx.minReliability = 0.7;
  ctx.weekday = "wed";
  ctx.minutesAfterMidnight = 10 * 60;
  CompatEngine engine(app, ctx);
  const CompatibilityReport good = engine.check(c1, c2);
  CW_CHECK(good.verdict == Verdict::COMPATIBLE);
  CW_CHECK(findCheck(good, "reliability")->outcome == Outcome::PASS);
  CW_CHECK(findCheck(good, "availability")->outcome == Outcome::PASS);

  Context weekend = ctx;
  weekend.weekday = "sat";
  CompatEngine closed(app, weekend);
  const CompatibilityReport bad = closed.check(c1, c2);
  CW_CHECK(bad.verdict == Verdict::INCOMPATIBLE);
  CW_CHECK(findCheck(bad, "availability")->outcome == Outcome::FAIL);

  Context strict = ctx;
  strict.minReliability = 0.9;
  CompatEngine weak(app, strict);
  const CompatibilityReport low = weak.check(c1, c2);
  CW_CHECK(low.verdict == Verdict::INCOMPATIBLE);
  CW_CHECK(findCheck(low, "reliability")->outcome == Outcome::FAIL);

  // An unavailable capability is rejected regardless of time.
  ApplicationModel appDown = app;
  appDown.capabilities[0].operational.available = false;
  CompatEngine down(appDown, Context());
  const CompatibilityReport offline = down.check(appDown.capabilities[0], c2);
  CW_CHECK(offline.verdict == Verdict::INCOMPATIBLE);
  CW_CHECK(findCheck(offline, "availability")->outcome == Outcome::FAIL);

  // The A_i(t) form: `always: false` plus windows schedules the capability instead of withdrawing
  // it, so the window decides and the pair passes during staffed hours and fails outside them.
  ApplicationModel appScheduled = app;
  appScheduled.capabilities[1].operational.available = false;
  CompatEngine scheduled(appScheduled, ctx);
  const CompatibilityReport duringWindow = scheduled.check(c1, appScheduled.capabilities[1]);
  CW_CHECK(duringWindow.verdict == Verdict::COMPATIBLE);
  CW_CHECK(findCheck(duringWindow, "availability")->outcome == Outcome::PASS);
  CompatEngine scheduledWeekend(appScheduled, weekend);
  const CompatibilityReport outsideWindow = scheduledWeekend.check(c1, appScheduled.capabilities[1]);
  CW_CHECK(outsideWindow.verdict == Verdict::INCOMPATIBLE);
  CW_CHECK(findCheck(outsideWindow, "availability")->outcome == Outcome::FAIL);
}

CW_TEST_CASE(resources_roles_and_constraints) {
  ApplicationModel app = storeApp();
  CapabilitySpec c1 = createOrder();
  CapabilitySpec c2 = makePayment();
  c1.resources = {"orders-db"};
  c2.resources = {"payments-queue"};
  c2.roles = {"cashier"};
  app.capabilities = {c1, c2};

  Context ctx;
  ctx.enforceResources = true;
  ctx.availableResources = {"orders-db", "payments-queue"};
  ctx.enforceRoles = true;
  ctx.grantedRoles = {"cashier", "nurse"};
  CompatEngine engine(app, ctx);
  const CompatibilityReport ok = engine.check(c1, c2);
  CW_CHECK(ok.verdict == Verdict::COMPATIBLE);
  CW_CHECK(findCheck(ok, "resources")->outcome == Outcome::PASS);
  CW_CHECK(findCheck(ok, "roles")->outcome == Outcome::PASS);

  Context missing = ctx;
  missing.availableResources = {"orders-db"};
  missing.grantedRoles = {"nurse"};
  CompatEngine poor(app, missing);
  const CompatibilityReport bad = poor.check(c1, c2);
  CW_CHECK(bad.verdict == Verdict::INCOMPATIBLE);
  CW_CHECK(findCheck(bad, "resources")->outcome == Outcome::FAIL);
  CW_CHECK(findCheck(bad, "roles")->outcome == Outcome::FAIL);

  // A model constraint that the composed state violates.
  Context constrained = ctx;
  constrained.assumptions = {cond("Order.exists", ConditionOp::EQ, Value(false))};
  CompatEngine careful(app, constrained);
  const CompatibilityReport violated = careful.check(c1, c2);
  CW_CHECK(violated.verdict == Verdict::INCOMPATIBLE);
  CW_CHECK(findCheck(violated, "constraints")->outcome == Outcome::FAIL);

  Context satisfied = ctx;
  satisfied.assumptions = {cond("Payment.status", ConditionOp::NEQ, Value("refunded"))};
  CompatEngine sound(app, satisfied);
  const CompatibilityReport kept = sound.check(c1, c2);
  CW_CHECK(kept.verdict == Verdict::COMPATIBLE);
  CW_CHECK(findCheck(kept, "constraints")->outcome == Outcome::PASS);
}

CW_TEST_CASE(report_renders_and_serializes) {
  const ApplicationModel app = storeApp();
  const CompatEngine engine(app);
  const CompatibilityReport r = engine.check(createOrder(), makePayment());
  const std::string text = r.render();
  CW_CHECK(text.find("compatibility C1 -> C2: compatible") != std::string::npos);
  CW_CHECK(text.find("[pass] precondition-entailment") != std::string::npos);
  const std::string json = r.toJsonString();
  CW_CHECK(json.find("\"verdict\": \"compatible\"") != std::string::npos);
  CW_CHECK(json.find("\"earlier\": \"C1\"") != std::string::npos);
  CW_CHECK(json.find("\"vectorScore\"") != std::string::npos);

  const CompatibilityReport n = engine.check(createOrder(), cancelCart());
  CW_CHECK(n.render().find("compatibility C1 -> C3: incompatible") != std::string::npos);
  CW_CHECK(n.render().find("rejections:") != std::string::npos);
}

int main() { return careweave::testing::runAll("test_compat_engine"); }
