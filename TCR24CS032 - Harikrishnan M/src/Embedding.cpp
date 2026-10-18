#include "Embedding.hpp"
#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>

EmbeddingFramework::EmbeddingFramework(size_t dimension) : state_dim(dimension) {}

std::vector<double> EmbeddingFramework::encode(const Capability &cap) const
{
    if (cap.get_state_dimension() != state_dim)
    {
        throw std::invalid_argument("Capability dimension does not match embedding framework dimension.");
    }
    return cap.to_embedding_vector();
}

double EmbeddingFramework::compute_compatibility(const Capability &c1, const Capability &c2) const
{
    if (c1.effects.size() != state_dim || c2.preconditions.size() != state_dim)
    {
        throw std::invalid_argument("Dimension mismatch in compatibility calculation.");
    }
    // Inner product: <e1, p2>
    double inner_product = 0.0;
    for (size_t i = 0; i < state_dim; ++i)
    {
        inner_product += c1.effects[i] * c2.preconditions[i];
    }
    return inner_product;
}

Capability EmbeddingFramework::compose(const Capability &c1, const Capability &c2) const
{
    if (c1.get_state_dimension() != state_dim || c2.get_state_dimension() != state_dim)
    {
        throw std::invalid_argument("Dimension mismatch during capability composition.");
    }

    std::vector<double> p_composite(state_dim);
    std::vector<double> e_composite(state_dim);

    // Preconditions math: p12 = max(p1, p2 - e1)
    for (size_t i = 0; i < state_dim; ++i)
    {
        double diff = c2.preconditions[i] - c1.effects[i];
        p_composite[i] = std::max(c1.preconditions[i], std::max(0.0, diff));
    }

    // Effects math: e12 = max(e1, e2)
    for (size_t i = 0; i < state_dim; ++i)
    {
        e_composite[i] = std::max(c1.effects[i], c2.effects[i]);
    }

    // Operational Attributes Compounding
    double cost_composite = c1.cost + c2.cost;
    double rel_composite = c1.reliability * c2.reliability;
    double avail_composite = std::min(c1.availability, c2.availability);

    std::string comp_id = "(" + c1.id + " o " + c2.id + ")";
    std::string comp_name = c1.name + " -> " + c2.name;

    return Capability(comp_id, comp_name, "COMPOSITE", p_composite, e_composite,
                      cost_composite, rel_composite, avail_composite);
}

double EmbeddingFramework::cosine_similarity(const std::vector<double> &v1, const std::vector<double> &v2)
{
    if (v1.size() != v2.size() || v1.empty())
        return 0.0;

    double dot = 0.0, norm_a = 0.0, norm_b = 0.0;
    for (size_t i = 0; i < v1.size(); ++i)
    {
        dot += v1[i] * v2[i];
        norm_a += v1[i] * v1[i];
        norm_b += v2[i] * v2[i];
    }
    if (norm_a == 0.0 || norm_b == 0.0)
        return 0.0;
    return dot / (std::sqrt(norm_a) * std::sqrt(norm_b));
}