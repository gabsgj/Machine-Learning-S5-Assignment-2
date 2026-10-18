#ifndef TYPES_H
#define TYPES_H

#include <string>
#include <vector>
#include <map>
#include <initializer_list>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <iostream>

/**
 * @brief Formal Capability classification types as defined in the assignment specifications.
 */
enum class CapabilityType {
    API,
    DATABASE,
    GUI,
    EVENT,
    FUNCTION,
    FILE,
    COMPUTATION,
    MESSAGE,
    SERVICE
};

/**
 * @brief Converts a CapabilityType enum to its canonical string representation.
 */
std::string capabilityTypeToString(CapabilityType type);

/**
 * @brief Parses a string into the corresponding CapabilityType enum.
 */
CapabilityType stringToCapabilityType(const std::string& str);

/**
 * @brief Formally specified State representing world propositions and variable assignments.
 *
 * Example:
 *   User.authenticated = true
 *   Cart.exists = true
 *   Order.exists = false
 */
struct State {
    std::map<std::string, std::string> variables;

    State() = default;
    State(std::initializer_list<std::pair<const std::string, std::string>> init);

    void set(const std::string& key, const std::string& value);
    void set(const std::string& key, bool value);
    std::string get(const std::string& key, const std::string& defaultVal = "") const;
    bool getBool(const std::string& key, bool defaultVal = false) const;
    bool has(const std::string& key) const;
    bool matches(const std::string& key, const std::string& expectedValue) const;

    std::string toString() const;
};

/**
 * @brief Formally specified Goal representing desired conditions to be satisfied in the world.
 *
 * Example:
 *   Order.exists = true
 *   Payment.status = SUCCESS
 */
struct Goal {
    std::string name;
    std::map<std::string, std::string> conditions;

    Goal() = default;
    explicit Goal(const std::string& name);
    Goal(const std::string& name, std::initializer_list<std::pair<const std::string, std::string>> init);

    void addCondition(const std::string& key, const std::string& value);
    void addCondition(const std::string& key, bool value);
    bool isSatisfied(const State& state) const;
    double satisfactionRatio(const State& state) const;

    std::string toString() const;
};

/**
 * @brief Formally specified Capability definition incorporating structural, semantic,
 *        and operational attributes.
 *
 * Attributes:
 * - name: Identifier of the capability
 * - type: Architectural classification (API, DATABASE, GUI, EVENT, etc.)
 * - executionMechanism: Underlying execution paradigm (REST, SQL, Qt event, etc.)
 * - inputs: Required input parameters / data fields
 * - outputs: Produced output attributes / data fields
 * - preconditions: World state conditions required prior to execution
 * - effects: World state mutations produced upon successful execution
 * - constraints: Execution constraints and invariant assertions
 * - resources: Physical or logical resources utilized
 * - cost: Normalized execution cost / latency / fee
 * - reliability: Probability of successful execution in [0.0, 1.0]
 * - availability: Uptime / readiness probability in [0.0, 1.0]
 */
struct Capability {
    std::string name;
    CapabilityType type{CapabilityType::SERVICE};
    std::string executionMechanism;
    std::vector<std::string> inputs;
    std::vector<std::string> outputs;
    std::map<std::string, std::string> preconditions;
    std::map<std::string, std::string> effects;
    std::vector<std::string> constraints;
    std::vector<std::string> resources;
    double cost{0.0};
    double reliability{1.0};
    double availability{1.0};

    Capability() = default;
    Capability(const std::string& name, CapabilityType type, const std::string& mechanism);

    // Fluent builder methods for clean declarative construction
    Capability& setName(const std::string& n) { name = n; return *this; }
    Capability& setType(CapabilityType t) { type = t; return *this; }
    Capability& setExecutionMechanism(const std::string& em) { executionMechanism = em; return *this; }
    Capability& addInput(const std::string& in);
    Capability& addOutput(const std::string& out);
    Capability& addPrecondition(const std::string& key, const std::string& value);
    Capability& addPrecondition(const std::string& key, bool value);
    Capability& addEffect(const std::string& key, const std::string& value);
    Capability& addEffect(const std::string& key, bool value);
    Capability& addConstraint(const std::string& constraint);
    Capability& addResource(const std::string& resource);
    Capability& setCost(double c) { cost = c; return *this; }
    Capability& setReliability(double r) { reliability = r; return *this; }
    Capability& setAvailability(double a) { availability = a; return *this; }

    std::string toString() const;
};

/**
 * @brief Structured report detailing compatibility analysis between two capabilities.
 */
struct CompatibilityReport {
    bool isCompatible{false};
    bool outputInputCompatible{false};
    bool effectPreconditionCompatible{false};
    std::vector<std::string> satisfiedPreconditions;
    std::vector<std::string> conflictingEffects;
    std::vector<std::string> satisfiedInputs;
    std::vector<std::string> unsatisfiedInputs;
    std::vector<std::string> diagnosticMessages;

    std::string toString() const;
};

#endif // TYPES_H
