#include "careweave/embedding/encoders.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <sstream>

namespace careweave {
namespace embedding {

namespace {

// Operator one-hot hashed into the structured sub-block.
std::string operatorFeature(const std::string& prefix, const std::string& op) {
  return prefix + ":" + op;
}

std::string joinWith(const std::vector<std::string>& parts, const std::string& sep) {
  std::string out;
  for (size_t i = 0; i < parts.size(); ++i) {
    if (i) out += sep;
    out += parts[i];
  }
  return out;
}

// Cosine that treats two identically empty blocks as a structural match instead of the
// undefined 0.0 of a zero-length vector, so a capability compared with itself scores exactly 1
// in every weighting even when some of its blocks carry no content (no inputs, no
// preconditions). One empty and one populated block stays a mismatch at 0.0.
double blockCosine(const Vector& a, const Vector& b) {
  const bool aEmpty = a.empty() || VectorMath::norm(a) <= 1e-12;
  const bool bEmpty = b.empty() || VectorMath::norm(b) <= 1e-12;
  if (aEmpty && bEmpty) return 1.0;
  if (aEmpty || bEmpty) return 0.0;
  return VectorMath::cosine(a, b);
}

}  // namespace

// ---- EncodedCapability ----

Vector EncodedCapability::block(const std::string& blockName) const {
  auto it = blocks.find(blockName);
  if (it != blocks.end()) return it->second;
  return Vector();
}

Vector EncodedCapability::functionalView() const {
  std::vector<Vector> parts{block("preconditions"), block("effects"), block("delta"),
                            block("inputs"), block("outputs")};
  return VectorMath::mean(parts);
}

Vector EncodedCapability::implementationView() const {
  std::vector<Vector> parts{block("type"), block("mechanism"), block("resources"),
                            block("quality")};
  return VectorMath::mean(parts);
}

Vector EncodedCapability::conditionView() const {
  const Vector pre = block("preconditions");
  const Vector eff = block("effects");
  if (pre.empty()) return eff;
  if (eff.empty()) return pre;
  Vector combined(pre.size(), 0.0);
  for (size_t i = 0; i < pre.size(); ++i) {
    const double e = i < eff.size() ? eff[i] : 0.0;
    combined[i] = 0.5 * (pre[i] + e);
  }
  return VectorMath::normalize(combined);
}

// ---- EncodedEntity ----

EncodedEntity EncodedEntity::state(const core::AppState& s, const std::string& label) {
  EncodedEntity e;
  e.kind = Kind::STATE;
  e.label = label;
  const Encoder encoder;
  e.vector = encoder.encodeState(s);
  e.blocks["core"] = encoder.stateCore(s);
  e.blocks["full"] = e.vector;
  return e;
}

EncodedEntity EncodedEntity::goal(const core::Goal& g, const std::string& label) {
  EncodedEntity e;
  e.kind = Kind::GOAL;
  e.label = label;
  const Encoder encoder;
  e.vector = encoder.encodeGoal(g);
  e.blocks["core"] = encoder.goalCore(g);
  e.blocks["full"] = e.vector;
  return e;
}

EncodedEntity EncodedEntity::capability(const EncodedCapability& c) {
  EncodedEntity e;
  e.kind = Kind::CAPABILITY;
  e.label = c.id.empty() ? c.name : c.id;
  e.vector = c.vector;
  e.blocks = c.blocks;
  return e;
}

// ---- Encoder: helpers ----

double Encoder::signedValue(const core::Value& value) {
  switch (value.type()) {
    case core::ValueType::BOOL:
      return value.asBool() ? 1.0 : -1.0;
    case core::ValueType::INT:
    case core::ValueType::REAL:
      return std::tanh(value.asDouble() / 100.0);
    case core::ValueType::STRING:
    case core::ValueType::ENUM: {
      const double projection = value.toNumeric();  // [0,1)
      return 2.0 * projection - 1.0;
    }
    case core::ValueType::LIST: {
      const auto& items = value.asList();
      if (items.empty()) return 0.0;
      double sum = 0.0;
      for (const auto& item : items) sum += signedValue(core::Value(item));
      return sum / static_cast<double>(items.size());
    }
  }
  return 0.0;
}

Vector Encoder::conditionSpaceFromFeatures(const std::vector<Feature>& textFeatures,
                                          const std::vector<Feature>& structFeatures) const {
  const Vector text = TextFeatures::project(textFeatures, Blocks::kCondTextDim,
                                            Blocks::kConditionSeed);
  const Vector structured = TextFeatures::project(structFeatures, Blocks::kCondStructDim,
                                                  Blocks::kConditionSeed);
  return VectorMath::concat(text, structured);
}

Vector Encoder::encodeConditionBlock(const std::vector<core::Condition>& conditions) const {
  std::vector<Feature> text;
  std::vector<Feature> structured;
  for (const auto& c : conditions) {
    const auto tf = TextFeatures::featuresForText(c.variable);
    text.insert(text.end(), tf.begin(), tf.end());
    if (c.value.type() == core::ValueType::STRING) {
      const auto vf = TextFeatures::featuresForText(c.value.asString());
      text.insert(text.end(), vf.begin(), vf.end());
    }
    for (const auto& v : c.value.asList()) {
      const auto vf = TextFeatures::featuresForText(v);
      text.insert(text.end(), vf.begin(), vf.end());
    }
    // Structured: the signed variable identity carries the conflict information, the operator
    // tells comparison kinds apart, and the exact value keeps enum members distinguishable.
    const double idf = Lexicon::instance().idf(joinWith(TextFeatures::tokenize(c.variable), "_"));
    structured.push_back({"s:" + c.variable, signedValue(c.value) * (0.5 + 0.5 * idf)});
    structured.push_back({operatorFeature("op", core::conditionOpToString(c.op)), 0.3});
    structured.push_back({"ex:" + c.variable + "#" + c.value.toString(), 0.45});
    if (c.value.type() == core::ValueType::INT || c.value.type() == core::ValueType::REAL) {
      structured.push_back({"mag:" + c.variable,
                            std::tanh(std::fabs(c.value.asDouble()) / 100.0)});
    }
  }
  return conditionSpaceFromFeatures(text, structured);
}

Vector Encoder::encodeEffectBlock(const std::vector<core::Effect>& effects,
                                 const std::string* nameHint) const {
  std::vector<Feature> text;
  std::vector<Feature> structured;
  for (const auto& e : effects) {
    const auto tf = TextFeatures::featuresForText(e.variable);
    text.insert(text.end(), tf.begin(), tf.end());
    if (e.value.type() == core::ValueType::STRING) {
      const auto vf = TextFeatures::featuresForText(e.value.asString());
      text.insert(text.end(), vf.begin(), vf.end());
    }
    double signedMagnitude = signedValue(e.value);
    switch (e.op) {
      case core::EffectOp::INCREMENT:
        signedMagnitude = std::fabs(signedMagnitude);
        break;
      case core::EffectOp::DECREMENT:
        signedMagnitude = -std::fabs(signedMagnitude);
        break;
      case core::EffectOp::DELETE_:
        signedMagnitude = -1.0;
        break;
      case core::EffectOp::SET:
        break;
    }
    structured.push_back({"s:" + e.variable, signedMagnitude});
    structured.push_back({operatorFeature("eop", core::effectOpToString(e.op)), 0.3});
    structured.push_back({"ex:" + e.variable + "#" + e.value.toString(), 0.45});
  }
  if (nameHint && !nameHint->empty()) {
    const auto nf = TextFeatures::featuresForText(*nameHint);
    text.insert(text.end(), nf.begin(), nf.end());
  }
  return conditionSpaceFromFeatures(text, structured);
}

Vector Encoder::encodeVariableIdentity(const std::string& variable) const {
  return TextFeatures::encodeText(variable, Blocks::kCondTextDim, Blocks::kConditionSeed);
}

Vector Encoder::encodeFieldIdentity(const std::string& name, const std::string& type,
                                   const std::string& domain,
                                   const std::vector<std::string>& domainValues) const {
  // The text part carries the field name only and is scaled above the structured part. Every
  // string field shares the type and domain features, so with the type words inside the text and
  // an unscaled structure, two unrelated string fields would cosine near 1.0 and swamp the
  // vocabulary signal the mapper needs (track_id against mrn must not read as a field match just
  // because both are strings). Type and domain still contribute through the structured part,
  // where a mismatch pulls the cosine down instead of a shared boilerplate pushing it up.
  const Vector text =
      VectorMath::scale(TextFeatures::encodeText(name, Blocks::kIoTextDim, Blocks::kIoSeed), 2.0);
  std::vector<Feature> structured;
  structured.push_back({"itype:" + type, 0.5});
  structured.push_back({"idomain:" + domain, 0.3});
  for (const auto& v : domainValues) {
    structured.push_back({"ival:" + v, 0.5});
  }
  const Vector structuredVector =
      TextFeatures::project(structured, Blocks::kIoStructDim, Blocks::kIoSeed);
  return VectorMath::concat(text, structuredVector);
}

Vector Encoder::stateCore(const core::AppState& state) const {
  std::vector<Feature> text;
  std::vector<Feature> structured;
  for (const auto& kv : state.all()) {
    const auto tf = TextFeatures::featuresForText(kv.first);
    text.insert(text.end(), tf.begin(), tf.end());
    if (kv.second.type() == core::ValueType::STRING) {
      const auto vf = TextFeatures::featuresForText(kv.second.asString());
      text.insert(text.end(), vf.begin(), vf.end());
    }
    structured.push_back({"s:" + kv.first, signedValue(kv.second)});
    structured.push_back({"ex:" + kv.first + "#" + kv.second.toString(), 0.45});
    if (kv.second.isNumeric()) {
      structured.push_back({"mag:" + kv.first, std::tanh(std::fabs(kv.second.asDouble()) / 100.0)});
    }
  }
  return conditionSpaceFromFeatures(text, structured);
}

Vector Encoder::goalCore(const core::Goal& goal) const {
  std::vector<Feature> text;
  std::vector<Feature> structured;
  for (const auto& c : goal.conditions) {
    const auto tf = TextFeatures::featuresForText(c.variable);
    text.insert(text.end(), tf.begin(), tf.end());
    if (c.value.type() == core::ValueType::STRING) {
      const auto vf = TextFeatures::featuresForText(c.value.asString());
      text.insert(text.end(), vf.begin(), vf.end());
    }
    structured.push_back({"s:" + c.variable, signedValue(c.value)});
    structured.push_back({operatorFeature("op", core::conditionOpToString(c.op)), 0.3});
    structured.push_back({"ex:" + c.variable + "#" + c.value.toString(), 0.45});
  }
  return conditionSpaceFromFeatures(text, structured);
}

// ---- Encoder: the five interface operations ----

Vector Encoder::encodeState(const core::AppState& state) const {
  const Vector core = stateCore(state);
  // Numeric block: signed magnitudes of numeric bindings.
  std::vector<Feature> numeric;
  std::vector<Feature> coverage;
  for (const auto& kv : state.all()) {
    coverage.push_back({"p:" + kv.first, 1.0});
    if (kv.second.isNumeric()) {
      const double scale = std::fabs(kv.second.asDouble()) > 1.0 ? 100.0 : 1.0;
      numeric.push_back({"n:" + kv.first,
                         std::tanh(kv.second.asDouble() / scale)});
    } else if (kv.second.type() == core::ValueType::BOOL) {
      numeric.push_back({"n:" + kv.first, kv.second.asBool() ? 1.0 : -1.0});
    } else {
      numeric.push_back({"n:" + kv.first, signedValue(kv.second)});
    }
  }
  const Vector numericVector =
      TextFeatures::project(numeric, 32, Blocks::kStateValueSeed);
  const Vector coverageVector =
      TextFeatures::project(coverage, 32, Blocks::kConditionSeed + 0x51ULL);
  return VectorMath::concat(core, VectorMath::concat(numericVector, coverageVector));
}

Vector Encoder::encodeGoal(const core::Goal& goal) const {
  const Vector core = goalCore(goal);
  std::vector<Feature> values;
  std::vector<Feature> mask;
  for (const auto& c : goal.conditions) {
    mask.push_back({"p:" + c.variable, 1.0});
    if (c.value.isNumeric()) {
      values.push_back({"n:" + c.variable, std::tanh(c.value.asDouble() / 100.0)});
    } else {
      values.push_back({"n:" + c.variable, signedValue(c.value)});
    }
  }
  const Vector valueVector = TextFeatures::project(values, 32, Blocks::kStateValueSeed);
  const Vector maskVector =
      TextFeatures::project(mask, 32, Blocks::kConditionSeed + 0x51ULL);
  return VectorMath::concat(core, VectorMath::concat(valueVector, maskVector));
}

EncodedCapability Encoder::encodeCapabilityDetailed(const core::CapabilitySpec& capability) const {
  EncodedCapability out;
  out.id = capability.id;
  out.name = capability.name;
  out.spec = capability;

  // phi_type: one-hot over the nine capability types.
  Vector type(Blocks::kTypeDim, 0.0);
  const auto& types = core::allCapabilityTypes();
  for (size_t i = 0; i < types.size(); ++i) {
    if (types[i] == capability.type) type[i] = 1.0;
  }

  // phi_mech: implementation detail text, hashed into the mechanism block.
  std::vector<std::string> mechParts = {
      capability.mechanism.method,    capability.mechanism.endpoint,
      capability.mechanism.operation, capability.mechanism.table,
      capability.mechanism.action,    capability.mechanism.component,
      capability.mechanism.page,      capability.mechanism.trigger,
      capability.mechanism.handler,   capability.mechanism.topic,
      capability.mechanism.queue,     capability.mechanism.function,
      capability.mechanism.path,      capability.mechanism.expression,
      capability.mechanism.service,   capability.name};
  const Vector mechanism =
      TextFeatures::encodeText(joinWith(mechParts, " "), Blocks::kMechDim, Blocks::kMechSeed);

  // phi_in: mean of per-field vectors, plus the fraction of required inputs.
  std::vector<Vector> inputVectors;
  for (const auto& in : capability.inputs) {
    inputVectors.push_back(encodeFieldIdentity(in.name, in.type, in.domain, in.domainValues));
  }
  Vector inputs(Blocks::kInDim, 0.0);
  if (!inputVectors.empty()) {
    inputs = VectorMath::mean(inputVectors);
    const double requiredFraction = static_cast<double>(
                                        std::count_if(capability.inputs.begin(), capability.inputs.end(),
                                                      [](const core::InputSpec& i) { return i.required; })) /
                                    static_cast<double>(capability.inputs.size());
    inputs[Blocks::kIoTextDim] += requiredFraction;
    inputs = VectorMath::normalize(inputs);
  }

  // phi_out: mean of per-field vectors.
  std::vector<Vector> outputVectors;
  for (const auto& o : capability.outputs) {
    outputVectors.push_back(encodeFieldIdentity(o.name, o.type, o.domain, o.domainValues));
  }
  const Vector outputs = outputVectors.empty() ? Vector(Blocks::kOutDim, 0.0)
                                              : VectorMath::normalize(VectorMath::mean(outputVectors));

  // phi_res: hashed resource identifiers.
  std::vector<Feature> resourceFeatures;
  for (const auto& r : capability.resources) {
    const auto f = TextFeatures::featuresForText(r);
    resourceFeatures.insert(resourceFeatures.end(), f.begin(), f.end());
  }
  const Vector resources =
      TextFeatures::project(resourceFeatures, Blocks::kResDim, Blocks::kResourceSeed);

  // phi_Q: normalised quality block. Reliability and availability appear here and again in the
  // dedicated scalar blocks; the separate AttributeVector in the operational model keeps the
  // exact values for constraint enforcement.
  Vector quality(Blocks::kQDim, 0.0);
  quality[0] = std::tanh(std::log1p(std::max(0.0, capability.operational.cost.timeMs)) / 6.0);
  quality[1] = std::tanh(capability.operational.cost.money / 10.0);
  quality[2] = std::tanh(capability.operational.cost.resource / 10.0);
  quality[3] = std::min(1.0, std::max(0.0, capability.operational.cost.risk));
  quality[4] = std::tanh(capability.operational.cost.energy / 10.0);
  quality[5] = std::min(1.0, capability.operational.cost.timeMs / 1000.0);
  quality[6] = capability.operational.reliability;
  quality[7] = capability.operational.available ? 1.0 : 0.0;

  // phi_delta: summary statistics of the state change plus a hashed signed variable block.
  Vector delta(Blocks::kDeltaDim, 0.0);
  double signedSum = 0.0, trueCount = 0.0, falseCount = 0.0, numericCount = 0.0, counterCount = 0.0,
         stringCount = 0.0;
  std::vector<Feature> deltaFeatures;
  for (const auto& e : capability.effects) {
    const double sv = signedValue(e.value);
    if (e.op == core::EffectOp::INCREMENT) {
      signedSum += std::fabs(sv);
    } else if (e.op == core::EffectOp::DECREMENT) {
      signedSum -= std::fabs(sv);
    } else if (e.op == core::EffectOp::DELETE_) {
      signedSum -= 1.0;
    } else {
      signedSum += sv;
    }
    if (e.op == core::EffectOp::INCREMENT || e.op == core::EffectOp::DECREMENT) counterCount += 1;
    if (e.value.type() == core::ValueType::BOOL) {
      if (e.value.asBool()) trueCount += 1;
      else falseCount += 1;
    } else if (e.value.isNumeric()) {
      numericCount += 1;
    } else {
      stringCount += 1;
    }
    const double sign = (e.op == core::EffectOp::DECREMENT || e.op == core::EffectOp::DELETE_)
                            ? -std::fabs(sv)
                            : sv;
    deltaFeatures.push_back({"d:" + e.variable, sign});
  }
  const double effectCount = static_cast<double>(capability.effects.size());
  const double total = std::max(1.0, effectCount);
  delta[0] = std::tanh(signedSum);
  delta[1] = std::min(1.0, effectCount / 8.0);
  delta[2] = trueCount / total;
  delta[3] = falseCount / total;
  delta[4] = numericCount / total;
  delta[5] = counterCount / total;
  delta[6] = stringCount / total;
  delta[7] = std::min(1.0, static_cast<double>(capability.preconditions.size()) / 6.0);
  const Vector deltaHashed =
      TextFeatures::project(deltaFeatures, Blocks::kDeltaDim - 8, Blocks::kDeltaSeed);
  for (size_t i = 0; i < deltaHashed.size(); ++i) delta[8 + i] = deltaHashed[i];

  out.blocks["type"] = type;
  out.blocks["mechanism"] = mechanism;
  out.blocks["inputs"] = inputs;
  out.blocks["outputs"] = outputs;
  out.blocks["preconditions"] = encodeConditionBlock(capability.preconditions);
  out.blocks["effects"] = encodeEffectBlock(capability.effects, &capability.name);
  out.blocks["delta"] = delta;
  out.blocks["resources"] = resources;
  out.blocks["quality"] = quality;
  out.blocks["reliability"] = Vector{capability.operational.reliability};
  out.blocks["availability"] = Vector{capability.operational.available ? 1.0 : 0.0};

  Vector unified;
  for (const auto& spec : Blocks::capabilityBlocks()) {
    const Vector block = out.blocks[spec.name];
    unified.insert(unified.end(), block.begin(), block.end());
  }
  out.vector = unified;
  return out;
}

Vector Encoder::encodeCapability(const core::CapabilitySpec& capability) const {
  return encodeCapabilityDetailed(capability).vector;
}

Vector Encoder::signedPreconditionVector(const core::CapabilitySpec& capability) const {
  std::vector<Feature> features;
  for (const auto& c : capability.preconditions) {
    features.push_back({"s:" + c.variable, signedValue(c.value)});
  }
  return TextFeatures::project(features, Blocks::kCondStructDim, Blocks::kConditionSeed);
}

Vector Encoder::signedEffectVector(const core::CapabilitySpec& capability) const {
  std::vector<Feature> features;
  for (const auto& e : capability.effects) {
    double sv = signedValue(e.value);
    if (e.op == core::EffectOp::INCREMENT) sv = std::fabs(sv);
    else if (e.op == core::EffectOp::DECREMENT) sv = -std::fabs(sv);
    else if (e.op == core::EffectOp::DELETE_) sv = -1.0;
    features.push_back({"s:" + e.variable, sv});
  }
  return TextFeatures::project(features, Blocks::kCondStructDim, Blocks::kConditionSeed);
}

double Encoder::variableCoverage(const core::CapabilitySpec& earlier,
                                const core::CapabilitySpec& later) const {
  if (later.preconditions.empty()) return 1.0;
  std::vector<Vector> writeIdentities;
  for (const auto& e : earlier.effects) {
    writeIdentities.push_back(encodeVariableIdentity(e.variable));
  }
  if (writeIdentities.empty()) return 0.0;
  double total = 0.0;
  for (const auto& pre : later.preconditions) {
    const Vector target = encodeVariableIdentity(pre.variable);
    double best = 0.0;
    for (const auto& write : writeIdentities) {
      best = std::max(best, std::max(0.0, VectorMath::cosine(target, write)));
    }
    total += best;
  }
  return total / static_cast<double>(later.preconditions.size());
}

// ---- Encoder: similarity ----

double Encoder::functionalityWeight(const std::string& block) {
  if (block == "preconditions") return 0.22;
  if (block == "effects") return 0.26;
  if (block == "delta") return 0.14;
  if (block == "inputs") return 0.16;
  if (block == "outputs") return 0.16;
  return 0.0;
}

double Encoder::implementationWeight(const std::string& block) {
  if (block == "type") return 0.30;
  if (block == "mechanism") return 0.40;
  if (block == "resources") return 0.15;
  if (block == "quality") return 0.15;
  return 0.0;
}

std::map<std::string, double> Encoder::similarityPartitioned(const EncodedEntity& a,
                                                            const EncodedEntity& b) const {
  std::map<std::string, double> out;
  if (a.kind != EncodedEntity::Kind::CAPABILITY || b.kind != EncodedEntity::Kind::CAPABILITY) {
    out["full"] = similarity(a, b);
    return out;
  }
  for (const auto& spec : Blocks::capabilityBlocks()) {
    const Vector va = a.blocks.count(spec.name) ? a.blocks.at(spec.name) : Vector();
    const Vector vb = b.blocks.count(spec.name) ? b.blocks.at(spec.name) : Vector();
    out[spec.name] = blockCosine(va, vb);
  }
  out["functional"] = similarity(a, b);
  return out;
}

double Encoder::similarity(const EncodedEntity& a, const EncodedEntity& b) const {
  if (a.kind == b.kind) {
    if (a.kind == EncodedEntity::Kind::CAPABILITY) {
      // Weighted combination over the functional and implementation partitions.
      double functional = 0.0, wf = 0.0, wi = 0.0, implementation = 0.0;
      for (const auto& spec : Blocks::capabilityBlocks()) {
        const double wa = functionalityWeight(spec.name);
        const double wb = implementationWeight(spec.name);
        if (wa > 0.0) {
          const Vector va = a.blocks.count(spec.name) ? a.blocks.at(spec.name) : Vector();
          const Vector vb = b.blocks.count(spec.name) ? b.blocks.at(spec.name) : Vector();
          functional += wa * blockCosine(va, vb);
          wf += wa;
        }
        if (wb > 0.0) {
          const Vector va = a.blocks.count(spec.name) ? a.blocks.at(spec.name) : Vector();
          const Vector vb = b.blocks.count(spec.name) ? b.blocks.at(spec.name) : Vector();
          implementation += wb * blockCosine(va, vb);
          wi += wb;
        }
      }
      if (wf > 0.0) functional /= wf;
      if (wi > 0.0) implementation /= wi;
      (void)implementation;
      // The general similarity reported by similarity(x, y) for two capabilities is their
      // functional similarity; the implementation view is available separately through
      // similarityPartitioned and through EncodedCapability::implementationView.
      return functional;
    }
    return VectorMath::cosine(a.vector, b.vector);
  }
  // Cross-kind comparison happens in the shared 64 dimensional condition space.
  const auto coreOf = [](const EncodedEntity& e) -> Vector {
    if (e.kind != EncodedEntity::Kind::CAPABILITY) {
      auto it = e.blocks.find("core");
      if (it != e.blocks.end()) return it->second;
      return VectorMath::slice(e.vector, 0, Blocks::kSharedCoreDim);
    }
    auto it = e.blocks.find("preconditions");
    auto et = e.blocks.find("effects");
    const Vector pre = it != e.blocks.end() ? it->second : Vector();
    const Vector eff = et != e.blocks.end() ? et->second : Vector();
    if (pre.empty()) return eff;
    if (eff.empty()) return pre;
    Vector mean(pre.size(), 0.0);
    for (size_t i = 0; i < pre.size(); ++i) {
      mean[i] = 0.5 * (pre[i] + (i < eff.size() ? eff[i] : 0.0));
    }
    return VectorMath::normalize(mean);
  };
  return VectorMath::cosine(coreOf(a), coreOf(b));
}

}  // namespace embedding
}  // namespace careweave
