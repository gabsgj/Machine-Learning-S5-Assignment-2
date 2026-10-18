#include "Embedding.h"
#include <cmath>
#include <sstream>
#include <iomanip>
#include <iostream>
#include <algorithm>
#include <stdexcept>
#include <cctype>

namespace {

// ============================================================================
// Embedding Dimension Layout Constants
// ============================================================================
// Total Dimension: 92
// [0 .. 8]   (9 dims): Capability Type (one-hot)
// [9 .. 11]  (3 dims): Operational Attributes (Normalized Cost, Reliability, Availability)
// [12 .. 27] (16 dims): Preconditions (State Predicates)
// [28 .. 43] (16 dims): Effects / State World Variables (State Predicates)
// [44 .. 59] (16 dims): Data Inputs
// [60 .. 75] (16 dims): Data Outputs
// [76 .. 83] (8 dims):  Resources
// [84 .. 91] (8 dims):  Constraints
// ============================================================================

constexpr size_t OFFSET_TYPE = 0;
constexpr size_t DIM_TYPE = 9;

constexpr size_t OFFSET_OPS = 9;
constexpr size_t DIM_OPS = 3;

constexpr size_t OFFSET_PRECONDITIONS = 12;
constexpr size_t DIM_PRECONDITIONS = 16;

constexpr size_t OFFSET_EFFECTS = 28;
constexpr size_t DIM_EFFECTS = 16;

constexpr size_t OFFSET_INPUTS = 44;
constexpr size_t DIM_INPUTS = 16;

constexpr size_t OFFSET_OUTPUTS = 60;
constexpr size_t DIM_OUTPUTS = 16;

constexpr size_t OFFSET_RESOURCES = 76;
constexpr size_t DIM_RESOURCES = 8;

constexpr size_t OFFSET_CONSTRAINTS = 84;
constexpr size_t DIM_CONSTRAINTS = 8;

constexpr size_t TOTAL_EMBEDDING_DIM = 92;

// Helper: Normalize string (lowercase, trimmed)
std::string toLower(const std::string& str) {
    std::string s;
    s.reserve(str.size());
    for (char ch : str) {
        s.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
    }
    return s;
}

// Simple deterministic string hash for dynamic token mapping
size_t hashString(const std::string& str) {
    size_t hash = 2166136261u;
    for (char c : str) {
        hash = (hash ^ static_cast<size_t>(static_cast<unsigned char>(c))) * 16777619u;
    }
    return hash;
}

/**
 * @brief Thread-safe semantic dictionary mapping string tokens to dedicated slot indices.
 */
class DomainRegistry {
public:
    static DomainRegistry& instance() {
        static DomainRegistry reg;
        return reg;
    }

    size_t getPredicateIndex(const std::string& name) const {
        std::string key = toLower(name);
        auto it = predicateMap.find(key);
        if (it != predicateMap.end()) return it->second;
        return 9 + (hashString(key) % (DIM_PRECONDITIONS - 9));
    }

    size_t getDataIndex(const std::string& name) const {
        std::string key = toLower(name);
        auto it = dataMap.find(key);
        if (it != dataMap.end()) return it->second;
        return 11 + (hashString(key) % (DIM_INPUTS - 11));
    }

    size_t getResourceIndex(const std::string& name) const {
        std::string key = toLower(name);
        auto it = resourceMap.find(key);
        if (it != resourceMap.end()) return it->second;
        return hashString(key) % DIM_RESOURCES;
    }

    size_t getConstraintIndex(const std::string& name) const {
        std::string key = toLower(name);
        auto it = constraintMap.find(key);
        if (it != constraintMap.end()) return it->second;
        return hashString(key) % DIM_CONSTRAINTS;
    }

private:
    DomainRegistry() {
        // Canonical Predicates / State Variables
        predicateMap["cartexists"] = 0;
        predicateMap["cart.exists"] = 0;
        predicateMap["orderexists"] = 1;
        predicateMap["order.exists"] = 1;
        predicateMap["paymentstatus"] = 2;
        predicateMap["payment.status"] = 2;
        predicateMap["user.authenticated"] = 3;
        predicateMap["userauthenticated"] = 3;
        predicateMap["notificationsent"] = 4;
        predicateMap["customernotified"] = 4;
        predicateMap["audiodeviceready"] = 5;
        predicateMap["musicplaying"] = 6;
        predicateMap["trackselected"] = 7;
        predicateMap["cartcanceled"] = 8;
        predicateMap["cancellationstatus"] = 8;

        // Canonical Data flow terms (Inputs & Outputs)
        dataMap["cartid"] = 0;
        dataMap["userid"] = 1;
        dataMap["orderid"] = 2;
        dataMap["amount"] = 3;
        dataMap["paymentid"] = 4;
        dataMap["receipturl"] = 5;
        dataMap["receipt"] = 5;
        dataMap["notificationid"] = 6;
        dataMap["trackid"] = 7;
        dataMap["volume"] = 8;
        dataMap["playbackstate"] = 9;
        dataMap["cancellationstatus"] = 10;

        // Canonical Resources
        resourceMap["order_db"] = 0;
        resourceMap["cart_db"] = 1;
        resourceMap["payment_gateway"] = 2;
        resourceMap["network"] = 3;
        resourceMap["cpu"] = 4;
        resourceMap["audio_device"] = 5;
        resourceMap["display"] = 6;

        // Canonical Constraints
        constraintMap["cart_not_empty"] = 0;
        constraintMap["valid_card"] = 1;
        constraintMap["cart_active"] = 2;
        constraintMap["valid_user"] = 3;
        constraintMap["ssl_enabled"] = 4;
        constraintMap["timeout_limit"] = 5;
        constraintMap["volume_in_range"] = 6;
    }

    std::map<std::string, size_t> predicateMap;
    std::map<std::string, size_t> dataMap;
    std::map<std::string, size_t> resourceMap;
    std::map<std::string, size_t> constraintMap;
};

// Converts formal values (e.g. true, false, SUCCESS, FAILURE) to numerical signs
double encodeValue(const std::string& val) {
    std::string s = toLower(val);
    if (s == "true" || s == "success" || s == "1" || s == "yes" || s == "active" || s == "valid") {
        return 1.0;
    }
    if (s == "false" || s == "failure" || s == "0" || s == "no" || s == "inactive" || s == "invalid") {
        return -1.0;
    }
    return 1.0; // Positive assertion for arbitrary values
}

} // namespace

// ============================================================================
// CapabilityType Helpers
// ============================================================================

std::string capabilityTypeToString(CapabilityType type) {
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

CapabilityType stringToCapabilityType(const std::string& str) {
    std::string s = toLower(str);
    if (s == "api") return CapabilityType::API;
    if (s == "database") return CapabilityType::DATABASE;
    if (s == "gui") return CapabilityType::GUI;
    if (s == "event") return CapabilityType::EVENT;
    if (s == "function") return CapabilityType::FUNCTION;
    if (s == "file") return CapabilityType::FILE;
    if (s == "computation") return CapabilityType::COMPUTATION;
    if (s == "message") return CapabilityType::MESSAGE;
    return CapabilityType::SERVICE;
}

// ============================================================================
// State Implementation
// ============================================================================

State::State(std::initializer_list<std::pair<const std::string, std::string>> init)
    : variables(init) {}

void State::set(const std::string& key, const std::string& value) {
    variables[key] = value;
}

void State::set(const std::string& key, bool value) {
    variables[key] = value ? "true" : "false";
}

std::string State::get(const std::string& key, const std::string& defaultVal) const {
    auto it = variables.find(key);
    return (it != variables.end()) ? it->second : defaultVal;
}

bool State::getBool(const std::string& key, bool defaultVal) const {
    auto it = variables.find(key);
    if (it == variables.end()) return defaultVal;
    return encodeValue(it->second) > 0.0;
}

bool State::has(const std::string& key) const {
    return variables.find(key) != variables.end();
}

bool State::matches(const std::string& key, const std::string& expectedValue) const {
    auto it = variables.find(key);
    if (it == variables.end()) return false;
    return encodeValue(it->second) == encodeValue(expectedValue);
}

std::string State::toString() const {
    std::ostringstream oss;
    oss << "State {\n";
    for (const auto& entry : variables) {
        oss << "  " << std::left << std::setw(24) << entry.first << " = " << entry.second << "\n";
    }
    oss << "}";
    return oss.str();
}

// ============================================================================
// Goal Implementation
// ============================================================================

Goal::Goal(const std::string& name) : name(name) {}

Goal::Goal(const std::string& name, std::initializer_list<std::pair<const std::string, std::string>> init)
    : name(name), conditions(init) {}

void Goal::addCondition(const std::string& key, const std::string& value) {
    conditions[key] = value;
}

void Goal::addCondition(const std::string& key, bool value) {
    conditions[key] = value ? "true" : "false";
}

bool Goal::isSatisfied(const State& state) const {
    if (conditions.empty()) return true;
    for (const auto& entry : conditions) {
        if (!state.matches(entry.first, entry.second)) return false;
    }
    return true;
}

double Goal::satisfactionRatio(const State& state) const {
    if (conditions.empty()) return 1.0;
    size_t satisfied = 0;
    for (const auto& entry : conditions) {
        if (state.matches(entry.first, entry.second)) satisfied++;
    }
    return static_cast<double>(satisfied) / static_cast<double>(conditions.size());
}

std::string Goal::toString() const {
    std::ostringstream oss;
    oss << "Goal";
    if (!name.empty()) oss << " (" << name << ")";
    oss << " {\n";
    for (const auto& entry : conditions) {
        oss << "  " << std::left << std::setw(24) << entry.first << " = " << entry.second << "\n";
    }
    oss << "}";
    return oss.str();
}

// ============================================================================
// Capability Implementation
// ============================================================================

Capability::Capability(const std::string& name, CapabilityType type, const std::string& mechanism)
    : name(name), type(type), executionMechanism(mechanism) {}

Capability& Capability::addInput(const std::string& in) {
    if (std::find(inputs.begin(), inputs.end(), in) == inputs.end()) {
        inputs.push_back(in);
    }
    return *this;
}

Capability& Capability::addOutput(const std::string& out) {
    if (std::find(outputs.begin(), outputs.end(), out) == outputs.end()) {
        outputs.push_back(out);
    }
    return *this;
}

Capability& Capability::addPrecondition(const std::string& key, const std::string& value) {
    preconditions[key] = value;
    return *this;
}

Capability& Capability::addPrecondition(const std::string& key, bool value) {
    preconditions[key] = value ? "true" : "false";
    return *this;
}

Capability& Capability::addEffect(const std::string& key, const std::string& value) {
    effects[key] = value;
    return *this;
}

Capability& Capability::addEffect(const std::string& key, bool value) {
    effects[key] = value ? "true" : "false";
    return *this;
}

Capability& Capability::addConstraint(const std::string& constraint) {
    if (std::find(constraints.begin(), constraints.end(), constraint) == constraints.end()) {
        constraints.push_back(constraint);
    }
    return *this;
}

Capability& Capability::addResource(const std::string& resource) {
    if (std::find(resources.begin(), resources.end(), resource) == resources.end()) {
        resources.push_back(resource);
    }
    return *this;
}

std::string Capability::toString() const {
    std::ostringstream oss;
    oss << "Capability: " << name << "\n"
        << "  Type:                " << capabilityTypeToString(type) << "\n"
        << "  Execution Mechanism: " << executionMechanism << "\n"
        << "  Cost:                " << std::fixed << std::setprecision(2) << cost << "\n"
        << "  Reliability:         " << std::fixed << std::setprecision(4) << reliability << "\n"
        << "  Availability:        " << std::fixed << std::setprecision(4) << availability << "\n";

    oss << "  Inputs:              [";
    for (size_t i = 0; i < inputs.size(); ++i) {
        oss << inputs[i] << (i + 1 < inputs.size() ? ", " : "");
    }
    oss << "]\n";

    oss << "  Outputs:             [";
    for (size_t i = 0; i < outputs.size(); ++i) {
        oss << outputs[i] << (i + 1 < outputs.size() ? ", " : "");
    }
    oss << "]\n";

    oss << "  Preconditions:       {";
    bool first = true;
    for (const auto& entry : preconditions) {
        if (!first) oss << ", ";
        oss << entry.first << ": " << entry.second;
        first = false;
    }
    oss << "}\n";

    oss << "  Effects:             {";
    first = true;
    for (const auto& entry : effects) {
        if (!first) oss << ", ";
        oss << entry.first << ": " << entry.second;
        first = false;
    }
    oss << "}\n";

    oss << "  Resources:           [";
    for (size_t i = 0; i < resources.size(); ++i) {
        oss << resources[i] << (i + 1 < resources.size() ? ", " : "");
    }
    oss << "]\n";

    oss << "  Constraints:         [";
    for (size_t i = 0; i < constraints.size(); ++i) {
        oss << constraints[i] << (i + 1 < constraints.size() ? ", " : "");
    }
    oss << "]";

    return oss.str();
}

// ============================================================================
// CompatibilityReport Implementation
// ============================================================================

std::string CompatibilityReport::toString() const {
    std::ostringstream oss;
    oss << "Compatibility Assessment: " << (isCompatible ? "COMPATIBLE [YES]" : "INCOMPATIBLE [NO]") << "\n";
    oss << "  1. Output-Input Compatibility:      " << (outputInputCompatible ? "PASS" : "FAIL") << "\n";
    for (const auto& in : satisfiedInputs) {
        oss << "     + Satisfied input: " << in << "\n";
    }
    for (const auto& in : unsatisfiedInputs) {
        oss << "     - Missing/unsatisfied input: " << in << "\n";
    }
    oss << "  2. Effect-Precondition Compatibility: " << (effectPreconditionCompatible ? "PASS" : "FAIL") << "\n";
    for (const auto& pre : satisfiedPreconditions) {
        oss << "     + Satisfied precondition: " << pre << "\n";
    }
    for (const auto& conflict : conflictingEffects) {
        oss << "     x Conflict: " << conflict << "\n";
    }
    for (const auto& msg : diagnosticMessages) {
        oss << "     * Detail: " << msg << "\n";
    }
    return oss.str();
}

// ============================================================================
// Embedding Encoders
// ============================================================================

std::vector<double> encodeState(const State& state) {
    std::vector<double> vec(TOTAL_EMBEDDING_DIM, 0.0);
    // Encode state variables directly into the world state / effects subspace [28 .. 43]
    for (const auto& entry : state.variables) {
        size_t idx = DomainRegistry::instance().getPredicateIndex(entry.first);
        vec[OFFSET_EFFECTS + idx] = encodeValue(entry.second);
    }
    return vec;
}

std::vector<double> encodeGoal(const Goal& goal) {
    std::vector<double> vec(TOTAL_EMBEDDING_DIM, 0.0);
    // Goals represent desired target world conditions in the effects/world subspace [28 .. 43]
    for (const auto& entry : goal.conditions) {
        size_t idx = DomainRegistry::instance().getPredicateIndex(entry.first);
        vec[OFFSET_EFFECTS + idx] = encodeValue(entry.second);
    }
    return vec;
}

std::vector<double> encodeCapability(const Capability& capability) {
    std::vector<double> vec(TOTAL_EMBEDDING_DIM, 0.0);

    // 1. Capability Type (One-hot categorical encoding: indices 0 .. 8)
    size_t typeIdx = static_cast<size_t>(capability.type);
    if (typeIdx < DIM_TYPE) {
        vec[OFFSET_TYPE + typeIdx] = 1.0;
    }

    // 2. Operational Attributes (indices 9 .. 11)
    // Normalized cost via logistic softsign: c_norm = cost / (cost + 50.0) in [0, 1)
    double normCost = (capability.cost > 0.0) ? (capability.cost / (capability.cost + 50.0)) : 0.0;
    vec[OFFSET_OPS + 0] = normCost;
    vec[OFFSET_OPS + 1] = std::max(0.0, std::min(1.0, capability.reliability));
    vec[OFFSET_OPS + 2] = std::max(0.0, std::min(1.0, capability.availability));

    // 3. Preconditions (indices 12 .. 27)
    for (const auto& entry : capability.preconditions) {
        size_t idx = DomainRegistry::instance().getPredicateIndex(entry.first);
        vec[OFFSET_PRECONDITIONS + idx] = encodeValue(entry.second);
    }

    // 4. Effects (indices 28 .. 43)
    for (const auto& entry : capability.effects) {
        size_t idx = DomainRegistry::instance().getPredicateIndex(entry.first);
        vec[OFFSET_EFFECTS + idx] = encodeValue(entry.second);
    }

    // 5. Inputs (indices 44 .. 59)
    for (const auto& in : capability.inputs) {
        size_t idx = DomainRegistry::instance().getDataIndex(in);
        vec[OFFSET_INPUTS + idx] = 1.0;
    }

    // 6. Outputs (indices 60 .. 75)
    for (const auto& out : capability.outputs) {
        size_t idx = DomainRegistry::instance().getDataIndex(out);
        vec[OFFSET_OUTPUTS + idx] = 1.0;
    }

    // 7. Resources (indices 76 .. 83)
    for (const auto& res : capability.resources) {
        size_t idx = DomainRegistry::instance().getResourceIndex(res);
        vec[OFFSET_RESOURCES + idx] = 1.0;
    }

    // 8. Constraints (indices 84 .. 91)
    for (const auto& con : capability.constraints) {
        size_t idx = DomainRegistry::instance().getConstraintIndex(con);
        vec[OFFSET_CONSTRAINTS + idx] = 1.0;
    }

    return vec;
}

// ============================================================================
// Cosine Similarity
// ============================================================================

double similarity(const std::vector<double>& a, const std::vector<double>& b) {
    if (a.size() != b.size()) {
        throw std::invalid_argument("Vector dimension mismatch: vector 'a' size " +
                                    std::to_string(a.size()) + " vs vector 'b' size " +
                                    std::to_string(b.size()));
    }

    double dotProduct = 0.0;
    double normA = 0.0;
    double normB = 0.0;

    for (size_t i = 0; i < a.size(); ++i) {
        dotProduct += a[i] * b[i];
        normA += a[i] * a[i];
        normB += b[i] * b[i];
    }

    if (normA <= 1e-12 || normB <= 1e-12) {
        return 0.0;
    }

    double denom = std::sqrt(normA) * std::sqrt(normB);
    double sim = dotProduct / denom;

    // Clamp numerical drift into [-1.0, 1.0]
    return std::max(-1.0, std::min(1.0, sim));
}

// ============================================================================
// Compatibility Checking
// ============================================================================

CompatibilityReport checkCompatibility(const Capability& first, const Capability& second) {
    CompatibilityReport report;

    // -------------------------------------------------------------
    // Check 1: Effect-Precondition Compatibility
    // -------------------------------------------------------------
    bool hasContradiction = false;
    size_t preconditionsSatisfied = 0;

    for (const auto& entry : second.preconditions) {
        const std::string& reqVar = entry.first;
        const std::string& reqVal = entry.second;

        auto it = first.effects.find(reqVar);
        if (it != first.effects.end()) {
            double effSign = encodeValue(it->second);
            double reqSign = encodeValue(reqVal);

            if (effSign != reqSign) {
                // Direct state conflict!
                hasContradiction = true;
                report.conflictingEffects.push_back(
                    reqVar + " (first.effect=" + it->second + " contradicts second.precondition=" + reqVal + ")"
                );
            } else {
                preconditionsSatisfied++;
                report.satisfiedPreconditions.push_back(
                    reqVar + "=" + reqVal + " (satisfied by first.effect)"
                );
            }
        }
    }

    report.effectPreconditionCompatible = !hasContradiction;

    // -------------------------------------------------------------
    // Check 2: Output-Input Compatibility
    // -------------------------------------------------------------
    if (second.inputs.empty()) {
        report.outputInputCompatible = true;
        report.diagnosticMessages.push_back("Second capability requires no inputs; dataflow trivially satisfied.");
    } else {
        size_t matchedInputs = 0;
        for (const auto& inB : second.inputs) {
            auto it = std::find(first.outputs.begin(), first.outputs.end(), inB);
            if (it != first.outputs.end()) {
                matchedInputs++;
                report.satisfiedInputs.push_back(inB + " (supplied by first.outputs)");
            } else {
                report.unsatisfiedInputs.push_back(inB);
            }
        }

        if (matchedInputs > 0) {
            report.outputInputCompatible = true;
            if (matchedInputs == second.inputs.size()) {
                report.diagnosticMessages.push_back("All inputs of second are fully satisfied by first outputs.");
            } else {
                report.diagnosticMessages.push_back("Partial inputs satisfied by first outputs; remaining inputs assumed external.");
            }
        } else {
            if (preconditionsSatisfied > 0 && !hasContradiction) {
                // State-driven pipeline without direct dataflow
                report.outputInputCompatible = true;
                report.diagnosticMessages.push_back("State-driven composition: no shared data parameters, but state preconditions aligned.");
            } else {
                report.outputInputCompatible = false;
                report.diagnosticMessages.push_back("Dataflow mismatch: first outputs none of the inputs required by second.");
            }
        }
    }

    report.isCompatible = report.effectPreconditionCompatible &&
                          report.outputInputCompatible &&
                          (!hasContradiction);

    return report;
}

bool areCompatible(const Capability& first, const Capability& second) {
    return checkCompatibility(first, second).isCompatible;
}

// ============================================================================
// Capability Composition
// ============================================================================

Capability composeCapabilities(const Capability& c1, const Capability& c2, const std::string& compositeName) {
    Capability comp;

    // Name
    if (!compositeName.empty()) {
        comp.name = compositeName;
    } else {
        comp.name = c1.name + "+" + c2.name;
    }

    // Capability Type
    comp.type = (c1.type == c2.type) ? c1.type : CapabilityType::SERVICE;

    // Execution Mechanism
    comp.executionMechanism = c1.executionMechanism + " | " + c2.executionMechanism;

    // Merge Inputs: In(c1) U (In(c2) \ Out(c1))
    comp.inputs = c1.inputs;
    for (const auto& in2 : c2.inputs) {
        bool providedByC1 = (std::find(c1.outputs.begin(), c1.outputs.end(), in2) != c1.outputs.end());
        if (!providedByC1) {
            if (std::find(comp.inputs.begin(), comp.inputs.end(), in2) == comp.inputs.end()) {
                comp.inputs.push_back(in2);
            }
        }
    }

    // Merge Outputs: Out(c1) U Out(c2)
    comp.outputs = c1.outputs;
    for (const auto& out2 : c2.outputs) {
        if (std::find(comp.outputs.begin(), comp.outputs.end(), out2) == comp.outputs.end()) {
            comp.outputs.push_back(out2);
        }
    }

    // Merge Preconditions: Pre(c1) U (Pre(c2) \ Eff(c1))
    comp.preconditions = c1.preconditions;
    for (const auto& entry : c2.preconditions) {
        const std::string& reqVar = entry.first;
        const std::string& reqVal = entry.second;

        auto effIt = c1.effects.find(reqVar);
        if (effIt != c1.effects.end() && encodeValue(effIt->second) == encodeValue(reqVal)) {
            // Satisfied by c1's intermediate effects
            continue;
        }
        comp.preconditions[reqVar] = reqVal;
    }

    // Merge Effects: Eff(c1) sequentially updated with Eff(c2)
    comp.effects = c1.effects;
    for (const auto& entry : c2.effects) {
        comp.effects[entry.first] = entry.second; // c2 effect overwrites/augments c1
    }

    // Merge Constraints (Union)
    comp.constraints = c1.constraints;
    for (const auto& con : c2.constraints) {
        if (std::find(comp.constraints.begin(), comp.constraints.end(), con) == comp.constraints.end()) {
            comp.constraints.push_back(con);
        }
    }

    // Merge Resources (Union)
    comp.resources = c1.resources;
    for (const auto& res : c2.resources) {
        if (std::find(comp.resources.begin(), comp.resources.end(), res) == comp.resources.end()) {
            comp.resources.push_back(res);
        }
    }

    // Operational Attributes Combination
    // 1. Cost is additive in sequential execution
    comp.cost = c1.cost + c2.cost;

    // 2. Reliability is multiplicative (serial execution failure model: R_comp = R_1 * R_2)
    comp.reliability = c1.reliability * c2.reliability;

    // 3. Availability is multiplicative (serial system availability: A_comp = A_1 * A_2)
    comp.availability = c1.availability * c2.availability;

    return comp;
}

Capability composeCapabilities(const std::vector<Capability>& chain, const std::string& compositeName) {
    if (chain.empty()) {
        throw std::invalid_argument("Cannot compose an empty capability chain.");
    }
    if (chain.size() == 1) {
        Capability single = chain[0];
        if (!compositeName.empty()) single.name = compositeName;
        return single;
    }

    Capability current = chain[0];
    for (size_t i = 1; i < chain.size(); ++i) {
        std::string stepName = (i == chain.size() - 1 && !compositeName.empty()) ? compositeName : "";
        current = composeCapabilities(current, chain[i], stepName);
    }
    return current;
}

std::vector<double> encodeCompositeCapability(const Capability& c1, const Capability& c2, const std::string& compositeName) {
    Capability composite = composeCapabilities(c1, c2, compositeName);
    return encodeCapability(composite);
}

std::vector<double> encodeCompositeCapability(const std::vector<Capability>& chain, const std::string& compositeName) {
    Capability composite = composeCapabilities(chain, compositeName);
    return encodeCapability(composite);
}

// ============================================================================
// Goal Relevance
// ============================================================================

double goalRelevance(const Capability& capability, const Goal& goal) {
    if (goal.conditions.empty() || capability.effects.empty()) {
        return 0.0;
    }

    // Construct effect sub-vector in world state subspace [28 .. 43]
    std::vector<double> capEffVec(TOTAL_EMBEDDING_DIM, 0.0);
    for (const auto& entry : capability.effects) {
        size_t idx = DomainRegistry::instance().getPredicateIndex(entry.first);
        capEffVec[OFFSET_EFFECTS + idx] = encodeValue(entry.second);
    }

    // Construct goal vector
    std::vector<double> goalVec = encodeGoal(goal);

    // Compute cosine similarity between capability effects and desired goal
    double cosSim = similarity(capEffVec, goalVec);

    // If effects oppose the goal (negative dot product), relevance is 0.0
    if (cosSim <= 0.0) {
        return 0.0;
    }

    return std::max(0.0, std::min(1.0, cosSim));
}

// ============================================================================
// Formatting & Diagnostic Utilities
// ============================================================================

void printVector(const std::string& label, const std::vector<double>& vec, size_t maxElements) {
    std::cout << label << " [dim=" << vec.size() << "]: [";
    size_t count = std::min(vec.size(), maxElements);
    for (size_t i = 0; i < count; ++i) {
        std::cout << std::fixed << std::setprecision(3) << vec[i] << (i + 1 < count ? ", " : "");
    }
    if (vec.size() > maxElements) {
        std::cout << ", ... (" << (vec.size() - maxElements) << " more)";
    }
    std::cout << "]\n";
}

void printSimilarityMatrix(const std::vector<std::string>& labels, const std::vector<std::vector<double>>& matrix) {
    size_t n = labels.size();
    size_t colWidth = 14;

    // Header
    std::cout << std::left << std::setw(26) << "Capability / Service";
    for (size_t j = 0; j < n; ++j) {
        std::cout << std::right << std::setw(colWidth) << labels[j].substr(0, colWidth - 1);
    }
    std::cout << "\n" << std::string(26 + n * colWidth, '-') << "\n";

    // Rows
    for (size_t i = 0; i < n; ++i) {
        std::cout << std::left << std::setw(26) << labels[i];
        for (size_t j = 0; j < n; ++j) {
            std::cout << std::right << std::setw(colWidth) << std::fixed << std::setprecision(4) << matrix[i][j];
        }
        std::cout << "\n";
    }
}

std::string describeEmbeddingLayout() {
    std::ostringstream oss;
    oss << "Embedding Space Layout (" << TOTAL_EMBEDDING_DIM << " total dimensions):\n"
        << "  [00 .. 08] (9 dims):  Capability Type (One-hot: API, DB, GUI, EVENT, FUNC, FILE, COMP, MSG, SERVICE)\n"
        << "  [09 .. 11] (3 dims):  Operational Attributes (Normalized Cost, Reliability, Availability)\n"
        << "  [12 .. 27] (16 dims): Preconditions (State Proposition Sign Vectors)\n"
        << "  [28 .. 43] (16 dims): Effects / Desired State Variables (State Proposition Sign Vectors)\n"
        << "  [44 .. 59] (16 dims): Data Inputs (Attribute Presence Indicator Vectors)\n"
        << "  [60 .. 75] (16 dims): Data Outputs (Attribute Presence Indicator Vectors)\n"
        << "  [76 .. 83] (8 dims):  Resources (Physical / Logical Dependency Indicators)\n"
        << "  [84 .. 91] (8 dims):  Constraints (Safety & Operational Invariants)\n";
    return oss.str();
}
