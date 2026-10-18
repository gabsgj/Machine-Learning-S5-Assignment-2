#pragma once
// Requirement to capability mapping.
//
// A client requirement is expressed as a capability template (name, description, typed inputs and
// outputs, desired preconditions and effects). The mapper scores it against candidate
// capabilities in three independent views and combines them:
//
//   name        cosine of the name and description text in the shared condition space
//   fields      Hungarian maximum weight assignment over the typed IO fields, so that
//               register_pat binds to Pat_reg through shared tokens, character trigrams and the
//               typed field structure even when the vocabularies differ
//   conditions  cosine of the desired signed effects and preconditions
//
// The assignment is optimal in total similarity, not greedy, and every field pair is reported
// with its similarity so the mapping studio can explain the decision. Confidence is the best
// total; ambiguity compares the best against the runner up, so a near tie is reported as
// ambiguous instead of silently picking one, and a requirement that nothing resembles stays
// below the threshold instead of mapping to an unrelated capability.
#include <string>
#include <vector>

#include "careweave/core/types.hpp"
#include "careweave/embedding/encoders.hpp"

namespace careweave {
namespace mapper {

struct FieldMatch {
  std::string required;
  std::string provided;
  double similarity = 0.0;
  bool assigned = false;
};

struct MatchResult {
  std::string candidateId;
  std::string candidateName;
  double nameSimilarity = 0.0;
  double fieldSimilarity = 0.0;
  double conditionSimilarity = 0.0;
  double total = 0.0;
  // The delivery kind of the candidate and whether it is the kind the requirement asks for.
  // A near tie is resolved by this when it singles out exactly one candidate.
  core::CapabilityType type = core::CapabilityType::API;
  bool kindMatches = true;
  std::vector<FieldMatch> inputs;
  std::vector<FieldMatch> outputs;
  std::vector<std::string> explanation;
  std::string render() const;
};

// Weights used to combine the three views. The defaults are the ones documented in
// documents/04_MAPPING_AND_ADAPTERS.md; the experiments sweep them.
struct Weights {
  double name = 0.35;
  double fields = 0.35;
  double conditions = 0.30;
};

class Mapper {
 public:
  explicit Mapper(Weights weights = Weights()) : weights_(weights) {}

  MatchResult score(const core::CapabilitySpec& requirement,
                    const core::CapabilitySpec& candidate) const;
  // Sorted by total, descending.
  std::vector<MatchResult> rank(const core::CapabilitySpec& requirement,
                                const std::vector<core::CapabilitySpec>& candidates) const;

  struct Selection {
    int bestIndex = -1;      // index into the ranked vector, -1 when nothing passes
    bool ambiguous = false;  // runner up within the margin
    bool belowThreshold = false;
    double margin = 0.0;
    // True when a near tie was decided by the delivery kind of the requirement: exactly one
    // candidate within the margin has the requested kind.
    bool kindTieBreak = false;
  };
  // minScore defaults to the calibrated threshold. Two measurement campaigns fixed it: on the
  // corpus alone every intended mapping scores 0.7909 or above while unrelated corpus
  // capabilities peak at 0.4092, and the adversarial decoys of experiment 4 (capabilities
  // sharing a token with a requirement on purpose) reach 0.4962. 0.55 separates the intended
  // answers from both ceilings with margin on either side. The experiments report the measured
  // separation. ambiguityMargin is the near tie distance.
  Selection select(const std::vector<MatchResult>& ranked, double minScore = 0.55,
                   double ambiguityMargin = 0.05) const;

  const Weights& weights() const { return weights_; }

 private:
  Weights weights_;
  embedding::Encoder encoder_;
};

// Maximum weight assignment over a similarity matrix. Returns, for every row, the assigned
// column or -1 when assigned to a padded dummy column. Exposed for the tests and the mapping
// studio; deterministic for a given matrix.
std::vector<int> hungarianAssignment(const std::vector<std::vector<double>>& similarity);

}  // namespace mapper
}  // namespace careweave
