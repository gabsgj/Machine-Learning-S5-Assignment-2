#pragma once
// Deterministic text feature encoder.
//
// The embedding must be reproducible bit for bit across processes and machines, must work
// offline, and must handle the name-resolution problem of the assignment (register_pat must be
// recognisable as the same function as Pat_reg). This component provides the four mechanisms
// the design relies on:
//
//   1. identifier tokenisation: snake_case, camelCase, kebab-case, SHOUT_CASE and letter/digit
//      boundaries are split into lowercase tokens, with a light stemming rule for plurals
//   2. a curated domain synonym lexicon: each token maps to one or more canonical concepts with
//      weights, so patient, pat, client, individual all land on the CAPIENT concept
//   3. character trigram hashing: catches morphology and abbreviations the lexicon misses
//   4. TF-IDF weighting: term frequency within an entity times a fixed inverse document
//      frequency prior, so common verbs contribute less than discriminating ones
//
// Features are projected into a fixed width vector with the signed hashing trick using FNV-1a,
// which is stable across standard library implementations.
#include <map>
#include <string>
#include <vector>

#include "careweave/embedding/vector.hpp"

namespace careweave {
namespace embedding {

struct Feature {
  std::string id;      // "t:patient", "c:patient", "g:pat", "n:patient#3"
  double weight = 1.0;
};

// One token plus the concepts the lexicon maps it to.
struct ConceptMatch {
  std::string concept;
  double weight = 1.0;
};

class Lexicon {
 public:
  static const Lexicon& instance();
  // Concepts associated with a token. Empty when the token is unknown.
  const std::vector<ConceptMatch>& conceptsFor(const std::string& token) const;
  // 1.0 for a canonical term of a concept, less for related terms.
  double conceptWeight(const std::string& token, const std::string& concept) const;
  // Inverse document frequency prior: 0.15 for stopwords and very common API verbs, 1.0 for
  // everything else, 1.4 for the strongly domain specific terms below.
  double idf(const std::string& token) const;
  size_t size() const { return concepts_.size(); }
  // Number of distinct terms in the lexicon, used by the developer guide and the tests.
  size_t termCount() const { return termIndex_.size(); }

 private:
  Lexicon();
  std::map<std::string, std::vector<ConceptMatch>> termIndex_;
  std::map<std::string, int> concepts_;
};

class TextFeatures {
 public:
  // Split an identifier or free text into lowercase tokens.
  static std::vector<std::string> tokenize(const std::string& text);
  // Token features: the token itself, its concepts, and its character trigrams.
  static std::vector<Feature> featuresForToken(const std::string& token);
  // Full feature set for a phrase, with term frequency counted and IDF applied.
  static std::vector<Feature> featuresForText(const std::string& text);
  // Feature list rendered as a "name=weight" string list, used in explanations and reports.
  static std::vector<std::string> explain(const std::string& text);
  // Signed hashing projection into `dims` dimensions. Deterministic.
  static Vector project(const std::vector<Feature>& features, size_t dims, uint64_t seed);
  // Convenience: tokenize, weight, project and L2 normalise.
  static Vector encodeText(const std::string& text, size_t dims, uint64_t seed);
  // Cosine over the sparse feature maps themselves, with no projection into a fixed width block.
  // The short strings of field names carry too few features for a hashed projection of practical
  // width to stay discriminative (accidental collisions between unrelated names would show up as
  // substantial cosine), so matching components use this exact form while the fixed width
  // vectors keep the projected form for cross-space cosine work.
  static double sparseCosine(const std::string& textA, const std::string& textB);
};

}  // namespace embedding
}  // namespace careweave
