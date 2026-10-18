#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <iostream>
#include <iomanip>

namespace capability_embedding {

// =============================================================================
// PCCST503 Assignment 2: Formal Types & Capability Specification
// Section 3: Formal Application Model A = (S, C, S_I, G, R, K)
// Section 4: Formal Capability Model C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
// =============================================================================

// Fixed canonical universe of 11 state variables
const std::vector<std::string> CANONICAL_STATE_VARIABLES = {
    "authenticated",        // Index 0: Customer authentication verified
    "customer_exists",      // Index 1: Customer record exists in system
    "cart_exists",          // Index 2: Active shopping cart initialized
    "cart_has_items",       // Index 3: Shopping cart contains items
    "inventory_available",  // Index 4: Requested stock reserved/available
    "order_exists",         // Index 5: Formal order entity exists
    "order_created",        // Index 6: Order status set to created
    "payment_success",      // Index 7: Transaction payment captured
    "notification_sent",    // Index 8: Customer dispatch notification sent
    "order_cancelled",      // Index 9: Order/cart marked cancelled/abandoned
    "shipment_dispatched"   // Index 10: Courier package dispatched
};

// Canonical capability types (6-dimensional one-hot basis)
const std::vector<std::string> CANONICAL_CAPABILITY_TYPES = {
    "API",
    "DATABASE",
    "GUI",
    "EVENT",
    "FUNCTION",
    "SERVICE"
};

// Input and Output Port Specification (Section 4.2)
// i_j = (name, type, domain, required), o_j = (name, type, domain)
struct Port {
    std::string name;
    std::string type;       // e.g., "UUID", "double", "string"
    std::string domain;     // e.g., "valid UUIDs", "non-negative currency"
    bool required = true;   // applicable to inputs
};

// Condition / Predicate on a state variable (Section 4.3)
struct Condition {
    std::string variable;
    bool expectedValue = true;
};

// Effect on a state variable (Section 4.3)
struct Effect {
    std::string variable;
    bool value = true;
};

// Operational Quality Attributes Q_i = (C_time, C_resource, C_money, C_risk) (Section 4.5)
struct QualityAttributes {
    double timeCostMs = 100.0;    // Latency in milliseconds
    double moneyCost = 0.01;      // Monetary cost in USD
    double resourceCost = 1.0;    // CPU / Memory compute units
    double risk = 0.05;           // Risk factor in [0, 1]
};

// Application State S = {(x_1, v_1), ..., (x_n, v_n)} (Section 3.1)
struct State {
    std::unordered_map<std::string, bool> vars;

    bool get(const std::string& key, bool defaultVal = false) const {
        auto it = vars.find(key);
        return (it != vars.end()) ? it->second : defaultVal;
    }

    void set(const std::string& key, bool val) {
        vars[key] = val;
    }
};

// Goal Specification G = {g_1, ..., g_m} (Section 3.2)
struct Goal {
    std::vector<Condition> conditions;

    bool isSatisfied(const State& s) const {
        for (const auto& cond : conditions) {
            if (s.get(cond.variable, false) != cond.expectedValue) {
                return false;
            }
        }
        return true;
    }
};

// Formal Capability 11-tuple (Section 4)
// C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
struct Capability {
    std::string id;
    std::string name;
    std::string description;

    std::string type = "API";               // T_i: Capability type
    std::vector<Port> inputs;              // I_i: Inputs
    std::vector<Port> outputs;             // O_i: Outputs
    std::vector<Condition> preconditions;  // P_i: Preconditions
    std::vector<Effect> effects;           // E_i: Effects
    std::vector<std::string> constraints;  // K_i: Constraints
    std::vector<std::string> resources;    // R_i: Resources
    QualityAttributes qos;                 // Q_i: Quality attributes
    double reliability = 0.99;             // Rel_i: Reliability in [0, 1]
    double availability = 1.0;             // A_i: Availability in {0, 1}
    std::string mechanism = "HTTP_POST";   // M_i: Execution mechanism
};

// Formal Application Model A = (S, C, S_I, G, R, K) (Section 3)
struct ApplicationProblem {
    std::string applicationName;
    std::string domain;
    State initialState;                            // S_I
    Goal goal;                                     // G
    std::vector<Capability> capabilities;          // C
    std::vector<std::string> resources;            // R
    std::vector<std::string> globalConstraints;    // K
};

} // namespace capability_embedding
