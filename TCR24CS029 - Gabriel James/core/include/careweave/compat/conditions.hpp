#pragma once
// Abstract state domain and typed entailment.
//
// The assignment requires entailment checks E_i |= P_j over typed conditions, including numeric
// intervals and enum sets. This component implements a small abstract domain:
//
//   Domain := Boolean{true}, Boolean{false}, Boolean{true,false}
//           | Interval[lo, hi] with optional open bounds
//           | EnumSet{members} | Universe (everything)
//
// Effects are applied to a domain with interval arithmetic (SET replaces, INCREMENT shifts both
// bounds, DECREMENT shifts, DELETE clears). A precondition is then evaluated against the
// resulting domain and reported as ENTAILED, POSSIBLE, CONFLICT or UNKNOWN:
//
//   ENTAILED  the domain satisfies the condition for every member  (E_i |= P_j holds)
//   POSSIBLE  some members satisfy it and some do not
//   CONFLICT  no member satisfies it, so the composition can never run
//   UNKNOWN   the variable is not constrained by the domain at all
//
// This is what makes CreateOrder -> MakePayment entailed while CreateOrder -> CancelCart is a
// conflict (Order.exists = true against a precondition of Order.exists = false).
#include <map>
#include <string>
#include <vector>

#include "careweave/core/types.hpp"

namespace careweave {
namespace compat {

// Tri-state satisfaction lattice.
enum class Truth { TRUE_, FALSE_, UNKNOWN_ };

std::string truthToString(Truth t);
// Entailment outcome for one condition.
enum class Entailment { ENTAILED, POSSIBLE, CONFLICT, UNKNOWN };

std::string entailmentToString(Entailment e);

struct Domain {
  enum class Kind { UNIVERSE, BOOL_SET, INTERVAL, ENUM_SET };
  Kind kind = Kind::UNIVERSE;
  bool boolValue = false;          // BOOL_SET: the single allowed value
  bool boolExact = false;          // BOOL_SET: true when a single value is pinned
  double lo = 0.0;                 // INTERVAL
  double hi = 0.0;
  bool loOpen = false;
  bool hiOpen = false;
  bool numericIntegral = false;    // INTERVAL over integers
  std::vector<std::string> members;  // ENUM_SET

  static Domain universe();
  static Domain boolean(bool value);
  static Domain booleanBoth();
  static Domain interval(double lo, double hi, bool integral);
  static Domain enumerated(std::vector<std::string> members);
  static Domain singleton(const core::Value& value);
  std::string toString() const;
};

// The abstract state: one domain per variable.
class DomainState {
 public:
  // The full snapshot as a domain per variable (used for goal and state analysis).
  static DomainState fromConcrete(const core::AppState& state);
  // Apply an effect set. Only variables the effects mention are seeded from the concrete state,
  // so interval arithmetic has a base to shift while everything else stays unconstrained: a
  // pairwise analysis must not assume that nothing else ran in between.
  static DomainState apply(const core::AppState& state, const std::vector<core::Effect>& effects);
  void set(const std::string& variable, const Domain& d);
  bool has(const std::string& variable) const;
  Domain get(const std::string& variable) const;  // universe when unknown
  std::vector<std::string> keysSorted() const;
  std::string toString() const;

 private:
  std::map<std::string, Domain> domains_;
};

// Evaluate a condition against a domain.
Entailment evaluate(const Domain& domain, const core::Condition& condition);

// Per-precondition entailment result for an effect set.
struct EffectEntailment {
  std::string precondition;   // rendered condition
  Entailment result = Entailment::UNKNOWN;
  std::string explanation;
};

struct EntailmentReport {
  std::vector<EffectEntailment> items;
  // ENTAILED when every precondition is entailed, CONFLICT when any is a conflict, POSSIBLE
  // when the rest is possible or unknown.
  Entailment overall = Entailment::UNKNOWN;
  int entailed = 0, possible = 0, conflicts = 0, unknown = 0;
  std::string render() const;
};

// E_i |= P_j: does the effect set of the earlier capability establish the preconditions of the
// later one, starting from the given initial state? Variables the effects never write stay
// unconstrained and their preconditions report UNKNOWN (or POSSIBLE overall), never a conflict.
EntailmentReport entails(const core::AppState& initial, const std::vector<core::Effect>& effects,
                         const std::vector<core::Condition>& preconditions);

// True when the two condition sets cannot hold at the same time in any state: the conditions on
// each variable are intersected and the result is checked for emptiness. Used to reject
// compositions whose preconditions are mutually exclusive (Order.exists = true against
// Order.exists = false).
bool conditionsConflict(const std::vector<core::Condition>& a,
                        const std::vector<core::Condition>& b);

}  // namespace compat
}  // namespace careweave
