// Core value model tests: typed values, all condition operators, effects, availability windows,
// quality accumulation and stable numeric projection.
#include <sstream>

#include "careweave/core/types.hpp"
#include "careweave/test/framework.hpp"

using namespace careweave::core;

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
}  // namespace

CW_TEST_CASE(value_types_round_trip) {
  CW_CHECK(Value(true).type() == ValueType::BOOL);
  CW_CHECK(Value(int64_t(7)).type() == ValueType::INT);
  CW_CHECK(Value(2.5).type() == ValueType::REAL);
  CW_CHECK(Value("abc").type() == ValueType::STRING);
  CW_CHECK(Value(std::vector<std::string>{"a", "b"}).type() == ValueType::LIST);
  CW_CHECK(Value(true).toString() == "true");
  CW_CHECK(Value(int64_t(-3)).toString() == "-3");
  CW_CHECK(Value("x").toString() == "x");
  CW_CHECK(ValueType::INT == valueTypeFromString(valueTypeToString(ValueType::INT)));
}

CW_TEST_CASE(condition_operators_typed) {
  AppState s;
  s.set("n", Value(int64_t(5)));
  s.set("flag", Value(true));
  s.set("role", Value("CUSTOMER"));
  CW_CHECK(satisfies(cond("n", ConditionOp::EQ, Value(int64_t(5))), s));
  CW_CHECK(!satisfies(cond("n", ConditionOp::EQ, Value(int64_t(6))), s));
  CW_CHECK(satisfies(cond("n", ConditionOp::NEQ, Value(int64_t(6))), s));
  CW_CHECK(satisfies(cond("n", ConditionOp::GT, Value(int64_t(4))), s));
  CW_CHECK(!satisfies(cond("n", ConditionOp::GT, Value(int64_t(5))), s));
  CW_CHECK(satisfies(cond("n", ConditionOp::GTE, Value(int64_t(5))), s));
  CW_CHECK(satisfies(cond("n", ConditionOp::LT, Value(double(5.5))), s));
  CW_CHECK(satisfies(cond("n", ConditionOp::LTE, Value(int64_t(5))), s));
  CW_CHECK(satisfies(cond("flag", ConditionOp::EQ, Value(true)), s));
  CW_CHECK(satisfies(cond("role", ConditionOp::IN, Value(std::vector<std::string>{"ADMIN", "CUSTOMER"})), s));
  CW_CHECK(!satisfies(cond("role", ConditionOp::IN, Value(std::vector<std::string>{"ADMIN", "GUEST"})), s));
  // Missing variables are false for every operator except NEQ.
  CW_CHECK(!satisfies(cond("absent", ConditionOp::EQ, Value(int64_t(0))), s));
  CW_CHECK(satisfies(cond("absent", ConditionOp::NEQ, Value(int64_t(0))), s));
  // Numeric comparison across integer and real representations.
  CW_CHECK(satisfies(cond("n", ConditionOp::EQ, Value(5.0)), s));
}

CW_TEST_CASE(effects_apply_in_order) {
  AppState s;
  s.set("count", Value(int64_t(3)));
  applyEffect(eff("count", EffectOp::INCREMENT, Value(int64_t(2))), s);
  CW_CHECK(s.get("count").asInt() == 5);
  applyEffect(eff("count", EffectOp::DECREMENT, Value(int64_t(5))), s);
  CW_CHECK(s.get("count").asInt() == 0);
  applyEffect(eff("created", EffectOp::SET, Value(true)), s);
  CW_CHECK(s.get("created").asBool());
  applyEffect(eff("count", EffectOp::DELETE_, Value(0)), s);
  CW_CHECK(!s.has("count"));
  std::vector<Effect> effects{eff("a", EffectOp::SET, Value(int64_t(1))),
                              eff("a", EffectOp::INCREMENT, Value(int64_t(4)))};
  applyEffects(effects, s);
  CW_CHECK(s.get("a").asInt() == 5);
}

CW_TEST_CASE(goal_satisfaction) {
  AppState s;
  s.set("Order.exists", Value(true));
  s.set("Payment.status", Value("SUCCESS"));
  Goal g;
  g.conditions = {cond("Order.exists", ConditionOp::EQ, Value(true)),
                  cond("Payment.status", ConditionOp::EQ, Value("SUCCESS"))};
  CW_CHECK(g.isSatisfied(s));
  g.conditions.push_back(cond("Notification.sent", ConditionOp::EQ, Value(true)));
  CW_CHECK(!g.isSatisfied(s));
}

CW_TEST_CASE(availability_windows) {
  OperationalSpec always;
  CW_CHECK(always.availableAt("sun", 3));
  OperationalSpec windowed;
  windowed.windowed = true;
  windowed.available = true;
  AvailabilityWindow w;
  w.days = {"mon", "tue", "wed", "thu", "fri"};
  w.fromMinutes = 8 * 60;
  w.toMinutes = 20 * 60;
  windowed.windows.push_back(w);
  CW_CHECK(windowed.availableAt("mon", 9 * 60));
  CW_CHECK(!windowed.availableAt("mon", 21 * 60));
  CW_CHECK(!windowed.availableAt("sat", 9 * 60));
  // The A_i(t) form of a capability that is not always open: a declared window governs, the
  // static flag stays false because the capability is open inside its windows only.
  OperationalSpec windowedOnly;
  windowedOnly.windowed = true;
  windowedOnly.available = false;
  windowedOnly.windows.push_back(w);
  CW_CHECK(windowedOnly.availableAt("mon", 9 * 60));
  CW_CHECK(!windowedOnly.availableAt("mon", 21 * 60));
  CW_CHECK(!windowedOnly.availableAt("sat", 9 * 60));
  OperationalSpec disabled;
  disabled.available = false;
  CW_CHECK(!disabled.availableAt("mon", 9 * 60));
}

CW_TEST_CASE(quality_accumulation) {
  QualityAttributes a;
  a.timeMs = 100;
  a.money = 0.02;
  a.resource = 2;
  a.energy = 1.5;
  a.risk = 0.1;
  QualityAttributes b;
  b.timeMs = 50;
  b.money = 0.01;
  b.resource = 1;
  b.energy = 0.5;
  b.risk = 0.2;
  const QualityAttributes sum = a.sequentialSum(b);
  CW_CHECK_NEAR(sum.timeMs, 150, 1e-9);
  CW_CHECK_NEAR(sum.money, 0.03, 1e-12);
  CW_CHECK_NEAR(sum.resource, 3, 1e-9);
  CW_CHECK_NEAR(sum.energy, 2.0, 1e-9);
  CW_CHECK_NEAR(sum.risk, 1.0 - 0.9 * 0.8, 1e-12);
}

CW_TEST_CASE(numeric_projection_is_stable) {
  // The projection must be identical across runs and process launches; this guards the
  // determinism requirement of the embedding.
  const double a = Value("register_patient").toNumeric();
  const double b = Value("register_patient").toNumeric();
  CW_CHECK(a == b);
  CW_CHECK(a >= 0.0 && a < 1.0);
  CW_CHECK(Value("register_patient").toNumeric() != Value("admit_patient").toNumeric());
}

CW_TEST_CASE(all_nine_capability_types_round_trip) {
  const std::vector<std::string> names = {"API",      "DATABASE", "GUI",     "EVENT",
                                          "FUNCTION", "FILE",     "COMPUTATION",
                                          "MESSAGE",  "SERVICE"};
  CW_CHECK(allCapabilityTypes().size() == 9);
  for (const auto& n : names) {
    CW_CHECK(capabilityTypeToString(capabilityTypeFromString(n)) == n);
  }
}

int main() { return careweave::testing::runAll("test_types"); }
