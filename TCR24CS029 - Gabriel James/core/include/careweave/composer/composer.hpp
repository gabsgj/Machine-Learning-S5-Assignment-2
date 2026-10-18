#pragma once
// Capability composition: C_1 o C_2 o ... o C_n.
//
// A composite capability is itself a capability: it consumes the inputs the sequence cannot bind
// internally, requires the preconditions that no earlier member establishes, carries the net
// state change of the whole sequence, and exposes the union of constrained outputs. The
// composite spec is therefore directly encodable and comparable with atomic capabilities, which
// is what experiment 2 investigates.
//
// Two views of the composite vector are produced and kept separate on purpose:
//
//   algebraic  a blockwise superposition of the member vectors (mean of the condition, IO and
//              implementation parts, sum of the delta superposition, product of reliability,
//              minimum of availability, FUNCTION one-hot for the type)
//   re-encoded the composite specification fed through the ordinary capability encoder
//
// The distance between the two is a measured quantity: when it is small the algebra of the
// embedding is faithful, and the experiments report it per test problem rather than assuming it.
//
// The composition laws implemented here (documented in documents/03_EMBEDDING_DESIGN.md):
//   - effects compose as a per-variable fold: SET overwrites, INCREMENT and DECREMENT accumulate
//     on counters, SET followed by INCREMENT folds into a single SET, DELETE clears earlier
//     writes, and an increment followed by an equal decrement cancels to nothing;
//   - cost attributes (time, money, resource, energy) add, risk accumulates as
//     1-(1-r1)(1-r2), reliability multiplies, availability is the conjunction of both windows
//     A(t), resources and roles union;
//   - composition is associative on all of the above, which the tests verify by comparing the
//     two bracketings.
#include <map>
#include <string>
#include <vector>

#include "careweave/core/types.hpp"
#include "careweave/embedding/encoders.hpp"
#include "careweave/embedding/vector.hpp"

namespace careweave {
namespace composer {

// The net state change of an effect sequence: fold the effects per variable and keep the final
// action, sorted by variable name so the result is deterministic.
std::vector<core::Effect> netEffects(const std::vector<core::CapabilitySpec>& sequence);

// Availability of a composition is the conjunction of the members: windows intersect pairwise.
core::OperationalSpec composeOperational(const core::CapabilitySpec& a,
                                         const core::CapabilitySpec& b);

class Composer {
 public:
  struct Composition {
    core::CapabilitySpec spec;
    embedding::Vector algebraic;
    embedding::Vector reencoded;
    double algebraicVsReencoded = 0.0;  // cosine, in [-1,1]
    double toFirst = 0.0;               // cos(algebraic, v(C_1))
    double toLast = 0.0;                // cos(algebraic, v(C_n))
    std::string id() const { return spec.id; }
  };

  Composer() = default;

  // Compose a non empty sequence in order. A single element composes to an equivalent copy of
  // itself; an empty sequence is rejected by returning an explicitly marked empty composite.
  core::CapabilitySpec composeSpec(const std::vector<core::CapabilitySpec>& sequence) const;
  core::CapabilitySpec composeTwo(const core::CapabilitySpec& a,
                                  const core::CapabilitySpec& b) const;
  embedding::Vector algebraicVector(const std::vector<core::CapabilitySpec>& sequence) const;
  Composition compose(const std::vector<core::CapabilitySpec>& sequence) const;

  // The identity element: no preconditions, no effects, no inputs or outputs, reliability 1.
  static core::CapabilitySpec identity();

 private:
  embedding::Encoder encoder_;
};

}  // namespace composer
}  // namespace careweave
