#pragma once
// CareWeave Mini core value model.
//
// Shared by the specification parser, the encoders, the compatibility engine, the registry
// and the gateway. This header contains data structures and pure value semantics only: no
// embedding, no HTTP, no JSON library types.
//
// Ported and extended from the parent project's core types (Value, Condition, Effect,
// CapabilitySpec). Extensions: typed comparison operators including IN over enum sets,
// capability constraints as typed conditions, availability windows A(t), and the formal
// application model A = (S, C, S_I, G, R, K) as first-class types.
#include <cstdint>
#include <map>
#include <string>
#include <variant>
#include <vector>

namespace careweave {
namespace core {

// Value kinds named by the assignment specification.
enum class ValueType { BOOL, INT, REAL, STRING, ENUM, LIST };
// Comparison operators required by the specification: =, !=, <, <=, >, >=, in.
enum class ConditionOp { EQ, NEQ, GT, GTE, LT, LTE, IN };
// Effect operators. SET assigns, INCREMENT and DECREMENT change numeric variables,
// DELETE removes the binding.
enum class EffectOp { SET, INCREMENT, DECREMENT, DELETE_ };
// The nine capability types from the specification.
enum class CapabilityType { API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE };

std::string valueTypeToString(ValueType t);
ValueType valueTypeFromString(const std::string& s);
std::string conditionOpToString(ConditionOp op);
ConditionOp conditionOpFromString(const std::string& s);
std::string effectOpToString(EffectOp op);
EffectOp effectOpFromString(const std::string& s);
std::string capabilityTypeToString(CapabilityType t);
CapabilityType capabilityTypeFromString(const std::string& s);
const std::vector<CapabilityType>& allCapabilityTypes();

// A runtime value: bool, int64, double, string, or a list of strings for enum sets.
class Value {
 public:
  Value();
  Value(bool b);
  Value(int i);
  Value(int64_t i);
  Value(double d);
  Value(const std::string& s);
  Value(const char* s);
  Value(std::vector<std::string> list);
  static Value boolean(bool b) { return Value(b); }

  ValueType type() const;
  bool isNumeric() const;
  bool asBool() const;
  int64_t asInt() const;
  double asDouble() const;
  const std::string& asString() const;
  const std::vector<std::string>& asList() const;

  // Stable numeric projection used for embedding only. Booleans map to 0/1, numbers to their
  // value, strings to a deterministic FNV-1a hash in [0,1), lists to their size in [0,1).
  // Never used for guard evaluation, which is strictly typed.
  double toNumeric() const;
  std::string toString() const;

  bool operator==(const Value& o) const;
  bool operator!=(const Value& o) const { return !(*this == o); }
  // Ordering for interval checks on numeric values and lexicographic order on strings.
  // Returns false in `less` when the two values are not comparable.
  bool lessThan(const Value& o, bool* comparable) const;

 private:
  std::variant<bool, int64_t, double, std::string, std::vector<std::string>> v_;
};

// A typed condition over a state variable: variable OP value.
struct Condition {
  std::string variable;
  ConditionOp op = ConditionOp::EQ;
  Value value;
  std::string toString() const;
};

// A state change instruction: variable OP value.
struct Effect {
  std::string variable;
  EffectOp op = EffectOp::SET;
  Value value;
  std::string toString() const;
};

struct InputSpec {
  std::string name;
  std::string type = "string";
  std::string domain = "any";
  std::vector<std::string> domainValues;
  bool required = true;
};

struct OutputSpec {
  std::string name;
  std::string type = "string";
  std::string domain = "any";
  std::vector<std::string> domainValues;
};

// Q_i = (C_time, C_resource, C_money, C_risk, C_energy). Additional attributes are allowed and
// carried in `extra`.
struct QualityAttributes {
  double timeMs = 0.0;
  double money = 0.0;
  double resource = 0.0;
  double risk = 0.0;
  double energy = 0.0;
  std::map<std::string, double> extra;
  // Sequential accumulation: time, money, resource and energy add; risk composes as
  // 1-(1-r1)(1-r2) because independent failure modes accumulate.
  QualityAttributes sequentialSum(const QualityAttributes& o) const;
};

// One availability window for the time dependent form A_i(t).
struct AvailabilityWindow {
  std::vector<std::string> days;  // mon, tue, wed, thu, fri, sat, sun
  int fromMinutes = 0;            // inclusive, minutes after midnight
  int toMinutes = 0;              // exclusive, minutes after midnight
};

struct OperationalSpec {
  QualityAttributes cost;
  double reliability = 1.0;             // Rel_i in [0,1]
  bool available = true;                // A_i static form
  bool windowed = false;                // true when A_i(t) windows are declared
  std::vector<AvailabilityWindow> windows;
  // A_i(t) evaluated at a weekday/minute. A declared window governs (true only inside it);
  // without a window the static flag decides.
  bool availableAt(const std::string& weekday, int minutesAfterMidnight) const;
};

// M_i: execution mechanism. Only the fields relevant to the capability type are filled.
struct ExecutionMechanism {
  CapabilityType kind = CapabilityType::FUNCTION;
  std::string method;     // API
  std::string endpoint;   // API
  std::string operation;  // DATABASE
  std::string table;      // DATABASE
  std::string action;     // GUI
  std::string component;  // GUI
  std::string page;       // GUI
  std::string trigger;    // EVENT
  std::string handler;    // EVENT
  std::string topic;      // MESSAGE
  std::string queue;      // MESSAGE
  std::string function;   // FUNCTION
  std::string modulePath; // FUNCTION
  std::string path;       // FILE
  std::string format;     // FILE
  std::string expression; // COMPUTATION
  std::string artifact;   // COMPUTATION
  std::string service;    // SERVICE
  std::string baseUrl;    // SERVICE
  std::string notes;
  // Human readable one line summary used in logs and reports.
  std::string toString() const;
};

// The formal capability tuple C_i = (T, I, O, P, E, K, R, Q, Rel, A, M).
struct CapabilitySpec {
  std::string id;
  std::string name;
  std::string description;
  CapabilityType type = CapabilityType::FUNCTION;
  std::vector<InputSpec> inputs;              // I_i
  std::vector<OutputSpec> outputs;            // O_i
  std::vector<Condition> preconditions;       // P_i
  std::vector<Effect> effects;                // E_i
  std::vector<Condition> constraints;         // K_i
  std::vector<std::string> resources;         // R_i
  OperationalSpec operational;                // Q_i, Rel_i, A_i
  ExecutionMechanism mechanism;               // M_i
  std::vector<std::string> roles;
  std::map<std::string, Value> stateDeltaHint;
};

// Typed state variable schema of an application.
struct StateVariableSchema {
  std::string name;
  std::string type;  // boolean, integer, real, categorical, enumerated, structured
  std::vector<std::string> domainValues;  // enumerated and categorical
  double domainMin = 0.0;
  double domainMax = 0.0;
  bool bounded = false;   // integer and real with a declared interval
  std::string domainText; // "unbounded", a range rendering, or a free text description
};

struct ResourceSpec {
  std::string id;
  std::string kind;
  bool available = true;
  std::string details;
};

struct ConstraintSpec {
  std::string id;
  std::string kind;  // input, state, resource, security, temporal, dependency, domain
  std::string expression;
  std::string enforcedBy;
};

// The formal application model A = (S, C, S_I, G, R, K) carried by one specification sheet.
struct ApplicationModel {
  std::string moduleId;
  std::string version;
  std::string domain;
  int port = 0;
  std::string baseUrl;
  std::string health;
  std::string description;
  std::string language;
  std::string databaseFile;
  std::string ui;
  std::vector<StateVariableSchema> stateSchema;   // S
  std::map<std::string, Value> initialState;      // S_I
  std::vector<ResourceSpec> resources;            // R
  std::vector<ConstraintSpec> constraints;        // K
  std::vector<Condition> goal;                    // G
  std::vector<CapabilitySpec> capabilities;       // C
};

class AppState {
 public:
  void set(const std::string& key, const Value& v);
  void remove(const std::string& key);
  bool has(const std::string& key) const;
  Value get(const std::string& key, const Value& dflt = Value(0)) const;
  const std::map<std::string, Value>& all() const { return m_; }
  std::vector<std::string> keysSorted() const;
  std::string toString() const;
  // Convenience for the many places that carry bindings as a plain map (application initial
  // states, JSON payloads, database rows).
  static AppState fromMap(const std::map<std::string, Value>& values);

 private:
  std::map<std::string, Value> m_;
};

struct Goal {
  std::vector<Condition> conditions;
  bool isSatisfied(const AppState& state) const;
  std::string toString() const;
};

// Typed condition evaluation against a concrete state. Used by the compatibility engine, the
// planner, the gateway and the tests. Missing variables evaluate to false for every operator
// except NEQ, which treats a missing binding as "not equal to the value".
bool satisfies(const Condition& c, const AppState& state);
// Apply one effect, producing the successor binding for the affected variable.
void applyEffect(Effect e, AppState& state);
// Apply a whole effect set in order.
void applyEffects(const std::vector<Effect>& effects, AppState& state);

}  // namespace core
}  // namespace careweave
