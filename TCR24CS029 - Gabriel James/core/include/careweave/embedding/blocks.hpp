#pragma once
// Block layout of the CareWeave Mini embeddings.
//
// Design decision (Assignment 2 Deliverable 1): three separate embeddings with one shared
// sub-space rather than a single unified vector.
//
//   phi_S : S -> R^128   state
//   phi_G : G -> R^128   goal
//   phi_C : C -> R^259   capability
//
// The shared sub-space is the 64 dimensional condition space used by the first block of
// phi_S and phi_G (40 text dimensions + 24 structured dimensions) and by the phi_pre and
// phi_eff blocks of phi_C. Because state, goal, precondition and effect all project their
// variables and values through the same hash function and the same dimensions, a cosine
// between any two of those blocks is meaningful, which is what the state awareness, goal
// relevance and precondition-effect checks need.
//
// Capability partition (the layout required by the assignment):
//   phi_C(C) = [ phi_type(9) ; phi_mech(16) ; phi_in(32) ; phi_out(32) ; phi_pre(64) ;
//                phi_eff(64) ; phi_delta(16) ; phi_res(16) ; phi_Q(8) ; phi_rel(1) ;
//                phi_avail(1) ]
//
// Decisions recorded here, justified in documents/03_EMBEDDING_DESIGN.md:
//   1. Type and mechanism are kept inside the capability vector but grouped into the
//      implementation blocks (type, mech) so that functional similarity can be computed by
//      excluding them. They are not folded into the semantic blocks: two capabilities that do
//      the same thing through different mechanisms must stay close in the functional view and
//      far in the implementation view.
//   2. Reliability and availability are represented twice: embedded (phi_rel, phi_avail and
//      the last two slots of phi_Q) so that vector similarity and QoS ranking can see them, and
//      also kept in a separate AttributeVector so that constraints can be enforced exactly
//      (a cost cap is a comparison, not a cosine).
#include <cstdint>
#include <string>
#include <vector>

namespace careweave {
namespace embedding {

struct BlockSpec {
  const char* name;
  size_t offset;
  size_t width;
};

struct Blocks {
  // Capability layout.
  static constexpr size_t kTypeDim = 9;
  static constexpr size_t kMechDim = 16;
  static constexpr size_t kInDim = 32;
  static constexpr size_t kOutDim = 32;
  static constexpr size_t kPreDim = 64;
  static constexpr size_t kEffDim = 64;
  static constexpr size_t kDeltaDim = 16;
  static constexpr size_t kResDim = 16;
  static constexpr size_t kQDim = 8;
  static constexpr size_t kRelDim = 1;
  static constexpr size_t kAvailDim = 1;

  static constexpr size_t kCapabilityDim = kTypeDim + kMechDim + kInDim + kOutDim + kPreDim +
                                           kEffDim + kDeltaDim + kResDim + kQDim + kRelDim +
                                           kAvailDim;  // 259

  // Offsets, in the order of phi_C.
  static constexpr size_t kTypeOffset = 0;
  static constexpr size_t kMechOffset = kTypeOffset + kTypeDim;
  static constexpr size_t kInOffset = kMechOffset + kMechDim;
  static constexpr size_t kOutOffset = kInOffset + kInDim;
  static constexpr size_t kPreOffset = kOutOffset + kOutDim;
  static constexpr size_t kEffOffset = kPreOffset + kPreDim;
  static constexpr size_t kDeltaOffset = kEffOffset + kEffDim;
  static constexpr size_t kResOffset = kDeltaOffset + kDeltaDim;
  static constexpr size_t kQOffset = kResOffset + kResDim;
  static constexpr size_t kRelOffset = kQOffset + kQDim;
  static constexpr size_t kAvailOffset = kRelOffset + kRelDim;

  // Sub-splits inside the condition blocks and the IO blocks.
  static constexpr size_t kCondTextDim = 40;
  static constexpr size_t kCondStructDim = 24;  // 40 + 24 = 64
  // The IO text sub-block is 16 dimensions: with fewer, unrelated field names correlate through
  // hash collisions (the projection noise floor grows like 1/sqrt(dims)) and the mapper could
  // not tell track_id from mrn.
  static constexpr size_t kIoTextDim = 16;
  static constexpr size_t kIoStructDim = 16;  // 16 + 16 = 32

  // State and goal layout: [ text(40) ; struct(24) ; values(32) ; extra(32) ] = 128.
  static constexpr size_t kStateDim = 128;
  static constexpr size_t kGoalDim = 128;
  static constexpr size_t kSharedCoreDim = kCondTextDim + kCondStructDim;  // 64

  // Hash seeds. Distinct seeds keep the blocks statistically independent while the condition
  // space deliberately shares one seed between state, goal, precondition and effect.
  static constexpr uint64_t kConditionSeed = 0x9E3779B97F4A7C15ULL;
  static constexpr uint64_t kIoSeed = 0xC2B2AE3D27D4EB4FULL;
  static constexpr uint64_t kMechSeed = 0x165667B19E3779F9ULL;
  static constexpr uint64_t kResourceSeed = 0x27D4EB2F165667C5ULL;
  static constexpr uint64_t kDeltaSeed = 0x85EBCA77C2B2AE63ULL;
  static constexpr uint64_t kStateValueSeed = 0xD6E8FEB86659FD93ULL;

  static std::vector<BlockSpec> capabilityBlocks();
  // Index of a capability block by name, or -1.
  static int capabilityBlockIndex(const std::string& name);
  // Same-dimension comparison groups: blocks that can be compared without a projection.
  static bool blocksComparable(const std::string& a, const std::string& b);
};

}  // namespace embedding
}  // namespace careweave
