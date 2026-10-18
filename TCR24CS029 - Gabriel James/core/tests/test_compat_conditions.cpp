// Abstract state domain tests: singleton seeding, interval arithmetic over effects, enum sets,
// boundary handling for all comparison operators, and the CreateOrder / MakePayment / CancelCart
// entailment pattern from the specification.
#include <sstream>

#include "careweave/compat/conditions.hpp"
#include "careweave/core/types.hpp"
#include "careweave/test/framework.hpp"

using careweave::compat::Domain;
using careweave::compat::DomainState;
using careweave::compat::Entailment;
using careweave::compat::EntailmentReport;
namespace compat = careweave::compat;
using careweave::core::AppState;
using careweave::core::Condition;
using careweave::core::ConditionOp;
using careweave::core::Effect;
using careweave::core::EffectOp;
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

const double kEps = 1e-9;

}  // namespace

CW_TEST_CASE(domain_singletons_cover_every_value_kind) {
  CW_CHECK(Domain::singleton(Value(true)).toString() == "true");
  CW_CHECK(Domain::singleton(Value(false)).toString() == "false");
  CW_CHECK(Domain::singleton(Value(int64_t(4))).toString() == "[4,4] (integer)");
  CW_CHECK(Domain::singleton(Value(2.5)).toString() == "[2.5,2.5] (real)");
  CW_CHECK(Domain::singleton(Value("paid")).toString() == "{paid}");
  CW_CHECK(Domain::singleton(Value(std::vector<std::string>{"a", "b"})).toString() == "{a,b}");
  CW_CHECK(Domain::universe().toString() == "any");
  CW_CHECK(Domain::booleanBoth().toString() == "{true,false}");
}

CW_TEST_CASE(boolean_equality_entailed_or_conflict) {
  const Domain yes = Domain::boolean(true);
  const Domain no = Domain::boolean(false);
  CW_CHECK(compat::evaluate(yes, cond("Order.exists", ConditionOp::EQ, Value(true))) ==
           Entailment::ENTAILED);
  CW_CHECK(compat::evaluate(yes, cond("Order.exists", ConditionOp::NEQ, Value(true))) ==
           Entailment::CONFLICT);
  CW_CHECK(compat::evaluate(no, cond("Order.exists", ConditionOp::EQ, Value(true))) ==
           Entailment::CONFLICT);
  CW_CHECK(compat::evaluate(no, cond("Order.exists", ConditionOp::NEQ, Value(true))) ==
           Entailment::ENTAILED);
  CW_CHECK(compat::evaluate(Domain::booleanBoth(), cond("Flag", ConditionOp::EQ, Value(true))) ==
           Entailment::POSSIBLE);
}

CW_TEST_CASE(closed_interval_boundaries_entail) {
  const Domain d = Domain::interval(10.0, 20.0, false);
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::GTE, Value(10.0))) ==
           Entailment::ENTAILED);
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::LTE, Value(20.0))) ==
           Entailment::ENTAILED);
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::GT, Value(20.0))) == Entailment::CONFLICT);
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::LT, Value(10.0))) == Entailment::CONFLICT);
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::GTE, Value(15.0))) ==
           Entailment::POSSIBLE);
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::LTE, Value(15.0))) ==
           Entailment::POSSIBLE);
  // Tolerance: a bound within kEps of the interval edge still entails.
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::GTE, Value(10.0 - kEps / 2))) ==
           Entailment::ENTAILED);
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::LTE, Value(20.0 + kEps / 2))) ==
           Entailment::ENTAILED);
  // Equality inside the interval is possible, equality outside is a conflict.
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::EQ, Value(15.0))) == Entailment::POSSIBLE);
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::EQ, Value(25.0))) == Entailment::CONFLICT);
  // NEQ is entailed outside the interval and possible inside.
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::NEQ, Value(25.0))) == Entailment::ENTAILED);
  CW_CHECK(compat::evaluate(d, cond("x", ConditionOp::NEQ, Value(15.0))) == Entailment::POSSIBLE);
}

CW_TEST_CASE(open_bounds_exclude_endpoints) {
  Domain d = Domain::interval(0.0, 1.0, false);
  d.loOpen = true;
  d.hiOpen = true;
  CW_CHECK(compat::evaluate(d, cond("p", ConditionOp::EQ, Value(0.0))) == Entailment::CONFLICT);
  CW_CHECK(compat::evaluate(d, cond("p", ConditionOp::EQ, Value(1.0))) == Entailment::CONFLICT);
  CW_CHECK(compat::evaluate(d, cond("p", ConditionOp::GT, Value(0.0))) == Entailment::ENTAILED);
  CW_CHECK(compat::evaluate(d, cond("p", ConditionOp::LT, Value(1.0))) == Entailment::ENTAILED);
}

CW_TEST_CASE(enum_set_membership) {
  const Domain d = Domain::enumerated({"red", "green", "blue"});
  CW_CHECK(compat::evaluate(d, cond("choice", ConditionOp::IN,
                                    Value(std::vector<std::string>{"red", "green", "blue"}))) ==
           Entailment::ENTAILED);
  CW_CHECK(compat::evaluate(d, cond("choice", ConditionOp::IN,
                                    Value(std::vector<std::string>{"red", "green"}))) ==
           Entailment::POSSIBLE);
  CW_CHECK(compat::evaluate(d, cond("choice", ConditionOp::IN,
                                    Value(std::vector<std::string>{"yellow"}))) ==
           Entailment::CONFLICT);
  CW_CHECK(compat::evaluate(d, cond("choice", ConditionOp::EQ, Value("green"))) ==
           Entailment::POSSIBLE);
  CW_CHECK(compat::evaluate(d, cond("choice", ConditionOp::EQ, Value("yellow"))) ==
           Entailment::CONFLICT);
}

CW_TEST_CASE(increment_and_decrement_shift_intervals) {
  AppState initial;
  initial.set("Cart.total", Value(0.0));
  initial.set("Cart.items", Value(int64_t(3)));
  const std::vector<Effect> effects = {
      eff("Cart.total", EffectOp::INCREMENT, Value(10.0)),
      eff("Cart.total", EffectOp::INCREMENT, Value(10.0)),
      eff("Cart.items", EffectOp::DECREMENT, Value(int64_t(1))),
  };
  const DomainState after = DomainState::apply(initial, effects);
  CW_CHECK(after.get("Cart.total").toString() == "[20,20] (real)");
  CW_CHECK(after.get("Cart.items").toString() == "[2,2] (integer)");
  const EntailmentReport report =
      compat::entails(initial, effects,
                      {cond("Cart.total", ConditionOp::GTE, Value(15.0)),
                       cond("Cart.items", ConditionOp::GTE, Value(int64_t(1)))});
  CW_CHECK(report.overall == Entailment::ENTAILED);
  CW_CHECK(report.entailed == 2);
}

CW_TEST_CASE(delete_clears_the_binding_to_universe) {
  AppState initial;
  initial.set("Session.token", Value("abc"));
  const std::vector<Effect> effects = {eff("Session.token", EffectOp::DELETE_, Value(0))};
  const DomainState after = DomainState::apply(initial, effects);
  CW_CHECK(after.get("Session.token").kind == Domain::Kind::UNIVERSE);
  CW_CHECK(compat::evaluate(after.get("Session.token"),
                            cond("Session.token", ConditionOp::EQ, Value("abc"))) ==
           Entailment::UNKNOWN);
}

CW_TEST_CASE(unconstrained_variables_report_unknown) {
  AppState initial;
  initial.set("Order.exists", Value(false));
  const EntailmentReport report = compat::entails(
      initial, {}, {cond("Shipment.tracking", ConditionOp::EQ, Value("TRK-1"))});
  // The single precondition is unknown, so the overall verdict cannot be stronger than possible.
  CW_CHECK(report.overall == Entailment::POSSIBLE);
  CW_CHECK(report.unknown == 1);
  CW_CHECK(report.items.size() == 1);
  CW_CHECK(report.items[0].explanation == "Shipment.tracking in any -> unknown");
}

CW_TEST_CASE(createorder_makepayment_entailed) {
  // Initial state of the store application: no order exists yet.
  AppState initial;
  initial.set("Order.exists", Value(false));
  initial.set("Payment.status", Value("none"));
  // CreateOrder effects and MakePayment preconditions as declared in the specification sheet.
  const std::vector<Effect> createOrder = {
      eff("Order.exists", EffectOp::SET, Value(true)),
      eff("Order.number", EffectOp::SET, Value("ORD-1001")),
  };
  const std::vector<Condition> makePaymentPre = {
      cond("Order.exists", ConditionOp::EQ, Value(true)),
  };
  const EntailmentReport report = compat::entails(initial, createOrder, makePaymentPre);
  CW_CHECK(report.overall == Entailment::ENTAILED);
  CW_CHECK(report.items.size() == 1);
  CW_CHECK(report.items[0].explanation == "Order.exists in true -> entailed");
}

CW_TEST_CASE(createorder_cancelcart_conflict) {
  AppState initial;
  initial.set("Order.exists", Value(false));
  const std::vector<Effect> createOrder = {
      eff("Order.exists", EffectOp::SET, Value(true)),
  };
  const std::vector<Condition> cancelCartPre = {
      cond("Order.exists", ConditionOp::EQ, Value(false)),
  };
  const EntailmentReport report = compat::entails(initial, createOrder, cancelCartPre);
  CW_CHECK(report.overall == Entailment::CONFLICT);
  CW_CHECK(report.conflicts == 1);
  CW_CHECK(report.items[0].explanation == "Order.exists in true -> conflict");
}

CW_TEST_CASE(empty_precondition_set_is_trivially_entailed) {
  AppState initial;
  const EntailmentReport report = compat::entails(initial, {}, {});
  CW_CHECK(report.overall == Entailment::ENTAILED);
  CW_CHECK(report.items.empty());
}

CW_TEST_CASE(conditions_conflict_detects_mutual_exclusion) {
  const std::vector<Condition> createOrder = {cond("Order.exists", ConditionOp::EQ, Value(true))};
  const std::vector<Condition> cancelCart = {cond("Order.exists", ConditionOp::EQ, Value(false))};
  CW_CHECK(compat::conditionsConflict(createOrder, cancelCart));
  CW_CHECK(!compat::conditionsConflict(createOrder, createOrder));
  CW_CHECK(!compat::conditionsConflict(cancelCart, cancelCart));
  // Two different pinned values for the same variable contradict each other.
  CW_CHECK(compat::conditionsConflict({cond("Review.text", ConditionOp::EQ, Value("ok"))},
                                      {cond("Review.text", ConditionOp::EQ, Value("bad"))}));
  // An inequality and an equality on the same value contradict each other.
  CW_CHECK(compat::conditionsConflict({cond("Review.text", ConditionOp::EQ, Value("ok"))},
                                      {cond("Review.text", ConditionOp::NEQ, Value("ok"))}));
  // Complementary conditions on different values are satisfiable together.
  CW_CHECK(!compat::conditionsConflict({cond("Review.text", ConditionOp::EQ, Value("ok"))},
                                       {cond("Review.text", ConditionOp::NEQ, Value("bad"))}));
  // Disjoint numeric bounds contradict; overlapping ones do not.
  CW_CHECK(compat::conditionsConflict({cond("Cart.total", ConditionOp::GTE, Value(10.0))},
                                      {cond("Cart.total", ConditionOp::LT, Value(5.0))}));
  CW_CHECK(!compat::conditionsConflict({cond("Cart.total", ConditionOp::GTE, Value(10.0))},
                                       {cond("Cart.total", ConditionOp::LT, Value(15.0))}));
  // Intervals that meet only at an open endpoint are empty.
  CW_CHECK(compat::conditionsConflict({cond("Cart.total", ConditionOp::GT, Value(10.0))},
                                      {cond("Cart.total", ConditionOp::LTE, Value(10.0))}));
  // Membership shrinking keeps satisfiable sets alive and empties disjoint ones.
  CW_CHECK(!compat::conditionsConflict(
      {cond("Status", ConditionOp::IN, Value(std::vector<std::string>{"paid", "shipped"}))},
      {cond("Status", ConditionOp::IN, Value(std::vector<std::string>{"shipped", "done"}))}));
  CW_CHECK(compat::conditionsConflict(
      {cond("Status", ConditionOp::IN, Value(std::vector<std::string>{"paid", "shipped"}))},
      {cond("Status", ConditionOp::IN, Value(std::vector<std::string>{"done"}))}));
}

CW_TEST_CASE(entailment_report_renders_every_item) {
  AppState initial;
  initial.set("Order.exists", Value(false));
  const std::vector<Effect> effects = {eff("Order.exists", EffectOp::SET, Value(true))};
  const EntailmentReport report =
      compat::entails(initial, effects,
                      {cond("Order.exists", ConditionOp::EQ, Value(true)),
                       cond("Order.exists", ConditionOp::EQ, Value(false))});
  CW_CHECK(report.overall == Entailment::CONFLICT);
  CW_CHECK(report.entailed == 1);
  CW_CHECK(report.conflicts == 1);
  const std::string rendered = report.render();
  CW_CHECK(rendered.find("overall conflict") != std::string::npos);
  CW_CHECK(rendered.find("Order.exists = true : Order.exists in true -> entailed") !=
           std::string::npos);
  CW_CHECK(rendered.find("Order.exists = false : Order.exists in true -> conflict") !=
           std::string::npos);
}

int main() { return careweave::testing::runAll("test_compat_conditions"); }
