#pragma once
#include "Types.h"
#include <array>
#include <string>
#include <vector>

namespace capembed {

constexpr std::size_t EMBEDDING_DIM = 92;

using Vector = std::array<double, EMBEDDING_DIM>;

struct CompatibilityResult {
    bool compatible = false;
    bool preconditionSatisfied = false;
    bool contradictionFree = false;
    bool dataflowSatisfied = false;
    std::string explanation;
};

class EmbeddingEngine {
public:
    Vector encodeState(const State& state) const;
    Vector encodeGoal(const Goal& goal) const;
    Vector encodeCapability(const Capability& capability) const;

    double cosineSimilarity(const Vector& a, const Vector& b) const;

    CompatibilityResult checkCompatibility(
        const Capability& first,
        const Capability& second) const;

    bool areCompatible(const Capability& first, const Capability& second) const;

    Capability compose(
        const Capability& first,
        const Capability& second) const;

    Capability composeChain(const std::vector<Capability>& chain) const;

    double goalRelevance(
        const Capability& capability,
        const Goal& goal) const;

private:
    static constexpr std::size_t TYPE_START = 0;
    static constexpr std::size_t OPS_START = 9;
    static constexpr std::size_t PRE_START = 12;
    static constexpr std::size_t EFFECT_START = 28;
    static constexpr std::size_t INPUT_START = 44;
    static constexpr std::size_t OUTPUT_START = 60;
    static constexpr std::size_t RESOURCE_START = 76;
    static constexpr std::size_t CONSTRAINT_START = 84;

    static int stateIndex(const std::string& key);
    static int resourceIndex(const std::string& resource);
    static int constraintIndex(const std::string& constraint);

    static double normalizedCost(double cost);
    static std::string canonicalDataKey(const DataSpec& spec);

    Vector effectOnly(const Capability& capability) const;
};

} // namespace capembed
