#pragma once
// Encoders: the public interface required by Assignment 2 Deliverable 2.
//
//   encode(state)       -> Vector
//   encode(goal)        -> Vector
//   encode(capability)  -> Vector (atomic or composite)
//   compose(capabilities) -> composite capability plus its vector (see compose.hpp)
//   similarity(x, y)    -> scalar, plus a partitioned variant per block
//
// Everything is deterministic: the same input always produces the identical vector, including
// across processes and machines, because all hashing is FNV-1a over stable string keys and all
// weights come from tables compiled into the binary.
#include <map>
#include <string>
#include <vector>

#include "careweave/core/types.hpp"
#include "careweave/embedding/blocks.hpp"
#include "careweave/embedding/text.hpp"
#include "careweave/embedding/vector.hpp"

namespace careweave {
namespace embedding {

// A capability vector plus its named blocks.
struct EncodedCapability {
  std::string id;
  std::string name;
  Vector vector;                          // the unified partitioned vector
  std::map<std::string, Vector> blocks;   // block name -> block vector
  core::CapabilitySpec spec;              // the source tuple, kept for explanations

  Vector block(const std::string& name) const;
  // Semantic (functional) similarity view: preconditions, effects, delta, inputs, outputs.
  Vector functionalView() const;
  // Implementation view: type, mechanism, resources and the quality block.
  Vector implementationView() const;
  // The 64 dimensional condition space view, used for cross-space comparisons.
  Vector conditionView() const;
};

// Any encoded entity, so that similarity(x, y) works across kinds.
struct EncodedEntity {
  enum class Kind { STATE, GOAL, CAPABILITY };
  Kind kind = Kind::STATE;
  std::string label;
  Vector vector;
  std::map<std::string, Vector> blocks;

  static EncodedEntity state(const core::AppState& s, const std::string& label = "state");
  static EncodedEntity goal(const core::Goal& g, const std::string& label = "goal");
  static EncodedEntity capability(const EncodedCapability& c);
};

class Encoder {
 public:
  // encode(state): [ condition core (64) ; numeric values (32) ; coverage (32) ] = 128
  Vector encodeState(const core::AppState& state) const;
  // encode(goal): [ condition core (64) ; goal values (32) ; goal mask (32) ] = 128
  Vector encodeGoal(const core::Goal& goal) const;
  // encode(capability): the partitioned 259 dimensional vector described in blocks.hpp
  Vector encodeCapability(const core::CapabilitySpec& capability) const;
  EncodedCapability encodeCapabilityDetailed(const core::CapabilitySpec& capability) const;

  // similarity(x, y). Same kind: cosine over the full vector. State against goal (or the goal
  // core against a capability condition block): cosine over the shared 64 dimensional condition
  // space, which is the projection that makes the three spaces comparable.
  double similarity(const EncodedEntity& a, const EncodedEntity& b) const;
  // Partitioned similarity: per-block cosine for capabilities.
  std::map<std::string, double> similarityPartitioned(const EncodedEntity& a,
                                                      const EncodedEntity& b) const;
  // Weighted combination of the partitions. Weights are documented in
  // documents/03_EMBEDDING_DESIGN.md and used by the experiments.
  static double functionalityWeight(const std::string& block);
  static double implementationWeight(const std::string& block);

  // Building blocks exposed for the experiments, the mapper and the compatibility engine.
  Vector encodeConditionBlock(const std::vector<core::Condition>& conditions) const;
  Vector encodeEffectBlock(const std::vector<core::Effect>& effects,
                           const std::string* nameHint) const;
  Vector encodeVariableIdentity(const std::string& variable) const;
  Vector encodeFieldIdentity(const std::string& name, const std::string& type,
                             const std::string& domain,
                             const std::vector<std::string>& domainValues) const;
  // Signed value in [-1,1]: booleans map to +/-1, numbers to tanh(v/100), strings to their
  // stable projection mapped onto [-1,1], enum sets to the mean of their members.
  static double signedValue(const core::Value& value);
  // The signed structured condition vector of a capability, used by the vector compatibility
  // score so that Order.exists = true and Order.exists = false land on opposite sides.
  Vector signedPreconditionVector(const core::CapabilitySpec& capability) const;
  Vector signedEffectVector(const core::CapabilitySpec& capability) const;
  // (text 40 dims ; structured 24 dims) with the shared condition seed.
  Vector conditionSpaceFromFeatures(const std::vector<Feature>& textFeatures,
                                    const std::vector<Feature>& structFeatures) const;
  Vector stateCore(const core::AppState& state) const;
  Vector goalCore(const core::Goal& goal) const;
  // Mean of the per-variable identity cosines; used by the vector compatibility score to
  // measure how much of a later precondition the earlier effects could write at all.
  double variableCoverage(const core::CapabilitySpec& earlier,
                          const core::CapabilitySpec& later) const;
};

}  // namespace embedding
}  // namespace careweave
