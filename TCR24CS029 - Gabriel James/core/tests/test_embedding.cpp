// Embedding tests: determinism, layout and dimensions, one-hot type block, signed condition
// separation, identity and distinctness, similarity against composability, goal relevance,
// the nine capability types, and the partitioned similarity view.
#include <cmath>
#include <sstream>

#include "careweave/core/types.hpp"
#include "careweave/embedding/blocks.hpp"
#include "careweave/embedding/encoders.hpp"
#include "careweave/embedding/vector.hpp"
#include "careweave/test/framework.hpp"

using careweave::core::AppState;
using careweave::core::CapabilitySpec;
using careweave::core::CapabilityType;
using careweave::core::Condition;
using careweave::core::ConditionOp;
using careweave::core::Effect;
using careweave::core::EffectOp;
using careweave::core::Goal;
using careweave::core::InputSpec;
using careweave::core::OutputSpec;
using careweave::core::Value;
using careweave::embedding::Blocks;
using careweave::embedding::EncodedCapability;
using careweave::embedding::EncodedEntity;
using careweave::embedding::Encoder;
using careweave::embedding::Vector;
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

CapabilitySpec createOrder() {
  CapabilitySpec s;
  s.id = "C1";
  s.name = "CreateOrder";
  s.description = "Create an order from the active cart";
  s.type = CapabilityType::API;
  s.mechanism.kind = CapabilityType::API;
  s.mechanism.method = "POST";
  s.mechanism.endpoint = "/api/orders";
  s.effects = {eff("Order.exists", EffectOp::SET, Value(true))};
  return s;
}

CapabilitySpec makePayment() {
  CapabilitySpec s;
  s.id = "C2";
  s.name = "MakePayment";
  s.description = "Charge the customer for the order";
  s.type = CapabilityType::API;
  s.mechanism.kind = CapabilityType::API;
  s.mechanism.method = "POST";
  s.mechanism.endpoint = "/api/payments";
  s.preconditions = {cond("Order.exists", ConditionOp::EQ, Value(true))};
  s.effects = {eff("Payment.status", EffectOp::SET, Value("paid"))};
  return s;
}

CapabilitySpec cancelCart() {
  CapabilitySpec s;
  s.id = "C3";
  s.name = "CancelCart";
  s.description = "Abandon the cart";
  s.type = CapabilityType::GUI;
  s.mechanism.kind = CapabilityType::GUI;
  s.mechanism.action = "cancel";
  s.preconditions = {cond("Order.exists", ConditionOp::EQ, Value(false))};
  return s;
}

CapabilitySpec weatherReport() {
  CapabilitySpec s;
  s.id = "W1";
  s.name = "WeatherReport";
  s.description = "Read the town forecast";
  s.type = CapabilityType::FILE;
  s.mechanism.kind = CapabilityType::FILE;
  s.mechanism.path = "/data/forecast.json";
  s.preconditions = {cond("Forecast.loaded", ConditionOp::EQ, Value(true))};
  s.effects = {eff("Forecast.temperature", EffectOp::SET, Value(21.0))};
  return s;
}

// A capability that does what MakePayment does through the GUI instead of the API.
CapabilitySpec payByGui() {
  CapabilitySpec s;
  s.id = "C2G";
  s.name = "MakePaymentPanel";
  s.description = "Charge the customer for the order";
  s.type = CapabilityType::GUI;
  s.mechanism.kind = CapabilityType::GUI;
  s.mechanism.page = "/payments";
  s.mechanism.action = "submit";
  s.preconditions = {cond("Order.exists", ConditionOp::EQ, Value(true))};
  s.effects = {eff("Payment.status", EffectOp::SET, Value("paid"))};
  return s;
}

}  // namespace

CW_TEST_CASE(vectors_are_deterministic_and_well_shaped) {
  const Encoder encoder;
  AppState state;
  state.set("Order.exists", Value(true));
  state.set("Cart.items", Value(int64_t(3)));
  Goal goal;
  goal.conditions = {cond("Order.exists", ConditionOp::EQ, Value(true))};
  const CapabilitySpec c = createOrder();

  CW_CHECK(encoder.encodeState(state) == encoder.encodeState(state));
  CW_CHECK(encoder.encodeGoal(goal) == encoder.encodeGoal(goal));
  CW_CHECK(encoder.encodeCapability(c) == encoder.encodeCapability(c));
  CW_CHECK(encoder.encodeState(state).size() == Blocks::kStateDim);
  CW_CHECK(encoder.encodeGoal(goal).size() == Blocks::kGoalDim);
  CW_CHECK(encoder.encodeCapability(c).size() == Blocks::kCapabilityDim);

  size_t width = 0;
  const EncodedCapability detailed = encoder.encodeCapabilityDetailed(c);
  for (const auto& block : Blocks::capabilityBlocks()) {
    CW_CHECK(detailed.blocks.count(block.name) == 1);
    CW_CHECK(detailed.block(block.name).size() == block.width);
    width += block.width;
  }
  CW_CHECK(width == Blocks::kCapabilityDim);
  // A different encoder instance on the same input produces the identical vector.
  const Encoder second;
  CW_CHECK(second.encodeCapability(c) == encoder.encodeCapability(c));
}

CW_TEST_CASE(type_block_is_one_hot_over_nine_types) {
  const Encoder encoder;
  const auto& types = careweave::core::allCapabilityTypes();
  CW_CHECK(types.size() == 9);
  for (size_t i = 0; i < types.size(); ++i) {
    CapabilitySpec c = createOrder();
    c.type = types[i];
    const EncodedCapability detailed = encoder.encodeCapabilityDetailed(c);
    const Vector type = detailed.block("type");
    double sum = 0.0;
    for (size_t j = 0; j < type.size(); ++j) {
      if (j == i) {
        CW_CHECK_NEAR(type[j], 1.0, 1e-12);
      } else {
        CW_CHECK_NEAR(type[j], 0.0, 1e-12);
      }
      sum += type[j];
    }
    CW_CHECK_NEAR(sum, 1.0, 1e-12);
  }
  // Two different types are orthogonal in the type block.
  CapabilitySpec api = createOrder();
  api.type = CapabilityType::API;
  CapabilitySpec gui = createOrder();
  gui.type = CapabilityType::GUI;
  const double cos = VectorMath::cosine(encoder.encodeCapabilityDetailed(api).block("type"),
                                        encoder.encodeCapabilityDetailed(gui).block("type"));
  CW_CHECK_NEAR(cos, 0.0, 1e-12);
}

CW_TEST_CASE(signed_conditions_separate_true_from_false) {
  const Encoder encoder;
  CapabilitySpec setTrue;
  setTrue.effects = {eff("Order.exists", EffectOp::SET, Value(true))};
  CapabilitySpec setFalse;
  setFalse.effects = {eff("Order.exists", EffectOp::SET, Value(false))};
  CapabilitySpec preTrue;
  preTrue.preconditions = {cond("Order.exists", ConditionOp::EQ, Value(true))};
  CapabilitySpec preFalse;
  preFalse.preconditions = {cond("Order.exists", ConditionOp::EQ, Value(false))};

  const double aligned = VectorMath::cosine(encoder.signedEffectVector(setTrue),
                                            encoder.signedPreconditionVector(preTrue));
  const double opposed = VectorMath::cosine(encoder.signedEffectVector(setTrue),
                                            encoder.signedPreconditionVector(preFalse));
  CW_CHECK(aligned > 0.9);
  CW_CHECK(opposed < -0.9);
  CW_CHECK(aligned - opposed > 1.8);
  CW_CHECK(VectorMath::cosine(encoder.signedEffectVector(setFalse),
                              encoder.signedPreconditionVector(preFalse)) > 0.9);
}

CW_TEST_CASE(similarity_identity_margin_and_distinctness) {
  const Encoder encoder;
  const EncodedEntity c1 = EncodedEntity::capability(encoder.encodeCapabilityDetailed(createOrder()));
  const EncodedEntity c1again =
      EncodedEntity::capability(encoder.encodeCapabilityDetailed(createOrder()));
  const EncodedEntity c2 =
      EncodedEntity::capability(encoder.encodeCapabilityDetailed(makePayment()));
  const EncodedEntity c3 =
      EncodedEntity::capability(encoder.encodeCapabilityDetailed(cancelCart()));
  CW_CHECK_NEAR(encoder.similarity(c1, c1again), 1.0, 1e-9);
  // CreateOrder and CancelCart both talk about the cart and the order, but their state direction
  // differs, so they must not be near identical.
  CW_CHECK(encoder.similarity(c1, c3) < 0.95);
  // Different capabilities are separated by a clear margin from identity.
  CW_CHECK(encoder.similarity(c1, c2) < 0.95);
}

CW_TEST_CASE(functional_similarity_survives_mechanism_change) {
  const Encoder encoder;
  const EncodedCapability api = encoder.encodeCapabilityDetailed(makePayment());
  const EncodedCapability gui = encoder.encodeCapabilityDetailed(payByGui());
  const double functional =
      VectorMath::cosine(api.functionalView(), gui.functionalView());
  const double implementation =
      VectorMath::cosine(api.implementationView(), gui.implementationView());
  // Same effects and preconditions: the functional view stays close.
  CW_CHECK(functional > 0.85);
  // Different mechanisms: the implementation view records the difference.
  CW_CHECK(implementation < functional);
}

CW_TEST_CASE(goal_relevance_ranks_relevant_above_irrelevant) {
  const Encoder encoder;
  Goal goal;
  goal.conditions = {cond("Order.exists", ConditionOp::EQ, Value(true))};
  const EncodedEntity g = EncodedEntity::goal(goal);
  const EncodedEntity relevant =
      EncodedEntity::capability(encoder.encodeCapabilityDetailed(createOrder()));
  const EncodedEntity clashing =
      EncodedEntity::capability(encoder.encodeCapabilityDetailed(cancelCart()));
  const EncodedEntity irrelevant =
      EncodedEntity::capability(encoder.encodeCapabilityDetailed(weatherReport()));
  const double relevantScore = encoder.similarity(g, relevant);
  const double clashingScore = encoder.similarity(g, clashing);
  const double irrelevantScore = encoder.similarity(g, irrelevant);
  CW_CHECK(relevantScore > clashingScore);
  CW_CHECK(relevantScore > irrelevantScore);
}

CW_TEST_CASE(state_goal_agreement_uses_the_shared_core) {
  const Encoder encoder;
  Goal goal;
  goal.conditions = {cond("Order.exists", ConditionOp::EQ, Value(true))};
  AppState satisfied;
  satisfied.set("Order.exists", Value(true));
  AppState unsatisfied;
  unsatisfied.set("Order.exists", Value(false));
  const double yes = encoder.similarity(EncodedEntity::state(satisfied),
                                        EncodedEntity::goal(goal));
  const double no = encoder.similarity(EncodedEntity::state(unsatisfied),
                                       EncodedEntity::goal(goal));
  CW_CHECK(yes > 0.9);
  CW_CHECK(no < yes - 0.2);
}

CW_TEST_CASE(partitioned_similarity_covers_every_block) {
  const Encoder encoder;
  const EncodedEntity c1 = EncodedEntity::capability(encoder.encodeCapabilityDetailed(createOrder()));
  const EncodedEntity c2 = EncodedEntity::capability(encoder.encodeCapabilityDetailed(makePayment()));
  const auto parts = encoder.similarityPartitioned(c1, c2);
  for (const auto& block : Blocks::capabilityBlocks()) {
    CW_CHECK(parts.count(block.name) == 1);
    CW_CHECK(parts.at(block.name) >= -1.0 - 1e-9 && parts.at(block.name) <= 1.0 + 1e-9);
  }
  CW_CHECK(parts.count("functional") == 1);
  // block() of an unknown name is empty rather than throwing.
  const EncodedCapability detailed = encoder.encodeCapabilityDetailed(createOrder());
  CW_CHECK(detailed.block("no_such_block").empty());
}

int main() { return careweave::testing::runAll("test_embedding"); }
