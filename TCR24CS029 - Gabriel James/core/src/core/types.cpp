#include "careweave/core/types.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <sstream>

namespace careweave {
namespace core {

namespace {

// FNV-1a 64 bit. Chosen over std::hash because std::hash is not stable across standard
// library implementations, and the embedding must be reproducible bit for bit.
uint64_t fnv1a64(const std::string& s) {
  uint64_t h = 1469598103934665603ULL;
  for (char ch : s) {
    const uint64_t c = static_cast<uint64_t>(static_cast<unsigned char>(ch));
    h ^= c;
    h *= 1099511628211ULL;
  }
  return h;
}

std::string joinList(const std::vector<std::string>& items, const std::string& sep) {
  std::string out;
  for (size_t i = 0; i < items.size(); ++i) {
    if (i) out += sep;
    out += items[i];
  }
  return out;
}

std::string formatDouble(double d) {
  char buf[64];
  std::snprintf(buf, sizeof(buf), "%.6g", d);
  return std::string(buf);
}

// Strict equality for typed values. Numeric comparison happens across INT and REAL.
bool valueEquals(const Value& a, const Value& b) {
  if (a.type() == ValueType::LIST || b.type() == ValueType::LIST) {
    if (a.type() != b.type()) return false;
    return a.asList() == b.asList();
  }
  const bool an = a.isNumeric(), bn = b.isNumeric();
  if (an && bn) return std::fabs(a.asDouble() - b.asDouble()) < 1e-9;
  if (a.type() != b.type()) return false;
  if (a.type() == ValueType::BOOL) return a.asBool() == b.asBool();
  return a.asString() == b.asString();
}

// Condition evaluation over a concrete state. Missing variables make the condition false,
// except for NEQ where a missing binding is treated as "not equal to the value".
bool evaluateCondition(const Condition& c, const AppState& state) {
  if (!state.has(c.variable)) {
    return c.op == ConditionOp::NEQ;
  }
  const Value cur = state.get(c.variable, Value(0));
  switch (c.op) {
    case ConditionOp::EQ:
      return valueEquals(cur, c.value);
    case ConditionOp::NEQ:
      return !valueEquals(cur, c.value);
    case ConditionOp::IN: {
      for (const auto& candidate : c.value.asList()) {
        if (valueEquals(cur, Value(candidate)) ||
            (cur.isNumeric() && valueEquals(Value(std::stod(candidate)), cur))) {
          return true;
        }
      }
      return false;
    }
    case ConditionOp::GT:
    case ConditionOp::GTE:
    case ConditionOp::LT:
    case ConditionOp::LTE: {
      bool comparable = false;
      const bool less = cur.lessThan(c.value, &comparable);
      if (!comparable) return false;
      const bool equal = valueEquals(cur, c.value);
      if (c.op == ConditionOp::GT) return !less && !equal;
      if (c.op == ConditionOp::GTE) return !less || equal;
      if (c.op == ConditionOp::LT) return less;
      return less || equal;
    }
  }
  return false;
}

}  // namespace

std::string valueTypeToString(ValueType t) {
  switch (t) {
    case ValueType::BOOL: return "boolean";
    case ValueType::INT: return "integer";
    case ValueType::REAL: return "real";
    case ValueType::STRING: return "string";
    case ValueType::ENUM: return "enum";
    case ValueType::LIST: return "list";
  }
  return "string";
}

ValueType valueTypeFromString(const std::string& s) {
  if (s == "boolean" || s == "bool") return ValueType::BOOL;
  if (s == "integer" || s == "int") return ValueType::INT;
  if (s == "real" || s == "number" || s == "float" || s == "double") return ValueType::REAL;
  if (s == "enumerated" || s == "enum" || s == "categorical") return ValueType::ENUM;
  if (s == "list" || s == "array") return ValueType::LIST;
  return ValueType::STRING;
}

std::string conditionOpToString(ConditionOp op) {
  switch (op) {
    case ConditionOp::EQ: return "=";
    case ConditionOp::NEQ: return "!=";
    case ConditionOp::GT: return ">";
    case ConditionOp::GTE: return ">=";
    case ConditionOp::LT: return "<";
    case ConditionOp::LTE: return "<=";
    case ConditionOp::IN: return "in";
  }
  return "=";
}

ConditionOp conditionOpFromString(const std::string& s) {
  if (s == "=" || s == "==" || s == "EQ") return ConditionOp::EQ;
  if (s == "!=" || s == "NEQ") return ConditionOp::NEQ;
  if (s == ">") return ConditionOp::GT;
  if (s == ">=") return ConditionOp::GTE;
  if (s == "<") return ConditionOp::LT;
  if (s == "<=") return ConditionOp::LTE;
  if (s == "in" || s == "IN") return ConditionOp::IN;
  return ConditionOp::EQ;
}

std::string effectOpToString(EffectOp op) {
  switch (op) {
    case EffectOp::SET: return "SET";
    case EffectOp::INCREMENT: return "INCREMENT";
    case EffectOp::DECREMENT: return "DECREMENT";
    case EffectOp::DELETE_: return "DELETE";
  }
  return "SET";
}

EffectOp effectOpFromString(const std::string& s) {
  if (s == "SET" || s == "=" || s == "==") return EffectOp::SET;
  if (s == "INCREMENT" || s == "+=") return EffectOp::INCREMENT;
  if (s == "DECREMENT" || s == "-=") return EffectOp::DECREMENT;
  if (s == "DELETE" || s == "DELETE_") return EffectOp::DELETE_;
  return EffectOp::SET;
}

std::string capabilityTypeToString(CapabilityType t) {
  switch (t) {
    case CapabilityType::API: return "API";
    case CapabilityType::DATABASE: return "DATABASE";
    case CapabilityType::GUI: return "GUI";
    case CapabilityType::EVENT: return "EVENT";
    case CapabilityType::FUNCTION: return "FUNCTION";
    case CapabilityType::FILE: return "FILE";
    case CapabilityType::COMPUTATION: return "COMPUTATION";
    case CapabilityType::MESSAGE: return "MESSAGE";
    case CapabilityType::SERVICE: return "SERVICE";
  }
  return "FUNCTION";
}

CapabilityType capabilityTypeFromString(const std::string& s) {
  if (s == "API") return CapabilityType::API;
  if (s == "DATABASE") return CapabilityType::DATABASE;
  if (s == "GUI") return CapabilityType::GUI;
  if (s == "EVENT") return CapabilityType::EVENT;
  if (s == "FUNCTION") return CapabilityType::FUNCTION;
  if (s == "FILE") return CapabilityType::FILE;
  if (s == "COMPUTATION") return CapabilityType::COMPUTATION;
  if (s == "MESSAGE") return CapabilityType::MESSAGE;
  if (s == "SERVICE") return CapabilityType::SERVICE;
  return CapabilityType::FUNCTION;
}

const std::vector<CapabilityType>& allCapabilityTypes() {
  static const std::vector<CapabilityType> types = {
      CapabilityType::API,       CapabilityType::DATABASE,    CapabilityType::GUI,
      CapabilityType::EVENT,     CapabilityType::FUNCTION,    CapabilityType::FILE,
      CapabilityType::COMPUTATION, CapabilityType::MESSAGE,   CapabilityType::SERVICE};
  return types;
}

// ---- Value ----

Value::Value() : v_(std::string()) {}
Value::Value(bool b) : v_(b) {}
Value::Value(int i) : v_(static_cast<int64_t>(i)) {}
Value::Value(int64_t i) : v_(i) {}
Value::Value(double d) : v_(d) {}
Value::Value(const std::string& s) : v_(s) {}
Value::Value(const char* s) : v_(std::string(s ? s : "")) {}
Value::Value(std::vector<std::string> list) : v_(std::move(list)) {}

ValueType Value::type() const {
  switch (v_.index()) {
    case 0: return ValueType::BOOL;
    case 1: return ValueType::INT;
    case 2: return ValueType::REAL;
    case 3: return ValueType::STRING;
    default: return ValueType::LIST;
  }
}

bool Value::isNumeric() const {
  return v_.index() == 1 || v_.index() == 2;
}

bool Value::asBool() const {
  if (v_.index() == 0) return std::get<bool>(v_);
  if (v_.index() == 1) return std::get<int64_t>(v_) != 0;
  if (v_.index() == 2) return std::get<double>(v_) != 0.0;
  if (v_.index() == 3) return !std::get<std::string>(v_).empty();
  return !std::get<std::vector<std::string>>(v_).empty();
}

int64_t Value::asInt() const {
  if (v_.index() == 0) return std::get<bool>(v_) ? 1 : 0;
  if (v_.index() == 1) return std::get<int64_t>(v_);
  if (v_.index() == 2) return static_cast<int64_t>(std::get<double>(v_));
  if (v_.index() == 3) {
    try {
      return std::stoll(std::get<std::string>(v_));
    } catch (...) {
      return 0;
    }
  }
  return static_cast<int64_t>(std::get<std::vector<std::string>>(v_).size());
}

double Value::asDouble() const {
  if (v_.index() == 0) return std::get<bool>(v_) ? 1.0 : 0.0;
  if (v_.index() == 1) return static_cast<double>(std::get<int64_t>(v_));
  if (v_.index() == 2) return std::get<double>(v_);
  if (v_.index() == 3) {
    try {
      return std::stod(std::get<std::string>(v_));
    } catch (...) {
      return 0.0;
    }
  }
  return static_cast<double>(std::get<std::vector<std::string>>(v_).size());
}

const std::string& Value::asString() const {
  static const std::string empty;
  if (v_.index() == 3) return std::get<std::string>(v_);
  return empty;
}

const std::vector<std::string>& Value::asList() const {
  static const std::vector<std::string> empty;
  if (v_.index() == 4) return std::get<std::vector<std::string>>(v_);
  return empty;
}

double Value::toNumeric() const {
  switch (v_.index()) {
    case 0: return std::get<bool>(v_) ? 1.0 : 0.0;
    case 1: return static_cast<double>(std::get<int64_t>(v_));
    case 2: return std::get<double>(v_);
    case 3: {
      const std::string& s = std::get<std::string>(v_);
      if (s.empty()) return 0.0;
      return static_cast<double>(fnv1a64(s) % 1000ULL) / 1000.0;
    }
    default:
      return static_cast<double>(std::get<std::vector<std::string>>(v_).size()) / 100.0;
  }
}

std::string Value::toString() const {
  switch (v_.index()) {
    case 0: return std::get<bool>(v_) ? "true" : "false";
    case 1: return std::to_string(std::get<int64_t>(v_));
    case 2: return formatDouble(std::get<double>(v_));
    case 3: return std::get<std::string>(v_);
    default: return "[" + joinList(std::get<std::vector<std::string>>(v_), ", ") + "]";
  }
}

bool Value::operator==(const Value& o) const { return valueEquals(*this, o); }

bool Value::lessThan(const Value& o, bool* comparable) const {
  if (comparable) *comparable = false;
  if (isNumeric() && o.isNumeric()) {
    if (comparable) *comparable = true;
    return asDouble() < o.asDouble();
  }
  if (type() == ValueType::BOOL && o.type() == ValueType::BOOL) {
    if (comparable) *comparable = true;
    return (!asBool()) && o.asBool();
  }
  if (type() == ValueType::STRING && o.type() == ValueType::STRING) {
    if (comparable) *comparable = true;
    return asString() < o.asString();
  }
  return false;
}

// ---- Condition and Effect ----

std::string Condition::toString() const {
  return variable + " " + conditionOpToString(op) + " " + value.toString();
}

std::string Effect::toString() const {
  return variable + " " + effectOpToString(op) + " " + value.toString();
}

// ---- Quality attributes ----

QualityAttributes QualityAttributes::sequentialSum(const QualityAttributes& o) const {
  QualityAttributes r;
  r.timeMs = timeMs + o.timeMs;
  r.money = money + o.money;
  r.resource = resource + o.resource;
  r.energy = energy + o.energy;
  // Risk: independent failure modes accumulate as 1-(1-r1)(1-r2).
  r.risk = 1.0 - (1.0 - risk) * (1.0 - o.risk);
  r.extra = extra;
  for (const auto& kv : o.extra) {
    r.extra[kv.first] += kv.second;
  }
  return r;
}

// ---- Availability ----

bool OperationalSpec::availableAt(const std::string& weekday, int minutesAfterMidnight) const {
  // Two forms: a declared window governs (A_i(t) form; `always: false` with windows means the
  // capability is open inside its windows only), otherwise the static flag decides.
  if (!windowed || windows.empty()) return available;
  for (const auto& w : windows) {
    const bool dayMatch =
        w.days.empty() || std::find(w.days.begin(), w.days.end(), weekday) != w.days.end();
    if (!dayMatch) continue;
    if (minutesAfterMidnight >= w.fromMinutes && minutesAfterMidnight < w.toMinutes) return true;
  }
  return false;
}

// ---- Mechanism ----

std::string ExecutionMechanism::toString() const {
  std::ostringstream os;
  os << capabilityTypeToString(kind);
  switch (kind) {
    case CapabilityType::API:
      os << " " << (method.empty() ? std::string("POST") : method) << " " << endpoint;
      break;
    case CapabilityType::DATABASE:
      os << " " << operation << " " << table;
      break;
    case CapabilityType::GUI:
      os << " " << action << " " << component << " on " << page;
      break;
    case CapabilityType::EVENT:
      os << " " << trigger << " -> " << handler;
      break;
    case CapabilityType::FUNCTION:
      os << " " << function;
      break;
    case CapabilityType::FILE:
      os << " " << path;
      break;
    case CapabilityType::COMPUTATION:
      os << " " << expression;
      break;
    case CapabilityType::MESSAGE:
      os << " " << topic << " -> " << queue;
      break;
    case CapabilityType::SERVICE:
      os << " " << service << " " << baseUrl;
      break;
  }
  return os.str();
}

// ---- AppState ----

void AppState::set(const std::string& key, const Value& v) { m_[key] = v; }

AppState AppState::fromMap(const std::map<std::string, Value>& values) {
  AppState s;
  s.m_ = values;
  return s;
}
void AppState::remove(const std::string& key) { m_.erase(key); }
bool AppState::has(const std::string& key) const { return m_.count(key) != 0; }
Value AppState::get(const std::string& key, const Value& dflt) const {
  auto it = m_.find(key);
  return it == m_.end() ? dflt : it->second;
}

std::vector<std::string> AppState::keysSorted() const {
  std::vector<std::string> keys;
  keys.reserve(m_.size());
  for (const auto& kv : m_) keys.push_back(kv.first);
  return keys;
}

std::string AppState::toString() const {
  std::ostringstream os;
  os << "{";
  bool first = true;
  for (const auto& kv : m_) {
    if (!first) os << ", ";
    first = false;
    os << kv.first << "=" << kv.second.toString();
  }
  os << "}";
  return os.str();
}

// ---- Goal ----

bool Goal::isSatisfied(const AppState& state) const {
  for (const auto& c : conditions) {
    if (!evaluateCondition(c, state)) return false;
  }
  return true;
}

std::string Goal::toString() const {
  std::string out = "G = {";
  for (size_t i = 0; i < conditions.size(); ++i) {
    if (i) out += ", ";
    out += conditions[i].toString();
  }
  out += "}";
  return out;
}

// Shared with the compatibility engine: evaluate one condition against a state.
bool satisfies(const Condition& c, const AppState& state) {
  return evaluateCondition(c, state);
}

// Apply one effect to a state.
void applyEffect(Effect e, AppState& state) {
  if (e.value.type() == ValueType::STRING) {
    const std::string s = e.value.asString();
    if (!s.empty() && (s[0] == '+' || s[0] == '-')) {
      // Support the "+=" and "-=" spellings arriving as string operators in JSON.
      const double delta = std::stod(s);
      e.op = delta >= 0 ? EffectOp::INCREMENT : EffectOp::DECREMENT;
      e.value = Value(std::fabs(delta));
    }
  }
  switch (e.op) {
    case EffectOp::SET:
      state.set(e.variable, e.value);
      break;
    case EffectOp::INCREMENT: {
      const Value cur = state.get(e.variable, Value(0));
      if (cur.type() == ValueType::REAL || e.value.type() == ValueType::REAL) {
        state.set(e.variable, Value(cur.asDouble() + e.value.asDouble()));
      } else {
        state.set(e.variable, Value(cur.asInt() + e.value.asInt()));
      }
      break;
    }
    case EffectOp::DECREMENT: {
      const Value cur = state.get(e.variable, Value(0));
      if (cur.type() == ValueType::REAL || e.value.type() == ValueType::REAL) {
        state.set(e.variable, Value(cur.asDouble() - e.value.asDouble()));
      } else {
        state.set(e.variable, Value(cur.asInt() - e.value.asInt()));
      }
      break;
    }
    case EffectOp::DELETE_:
      state.remove(e.variable);
      break;
  }
}

void applyEffects(const std::vector<Effect>& effects, AppState& state) {
  for (const auto& e : effects) {
    applyEffect(e, state);
  }
}

}  // namespace core
}  // namespace careweave
