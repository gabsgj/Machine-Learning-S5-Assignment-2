#include "careweave/compat/conditions.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <sstream>

namespace careweave {
namespace compat {

namespace {
constexpr double kEps = 1e-9;

bool valueIsIntegral(const core::Value& v) { return v.type() == core::ValueType::INT; }

std::string joinMembers(const std::vector<std::string>& members) {
  std::string out;
  for (size_t i = 0; i < members.size(); ++i) {
    if (i) out += ",";
    out += members[i];
  }
  return out;
}

Truth containsValue(const Domain& d, const core::Value& v) {
  switch (d.kind) {
    case Domain::Kind::UNIVERSE:
      return Truth::UNKNOWN_;
    case Domain::Kind::BOOL_SET: {
      if (v.type() != core::ValueType::BOOL) return Truth::UNKNOWN_;
      const bool b = v.asBool();
      if (!d.boolExact) return Truth::UNKNOWN_;
      return b == d.boolValue ? Truth::TRUE_ : Truth::FALSE_;
    }
    case Domain::Kind::ENUM_SET: {
      const std::string s = v.toString();
      const bool found = std::find(d.members.begin(), d.members.end(), s) != d.members.end();
      return found ? Truth::TRUE_ : Truth::FALSE_;
    }
    case Domain::Kind::INTERVAL: {
      if (!v.isNumeric()) return Truth::UNKNOWN_;
      const double x = v.asDouble();
      const bool aboveLow = d.loOpen ? x > d.lo + kEps : x >= d.lo - kEps;
      const bool belowHigh = d.hiOpen ? x < d.hi - kEps : x <= d.hi + kEps;
      if (aboveLow && belowHigh) return Truth::TRUE_;
      return Truth::FALSE_;
    }
  }
  return Truth::UNKNOWN_;
}

// Refines one numeric bound with the max (lower) or min (upper) of the current bound and the new
// one. Equal bounds combine their openness, so (0,1] and [0,1) meet at (0,1).
void applyLower(double v, bool open, double& lo, bool& loOpen) {
  if (v > lo + kEps) {
    lo = v;
    loOpen = open;
  } else if (v >= lo - kEps) {
    loOpen = loOpen || open;
  }
}

void applyUpper(double v, bool open, double& hi, bool& hiOpen) {
  if (v < hi - kEps) {
    hi = v;
    hiOpen = open;
  } else if (v <= hi + kEps) {
    hiOpen = hiOpen || open;
  }
}

// True when some state can satisfy every condition pinned on one variable. The check tracks the
// same domains as the entailment evaluator: boolean pinning, numeric bounds with openness, and
// membership sets, intersected until a contradiction or a surviving witness set remains.
bool variableSatisfiable(const std::vector<core::Condition>& conditions) {
  bool boolPinned = false;
  bool boolValue = false;
  std::vector<std::string> excludedValues;
  double lo = -std::numeric_limits<double>::infinity();
  double hi = std::numeric_limits<double>::infinity();
  bool loOpen = false;
  bool hiOpen = false;
  bool numericBounds = false;
  std::vector<std::string> members;
  bool hasMembers = false;

  for (const auto& c : conditions) {
    switch (c.op) {
      case core::ConditionOp::EQ:
        if (c.value.type() == core::ValueType::BOOL) {
          if (boolPinned && boolValue != c.value.asBool()) return false;
          boolPinned = true;
          boolValue = c.value.asBool();
        } else if (c.value.isNumeric()) {
          numericBounds = true;
          applyLower(c.value.asDouble(), false, lo, loOpen);
          applyUpper(c.value.asDouble(), false, hi, hiOpen);
        } else {
          const std::vector<std::string> singleton{c.value.toString()};
          if (!hasMembers) {
            members = singleton;
            hasMembers = true;
          } else {
            std::vector<std::string> kept;
            for (const auto& m : members) {
              if (std::find(singleton.begin(), singleton.end(), m) != singleton.end()) {
                kept.push_back(m);
              }
            }
            members = kept;
          }
        }
        break;
      case core::ConditionOp::NEQ:
        if (c.value.type() == core::ValueType::BOOL) {
          if (boolPinned && boolValue == c.value.asBool()) return false;
        } else {
          excludedValues.push_back(c.value.toString());
        }
        break;
      case core::ConditionOp::GT:
        if (c.value.isNumeric()) {
          numericBounds = true;
          applyLower(c.value.asDouble(), true, lo, loOpen);
        }
        break;
      case core::ConditionOp::GTE:
        if (c.value.isNumeric()) {
          numericBounds = true;
          applyLower(c.value.asDouble(), false, lo, loOpen);
        }
        break;
      case core::ConditionOp::LT:
        if (c.value.isNumeric()) {
          numericBounds = true;
          applyUpper(c.value.asDouble(), true, hi, hiOpen);
        }
        break;
      case core::ConditionOp::LTE:
        if (c.value.isNumeric()) {
          numericBounds = true;
          applyUpper(c.value.asDouble(), false, hi, hiOpen);
        }
        break;
      case core::ConditionOp::IN: {
        const std::vector<std::string> wanted = c.value.asList();
        if (!hasMembers) {
          members = wanted;
          hasMembers = true;
        } else {
          std::vector<std::string> kept;
          for (const auto& m : members) {
            if (std::find(wanted.begin(), wanted.end(), m) != wanted.end()) kept.push_back(m);
          }
          members = kept;
        }
        break;
      }
    }
  }

  if (numericBounds && (lo > hi + kEps || (std::fabs(lo - hi) <= kEps && (loOpen || hiOpen)))) {
    return false;
  }
  if (hasMembers) {
    std::vector<std::string> kept;
    for (const auto& m : members) {
      if (std::find(excludedValues.begin(), excludedValues.end(), m) != excludedValues.end()) {
        continue;
      }
      if (numericBounds) {
        double numeric = 0.0;
        try {
          numeric = std::stod(m);
        } catch (...) {
          continue;  // a non numeric member survives no numeric bound
        }
        if (numeric < lo - kEps || numeric > hi + kEps) continue;
        if (loOpen && numeric <= lo + kEps) continue;
        if (hiOpen && numeric >= hi - kEps) continue;
      }
      kept.push_back(m);
    }
    if (kept.empty()) return false;
  }
  return true;
}

}  // namespace

std::string truthToString(Truth t) {
  switch (t) {
    case Truth::TRUE_: return "true";
    case Truth::FALSE_: return "false";
    case Truth::UNKNOWN_: return "unknown";
  }
  return "unknown";
}

std::string entailmentToString(Entailment e) {
  switch (e) {
    case Entailment::ENTAILED: return "entailed";
    case Entailment::POSSIBLE: return "possible";
    case Entailment::CONFLICT: return "conflict";
    case Entailment::UNKNOWN: return "unknown";
  }
  return "unknown";
}

Domain Domain::universe() { return Domain(); }

Domain Domain::boolean(bool value) {
  Domain d;
  d.kind = Kind::BOOL_SET;
  d.boolValue = value;
  d.boolExact = true;
  return d;
}

Domain Domain::booleanBoth() {
  Domain d;
  d.kind = Kind::BOOL_SET;
  d.boolValue = false;
  d.boolExact = false;
  return d;
}

Domain Domain::interval(double lo, double hi, bool integral) {
  Domain d;
  d.kind = Kind::INTERVAL;
  d.lo = lo;
  d.hi = hi;
  d.numericIntegral = integral;
  return d;
}

Domain Domain::enumerated(std::vector<std::string> members) {
  Domain d;
  d.kind = Kind::ENUM_SET;
  d.members = std::move(members);
  return d;
}

Domain Domain::singleton(const core::Value& value) {
  switch (value.type()) {
    case core::ValueType::BOOL:
      return boolean(value.asBool());
    case core::ValueType::INT:
    case core::ValueType::REAL:
      return interval(value.asDouble(), value.asDouble(), valueIsIntegral(value));
    case core::ValueType::LIST:
      return enumerated(value.asList());
    default:
      return enumerated({value.asString()});
  }
}

std::string Domain::toString() const {
  std::ostringstream os;
  switch (kind) {
    case Kind::UNIVERSE:
      return "any";
    case Kind::BOOL_SET:
      return boolExact ? (boolValue ? "true" : "false") : "{true,false}";
    case Kind::INTERVAL:
      os << "[" << lo << "," << hi << "]" << (numericIntegral ? " (integer)" : " (real)");
      return os.str();
    case Kind::ENUM_SET:
      os << "{" << joinMembers(members) << "}";
      return os.str();
  }
  return "any";
}

DomainState DomainState::fromConcrete(const core::AppState& state) {
  DomainState ds;
  for (const auto& kv : state.all()) {
    ds.domains_[kv.first] = Domain::singleton(kv.second);
  }
  return ds;
}

DomainState DomainState::apply(const core::AppState& state,
                              const std::vector<core::Effect>& effects) {
  DomainState ds;
  // Seed domains only for the variables the effect set actually mentions: interval arithmetic
  // needs a concrete base to shift, but bundling never assumes nothing else ran in between, so
  // every other variable stays unconstrained (universe) and preconditions over it report
  // UNKNOWN rather than borrowing the initial snapshot.
  for (const auto& e : effects) {
    if (ds.has(e.variable)) continue;
    if (state.has(e.variable)) ds.domains_[e.variable] = Domain::singleton(state.get(e.variable));
  }
  for (const auto& e : effects) {
    const Domain current = ds.get(e.variable);
    switch (e.op) {
      case core::EffectOp::SET:
        ds.domains_[e.variable] = Domain::singleton(e.value);
        break;
      case core::EffectOp::INCREMENT: {
        if (current.kind == Domain::Kind::INTERVAL && e.value.isNumeric()) {
          const double delta = e.value.asDouble();
          ds.domains_[e.variable] =
              Domain::interval(current.lo + delta, current.hi + delta, current.numericIntegral);
        } else if (current.kind == Domain::Kind::UNIVERSE) {
          ds.domains_[e.variable] = Domain::universe();
        } else if (current.kind == Domain::Kind::BOOL_SET) {
          ds.domains_[e.variable] = Domain::booleanBoth();
        }
        break;
      }
      case core::EffectOp::DECREMENT: {
        if (current.kind == Domain::Kind::INTERVAL && e.value.isNumeric()) {
          const double delta = e.value.asDouble();
          ds.domains_[e.variable] =
              Domain::interval(current.lo - delta, current.hi - delta, current.numericIntegral);
        } else if (current.kind == Domain::Kind::UNIVERSE) {
          ds.domains_[e.variable] = Domain::universe();
        }
        break;
      }
      case core::EffectOp::DELETE_:
        ds.domains_[e.variable] = Domain::universe();
        break;
    }
  }
  return ds;
}

void DomainState::set(const std::string& variable, const Domain& d) { domains_[variable] = d; }

bool DomainState::has(const std::string& variable) const {
  return domains_.count(variable) != 0;
}

Domain DomainState::get(const std::string& variable) const {
  auto it = domains_.find(variable);
  return it == domains_.end() ? Domain::universe() : it->second;
}

std::vector<std::string> DomainState::keysSorted() const {
  std::vector<std::string> keys;
  keys.reserve(domains_.size());
  for (const auto& kv : domains_) keys.push_back(kv.first);
  return keys;
}

std::string DomainState::toString() const {
  std::ostringstream os;
  os << "{";
  bool first = true;
  for (const auto& kv : domains_) {
    if (!first) os << ", ";
    first = false;
    os << kv.first << ":" << kv.second.toString();
  }
  os << "}";
  return os.str();
}

Entailment evaluate(const Domain& domain, const core::Condition& condition) {
  if (domain.kind == Domain::Kind::UNIVERSE) return Entailment::UNKNOWN;
  switch (condition.op) {
    case core::ConditionOp::EQ: {
      const Truth t = containsValue(domain, condition.value);
      if (t == Truth::FALSE_) return Entailment::CONFLICT;
      if (t == Truth::TRUE_) {
        // The value is inside the domain. Entailment additionally requires the domain to pin
        // exactly this value: singleton intervals, single member sets and exact booleans do, wider
        // numeric intervals and multi member sets merely allow it.
        switch (domain.kind) {
          case Domain::Kind::INTERVAL:
            return domain.hi - domain.lo <= kEps ? Entailment::ENTAILED : Entailment::POSSIBLE;
          case Domain::Kind::ENUM_SET:
            return domain.members.size() <= 1 ? Entailment::ENTAILED : Entailment::POSSIBLE;
          case Domain::Kind::BOOL_SET:
            return Entailment::ENTAILED;
          case Domain::Kind::UNIVERSE:
            break;
        }
        return Entailment::POSSIBLE;
      }
      // Indeterminate: a widened boolean domain, or a value whose type does not match an interval.
      return domain.kind == Domain::Kind::BOOL_SET ? Entailment::POSSIBLE : Entailment::UNKNOWN;
    }
    case core::ConditionOp::NEQ: {
      const Truth t = containsValue(domain, condition.value);
      // The value lies outside the domain, so it provably differs from every member.
      if (t == Truth::FALSE_) return Entailment::ENTAILED;
      if (t == Truth::TRUE_) {
        // The value is inside the domain. The inequality holds only when other members exist: a
        // singleton domain pins exactly the excluded value and therefore conflicts.
        switch (domain.kind) {
          case Domain::Kind::INTERVAL:
            return domain.hi - domain.lo <= kEps ? Entailment::CONFLICT : Entailment::POSSIBLE;
          case Domain::Kind::ENUM_SET:
            return domain.members.size() <= 1 ? Entailment::CONFLICT : Entailment::POSSIBLE;
          case Domain::Kind::BOOL_SET:
            return Entailment::CONFLICT;
          case Domain::Kind::UNIVERSE:
            break;
        }
        return Entailment::POSSIBLE;
      }
      return domain.kind == Domain::Kind::BOOL_SET ? Entailment::POSSIBLE : Entailment::UNKNOWN;
    }
    case core::ConditionOp::GT:
    case core::ConditionOp::GTE:
    case core::ConditionOp::LT:
    case core::ConditionOp::LTE: {
      if (domain.kind != Domain::Kind::INTERVAL || !condition.value.isNumeric()) {
        return Entailment::UNKNOWN;
      }
      const double v = condition.value.asDouble();
      switch (condition.op) {
        case core::ConditionOp::GT:
          // Every member exceeds v, or the open lower bound already excludes v itself.
          if (domain.lo > v + kEps || (domain.loOpen && domain.lo >= v - kEps)) {
            return Entailment::ENTAILED;
          }
          if (domain.hi <= v + kEps) return Entailment::CONFLICT;
          return Entailment::POSSIBLE;
        case core::ConditionOp::GTE:
          if (domain.lo >= v - kEps) return Entailment::ENTAILED;
          if (domain.hi < v - kEps || (domain.hiOpen && domain.hi <= v + kEps)) {
            return Entailment::CONFLICT;
          }
          return Entailment::POSSIBLE;
        case core::ConditionOp::LT:
          if (domain.hi < v - kEps || (domain.hiOpen && domain.hi <= v + kEps)) {
            return Entailment::ENTAILED;
          }
          if (domain.lo >= v - kEps) return Entailment::CONFLICT;
          return Entailment::POSSIBLE;
        case core::ConditionOp::LTE:
          if (domain.hi <= v + kEps) return Entailment::ENTAILED;
          if ((!domain.loOpen && domain.lo > v + kEps) ||
              (domain.loOpen && domain.lo >= v - kEps)) {
            return Entailment::CONFLICT;
          }
          return Entailment::POSSIBLE;
        default:
          break;
      }
      return Entailment::UNKNOWN;
    }
    case core::ConditionOp::IN: {
      const std::vector<std::string> wanted = condition.value.asList();
      if (domain.kind == Domain::Kind::ENUM_SET) {
        bool all = true, any = false;
        for (const auto& m : domain.members) {
          const bool in = std::find(wanted.begin(), wanted.end(), m) != wanted.end();
          all = all && in;
          any = any || in;
        }
        if (all && !domain.members.empty()) return Entailment::ENTAILED;
        if (!any) return Entailment::CONFLICT;
        return Entailment::POSSIBLE;
      }
      if (domain.kind == Domain::Kind::BOOL_SET && domain.boolExact) {
        const std::string asText = domain.boolValue ? "true" : "false";
        return std::find(wanted.begin(), wanted.end(), asText) != wanted.end()
                   ? Entailment::ENTAILED
                   : Entailment::CONFLICT;
      }
      if (domain.kind == Domain::Kind::INTERVAL && !wanted.empty()) {
        // Numeric membership over intervals: check whether the extremal members cover the domain.
        bool any = false, all = true;
        for (double candidate : {domain.lo, domain.hi}) {
          bool memberInSet = false;
          for (const auto& w : wanted) {
            try {
              if (std::fabs(std::stod(w) - candidate) <= kEps) memberInSet = true;
            } catch (...) {
            }
          }
          any = any || memberInSet;
          all = all && memberInSet;
        }
        if (all && std::fabs(domain.hi - domain.lo) <= kEps) return Entailment::ENTAILED;
        if (any) return Entailment::POSSIBLE;
        return Entailment::CONFLICT;
      }
      return Entailment::UNKNOWN;
    }
  }
  return Entailment::UNKNOWN;
}

EntailmentReport entails(const core::AppState& initial, const std::vector<core::Effect>& effects,
                         const std::vector<core::Condition>& preconditions) {
  EntailmentReport report;
  const DomainState after = DomainState::apply(initial, effects);
  for (const auto& pre : preconditions) {
    EffectEntailment item;
    item.precondition = pre.toString();
    const Domain domain = after.get(pre.variable);
    item.result = evaluate(domain, pre);
    std::ostringstream os;
    os << pre.variable << " in " << domain.toString() << " -> "
       << entailmentToString(item.result);
    item.explanation = os.str();
    switch (item.result) {
      case Entailment::ENTAILED: ++report.entailed; break;
      case Entailment::POSSIBLE: ++report.possible; break;
      case Entailment::CONFLICT: ++report.conflicts; break;
      case Entailment::UNKNOWN: ++report.unknown; break;
    }
    report.items.push_back(std::move(item));
  }
  if (report.conflicts > 0) {
    report.overall = Entailment::CONFLICT;
  } else if (report.entailed == static_cast<int>(preconditions.size()) && !preconditions.empty()) {
    report.overall = Entailment::ENTAILED;
  } else if (preconditions.empty()) {
    report.overall = Entailment::ENTAILED;
  } else {
    report.overall = Entailment::POSSIBLE;
  }
  return report;
}

std::string EntailmentReport::render() const {
  std::ostringstream os;
  os << "overall " << entailmentToString(overall) << " (entailed " << entailed << ", possible "
     << possible << ", conflicts " << conflicts << ", unknown " << unknown << ")";
  for (const auto& item : items) {
    os << "\n  - " << item.precondition << " : " << item.explanation;
  }
  return os.str();
}

bool conditionsConflict(const std::vector<core::Condition>& a,
                        const std::vector<core::Condition>& b) {
  // Two condition sets conflict when no state at all can satisfy both, independent of the current
  // state: conditions list what must hold after effects ran, so they are hypotheses to intersect,
  // not facts to check. CreateOrder establishes Order.exists = true while CancelCart requires
  // Order.exists = false, which intersects to the empty set.
  std::map<std::string, std::vector<core::Condition>> byVariable;
  for (const auto& c : a) byVariable[c.variable].push_back(c);
  for (const auto& c : b) byVariable[c.variable].push_back(c);
  for (const auto& kv : byVariable) {
    if (!variableSatisfiable(kv.second)) return true;
  }
  return false;
}

}  // namespace compat
}  // namespace careweave
