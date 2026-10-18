#include "careweave/composer/composer.hpp"

#include <algorithm>
#include <cmath>
#include <set>
#include <sstream>

namespace careweave {
namespace composer {

namespace {

constexpr double kEps = 1e-9;

std::string joinWith(const std::vector<std::string>& parts, const std::string& sep) {
  std::string out;
  for (size_t i = 0; i < parts.size(); ++i) {
    if (i) out += sep;
    out += parts[i];
  }
  return out;
}

core::Value numericSum(const core::Value& base, double delta) {
  if (base.type() == core::ValueType::INT) {
    const double r = static_cast<double>(base.asInt()) + delta;
    if (std::fabs(r - std::round(r)) <= kEps) {
      return core::Value(static_cast<int64_t>(std::llround(r)));
    }
    return core::Value(r);
  }
  return core::Value(base.asDouble() + delta);
}

core::Value counterValue(double amount) {
  const double magnitude = std::fabs(amount);
  if (std::fabs(magnitude - std::round(magnitude)) <= kEps) {
    return core::Value(static_cast<int64_t>(std::llround(magnitude)));
  }
  return core::Value(magnitude);
}

// One variable's folded final action.
struct Fold {
  enum class Kind { NONE, SET, COUNTER, DELETED };
  Kind kind = Kind::NONE;
  core::Value value;
  double amount = 0.0;  // signed counter amount
};

void foldEffect(Fold& f, const core::Effect& e) {
  const double delta = e.value.asDouble();
  switch (e.op) {
    case core::EffectOp::SET:
      f.kind = Fold::Kind::SET;
      f.value = e.value;
      return;
    case core::EffectOp::DELETE_:
      f.kind = Fold::Kind::DELETED;
      return;
    case core::EffectOp::INCREMENT:
    case core::EffectOp::DECREMENT: {
      const double signedDelta =
          e.op == core::EffectOp::INCREMENT ? std::fabs(delta) : -std::fabs(delta);
      switch (f.kind) {
        case Fold::Kind::NONE:
        case Fold::Kind::DELETED:
          f.kind = Fold::Kind::COUNTER;
          f.amount = signedDelta;
          return;
        case Fold::Kind::COUNTER:
          f.amount += signedDelta;
          return;
        case Fold::Kind::SET:
          // A write followed by a counter folds into one write when the value is numeric.
          if (f.value.isNumeric()) {
            f.value = numericSum(f.value, signedDelta);
          }
          return;
      }
      return;
    }
  }
}

}  // namespace

std::vector<core::Effect> netEffects(const std::vector<core::CapabilitySpec>& sequence) {
  std::map<std::string, Fold> folds;
  for (const auto& spec : sequence) {
    for (const auto& e : spec.effects) {
      foldEffect(folds[e.variable], e);
    }
  }
  std::vector<core::Effect> out;
  for (const auto& kv : folds) {  // std::map iterates in sorted variable order
    const Fold& f = kv.second;
    core::Effect e;
    e.variable = kv.first;
    switch (f.kind) {
      case Fold::Kind::NONE:
        continue;
      case Fold::Kind::SET:
        e.op = core::EffectOp::SET;
        e.value = f.value;
        break;
      case Fold::Kind::DELETED:
        e.op = core::EffectOp::DELETE_;
        e.value = core::Value(int64_t(0));
        break;
      case Fold::Kind::COUNTER:
        if (std::fabs(f.amount) <= kEps) continue;
        e.op = f.amount > 0 ? core::EffectOp::INCREMENT : core::EffectOp::DECREMENT;
        e.value = counterValue(f.amount);
        break;
    }
    out.push_back(e);
  }
  return out;
}

core::OperationalSpec composeOperational(const core::CapabilitySpec& a,
                                         const core::CapabilitySpec& b) {
  core::OperationalSpec out;
  out.cost = a.operational.cost.sequentialSum(b.operational.cost);
  out.reliability = a.operational.reliability * b.operational.reliability;
  out.available = a.operational.available && b.operational.available;
  out.windowed = a.operational.windowed || b.operational.windowed;
  if (!a.operational.windowed) {
    out.windows = b.operational.windows;
  } else if (!b.operational.windowed) {
    out.windows = a.operational.windows;
  } else {
    for (const auto& wa : a.operational.windows) {
      for (const auto& wb : b.operational.windows) {
        core::AvailabilityWindow w;
        for (const auto& day : wa.days) {
          if (std::find(wb.days.begin(), wb.days.end(), day) != wb.days.end()) {
            w.days.push_back(day);
          }
        }
        w.fromMinutes = std::max(wa.fromMinutes, wb.fromMinutes);
        w.toMinutes = std::min(wa.toMinutes, wb.toMinutes);
        if (!w.days.empty() && w.fromMinutes < w.toMinutes) out.windows.push_back(w);
      }
    }
    // Two windowed members with no overlapping window are never available together.
    if (out.windows.empty()) out.available = false;
  }
  return out;
}

core::CapabilitySpec Composer::identity() {
  core::CapabilitySpec s;
  s.id = "identity";
  s.name = "Identity";
  s.description = "Empty sequence: the state is unchanged";
  s.type = core::CapabilityType::FUNCTION;
  s.mechanism.kind = core::CapabilityType::FUNCTION;
  s.mechanism.function = "identity";
  return s;
}

core::CapabilitySpec Composer::composeTwo(const core::CapabilitySpec& a,
                                          const core::CapabilitySpec& b) const {
  return composeSpec({a, b});
}

core::CapabilitySpec Composer::composeSpec(const std::vector<core::CapabilitySpec>& sequence) const {
  if (sequence.empty()) return identity();
  if (sequence.size() == 1) {
    core::CapabilitySpec single = sequence.front();
    // Keep the representation canonical without distorting the member.
    return single;
  }

  core::CapabilitySpec out;
  std::vector<std::string> ids;
  for (const auto& s : sequence) ids.push_back(s.id.empty() ? s.name : s.id);
  out.id = joinWith(ids, "+");
  std::vector<std::string> names;
  for (const auto& s : sequence) names.push_back(s.name.empty() ? s.id : s.name);
  out.name = joinWith(names, " then ");
  out.description = "Composite of " + std::to_string(sequence.size()) + " capabilities: " + out.name;
  out.type = core::CapabilityType::FUNCTION;
  out.mechanism.kind = core::CapabilityType::FUNCTION;
  out.mechanism.function = "compose(" + joinWith(ids, ",") + ")";
  std::vector<std::string> mechanismNotes;
  for (const auto& s : sequence) mechanismNotes.push_back(s.mechanism.toString());
  out.mechanism.notes = joinWith(mechanismNotes, " -> ");

  // Inputs: everything later members need that no earlier member binds through outputs or
  // effects. The interface of the composite is what the caller must supply.
  std::map<std::string, core::InputSpec> inputs;
  std::set<std::string> bound;
  for (const auto& s : sequence) {
    for (const auto& in : s.inputs) {
      if (bound.count(in.name) != 0) continue;
      if (inputs.count(in.name) == 0) inputs[in.name] = in;
    }
    for (const auto& o : s.outputs) bound.insert(o.name);
    for (const auto& e : s.effects) bound.insert(e.variable);
  }
  for (const auto& kv : inputs) out.inputs.push_back(kv.second);

  // Outputs: union by name, later members overwrite on a name clash.
  std::map<std::string, core::OutputSpec> outputs;
  for (const auto& s : sequence) {
    for (const auto& o : s.outputs) outputs[o.name] = o;
  }
  for (const auto& kv : outputs) out.outputs.push_back(kv.second);

  // Preconditions: conservative union, deduplicated in first appearance order.
  std::set<std::string> seenPre;
  for (const auto& s : sequence) {
    for (const auto& p : s.preconditions) {
      if (seenPre.insert(p.toString()).second) out.preconditions.push_back(p);
    }
  }

  // Net state change.
  out.effects = netEffects(sequence);

  // Constraints, resources and roles: union with first appearance order, deduplicated.
  std::set<std::string> seenConstraint, seenResource, seenRole;
  for (const auto& s : sequence) {
    for (const auto& c : s.constraints) {
      if (seenConstraint.insert(c.toString()).second) out.constraints.push_back(c);
    }
    for (const auto& r : s.resources) {
      if (seenResource.insert(r).second) out.resources.push_back(r);
    }
    for (const auto& r : s.roles) {
      if (seenRole.insert(r).second) out.roles.push_back(r);
    }
  }

  // Operational law across the whole sequence.
  out.operational = sequence.front().operational;
  for (size_t i = 1; i < sequence.size(); ++i) {
    core::CapabilitySpec left;
    left.operational = out.operational;
    out.operational = composeOperational(left, sequence[i]);
  }

  for (const auto& s : sequence) {
    for (const auto& kv : s.stateDeltaHint) out.stateDeltaHint[kv.first] = kv.second;
  }
  return out;
}

embedding::Vector Composer::algebraicVector(
    const std::vector<core::CapabilitySpec>& sequence) const {
  using embedding::Blocks;
  using embedding::Vector;
  using embedding::VectorMath;
  if (sequence.empty()) return encoder_.encodeCapability(identity());
  std::vector<embedding::EncodedCapability> encoded;
  for (const auto& s : sequence) encoded.push_back(encoder_.encodeCapabilityDetailed(s));

  const auto blockMean = [&](const std::string& name) -> Vector {
    std::vector<Vector> parts;
    for (const auto& e : encoded) parts.push_back(e.block(name));
    return VectorMath::mean(parts);
  };
  const auto blockSumNormalized = [&](const std::string& name) -> Vector {
    Vector acc;
    for (const auto& e : encoded) {
      const Vector v = e.block(name);
      if (acc.size() < v.size()) acc.resize(v.size(), 0.0);
      for (size_t i = 0; i < acc.size() && i < v.size(); ++i) acc[i] += v[i];
    }
    return VectorMath::normalize(acc);
  };

  // Type: the composite executes as an orchestration.
  Vector type(Blocks::kTypeDim, 0.0);
  const auto& types = core::allCapabilityTypes();
  for (size_t i = 0; i < types.size(); ++i) {
    if (types[i] == core::CapabilityType::FUNCTION) type[i] = 1.0;
  }

  Vector out = type;
  const auto append = [&out](const Vector& v) {
    out.insert(out.end(), v.begin(), v.end());
  };
  append(blockMean("mechanism"));
  append(blockMean("inputs"));
  append(blockMean("outputs"));
  append(blockMean("preconditions"));
  append(blockMean("effects"));
  append(blockSumNormalized("delta"));
  append(blockSumNormalized("resources"));
  append(blockMean("quality"));

  double reliability = 1.0;
  double availability = 1.0;
  for (const auto& s : sequence) {
    reliability *= s.operational.reliability;
    availability = std::min(availability, s.operational.available ? 1.0 : 0.0);
  }
  append(Vector{reliability});
  append(Vector{availability});
  return out;
}

Composer::Composition Composer::compose(const std::vector<core::CapabilitySpec>& sequence) const {
  Composition result;
  result.spec = composeSpec(sequence);
  result.algebraic = algebraicVector(sequence);
  result.reencoded = encoder_.encodeCapability(result.spec);
  result.algebraicVsReencoded =
      embedding::VectorMath::cosine(result.algebraic, result.reencoded);
  if (!sequence.empty()) {
    result.toFirst =
        embedding::VectorMath::cosine(result.algebraic, encoder_.encodeCapability(sequence.front()));
    result.toLast =
        embedding::VectorMath::cosine(result.algebraic, encoder_.encodeCapability(sequence.back()));
  }
  return result;
}

}  // namespace composer
}  // namespace careweave
