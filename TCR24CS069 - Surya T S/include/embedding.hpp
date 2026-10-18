#pragma once

#include "types.hpp"
#include <cmath>
#include <numeric>
#include <sstream>
#include <iomanip>
#include <algorithm>

namespace capability_embedding {

// =============================================================================
// PCCST503 Assignment 2: Vector Embedding Engine
// Section 6: Embedding Design Problem
//
// Structured Concatenated Capability Representation:
//   phi_C(C) = [ p(C) || e(C) || t(C) || io(C) || q(C) ] in R^34
//
// 1. Preconditions p(C) in {-1, 0, +1}^11 (11 dimensions)
// 2. Effects       e(C) in {-1, 0, +1}^11 (11 dimensions)
// 3. Type          t(C) in {0, 1}^6       (6 dimensions, one-hot)
// 4. I/O Ports     io(C) in [0, 1]^2      (2 dimensions, count normalized)
// 5. QoS/Ops       q(C) in [0, 1]^4       (4 dimensions, normalized time, cost, risk, rel)
// =============================================================================

class VectorEmbeddingEngine {
private:
    std::unordered_map<std::string, size_t> varIndexMap;
    std::unordered_map<std::string, size_t> typeIndexMap;

public:
    VectorEmbeddingEngine() {
        for (size_t i = 0; i < CANONICAL_STATE_VARIABLES.size(); ++i) {
            varIndexMap[CANONICAL_STATE_VARIABLES[i]] = i;
        }
        for (size_t i = 0; i < CANONICAL_CAPABILITY_TYPES.size(); ++i) {
            typeIndexMap[CANONICAL_CAPABILITY_TYPES[i]] = i;
        }
    }

    size_t stateDimension() const {
        return CANONICAL_STATE_VARIABLES.size(); // 11
    }

    size_t capabilityDimension() const {
        // 11 (pre) + 11 (eff) + 6 (type) + 2 (io) + 6 (qos: time, money, resource, risk, rel, avail) = 36
        return stateDimension() + stateDimension() + CANONICAL_CAPABILITY_TYPES.size() + 2 + 6;
    }

    // -------------------------------------------------------------------------
    // Deliverable 2: encode(state) -> phi_S(S) in {-1, +1}^11
    // Bipolar encoding: true -> +1.0, false -> -1.0
    // -------------------------------------------------------------------------
    std::vector<double> encodeState(const State& s) const {
        std::vector<double> vec(stateDimension(), -1.0);
        for (size_t i = 0; i < stateDimension(); ++i) {
            const auto& varName = CANONICAL_STATE_VARIABLES[i];
            vec[i] = s.get(varName, false) ? 1.0 : -1.0;
        }
        return vec;
    }

    // -------------------------------------------------------------------------
    // Deliverable 2: encode(goal) -> phi_G(G) in {-1, 0, +1}^11
    // Required true -> +1.0, Required false -> -1.0, Unspecified -> 0.0
    // -------------------------------------------------------------------------
    std::vector<double> encodeGoal(const Goal& g) const {
        std::vector<double> vec(stateDimension(), 0.0);
        for (const auto& cond : g.conditions) {
            auto it = varIndexMap.find(cond.variable);
            if (it != varIndexMap.end()) {
                vec[it->second] = cond.expectedValue ? 1.0 : -1.0;
            }
        }
        return vec;
    }

    // -------------------------------------------------------------------------
    // Precondition Vector: p(C) in {-1, 0, +1}^11
    // Requires true -> +1.0, Requires false -> -1.0, No requirement -> 0.0
    // -------------------------------------------------------------------------
    std::vector<double> encodePreconditions(const Capability& c) const {
        std::vector<double> vec(stateDimension(), 0.0);
        for (const auto& pre : c.preconditions) {
            auto it = varIndexMap.find(pre.variable);
            if (it != varIndexMap.end()) {
                vec[it->second] = pre.expectedValue ? 1.0 : -1.0;
            }
        }
        return vec;
    }

    // -------------------------------------------------------------------------
    // Effect Vector: e(C) in {-1, 0, +1}^11
    // Sets true -> +1.0, Sets false -> -1.0, Does not modify -> 0.0
    // -------------------------------------------------------------------------
    std::vector<double> encodeEffects(const Capability& c) const {
        std::vector<double> vec(stateDimension(), 0.0);
        for (const auto& eff : c.effects) {
            auto it = varIndexMap.find(eff.variable);
            if (it != varIndexMap.end()) {
                vec[it->second] = eff.value ? 1.0 : -1.0;
            }
        }
        return vec;
    }

    // -------------------------------------------------------------------------
    // One-hot Type Vector: t(C) in {0, 1}^6
    // -------------------------------------------------------------------------
    std::vector<double> encodeType(const Capability& c) const {
        std::vector<double> vec(CANONICAL_CAPABILITY_TYPES.size(), 0.0);
        auto it = typeIndexMap.find(c.type);
        if (it != typeIndexMap.end()) {
            vec[it->second] = 1.0;
        }
        return vec;
    }

    // -------------------------------------------------------------------------
    // Deliverable 2: encode(capability) -> phi_C(C) in R^36
    // Structured concatenation of all feature blocks
    // -------------------------------------------------------------------------
    std::vector<double> encodeCapability(const Capability& c) const {
        std::vector<double> fullVec;
        fullVec.reserve(capabilityDimension());

        // 1. Preconditions (11 dims)
        auto pre = encodePreconditions(c);
        fullVec.insert(fullVec.end(), pre.begin(), pre.end());

        // 2. Effects (11 dims)
        auto eff = encodeEffects(c);
        fullVec.insert(fullVec.end(), eff.begin(), eff.end());

        // 3. Type (6 dims)
        auto typ = encodeType(c);
        fullVec.insert(fullVec.end(), typ.begin(), typ.end());

        // 4. I/O Port Counts (2 dims: normalized by 5.0)
        double inNorm = std::min(1.0, static_cast<double>(c.inputs.size()) / 5.0);
        double outNorm = std::min(1.0, static_cast<double>(c.outputs.size()) / 5.0);
        fullVec.push_back(inNorm);
        fullVec.push_back(outNorm);

        // 5. Operational Features (6 dims: normalized time, money, resource, risk, reliability, availability)
        double timeNorm = std::min(1.0, c.qos.timeCostMs / 1000.0);
        double moneyNorm = std::min(1.0, c.qos.moneyCost / 1.0);
        double resNorm = std::min(1.0, c.qos.resourceCost / 10.0);
        double riskNorm = std::max(0.0, std::min(1.0, c.qos.risk));
        double relNorm = std::max(0.0, std::min(1.0, c.reliability));
        double availNorm = (c.availability > 0.5) ? 1.0 : 0.0;

        fullVec.push_back(timeNorm);
        fullVec.push_back(moneyNorm);
        fullVec.push_back(resNorm);
        fullVec.push_back(riskNorm);
        fullVec.push_back(relNorm);
        fullVec.push_back(availNorm);

        return fullVec;
    }

    // -------------------------------------------------------------------------
    // Cosine Similarity: Sim(u, v) in [-1, +1]
    // Sim(u, v) = (u . v) / (||u|| * ||v|| + eps)
    // -------------------------------------------------------------------------
    static double cosineSimilarity(const std::vector<double>& v1, const std::vector<double>& v2) {
        if (v1.size() != v2.size() || v1.empty()) return 0.0;
        double dot = 0.0, norm1 = 0.0, norm2 = 0.0;
        for (size_t i = 0; i < v1.size(); ++i) {
            dot += v1[i] * v2[i];
            norm1 += v1[i] * v1[i];
            norm2 += v2[i] * v2[i];
        }
        if (norm1 < 1e-12 || norm2 < 1e-12) return 0.0;
        return dot / (std::sqrt(norm1) * std::sqrt(norm2));
    }

    static double similarity(const std::vector<double>& v1, const std::vector<double>& v2) {
        return cosineSimilarity(v1, v2);
    }

    // -------------------------------------------------------------------------
    // Precondition-Effect Compatibility: Comp(C1, C2)
    // Comp(C1, C2) = dot(e(C1), p(C2)) / (||p(C2)||^2 + eps)
    // Returns:
    //   +1.0: C1 enables/satisfies C2's preconditions
    //    0.0: neutral / no interaction
    //   -1.0: C1 actively conflicts with C2's preconditions
    // -------------------------------------------------------------------------
    double compatibility(const Capability& c1, const Capability& c2) const {
        auto eff1 = encodeEffects(c1);
        auto pre2 = encodePreconditions(c2);

        double dot = 0.0;
        double preNormSq = 0.0;
        for (size_t i = 0; i < stateDimension(); ++i) {
            dot += eff1[i] * pre2[i];
            preNormSq += pre2[i] * pre2[i];
        }

        if (preNormSq < 1e-9) {
            // C2 has no preconditions; unconditionally applicable
            return 1.0;
        }

        return dot / preNormSq;
    }

    // -------------------------------------------------------------------------
    // Input-Output Compatibility: IOCompatibility(C1, C2) in [0, 1]
    // Computes the fraction of required inputs of C2 satisfied by outputs of C1
    // -------------------------------------------------------------------------
    double inputOutputCompatibility(const Capability& c1, const Capability& c2) const {
        if (c2.inputs.empty()) return 1.0;

        size_t requiredCount = 0;
        size_t satisfiedCount = 0;

        for (const auto& in : c2.inputs) {
            if (!in.required) continue;
            requiredCount++;
            for (const auto& out : c1.outputs) {
                if (in.name == out.name && in.type == out.type) {
                    satisfiedCount++;
                    break;
                }
            }
        }

        if (requiredCount == 0) return 1.0;
        return static_cast<double>(satisfiedCount) / static_cast<double>(requiredCount);
    }

    // -------------------------------------------------------------------------
    // Goal Relevance: Alignment between Capability Effects and Desired Goal
    // Relevance(C, G) = e(C) . phi_G(G)
    // -------------------------------------------------------------------------
    double goalRelevance(const Capability& c, const Goal& g) const {
        auto eff = encodeEffects(c);
        auto goalVec = encodeGoal(g);

        double dot = 0.0;
        for (size_t i = 0; i < stateDimension(); ++i) {
            dot += eff[i] * goalVec[i];
        }
        return dot;
    }

    // -------------------------------------------------------------------------
    // Deliverable 2: compose(C1, C2) -> C_12 = C_2 o C_1
    // Executes C1 first, followed by C2.
    // -------------------------------------------------------------------------
    Capability compose(const Capability& c1, const Capability& c2) const {
        Capability comp;
        comp.id = c1.id + "_THEN_" + c2.id;
        comp.name = "Composite(" + c1.name + " -> " + c2.name + ")";
        comp.description = "Sequential composition: " + c1.id + " followed by " + c2.id;
        comp.type = "SERVICE"; // composite service
        comp.mechanism = "COMPOSITE_CHAIN(" + c1.mechanism + " -> " + c2.mechanism + ")";

        // 1. Preconditions: P(C1) union (P(C2) minus effects of C1 that satisfy those preconditions)
        comp.preconditions = c1.preconditions;
        for (const auto& p2 : c2.preconditions) {
            bool satisfiedByC1 = false;
            for (const auto& e1 : c1.effects) {
                if (e1.variable == p2.variable) {
                    if (e1.value == p2.expectedValue) {
                        satisfiedByC1 = true;
                    }
                    break;
                }
            }
            if (!satisfiedByC1) {
                // Check if already in preconditions
                bool alreadyPresent = false;
                for (const auto& existing : comp.preconditions) {
                    if (existing.variable == p2.variable) {
                        alreadyPresent = true;
                        break;
                    }
                }
                if (!alreadyPresent) {
                    comp.preconditions.push_back(p2);
                }
            }
        }

        // 2. Effects: E(C1) followed by E(C2) (C2 overrides C1 on the same variable)
        comp.effects = c1.effects;
        for (const auto& e2 : c2.effects) {
            bool overridden = false;
            for (auto& ce : comp.effects) {
                if (ce.variable == e2.variable) {
                    ce = e2;
                    overridden = true;
                    break;
                }
            }
            if (!overridden) {
                comp.effects.push_back(e2);
            }
        }

        // 3. Inputs: Inputs of C1 + inputs of C2 that are not provided by C1's outputs
        comp.inputs = c1.inputs;
        for (const auto& in2 : c2.inputs) {
            bool suppliedByC1 = false;
            for (const auto& out1 : c1.outputs) {
                if (out1.name == in2.name && out1.type == in2.type) {
                    suppliedByC1 = true;
                    break;
                }
            }
            if (!suppliedByC1) {
                comp.inputs.push_back(in2);
            }
        }

        // 4. Outputs: C2 outputs + C1 outputs (accumulated)
        comp.outputs = c2.outputs;
        for (const auto& out1 : c1.outputs) {
            bool existsInC2 = false;
            for (const auto& out2 : c2.outputs) {
                if (out2.name == out1.name) {
                    existsInC2 = true;
                    break;
                }
            }
            if (!existsInC2) {
                comp.outputs.push_back(out1);
            }
        }

        // 5. Constraints and Resources (union)
        comp.constraints = c1.constraints;
        for (const auto& k : c2.constraints) {
            if (std::find(comp.constraints.begin(), comp.constraints.end(), k) == comp.constraints.end()) {
                comp.constraints.push_back(k);
            }
        }
        comp.resources = c1.resources;
        for (const auto& r : c2.resources) {
            if (std::find(comp.resources.begin(), comp.resources.end(), r) == comp.resources.end()) {
                comp.resources.push_back(r);
            }
        }

        // 6. Operational Aggregation:
        //    Time: add
        //    Money: add
        //    Resource: add
        //    Risk: 1 - (1 - R1)*(1 - R2)
        //    Reliability: multiply
        //    Availability: multiply (false if any component is unavailable)
        comp.qos.timeCostMs = c1.qos.timeCostMs + c2.qos.timeCostMs;
        comp.qos.moneyCost = c1.qos.moneyCost + c2.qos.moneyCost;
        comp.qos.resourceCost = c1.qos.resourceCost + c2.qos.resourceCost;
        comp.qos.risk = 1.0 - ((1.0 - c1.qos.risk) * (1.0 - c2.qos.risk));
        comp.reliability = c1.reliability * c2.reliability;
        comp.availability = (c1.availability > 0.5 && c2.availability > 0.5) ? 1.0 : 0.0;

        return comp;
    }
};

} // namespace capability_embedding
