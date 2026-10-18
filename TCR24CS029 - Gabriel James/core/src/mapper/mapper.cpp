#include "careweave/mapper/mapper.hpp"

#include <algorithm>
#include <iomanip>
#include <limits>
#include <set>
#include <sstream>

#include "careweave/embedding/blocks.hpp"

namespace careweave {
namespace mapper {

namespace {

std::string format(double v) {
  std::ostringstream os;
  os << std::setprecision(4) << v;
  return os.str();
}

double fieldSimilarity(const embedding::Encoder& encoder, const std::string& reqName,
                       const std::string& reqType, const std::string& reqDomain,
                       const std::vector<std::string>& reqValues, const std::string& candName,
                       const std::string& candType, const std::string& candDomain,
                       const std::vector<std::string>& candValues) {
  // The name carries the vocabulary signal through the exact sparse cosine, because hashed
  // projections of short names are collision dominated. Type, domain and declared enum values
  // contribute as exact structural agreement, so a mismatch pulls the score down instead of a
  // shared boilerplate pulling every string field towards 1.
  const double name = std::max(0.0, embedding::TextFeatures::sparseCosine(reqName, candName));
  double structure = 0.0;
  structure += 0.55 * (reqType == candType ? 1.0 : 0.0);
  structure += 0.25 * (reqDomain == candDomain ? 1.0 : 0.0);
  std::set<std::string> reqSet(reqValues.begin(), reqValues.end());
  std::set<std::string> candSet(candValues.begin(), candValues.end());
  if (!reqSet.empty() || !candSet.empty()) {
    size_t overlap = 0;
    for (const auto& v : reqSet) {
      if (candSet.count(v) != 0) ++overlap;
    }
    const size_t unionSize = reqSet.size() + candSet.size() - overlap;
    structure += 0.20 * (unionSize == 0 ? 0.0
                                        : static_cast<double>(overlap) /
                                              static_cast<double>(unionSize));
  } else {
    structure += 0.20;  // both sides declare no enum domain: a structural match
  }
  (void)encoder;  // the projected field identity remains available to the IO blocks
  return 0.7 * name + 0.3 * std::min(1.0, structure);
}

// Builds the similarity matrix between two field lists and assigns optimally.
void assignFields(const embedding::Encoder& encoder, const std::vector<core::InputSpec>& required,
                  const std::vector<core::InputSpec>& provided, std::vector<FieldMatch>& out) {
  const size_t rows = required.size();
  const size_t cols = provided.size();
  std::vector<std::vector<double>> sim(rows, std::vector<double>(cols, 0.0));
  for (size_t i = 0; i < rows; ++i) {
    for (size_t j = 0; j < cols; ++j) {
      sim[i][j] = fieldSimilarity(encoder, required[i].name, required[i].type, required[i].domain,
                                  required[i].domainValues, provided[j].name, provided[j].type,
                                  provided[j].domain, provided[j].domainValues);
    }
  }
  const std::vector<int> assignment = hungarianAssignment(sim);
  for (size_t i = 0; i < rows; ++i) {
    FieldMatch m;
    m.required = required[i].name;
    if (assignment[i] >= 0 && static_cast<size_t>(assignment[i]) < cols) {
      m.provided = provided[static_cast<size_t>(assignment[i])].name;
      m.similarity = sim[i][static_cast<size_t>(assignment[i])];
      m.assigned = true;
    }
    out.push_back(m);
  }
}

void assignFields(const embedding::Encoder& encoder, const std::vector<core::OutputSpec>& required,
                  const std::vector<core::OutputSpec>& provided, std::vector<FieldMatch>& out) {
  const size_t rows = required.size();
  const size_t cols = provided.size();
  std::vector<std::vector<double>> sim(rows, std::vector<double>(cols, 0.0));
  for (size_t i = 0; i < rows; ++i) {
    for (size_t j = 0; j < cols; ++j) {
      sim[i][j] = fieldSimilarity(encoder, required[i].name, required[i].type, required[i].domain,
                                  required[i].domainValues, provided[j].name, provided[j].type,
                                  provided[j].domain, provided[j].domainValues);
    }
  }
  const std::vector<int> assignment = hungarianAssignment(sim);
  for (size_t i = 0; i < rows; ++i) {
    FieldMatch m;
    m.required = required[i].name;
    if (assignment[i] >= 0 && static_cast<size_t>(assignment[i]) < cols) {
      m.provided = provided[static_cast<size_t>(assignment[i])].name;
      m.similarity = sim[i][static_cast<size_t>(assignment[i])];
      m.assigned = true;
    }
    out.push_back(m);
  }
}

double meanFieldScore(const std::vector<FieldMatch>& matches) {
  if (matches.empty()) return 1.0;  // nothing required means nothing can be missed
  double total = 0.0;
  for (const auto& m : matches) total += m.assigned ? m.similarity : 0.0;
  return total / static_cast<double>(matches.size());
}

}  // namespace

std::vector<int> hungarianAssignment(const std::vector<std::vector<double>>& similarity) {
  const size_t rows = similarity.size();
  if (rows == 0) return {};
  const size_t cols = similarity[0].size();
  const size_t n = std::max(rows, cols);
  const double kNoMatchCost = 1.0;  // a padded pair scores similarity 0
  std::vector<std::vector<double>> cost(n, std::vector<double>(n, kNoMatchCost));
  for (size_t i = 0; i < rows; ++i) {
    for (size_t j = 0; j < cols; ++j) {
      cost[i][j] = 1.0 - similarity[i][j];
    }
  }
  // Kuhn-Munkres with potentials, square matrix, rows <= columns trivially satisfied because the
  // matrix is square. Potentials u for rows, v for columns, p[j] the row matched to column j.
  const double kInf = std::numeric_limits<double>::infinity();
  std::vector<double> u(n + 1, 0.0), v(n + 1, 0.0);
  std::vector<int> p(n + 1, 0), way(n + 1, 0);
  for (size_t i = 1; i <= n; ++i) {
    p[0] = static_cast<int>(i);
    size_t j0 = 0;
    std::vector<double> minv(n + 1, kInf);
    std::vector<bool> used(n + 1, false);
    do {
      used[j0] = true;
      const size_t i0 = static_cast<size_t>(p[j0]);
      double delta = kInf;
      size_t j1 = 0;
      for (size_t j = 1; j <= n; ++j) {
        if (used[j]) continue;
        const double cur = cost[i0 - 1][j - 1] - u[i0] - v[j];
        if (cur < minv[j]) {
          minv[j] = cur;
          way[j] = static_cast<int>(j0);
        }
        if (minv[j] < delta) {
          delta = minv[j];
          j1 = j;
        }
      }
      for (size_t j = 0; j <= n; ++j) {
        if (used[j]) {
          u[static_cast<size_t>(p[j])] += delta;
          v[j] -= delta;
        } else {
          minv[j] -= delta;
        }
      }
      j0 = j1;
    } while (p[j0] != 0);
    do {
      const size_t j1 = static_cast<size_t>(way[j0]);
      p[j0] = p[j1];
      j0 = j1;
    } while (j0 != 0);
  }
  std::vector<int> assignment(rows, -1);
  for (size_t j = 1; j <= n; ++j) {
    const int row = p[j] - 1;
    if (p[j] > 0 && static_cast<size_t>(row) < rows) {
      const size_t col = j - 1;
      assignment[static_cast<size_t>(row)] = col < cols ? static_cast<int>(col) : -1;
    }
  }
  return assignment;
}

MatchResult Mapper::score(const core::CapabilitySpec& requirement,
                          const core::CapabilitySpec& candidate) const {
  MatchResult result;
  result.candidateId = candidate.id;
  result.candidateName = candidate.name;
  result.type = candidate.type;
  result.kindMatches = candidate.type == requirement.type;

  // Name and description text through the exact sparse cosine: hashed projections of short
  // strings are collision dominated (two unrelated capability names can project to a cosine near
  // 0.6 at 40 dimensions), so the matching component measures the feature space directly.
  result.nameSimilarity =
      std::max(0.0, embedding::TextFeatures::sparseCosine(
                        requirement.name + " " + requirement.description,
                        candidate.name + " " + candidate.description));

  // Typed IO fields through the Hungarian assignment.
  assignFields(encoder_, requirement.inputs, candidate.inputs, result.inputs);
  assignFields(encoder_, requirement.outputs, candidate.outputs, result.outputs);
  result.fieldSimilarity =
      0.5 * (meanFieldScore(result.inputs) + meanFieldScore(result.outputs));

  // Desired effects and preconditions in the signed condition space.
  const double effectAgreement = std::max(
      0.0, 0.5 * (1.0 + embedding::VectorMath::cosine(encoder_.signedEffectVector(requirement),
                                                      encoder_.signedEffectVector(candidate))));
  const double preconditionAgreement = std::max(
      0.0,
      0.5 * (1.0 + embedding::VectorMath::cosine(encoder_.signedPreconditionVector(requirement),
                                                 encoder_.signedPreconditionVector(candidate))));
  const bool hasEffects = !requirement.effects.empty();
  const bool hasPreconditions = !requirement.preconditions.empty();
  const bool hasConditions = hasEffects || hasPreconditions;
  if (hasEffects && hasPreconditions) {
    result.conditionSimilarity = 0.5 * (effectAgreement + preconditionAgreement);
  } else if (hasEffects) {
    result.conditionSimilarity = effectAgreement;
  } else if (hasPreconditions) {
    result.conditionSimilarity = preconditionAgreement;
  } else {
    result.conditionSimilarity = 0.0;  // unused: the condition weight is redistributed
  }

  // Views the requirement does not declare stay neutral instead of granting a free 1.0: their
  // weight is redistributed over the declared views, so a requirement that only names a
  // capability is judged on its name and fields rather than on the absence of conditions.
  const bool hasFields = !requirement.inputs.empty() || !requirement.outputs.empty();
  const double wName = weights_.name;
  const double wFields = hasFields ? weights_.fields : 0.0;
  const double wConditions = hasConditions ? weights_.conditions : 0.0;
  const double wTotal = wName + wFields + wConditions;
  result.total = (wName * result.nameSimilarity + wFields * result.fieldSimilarity +
                  wConditions * result.conditionSimilarity) /
                 wTotal;

  result.explanation.push_back("name similarity " + format(result.nameSimilarity));
  result.explanation.push_back("field similarity " + format(result.fieldSimilarity) + " (inputs " +
                               format(meanFieldScore(result.inputs)) + ", outputs " +
                               format(meanFieldScore(result.outputs)) + ")");
  result.explanation.push_back("condition similarity " +
                               (hasConditions ? format(result.conditionSimilarity)
                                              : std::string("not declared")) +
                               " (effects " + format(effectAgreement) + ", preconditions " +
                               format(preconditionAgreement) + ")");
  for (const auto& m : result.inputs) {
    if (m.assigned) {
      result.explanation.push_back("input " + m.required + " -> " + m.provided + " (" +
                                   format(m.similarity) + ")");
    } else {
      result.explanation.push_back("input " + m.required + " -> unassigned");
    }
  }
  for (const auto& m : result.outputs) {
    if (m.assigned) {
      result.explanation.push_back("output " + m.required + " -> " + m.provided + " (" +
                                   format(m.similarity) + ")");
    } else {
      result.explanation.push_back("output " + m.required + " -> unassigned");
    }
  }
  return result;
}

std::vector<MatchResult> Mapper::rank(const core::CapabilitySpec& requirement,
                                      const std::vector<core::CapabilitySpec>& candidates) const {
  std::vector<MatchResult> out;
  out.reserve(candidates.size());
  for (const auto& c : candidates) out.push_back(score(requirement, c));
  std::stable_sort(out.begin(), out.end(),
                   [](const MatchResult& a, const MatchResult& b) { return a.total > b.total; });
  return out;
}

Mapper::Selection Mapper::select(const std::vector<MatchResult>& ranked, double minScore,
                                 double ambiguityMargin) const {
  Selection selection;
  if (ranked.empty()) {
    selection.belowThreshold = true;
    return selection;
  }
  if (ranked[0].total < minScore) {
    selection.belowThreshold = true;
    return selection;
  }
  selection.bestIndex = 0;
  if (ranked.size() > 1) {
    selection.margin = ranked[0].total - ranked[1].total;
    selection.ambiguous = selection.margin < ambiguityMargin;
  }
  if (selection.ambiguous) {
    // Delivery kind tie break: the candidates within the ambiguity margin of the best score are
    // inspected, and when the requirement's declared kind singles out exactly one of them the
    // tie is decided by it. A tie between two candidates of the requested kind stays ambiguous.
    std::vector<size_t> window;
    for (size_t i = 0; i < ranked.size(); ++i) {
      if (ranked[0].total - ranked[i].total < ambiguityMargin) window.push_back(i);
    }
    size_t matching = 0;
    size_t matchingIndex = 0;
    for (size_t i : window) {
      if (ranked[i].kindMatches) {
        ++matching;
        matchingIndex = i;
      }
    }
    if (matching == 1) {
      selection.bestIndex = static_cast<int>(matchingIndex);
      selection.kindTieBreak = true;
      selection.ambiguous = false;
    }
  }
  return selection;
}

std::string MatchResult::render() const {
  std::ostringstream os;
  os << "candidate " << candidateId << " (" << candidateName << "): total " << format(total)
     << " [name " << format(nameSimilarity) << ", fields " << format(fieldSimilarity)
     << ", conditions " << format(conditionSimilarity) << "]\n";
  for (const auto& line : explanation) os << "    " << line << "\n";
  return os.str();
}

}  // namespace mapper
}  // namespace careweave
