// Composition tests: the effect fold (SET overwriting, counter accumulation, delete clearing),
// the operational laws (cost addition, risk accumulation, reliability product, window
// intersection), interface union, associativity, and the relation between the algebraically
// composed vector and the re-encoded composite.
#include <cmath>
#include <sstream>

#include "careweave/composer/composer.hpp"
#include "careweave/core/types.hpp"
#include "careweave/embedding/vector.hpp"
#include "careweave/test/framework.hpp"

using careweave::composer::Composer;
using careweave::composer::composeOperational;
using careweave::composer::netEffects;
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
using careweave::embedding::VectorMath;

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

CapabilitySpec cap(const std::string& id, const std::string& name) {
  CapabilitySpec s;
  s.id = id;
  s.name = name;
  s.type = CapabilityType::API;
  s.mechanism.kind = CapabilityType::API;
  s.mechanism.method = "POST";
  s.mechanism.endpoint = "/" + id;
  return s;
}

CapabilitySpec createOrder() {
  CapabilitySpec s = cap("C1", "CreateOrder");
  s.effects = {eff("Order.exists", EffectOp::SET, Value(true))};
  return s;
}

CapabilitySpec makePayment() {
  CapabilitySpec s = cap("C2", "MakePayment");
  s.preconditions = {cond("Order.exists", ConditionOp::EQ, Value(true))};
  s.effects = {eff("Payment.status", EffectOp::SET, Value("paid"))};
  return s;
}

CapabilitySpec shipOrder() {
  CapabilitySpec s = cap("C3", "ShipOrder");
  s.preconditions = {cond("Payment.status", ConditionOp::EQ, Value("paid"))};
  s.effects = {eff("Shipment.status", EffectOp::SET, Value("shipped"))};
  return s;
}

std::string effectsSignature(const std::vector<Effect>& effects) {
  std::string out;
  for (const auto& e : effects) {
    out += e.toString();
    out += ";";
  }
  return out;
}

// The parts of a composite that the associativity law constrains: everything but the derived
// identifiers and the mechanism notes.
std::string semanticSignature(const CapabilitySpec& s) {
  std::ostringstream os;
  os << effectsSignature(s.effects) << "|";
  for (const auto& p : s.preconditions) os << p.toString() << ";";
  os << "|";
  for (const auto& in : s.inputs) os << in.name << ":" << in.type << ";";
  os << "|";
  for (const auto& o : s.outputs) os << o.name << ":" << o.type << ";";
  os << "|";
  for (const auto& r : s.resources) os << r << ";";
  os << "|";
  for (const auto& r : s.roles) os << r << ";";
  os << "|cost " << s.operational.cost.timeMs << "," << s.operational.cost.money << ","
     << s.operational.cost.resource << "," << s.operational.cost.energy << ","
     << s.operational.cost.risk << "|rel " << s.operational.reliability << "|avail "
     << (s.operational.available ? 1 : 0) << "|windows " << s.operational.windows.size();
  return os.str();
}

}  // namespace

CW_TEST_CASE(effect_fold_laws) {
  CapabilitySpec a = cap("A", "A");
  a.effects = {eff("X", EffectOp::SET, Value(int64_t(1)))};
  CapabilitySpec b = cap("B", "B");
  b.effects = {eff("X", EffectOp::SET, Value(int64_t(2)))};
  auto net = netEffects({a, b});
  CW_CHECK(net.size() == 1);
  CW_CHECK(net[0].op == EffectOp::SET);
  CW_CHECK(net[0].value.asInt() == 2);

  // SET then INCREMENT folds into one SET.
  CapabilitySpec inc = cap("I", "I");
  inc.effects = {eff("X", EffectOp::INCREMENT, Value(int64_t(5)))};
  net = netEffects({a, inc});
  CW_CHECK(net.size() == 1);
  CW_CHECK(net[0].op == EffectOp::SET);
  CW_CHECK(net[0].value.asInt() == 6);

  // Counters accumulate and cancel.
  CapabilitySpec inc2 = cap("I2", "I2");
  inc2.effects = {eff("Y", EffectOp::INCREMENT, Value(int64_t(3)))};
  CapabilitySpec dec1 = cap("D1", "D1");
  dec1.effects = {eff("Y", EffectOp::DECREMENT, Value(int64_t(1)))};
  net = netEffects({inc2, dec1});
  CW_CHECK(net.size() == 1);
  CW_CHECK(net[0].op == EffectOp::INCREMENT);
  CW_CHECK(net[0].value.asInt() == 2);
  CapabilitySpec dec3 = cap("D3", "D3");
  dec3.effects = {eff("Y", EffectOp::DECREMENT, Value(int64_t(3)))};
  CW_CHECK(netEffects({inc2, dec3}).empty());

  // DELETE clears an earlier write; a later write clears a delete.
  CapabilitySpec del = cap("DEL", "DEL");
  del.effects = {eff("X", EffectOp::DELETE_, Value(int64_t(0)))};
  net = netEffects({a, del});
  CW_CHECK(net.size() == 1);
  CW_CHECK(net[0].op == EffectOp::DELETE_);
  net = netEffects({del, b});
  CW_CHECK(net.size() == 1);
  CW_CHECK(net[0].op == EffectOp::SET);
  CW_CHECK(net[0].value.asInt() == 2);

  // Folded output is sorted by variable name.
  CapabilitySpec multi = cap("M", "M");
  multi.effects = {eff("Z", EffectOp::SET, Value(true)), eff("A", EffectOp::SET, Value(false))};
  net = netEffects({multi});
  CW_CHECK(net.size() == 2);
  CW_CHECK(net[0].variable == "A");
  CW_CHECK(net[1].variable == "Z");
}

CW_TEST_CASE(operational_laws_add_multiply_and_intersect) {
  CapabilitySpec a = cap("A", "A");
  CapabilitySpec b = cap("B", "B");
  a.operational.cost.timeMs = 10.0;
  b.operational.cost.timeMs = 25.0;
  a.operational.cost.money = 1.5;
  b.operational.cost.money = 2.0;
  a.operational.reliability = 0.9;
  b.operational.reliability = 0.8;
  a.operational.cost.risk = 0.1;
  b.operational.cost.risk = 0.2;
  const auto op = composeOperational(a, b);
  CW_CHECK_NEAR(op.cost.timeMs, 35.0, 1e-9);
  CW_CHECK_NEAR(op.cost.money, 3.5, 1e-9);
  CW_CHECK_NEAR(op.reliability, 0.72, 1e-9);
  CW_CHECK_NEAR(op.cost.risk, 1.0 - 0.9 * 0.8, 1e-9);

  // Availability windows intersect pairwise on the shared days.
  AvailabilityWindow wide;
  wide.days = {"mon", "tue", "wed", "thu", "fri"};
  wide.fromMinutes = 9 * 60;
  wide.toMinutes = 17 * 60;
  a.operational.windowed = true;
  a.operational.windows = {wide};
  AvailabilityWindow narrow;
  narrow.days = {"wed", "sat"};
  narrow.fromMinutes = 10 * 60;
  narrow.toMinutes = 12 * 60;
  b.operational.windowed = true;
  b.operational.windows = {narrow};
  const auto windowed = composeOperational(a, b);
  CW_CHECK(windowed.windowed);
  CW_CHECK(windowed.windows.size() == 1);
  CW_CHECK(windowed.windows[0].days.size() == 1 && windowed.windows[0].days[0] == "wed");
  CW_CHECK(windowed.windows[0].fromMinutes == 10 * 60);
  CW_CHECK(windowed.windows[0].toMinutes == 12 * 60);

  // Disjoint windows compose to never available.
  AvailabilityWindow night;
  night.days = {"mon"};
  night.fromMinutes = 0;
  night.toMinutes = 60;
  b.operational.windows = {night};
  const auto disjoint = composeOperational(a, b);
  CW_CHECK(!disjoint.available);
  CW_CHECK(disjoint.windows.empty());
}

CW_TEST_CASE(composite_interface_and_associativity) {
  CapabilitySpec c1 = createOrder();
  OutputSpec orderId;
  orderId.name = "order_id";
  orderId.type = "integer";
  c1.outputs = {orderId};
  CapabilitySpec c2 = makePayment();
  InputSpec wantsOrder;
  wantsOrder.name = "order_id";
  wantsOrder.type = "integer";
  c2.inputs = {wantsOrder};
  CapabilitySpec c3 = shipOrder();
  c2.resources = {"payments-db"};
  c3.resources = {"payments-db", "shipping-queue"};
  c2.roles = {"cashier"};
  c3.roles = {"cashier", "courier"};

  const Composer composer;
  const CapabilitySpec whole = composer.composeSpec({c1, c2, c3});
  // The composite interface drops the input earlier members bind.
  CW_CHECK(whole.inputs.empty());
  CW_CHECK(whole.outputs.size() == 1);
  CW_CHECK(whole.effects.size() == 3);
  CW_CHECK(whole.resources.size() == 2);
  CW_CHECK(whole.roles.size() == 2);
  CW_CHECK(whole.id == "C1+C2+C3");

  // Associativity: both bracketings yield the same semantics.
  const CapabilitySpec left = composer.composeTwo(composer.composeTwo(c1, c2), c3);
  const CapabilitySpec right = composer.composeTwo(c1, composer.composeTwo(c2, c3));
  CW_CHECK(semanticSignature(left) == semanticSignature(right));

  // A single element composes to its own semantics; the empty sequence is the identity.
  const CapabilitySpec single = composer.composeSpec({c1});
  CW_CHECK(semanticSignature(single) == semanticSignature(c1));
  const CapabilitySpec empty = composer.composeSpec({});
  CW_CHECK(empty.effects.empty());
  CW_CHECK(empty.preconditions.empty());
  CW_CHECK(empty.id == Composer::identity().id);
}

CW_TEST_CASE(algebraic_and_reencoded_composite_vectors_agree) {
  const Composer composer;
  const CapabilitySpec c1 = createOrder();
  const CapabilitySpec c2 = makePayment();
  const CapabilitySpec c3 = shipOrder();
  const Composer::Composition abc = composer.compose({c1, c2, c3});
  CW_CHECK(abc.algebraic.size() == 259);
  CW_CHECK(abc.reencoded.size() == 259);
  // The algebra of the embedding stays close to the re-encoded composite: the two views are
  // measured against each other rather than assumed identical.
  CW_CHECK(abc.algebraicVsReencoded > 0.5);
  // The composite remains recognisably related to its members.
  CW_CHECK(abc.toFirst > 0.0);
  CW_CHECK(abc.toLast > 0.0);

  // Associativity of the vector algebra: composing the composite with c3 gives the same vector
  // whether the pair was folded first or not.
  const Composer::Composition ab = composer.compose({c1, c2});
  const auto abThenC3 = composer.compose({ab.spec, c3});
  const auto aThenBc = composer.compose({c1, composer.composeTwo(c2, c3)});
  // The re-encoded vectors are compared because the algebraic view of a composite is itself not
  // a capability tuple; the semantic signature equality is checked separately.
  CW_CHECK(VectorMath::cosine(abThenC3.reencoded, aThenBc.reencoded) > 0.99);
}

CW_TEST_CASE(composite_is_distinguishable_from_its_members) {
  const Composer composer;
  const CapabilitySpec c1 = createOrder();
  const CapabilitySpec c2 = makePayment();
  const Composer::Composition ab = composer.compose({c1, c2});
  const auto embedder = careweave::embedding::Encoder();
  const auto v1 = embedder.encodeCapability(c1);
  const auto v2 = embedder.encodeCapability(c2);
  const double toComposite1 = VectorMath::cosine(v1, ab.reencoded);
  const double toComposite2 = VectorMath::cosine(v2, ab.reencoded);
  const double memberToMember = VectorMath::cosine(v1, v2);
  // The composite sits between its members, closer to neither extreme, and is not a copy of
  // either member.
  CW_CHECK(toComposite1 < 0.999);
  CW_CHECK(toComposite2 < 0.999);
  CW_CHECK(std::fabs(toComposite1 - toComposite2) < 0.5);
  CW_CHECK(memberToMember < 0.99);
}

int main() { return careweave::testing::runAll("test_composer"); }
