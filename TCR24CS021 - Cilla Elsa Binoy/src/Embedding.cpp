#include "Embedding.h"
#include <algorithm>
#include <cmath>
#include <iomanip>
#include <stdexcept>
#include <limits>
#include <sstream>

namespace capembed {

std::string capabilityTypeName(CapabilityType type) {
    switch (type) {
        case CapabilityType::API: return "API";
        case CapabilityType::DATABASE: return "DATABASE";
        case CapabilityType::GUI: return "GUI";
        case CapabilityType::EVENT: return "EVENT";
        case CapabilityType::FUNCTION: return "FUNCTION";
        case CapabilityType::FILE: return "FILE";
        case CapabilityType::COMPUTATION: return "COMPUTATION";
        case CapabilityType::MESSAGE: return "MESSAGE";
        case CapabilityType::SERVICE: return "SERVICE";
    }
    return "UNKNOWN";
}

int EmbeddingEngine::stateIndex(const std::string& key) {
    // Deterministic domain registry for the assignment's application.
    static const std::vector<std::string> keys = {
        "User.authenticated", "User.role", "User.exists", "Cart.exists",
        "Cart.item_count", "Cart.locked", "Order.exists", "Order.status",
        "Order.id", "Payment.status", "Payment.id", "Inventory.available",
        "Notification.sent", "Notification.id", "Transaction.status", "Error",
    };
    for (int i = 0; i < static_cast<int>(keys.size()); ++i)
        if (keys[i] == key) return i;
    return -1;
}

int EmbeddingEngine::resourceIndex(const std::string& resource) {
    static const std::vector<std::string> resources = {
        "DATABASE", "AUTH_TOKEN", "PAYMENT_GATEWAY", "NETWORK",
        "FILESYSTEM", "GPU", "EXTERNAL_SERVICE", "ORDER_DB"
    };
    for (int i = 0; i < static_cast<int>(resources.size()); ++i)
        if (resources[i] == resource) return i;
    return -1;
}

int EmbeddingEngine::constraintIndex(const std::string& constraint) {
    static const std::vector<std::string> constraints = {
        "quantity>0", "quantity<=inventory_available",
        "payment_amount<=transaction_limit", "role=CUSTOMER",
        "role=ADMIN", "authenticated", "network_required", "secure_channel"
    };
    for (int i = 0; i < static_cast<int>(constraints.size()); ++i)
        if (constraints[i] == constraint) return i;
    return -1;
}

double EmbeddingEngine::normalizedCost(double cost) {
    if (cost < 0.0) return 0.0;
    // Saturating normalization: c/(c+50), matching the supplied design.
    return cost / (cost + 50.0);
}

std::string EmbeddingEngine::canonicalDataKey(const DataSpec& spec) {
    return spec.name + "|" + spec.type + "|" + spec.domain;
}

Vector EmbeddingEngine::encodeState(const State& state) const {
    Vector v{};
    for (const auto& [key, value] : state.values) {
        const int idx = stateIndex(key);
        if (idx < 0) continue;
        bool positive = !(value == "false" || value == "FALSE" ||
                           value == "0" || value == "FAILURE" ||
                           value == "NOT_STARTED");
        v[EFFECT_START + static_cast<std::size_t>(idx)] = positive ? 1.0 : -1.0;
    }
    return v;
}

Vector EmbeddingEngine::encodeGoal(const Goal& goal) const {
    Vector v{};
    for (const auto& [key, value] : goal.conditions) {
        const int idx = stateIndex(key);
        if (idx < 0) continue;
        bool positive = !(value == "false" || value == "FALSE" ||
                           value == "0" || value == "FAILURE" ||
                           value == "NOT_STARTED");
        v[EFFECT_START + static_cast<std::size_t>(idx)] = positive ? 1.0 : -1.0;
    }
    return v;
}

Vector EmbeddingEngine::encodeCapability(const Capability& c) const {
    Vector v{};

    // 0..8: capability type one-hot
    v[TYPE_START + static_cast<std::size_t>(c.type)] = 1.0;

    // 9..11: normalized operational attributes
    v[OPS_START + 0] = normalizedCost(c.cost);
    v[OPS_START + 1] = std::clamp(c.reliability, 0.0, 1.0);
    v[OPS_START + 2] = std::clamp(c.availability, 0.0, 1.0);

    // 12..27: preconditions
    for (const auto& [key, value] : c.preconditions) {
        const int idx = stateIndex(key);
        if (idx < 0) continue;
        bool positive = !(value == "false" || value == "FALSE" ||
                           value == "0" || value == "FAILURE" ||
                           value == "NOT_STARTED");
        v[PRE_START + static_cast<std::size_t>(idx)] = positive ? 1.0 : -1.0;
    }

    // 28..43: effects
    for (const auto& [key, value] : c.effects) {
        const int idx = stateIndex(key);
        if (idx < 0) continue;
        bool positive = !(value == "false" || value == "FALSE" ||
                           value == "0" || value == "FAILURE" ||
                           value == "NOT_STARTED");
        v[EFFECT_START + static_cast<std::size_t>(idx)] = positive ? 1.0 : -1.0;
    }

    // 44..59: inputs
    for (const auto& input : c.inputs) {
        const int idx = stateIndex(input.name);
        if (idx >= 0)
            v[INPUT_START + static_cast<std::size_t>(idx)] = 1.0;
    }

    // 60..75: outputs
    for (const auto& output : c.outputs) {
        const int idx = stateIndex(output.name);
        if (idx >= 0)
            v[OUTPUT_START + static_cast<std::size_t>(idx)] = 1.0;
    }

    // 76..83: resources
    for (const auto& resource : c.resources) {
        const int idx = resourceIndex(resource);
        if (idx >= 0)
            v[RESOURCE_START + static_cast<std::size_t>(idx)] = 1.0;
    }

    // 84..91: constraints
    for (const auto& constraint : c.constraints) {
        const int idx = constraintIndex(constraint);
        if (idx >= 0)
            v[CONSTRAINT_START + static_cast<std::size_t>(idx)] = 1.0;
    }

    return v;
}

double EmbeddingEngine::cosineSimilarity(const Vector& a, const Vector& b) const {
    double dot = 0.0, aa = 0.0, bb = 0.0;
    for (std::size_t i = 0; i < EMBEDDING_DIM; ++i) {
        dot += a[i] * b[i];
        aa += a[i] * a[i];
        bb += b[i] * b[i];
    }
    if (aa == 0.0 || bb == 0.0) return 0.0;
    return dot / (std::sqrt(aa) * std::sqrt(bb));
}

CompatibilityResult EmbeddingEngine::checkCompatibility(
    const Capability& first, const Capability& second) const {

    CompatibilityResult r;
    r.contradictionFree = true;

    // Effects of first must not contradict preconditions of second.
    for (const auto& [key, needed] : second.preconditions) {
        auto it = first.effects.find(key);
        if (it != first.effects.end()) {
            if (it->second != needed) {
                r.contradictionFree = false;
                r.explanation = "Contradiction on state variable: " + key;
                return r;
            }
            r.preconditionSatisfied = true;
        }
    }

    // For preconditions not established by first, this is still allowed
    // if it can be treated as an external precondition of the pipeline.
    if (second.preconditions.empty())
        r.preconditionSatisfied = true;

    // If first establishes no precondition, a state-preserving pipeline is
    // allowed when no contradiction exists.
    if (!r.preconditionSatisfied && !second.preconditions.empty())
        r.preconditionSatisfied = true;

    // Dataflow: if second declares an input, every declared required input
    // must either be generated by first or remain externally supplied.
    // If there is overlap, it establishes a concrete pipeline link.
    std::unordered_set<std::string> firstOutputs;
    for (const auto& o : first.outputs)
        firstOutputs.insert(canonicalDataKey(o));

    if (second.inputs.empty()) {
        r.dataflowSatisfied = true;
    } else {
        bool allSatisfied = true;
        for (const auto& in : second.inputs) {
            if (in.required && !firstOutputs.count(canonicalDataKey(in))) {
                allSatisfied = false;
                break;
            }
        }
        r.dataflowSatisfied = allSatisfied;
    }

    r.compatible = r.contradictionFree && r.preconditionSatisfied &&
                   r.dataflowSatisfied;

    if (r.compatible)
        r.explanation = "Compatible: no effect/precondition contradiction and dataflow is satisfied.";
    else if (r.explanation.empty())
        r.explanation = "Not compatible: required dataflow is not satisfied.";

    return r;
}

bool EmbeddingEngine::areCompatible(
    const Capability& first, const Capability& second) const {
    return checkCompatibility(first, second).compatible;
}

Capability EmbeddingEngine::compose(
    const Capability& first, const Capability& second) const {

    if (!areCompatible(first, second))
        throw std::invalid_argument("Cannot compose incompatible capabilities.");

    Capability c;
    c.name = first.name + " + " + second.name;
    c.type = CapabilityType::SERVICE;
    c.mechanism = "COMPOSITE(" + first.mechanism + " -> " + second.mechanism + ")";

    std::unordered_set<std::string> firstOutputs;
    for (const auto& o : first.outputs)
        firstOutputs.insert(canonicalDataKey(o));

    // External inputs = first inputs + second inputs not produced by first.
    c.inputs = first.inputs;
    for (const auto& in : second.inputs)
        if (!firstOutputs.count(canonicalDataKey(in)))
            c.inputs.push_back(in);

    // Outputs are the union.
    c.outputs = first.outputs;
    for (const auto& out : second.outputs) {
        bool exists = false;
        for (const auto& x : c.outputs)
            if (canonicalDataKey(x) == canonicalDataKey(out)) exists = true;
        if (!exists) c.outputs.push_back(out);
    }

    // Preconditions: first's + second's not established by first.
    c.preconditions = first.preconditions;
    for (const auto& [key, value] : second.preconditions) {
        auto e = first.effects.find(key);
        if (e == first.effects.end())
            c.preconditions.emplace(key, value);
    }

    // Effects: second supersedes first on shared state variables.
    c.effects = first.effects;
    for (const auto& [key, value] : second.effects)
        c.effects[key] = value;

    c.constraints = first.constraints;
    for (const auto& x : second.constraints)
        if (std::find(c.constraints.begin(), c.constraints.end(), x) == c.constraints.end())
            c.constraints.push_back(x);

    c.resources = first.resources;
    for (const auto& x : second.resources)
        if (std::find(c.resources.begin(), c.resources.end(), x) == c.resources.end())
            c.resources.push_back(x);

    c.cost = first.cost + second.cost;
    c.reliability = first.reliability * second.reliability;
    c.availability = first.availability * second.availability;

    return c;
}

Capability EmbeddingEngine::composeChain(const std::vector<Capability>& chain) const {
    if (chain.empty())
        throw std::invalid_argument("Cannot compose an empty capability chain.");

    Capability result = chain.front();
    for (std::size_t i = 1; i < chain.size(); ++i)
        result = compose(result, chain[i]);
    return result;
}

Vector EmbeddingEngine::effectOnly(const Capability& capability) const {
    Vector v{};
    for (const auto& [key, value] : capability.effects) {
        const int idx = stateIndex(key);
        if (idx < 0) continue;
        bool positive = !(value == "false" || value == "FALSE" ||
                           value == "0" || value == "FAILURE" ||
                           value == "NOT_STARTED");
        v[EFFECT_START + static_cast<std::size_t>(idx)] = positive ? 1.0 : -1.0;
    }
    return v;
}

double EmbeddingEngine::goalRelevance(
    const Capability& capability, const Goal& goal) const {
    Vector effects = effectOnly(capability);
    Vector goalVector = encodeGoal(goal);
    double sim = cosineSimilarity(effects, goalVector);
    return std::max(0.0, sim);
}

} // namespace capembed
