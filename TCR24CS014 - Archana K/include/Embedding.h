#ifndef EMBEDDING_H
#define EMBEDDING_H

#include "Types.h"
#include <vector>
#include <string>

/**
 * @brief Encodes a formal State into a unified multidimensional numerical feature vector.
 *
 * @param state The formal State instance to encode.
 * @return std::vector<double> Numerical feature vector.
 */
std::vector<double> encodeState(const State& state);

/**
 * @brief Encodes a formal Goal into a unified multidimensional numerical feature vector.
 *
 * @param goal The formal Goal instance to encode.
 * @return std::vector<double> Numerical feature vector.
 */
std::vector<double> encodeGoal(const Goal& goal);

/**
 * @brief Encodes a formal Capability into a unified multidimensional numerical feature vector.
 *
 * Captures semantic and operational information across:
 * - capability type (one-hot categorical encoding)
 * - operational attributes (normalized cost, reliability, availability)
 * - preconditions (state predicate requirements)
 * - effects (state predicate mutations)
 * - inputs (data flow consumption attributes)
 * - outputs (data flow production attributes)
 * - resources (hardware/software resource dependencies)
 * - constraints (operational and safety invariant assertions)
 *
 * @param capability The formal Capability instance to encode.
 * @return std::vector<double> Numerical feature vector.
 */
std::vector<double> encodeCapability(const Capability& capability);

/**
 * @brief Computes the Cosine Similarity between two numerical feature vectors:
 *        similarity(a, b) = (a . b) / (||a||_2 * ||b||_2)
 *
 * Returns 0.0 if either vector has near-zero magnitude.
 * Throws std::invalid_argument if vectors have mismatched dimensions.
 *
 * @param a First feature vector.
 * @param b Second feature vector.
 * @return double Cosine similarity score in range [-1.0, 1.0].
 */
double similarity(const std::vector<double>& a, const std::vector<double>& b);

/**
 * @brief Determines if two capabilities are compatible for sequential pipeline composition (first -> second).
 *
 * Evaluates:
 * 1. Output-Input compatibility: Whether outputs produced by 'first' satisfy
 *    the inputs required by 'second'.
 * 2. Effect-Precondition compatibility: Whether effects produced by 'first' satisfy
 *    preconditions of 'second' without any contradictory state assignments.
 *
 * @param first The upstream capability executed first.
 * @param second The downstream capability executed second.
 * @return bool True if composition is valid and executable; false otherwise.
 */
bool areCompatible(const Capability& first, const Capability& second);

/**
 * @brief Generates a comprehensive diagnostic report detailing compatibility checks.
 *
 * @param first Upstream capability.
 * @param second Downstream capability.
 * @return CompatibilityReport Detailed analysis structure.
 */
CompatibilityReport checkCompatibility(const Capability& first, const Capability& second);

/**
 * @brief Composes two compatible capabilities into a single unified composite capability.
 *
 * Merging rules:
 * - inputs: In(c1) U (In(c2) \ Out(c1))  [internal data pipeline dependencies resolved]
 * - outputs: Out(c1) U Out(c2)
 * - preconditions: Pre(c1) U (Pre(c2) \ Eff(c1))  [preconditions satisfied by c1 removed]
 * - effects: Eff(c1) sequentially updated with Eff(c2)
 * - constraints: Constraints(c1) U Constraints(c2)
 * - resources: Resources(c1) U Resources(c2)
 * - cost: c1.cost + c2.cost (additive)
 * - reliability: c1.reliability * c2.reliability (multiplicative serial failure model)
 * - availability: c1.availability * c2.availability (multiplicative serial availability model)
 *
 * @param c1 Upstream capability.
 * @param c2 Downstream capability.
 * @param compositeName Optional custom name for the resulting composite capability.
 * @return Capability The synthesized composite capability.
 */
Capability composeCapabilities(const Capability& c1, const Capability& c2, const std::string& compositeName = "");

/**
 * @brief Composes a chain of multiple capabilities in sequential execution order.
 *
 * @param chain List of capabilities to compose sequentially.
 * @param compositeName Optional custom name for the composite capability.
 * @return Capability Synthesized composite capability.
 */
Capability composeCapabilities(const std::vector<Capability>& chain, const std::string& compositeName = "");

/**
 * @brief Synthesizes and encodes a composite capability directly into a numerical feature vector.
 *
 * @param c1 Upstream capability.
 * @param c2 Downstream capability.
 * @param compositeName Optional custom name for composite capability.
 * @return std::vector<double> Feature vector of the composed capability.
 */
std::vector<double> encodeCompositeCapability(const Capability& c1, const Capability& c2, const std::string& compositeName = "");

/**
 * @brief Synthesizes and encodes a chain of capabilities into a numerical feature vector.
 *
 * @param chain List of capabilities in execution sequence.
 * @param compositeName Optional custom name.
 * @return std::vector<double> Feature vector of the composed capability.
 */
std::vector<double> encodeCompositeCapability(const std::vector<Capability>& chain, const std::string& compositeName = "");

/**
 * @brief Computes the goal relevance score determining whether capability effects
 *        help satisfy the target goal conditions.
 *
 * Leverages vector alignment between the capability's effect subspace and the
 * desired goal conditions vector in the shared semantic space.
 *
 * @param capability The capability whose effects are evaluated.
 * @param goal The target goal conditions.
 * @return double Relevance score in range [0.0, 1.0].
 */
double goalRelevance(const Capability& capability, const Goal& goal);

/**
 * @brief Formats and prints a feature vector to standard output.
 *
 * @param label Prefix label.
 * @param vec The feature vector.
 * @param maxElements Maximum number of elements to display before truncating.
 */
void printVector(const std::string& label, const std::vector<double>& vec, size_t maxElements = 12);

/**
 * @brief Prints an ASCII formatted pairwise similarity matrix.
 *
 * @param labels Row/column labels.
 * @param matrix 2D matrix of similarity values.
 */
void printSimilarityMatrix(const std::vector<std::string>& labels, const std::vector<std::vector<double>>& matrix);

/**
 * @brief Returns an explanatory string outlining the embedding dimensions and semantic partition offsets.
 */
std::string describeEmbeddingLayout();

#endif // EMBEDDING_H
