#ifndef EMBEDDING_HPP
#define EMBEDDING_HPP

#include "Capability.hpp"
#include <vector>

class EmbeddingFramework
{
private:
    size_t state_dim;

public:
    explicit EmbeddingFramework(size_t dimension);

    // Encodes a capability into the unified (2d + 3) vector space
    std::vector<double> encode(const Capability &cap) const;

    // Computes compatibility score via inner product between effects of C1 and preconditions of C2
    double compute_compatibility(const Capability &c1, const Capability &c2) const;

    // Composes C1 and C2 -> C12 = C2 o C1
    Capability compose(const Capability &c1, const Capability &c2) const;

    // Calculates cosine similarity between two dense embedding vectors
    static double cosine_similarity(const std::vector<double> &v1, const std::vector<double> &v2);
};

#endif // EMBEDDING_HPP