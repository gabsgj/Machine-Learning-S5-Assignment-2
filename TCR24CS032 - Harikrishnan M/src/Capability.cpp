#include "Capability.hpp"
#include <stdexcept>

Capability::Capability()
    : cost(0.0), reliability(1.0), availability(1.0) {}

Capability::Capability(std::string id, std::string name, std::string type,
                       std::vector<double> preconditions, std::vector<double> effects,
                       double cost, double reliability, double availability)
    : id(std::move(id)), name(std::move(name)), implementation_type(std::move(type)),
      preconditions(std::move(preconditions)), effects(std::move(effects)),
      cost(cost), reliability(reliability), availability(availability)
{
    if (this->preconditions.size() != this->effects.size())
    {
        throw std::invalid_argument("Precondition and effect vectors must have identical dimensions.");
    }
}

size_t Capability::get_state_dimension() const
{
    return preconditions.size();
}

std::vector<double> Capability::to_embedding_vector() const
{
    std::vector<double> embedding;
    embedding.reserve(preconditions.size() + effects.size() + 3);

    // Concatenate Preconditions (d)
    embedding.insert(embedding.end(), preconditions.begin(), preconditions.end());
    // Concatenate Effects (d)
    embedding.insert(embedding.end(), effects.begin(), effects.end());
    // Concatenate Operational Attributes (3)
    embedding.push_back(cost);
    embedding.push_back(reliability);
    embedding.push_back(availability);

    return embedding;
}