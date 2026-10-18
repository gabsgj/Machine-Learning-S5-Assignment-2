#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <iomanip>
#include <cassert>
#include <numeric>
#include <sstream>
#include <algorithm>

// ============================================================================
// 1. FORMAL APPLICATION MODEL & VOCABULARIES
// ============================================================================

// State Predicates (11 Dimensions) - Section 3
enum StatePredicate {
    STUDENT_AUTHENTICATED = 0,
    STUDENT_EXISTS,
    STUDENT_ELIGIBLE,
    COURSE_EXISTS,
    COURSE_AVAILABLE,
    REGISTRATION_OPEN,
    ENROLLMENT_EXISTS,
    PAYMENT_COMPLETED,
    NOTIFICATION_SENT,
    REGISTRATION_CONFIRMED,
    REGISTRATION_REPORT_GENERATED,
    STATE_PREDICATE_COUNT
};

const std::vector<std::string> STATE_PREDICATE_NAMES = {
    "student_authenticated",
    "student_exists",
    "student_eligible",
    "course_exists",
    "course_available",
    "registration_open",
    "enrollment_exists",
    "payment_completed",
    "notification_sent",
    "registration_confirmed",
    "registration_report_generated"
};

// Ternary Condition Representation - Section 4
// +1 = TRUE / required or produced
// -1 = FALSE / required or produced
//  0 = IRRELEVANT
enum ConditionValue {
    FALSE_VALUE = -1,
    IRRELEVANT = 0,
    TRUE_VALUE = 1
};

// Input Vocabulary (5 Dimensions) - Section 7
enum InputType {
    IN_STUDENT_ID = 0,
    IN_COURSE_ID,
    IN_ENROLLMENT_ID,
    IN_PAYMENT_DETAILS,
    IN_REGISTRATION_DETAILS,
    INPUT_COUNT
};

const std::vector<std::string> INPUT_NAMES = {
    "student_id",
    "course_id",
    "enrollment_id",
    "payment_details",
    "registration_details"
};

// Output Vocabulary (8 Dimensions) - Section 8
enum OutputType {
    OUT_ELIGIBILITY_STATUS = 0,
    OUT_AVAILABILITY_STATUS,
    OUT_ENROLLMENT_ID,
    OUT_PAYMENT_RECEIPT,
    OUT_NOTIFICATION_ID,
    OUT_CONFIRMATION_ID,
    OUT_DROP_CONFIRMATION,
    OUT_REGISTRATION_REPORT,
    OUTPUT_COUNT
};

const std::vector<std::string> OUTPUT_NAMES = {
    "eligibility_status",
    "availability_status",
    "enrollment_id",
    "payment_receipt",
    "notification_id",
    "confirmation_id",
    "drop_confirmation",
    "registration_report"
};

// Resource Vocabulary (8 Dimensions) - Section 9
enum ResourceType {
    RES_STUDENT_DATABASE = 0,
    RES_COURSE_DATABASE,
    RES_REGISTRATION_DATABASE,
    RES_AUTHENTICATION_SERVICE,
    RES_PAYMENT_GATEWAY,
    RES_NETWORK,
    RES_NOTIFICATION_SERVICE,
    RES_FILE_SYSTEM,
    RESOURCE_COUNT
};

const std::vector<std::string> RESOURCE_NAMES = {
    "StudentDatabase",
    "CourseDatabase",
    "RegistrationDatabase",
    "AuthenticationService",
    "PaymentGateway",
    "Network",
    "NotificationService",
    "FileSystem"
};

// Constraint Vocabulary (5 Dimensions) - Section 10
enum ConstraintType {
    CON_AUTHENTICATION_REQUIRED = 0,
    CON_REGISTRATION_PERIOD_REQUIRED,
    CON_POSITIVE_PAYMENT,
    CON_VALID_STUDENT,
    CON_VALID_COURSE,
    CONSTRAINT_COUNT
};

const std::vector<std::string> CONSTRAINT_NAMES = {
    "authentication_required",
    "registration_period_required",
    "positive_payment",
    "valid_student",
    "valid_course"
};

// Capability Type Vocabulary (6 Dimensions) - Section 11
enum CapabilityType {
    TYPE_API = 0,
    TYPE_DATABASE,
    TYPE_FUNCTION,
    TYPE_SERVICE,
    TYPE_COMPUTATION,
    TYPE_GUI,
    CAPABILITY_TYPE_COUNT
};

const std::vector<std::string> CAPABILITY_TYPE_NAMES = {
    "API",
    "DATABASE",
    "FUNCTION",
    "SERVICE",
    "COMPUTATION",
    "GUI"
};

// Mechanism Vocabulary (8 Dimensions) - Section 12 & 16
// Preserves strictly 8 dimensions for the mechanism block M
enum MechanismType {
    MECH_LOCAL_FUNCTION = 0,       // In-memory functions: EligibilityFunction, ConfirmationFunction, localAvailabilityFunction
    MECH_SQL_DATABASE_QUERY,       // SQL/DB Queries: DatabaseQuery, SELECT availability FROM courses
    MECH_REST_POST_REGISTRATION,   // POST /registration
    MECH_REST_POST_PAYMENT,        // POST /payment
    MECH_REST_GET_AVAILABILITY,    // GET /courses/{id}/availability (C9)
    MECH_NOTIFICATION_SERVICE,     // NotificationService protocol (C5)
    MECH_REST_DELETE_REGISTRATION, // DELETE /registration (C7)
    MECH_REPORT_GENERATOR,         // ReportGenerator file computation (C8)
    MECHANISM_COUNT
};

const std::vector<std::string> MECHANISM_NAMES = {
    "Local Function / Logic",
    "SQL / Database Query",
    "POST /registration",
    "POST /payment",
    "GET /courses/{id}/availability",
    "NotificationService",
    "DELETE /registration",
    "ReportGenerator"
};

// ============================================================================
// 2. CORE STRUCTURES
// ============================================================================

// State representation (11 Boolean values) - Section 3
struct State {
    std::vector<bool> predicates;

    State() : predicates(STATE_PREDICATE_COUNT, false) {}

    explicit State(const std::vector<bool>& preds) : predicates(preds) {
        assert(predicates.size() == STATE_PREDICATE_COUNT);
    }

    bool get(StatePredicate p) const {
        return predicates[static_cast<size_t>(p)];
    }

    void set(StatePredicate p, bool val) {
        predicates[static_cast<size_t>(p)] = val;
    }
};

// Goal representation (11 Ternary values) - Section 6
struct Goal {
    std::vector<ConditionValue> conditions;

    Goal() : conditions(STATE_PREDICATE_COUNT, IRRELEVANT) {}

    void set(StatePredicate p, ConditionValue val) {
        conditions[static_cast<size_t>(p)] = val;
    }

    ConditionValue get(StatePredicate p) const {
        return conditions[static_cast<size_t>(p)];
    }

    bool isSatisfied(const State& state) const {
        for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
            if (conditions[i] == TRUE_VALUE && !state.predicates[i]) return false;
            if (conditions[i] == FALSE_VALUE && state.predicates[i]) return false;
        }
        return true;
    }
};

// Operational Properties - Section 14
struct OperationalProperties {
    double cost = 0.0;          // Absolute cost (Max in dataset = 20)
    double reliability = 1.0;   // [0.0, 1.0]
    double availability = 1.0;  // [0.0, 1.0]

    double normalizedCost() const {
        return cost / 20.0;
    }
};

// Capability representation - Section 13 & 15
struct Capability {
    std::string id;
    std::string name;
    std::string mechanismName;
    CapabilityType type;
    std::vector<ConditionValue> preconditions; // 11 dimensions
    std::vector<ConditionValue> effects;       // 11 dimensions
    std::vector<double> inputs;                // 5 dimensions (binary 0/1)
    std::vector<double> outputs;               // 8 dimensions (binary 0/1)
    std::vector<double> resources;             // 8 dimensions (binary 0/1)
    std::vector<double> constraints;           // 5 dimensions (binary 0/1)
    MechanismType mechanism;                   // 8 dimensions (one-hot)
    OperationalProperties operational;         // 3 dimensions

    Capability()
        : mechanismName(""),
          type(TYPE_FUNCTION),
          preconditions(STATE_PREDICATE_COUNT, IRRELEVANT),
          effects(STATE_PREDICATE_COUNT, IRRELEVANT),
          inputs(INPUT_COUNT, 0.0),
          outputs(OUTPUT_COUNT, 0.0),
          resources(RESOURCE_COUNT, 0.0),
          constraints(CONSTRAINT_COUNT, 0.0),
          mechanism(MECH_LOCAL_FUNCTION) {}
};

// ============================================================================
// 3. EMBEDDING FUNCTIONS
// ============================================================================

// State Embedding: phi_S(S) in {-1, +1}^11 - Section 5
std::vector<double> encodeState(const State& state) {
    std::vector<double> vec(STATE_PREDICATE_COUNT);
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        vec[i] = state.predicates[i] ? 1.0 : -1.0;
    }
    return vec;
}

// Goal Embedding: phi_G(G) in {-1, 0, +1}^11 - Section 6
std::vector<double> encodeGoal(const Goal& goal) {
    std::vector<double> vec(STATE_PREDICATE_COUNT);
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        vec[i] = static_cast<double>(goal.conditions[i]);
    }
    return vec;
}

// Capability Full Embedding: phi_C(C) in R^65 - Section 13
// [P(11), E(11), I(5), O(8), R(8), K(5), T(6), M(8), Q(3)] = 65 dimensions
std::vector<double> encodeCapability(const Capability& cap) {
    std::vector<double> vec;
    vec.reserve(65);

    // 1. Preconditions P (11)
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        vec.push_back(static_cast<double>(cap.preconditions[i]));
    }

    // 2. Effects E (11)
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        vec.push_back(static_cast<double>(cap.effects[i]));
    }

    // 3. Inputs I (5)
    for (size_t i = 0; i < INPUT_COUNT; ++i) {
        vec.push_back(cap.inputs[i]);
    }

    // 4. Outputs O (8)
    for (size_t i = 0; i < OUTPUT_COUNT; ++i) {
        vec.push_back(cap.outputs[i]);
    }

    // 5. Resources R (8)
    for (size_t i = 0; i < RESOURCE_COUNT; ++i) {
        vec.push_back(cap.resources[i]);
    }

    // 6. Constraints K (5)
    for (size_t i = 0; i < CONSTRAINT_COUNT; ++i) {
        vec.push_back(cap.constraints[i]);
    }

    // 7. Capability Type T (6, one-hot)
    for (size_t i = 0; i < CAPABILITY_TYPE_COUNT; ++i) {
        vec.push_back(cap.type == static_cast<CapabilityType>(i) ? 1.0 : 0.0);
    }

    // 8. Mechanism M (8, one-hot)
    for (size_t i = 0; i < MECHANISM_COUNT; ++i) {
        vec.push_back(cap.mechanism == static_cast<MechanismType>(i) ? 1.0 : 0.0);
    }

    // 9. Operational Q (3)
    vec.push_back(cap.operational.normalizedCost());
    vec.push_back(cap.operational.reliability);
    vec.push_back(cap.operational.availability);

    assert(vec.size() == 65 && "Capability embedding must have exactly 65 dimensions!");
    return vec;
}

// Capability Functional Embedding: phi_F(C) in R^35 - Section 17
// [P(11), E(11), I(5), O(8)] = 35 dimensions
std::vector<double> encodeFunctional(const Capability& cap) {
    std::vector<double> vec;
    vec.reserve(35);

    // P (11)
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        vec.push_back(static_cast<double>(cap.preconditions[i]));
    }
    // E (11)
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        vec.push_back(static_cast<double>(cap.effects[i]));
    }
    // I (5)
    for (size_t i = 0; i < INPUT_COUNT; ++i) {
        vec.push_back(cap.inputs[i]);
    }
    // O (8)
    for (size_t i = 0; i < OUTPUT_COUNT; ++i) {
        vec.push_back(cap.outputs[i]);
    }

    assert(vec.size() == 35 && "Functional embedding must have exactly 35 dimensions!");
    return vec;
}

// ============================================================================
// 4. SIMILARITY & DIAGNOSTIC METRICS
// ============================================================================

// Cosine Similarity with safe zero-vector handling - Section 18
double cosineSimilarity(const std::vector<double>& a, const std::vector<double>& b) {
    if (a.size() != b.size() || a.empty()) return 0.0;

    double dot = 0.0;
    double norm_a = 0.0;
    double norm_b = 0.0;

    for (size_t i = 0; i < a.size(); ++i) {
        dot += a[i] * b[i];
        norm_a += a[i] * a[i];
        norm_b += b[i] * b[i];
    }

    if (norm_a <= 1e-12 && norm_b <= 1e-12) return 1.0;
    if (norm_a <= 1e-12 || norm_b <= 1e-12) return 0.0;

    return dot / (std::sqrt(norm_a) * std::sqrt(norm_b));
}

// Block-Level & Overall Similarity - Section 19
struct BlockSimilarityResult {
    double sim_P;
    double sim_E;
    double sim_I;
    double sim_O;
    double sim_R;
    double sim_K;
    double sim_T;
    double sim_M;
    double sim_Q;
    double sim_functional;
    double sim_overall;
};

BlockSimilarityResult blockSimilarity(const Capability& c1, const Capability& c2) {
    BlockSimilarityResult res;

    auto subCosine = [](const auto& v1, const auto& v2) {
        std::vector<double> d1(v1.begin(), v1.end());
        std::vector<double> d2(v2.begin(), v2.end());
        return cosineSimilarity(d1, d2);
    };

    res.sim_P = subCosine(c1.preconditions, c2.preconditions);
    res.sim_E = subCosine(c1.effects, c2.effects);
    res.sim_I = subCosine(c1.inputs, c2.inputs);
    res.sim_O = subCosine(c1.outputs, c2.outputs);
    res.sim_R = subCosine(c1.resources, c2.resources);
    res.sim_K = subCosine(c1.constraints, c2.constraints);

    // Type one-hot (6)
    std::vector<double> t1(CAPABILITY_TYPE_COUNT, 0.0), t2(CAPABILITY_TYPE_COUNT, 0.0);
    t1[static_cast<size_t>(c1.type)] = 1.0;
    t2[static_cast<size_t>(c2.type)] = 1.0;
    res.sim_T = cosineSimilarity(t1, t2);

    // Mechanism one-hot (8)
    std::vector<double> m1(MECHANISM_COUNT, 0.0), m2(MECHANISM_COUNT, 0.0);
    m1[static_cast<size_t>(c1.mechanism)] = 1.0;
    m2[static_cast<size_t>(c2.mechanism)] = 1.0;
    res.sim_M = cosineSimilarity(m1, m2);

    // Operational (3)
    std::vector<double> q1 = {c1.operational.normalizedCost(), c1.operational.reliability, c1.operational.availability};
    std::vector<double> q2 = {c2.operational.normalizedCost(), c2.operational.reliability, c2.operational.availability};
    res.sim_Q = cosineSimilarity(q1, q2);

    // Functional similarity (on R^35)
    res.sim_functional = cosineSimilarity(encodeFunctional(c1), encodeFunctional(c2));

    // Overall similarity (average of 9 blocks)
    res.sim_overall = (res.sim_P + res.sim_E + res.sim_I + res.sim_O +
                       res.sim_R + res.sim_K + res.sim_T + res.sim_M + res.sim_Q) / 9.0;

    return res;
}

// ============================================================================
// 5. APPLICABILITY, TRANSITIONS & COMPOSITION
// ============================================================================

// State Applicability: Applicable(C, S) <=> S |= P_C - Section 20
bool isApplicable(const Capability& cap, const State& state) {
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        if (cap.preconditions[i] == TRUE_VALUE && !state.predicates[i]) {
            return false;
        }
        if (cap.preconditions[i] == FALSE_VALUE && state.predicates[i]) {
            return false;
        }
    }
    return true;
}

// State Transition: S' = Apply(S, E_C) - Section 21
State applyEffects(const State& state, const Capability& cap) {
    State nextState = state;
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        if (cap.effects[i] == TRUE_VALUE) {
            nextState.predicates[i] = true;
        } else if (cap.effects[i] == FALSE_VALUE) {
            nextState.predicates[i] = false;
        }
    }
    return nextState;
}

// State-Aware Composition: C1 -> C2 in S_I - Section 22
bool canCompose(const Capability& c1, const Capability& c2, const State& initialState) {
    if (!isApplicable(c1, initialState)) {
        return false;
    }
    State s1 = applyEffects(initialState, c1);
    return isApplicable(c2, s1);
}

// Direct Effect-Precondition Compatibility (Diagnostic Metric) - Section 23
// Measures how much of C2's preconditions are directly supplied by C1's effects
double effectPreconditionCompatibility(const Capability& c1, const Capability& c2) {
    int requiredCount = 0;
    int satisfiedCount = 0;

    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        if (c2.preconditions[i] != IRRELEVANT) {
            requiredCount++;
            if (c1.effects[i] == c2.preconditions[i]) {
                satisfiedCount++;
            }
        }
    }

    if (requiredCount == 0) return 1.0;
    return static_cast<double>(satisfiedCount) / static_cast<double>(requiredCount);
}

// Input-Output Compatibility: IOComp(C1, C2) = (O(C1) . I(C2)) / |I_flow(C2)| - Section 24
// Measures if outputs of C1 satisfy the data inputs of C2 (e.g. enrollment_id)
double inputOutputCompatibility(const Capability& c1, const Capability& c2) {
    double matched = 0.0;
    double requiredFlowInputs = 0.0;

    // Check shared pipeline data types between outputs and inputs
    // OUT_ENROLLMENT_ID (2) -> IN_ENROLLMENT_ID (2)
    if (c2.inputs[IN_ENROLLMENT_ID] > 0.0) {
        requiredFlowInputs += 1.0;
        if (c1.outputs[OUT_ENROLLMENT_ID] > 0.0) {
            matched += 1.0;
        }
    }

    if (requiredFlowInputs <= 1e-12) return 0.0;
    return matched / requiredFlowInputs;
}

// Goal Relevance: GoalRel(C, G) = |E_C cap G| / |G| - Section 25
double goalRelevance(const Capability& cap, const Goal& goal) {
    int goalCount = 0;
    int matchedCount = 0;

    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        if (goal.conditions[i] != IRRELEVANT) {
            goalCount++;
            if (cap.effects[i] == goal.conditions[i]) {
                matchedCount++;
            }
        }
    }

    if (goalCount == 0) return 0.0;
    return static_cast<double>(matchedCount) / static_cast<double>(goalCount);
}

// ============================================================================
// 6. COMPOSITION & SEQUENCE EXECUTION
// ============================================================================

// Composite Capability Construction - Section 27 & 28
Capability composeSequence(const std::vector<Capability>& sequence, const State& initialState) {
    Capability composite;
    composite.id = "C_composite";
    composite.name = "CompositeCourseRegistration";
    composite.mechanismName = "POST /registration (Pipeline)";
    composite.type = TYPE_SERVICE;
    composite.mechanism = MECH_REST_POST_REGISTRATION;

    State currentState = initialState;
    double totalCost = 0.0;
    double totalReliability = 1.0;
    double minAvailability = 1.0;

    for (size_t step = 0; step < sequence.size(); ++step) {
        const auto& cap = sequence[step];
        currentState = applyEffects(currentState, cap);

        totalCost += cap.operational.cost;
        totalReliability *= cap.operational.reliability;
        minAvailability = std::min(minAvailability, cap.operational.availability);

        for (size_t i = 0; i < INPUT_COUNT; ++i) {
            if (cap.inputs[i] > 0.0) composite.inputs[i] = 1.0;
        }
        for (size_t i = 0; i < OUTPUT_COUNT; ++i) {
            if (cap.outputs[i] > 0.0) composite.outputs[i] = 1.0;
        }
        for (size_t i = 0; i < RESOURCE_COUNT; ++i) {
            if (cap.resources[i] > 0.0) composite.resources[i] = 1.0;
        }
        for (size_t i = 0; i < CONSTRAINT_COUNT; ++i) {
            if (cap.constraints[i] > 0.0) composite.constraints[i] = 1.0;
        }
    }

    composite.operational.cost = totalCost;
    composite.operational.reliability = totalReliability;
    composite.operational.availability = minAvailability;

    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        if (currentState.predicates[i] != initialState.predicates[i]) {
            composite.effects[i] = currentState.predicates[i] ? TRUE_VALUE : FALSE_VALUE;
        }
    }

    auto embedding = encodeCapability(composite);
    assert(embedding.size() == 65);

    return composite;
}

// ============================================================================
// 7. DATASET DEFINITIONS
// ============================================================================

std::vector<Capability> createCapabilities() {
    std::vector<Capability> caps;

    // C1 — CheckEligibility
    {
        Capability c;
        c.id = "C1";
        c.name = "CheckEligibility";
        c.mechanismName = "EligibilityFunction";
        c.type = TYPE_FUNCTION;
        c.inputs[IN_STUDENT_ID] = 1.0;
        c.outputs[OUT_ELIGIBILITY_STATUS] = 1.0;
        c.preconditions[STUDENT_EXISTS] = TRUE_VALUE;
        c.preconditions[STUDENT_AUTHENTICATED] = TRUE_VALUE;
        c.effects[STUDENT_ELIGIBLE] = TRUE_VALUE;
        c.resources[RES_STUDENT_DATABASE] = 1.0;
        c.constraints[CON_AUTHENTICATION_REQUIRED] = 1.0;
        c.constraints[CON_VALID_STUDENT] = 1.0;
        c.operational.cost = 5.0;
        c.operational.reliability = 0.99;
        c.operational.availability = 1.0;
        c.mechanism = MECH_LOCAL_FUNCTION;
        caps.push_back(c);
    }

    // C2 — CheckCourseAvailability
    {
        Capability c;
        c.id = "C2";
        c.name = "CheckCourseAvailability";
        c.mechanismName = "DatabaseQuery";
        c.type = TYPE_DATABASE;
        c.inputs[IN_COURSE_ID] = 1.0;
        c.outputs[OUT_AVAILABILITY_STATUS] = 1.0;
        c.preconditions[COURSE_EXISTS] = TRUE_VALUE;
        c.preconditions[REGISTRATION_OPEN] = TRUE_VALUE;
        c.effects[COURSE_AVAILABLE] = TRUE_VALUE;
        c.resources[RES_COURSE_DATABASE] = 1.0;
        c.constraints[CON_REGISTRATION_PERIOD_REQUIRED] = 1.0;
        c.constraints[CON_VALID_COURSE] = 1.0;
        c.operational.cost = 3.0;
        c.operational.reliability = 0.995;
        c.operational.availability = 1.0;
        c.mechanism = MECH_SQL_DATABASE_QUERY;
        caps.push_back(c);
    }

    // C3 — RegisterCourse
    {
        Capability c;
        c.id = "C3";
        c.name = "RegisterCourse";
        c.mechanismName = "POST /registration";
        c.type = TYPE_API;
        c.inputs[IN_STUDENT_ID] = 1.0;
        c.inputs[IN_COURSE_ID] = 1.0;
        c.outputs[OUT_ENROLLMENT_ID] = 1.0;
        c.preconditions[STUDENT_AUTHENTICATED] = TRUE_VALUE;
        c.preconditions[STUDENT_ELIGIBLE] = TRUE_VALUE;
        c.preconditions[COURSE_AVAILABLE] = TRUE_VALUE;
        c.preconditions[REGISTRATION_OPEN] = TRUE_VALUE;
        c.effects[ENROLLMENT_EXISTS] = TRUE_VALUE;
        c.resources[RES_REGISTRATION_DATABASE] = 1.0;
        c.resources[RES_AUTHENTICATION_SERVICE] = 1.0;
        c.constraints[CON_AUTHENTICATION_REQUIRED] = 1.0;
        c.constraints[CON_REGISTRATION_PERIOD_REQUIRED] = 1.0;
        c.constraints[CON_VALID_STUDENT] = 1.0;
        c.constraints[CON_VALID_COURSE] = 1.0;
        c.operational.cost = 10.0;
        c.operational.reliability = 0.99;
        c.operational.availability = 1.0;
        c.mechanism = MECH_REST_POST_REGISTRATION;
        caps.push_back(c);
    }

    // C4 — MakePayment
    {
        Capability c;
        c.id = "C4";
        c.name = "MakePayment";
        c.mechanismName = "POST /payment";
        c.type = TYPE_API;
        c.inputs[IN_ENROLLMENT_ID] = 1.0;
        c.inputs[IN_PAYMENT_DETAILS] = 1.0;
        c.outputs[OUT_PAYMENT_RECEIPT] = 1.0;
        c.preconditions[ENROLLMENT_EXISTS] = TRUE_VALUE;
        c.effects[PAYMENT_COMPLETED] = TRUE_VALUE;
        c.resources[RES_PAYMENT_GATEWAY] = 1.0;
        c.resources[RES_NETWORK] = 1.0;
        c.constraints[CON_POSITIVE_PAYMENT] = 1.0;
        c.operational.cost = 15.0;
        c.operational.reliability = 0.98;
        c.operational.availability = 1.0;
        c.mechanism = MECH_REST_POST_PAYMENT;
        caps.push_back(c);
    }

    // C5 — SendNotification
    {
        Capability c;
        c.id = "C5";
        c.name = "SendNotification";
        c.mechanismName = "NotificationService";
        c.type = TYPE_SERVICE;
        c.inputs[IN_STUDENT_ID] = 1.0;
        c.inputs[IN_REGISTRATION_DETAILS] = 1.0;
        c.outputs[OUT_NOTIFICATION_ID] = 1.0;
        c.preconditions[ENROLLMENT_EXISTS] = TRUE_VALUE;
        c.preconditions[PAYMENT_COMPLETED] = TRUE_VALUE;
        c.effects[NOTIFICATION_SENT] = TRUE_VALUE;
        c.resources[RES_NOTIFICATION_SERVICE] = 1.0;
        c.resources[RES_NETWORK] = 1.0;
        c.constraints[CON_VALID_STUDENT] = 1.0;
        c.operational.cost = 4.0;
        c.operational.reliability = 0.97;
        c.operational.availability = 1.0;
        c.mechanism = MECH_NOTIFICATION_SERVICE;
        caps.push_back(c);
    }

    // C6 — ConfirmRegistration
    {
        Capability c;
        c.id = "C6";
        c.name = "ConfirmRegistration";
        c.mechanismName = "ConfirmationFunction";
        c.type = TYPE_FUNCTION;
        c.inputs[IN_ENROLLMENT_ID] = 1.0;
        c.outputs[OUT_CONFIRMATION_ID] = 1.0;
        c.preconditions[ENROLLMENT_EXISTS] = TRUE_VALUE;
        c.preconditions[PAYMENT_COMPLETED] = TRUE_VALUE;
        c.effects[REGISTRATION_CONFIRMED] = TRUE_VALUE;
        c.resources[RES_REGISTRATION_DATABASE] = 1.0;
        c.constraints[CON_VALID_STUDENT] = 1.0;
        c.operational.cost = 2.0;
        c.operational.reliability = 0.995;
        c.operational.availability = 1.0;
        c.mechanism = MECH_LOCAL_FUNCTION;
        caps.push_back(c);
    }

    // C7 — DropCourse (Designed for incompatibility testing)
    {
        Capability c;
        c.id = "C7";
        c.name = "DropCourse";
        c.mechanismName = "DELETE /registration";
        c.type = TYPE_API;
        c.inputs[IN_ENROLLMENT_ID] = 1.0;
        c.outputs[OUT_DROP_CONFIRMATION] = 1.0;
        c.preconditions[ENROLLMENT_EXISTS] = TRUE_VALUE;
        c.preconditions[PAYMENT_COMPLETED] = FALSE_VALUE; // Negative precondition!
        c.effects[ENROLLMENT_EXISTS] = FALSE_VALUE;
        c.resources[RES_REGISTRATION_DATABASE] = 1.0;
        c.constraints[CON_VALID_STUDENT] = 1.0;
        c.operational.cost = 8.0;
        c.operational.reliability = 0.99;
        c.operational.availability = 1.0;
        c.mechanism = MECH_REST_DELETE_REGISTRATION;
        caps.push_back(c);
    }

    // C8 — GenerateRegistrationReport (Designed for irrelevance testing)
    {
        Capability c;
        c.id = "C8";
        c.name = "GenerateRegistrationReport";
        c.mechanismName = "ReportGenerator";
        c.type = TYPE_COMPUTATION;
        c.inputs[IN_ENROLLMENT_ID] = 1.0;
        c.outputs[OUT_REGISTRATION_REPORT] = 1.0;
        c.preconditions[ENROLLMENT_EXISTS] = TRUE_VALUE;
        c.effects[REGISTRATION_REPORT_GENERATED] = TRUE_VALUE;
        c.resources[RES_FILE_SYSTEM] = 1.0;
        c.operational.cost = 20.0;
        c.operational.reliability = 0.95;
        c.operational.availability = 1.0;
        c.mechanism = MECH_REPORT_GENERATOR;
        caps.push_back(c);
    }

    // Alternative Implementations of CheckCourseAvailability - Section 16
    // C9 — CheckCourseAvailability_API
    {
        Capability c = caps[1]; // Copy functional P, E, I, O from C2
        c.id = "C9";
        c.name = "CheckCourseAvailability_API";
        c.mechanismName = "GET /courses/{id}/availability";
        c.type = TYPE_API;
        c.mechanism = MECH_REST_GET_AVAILABILITY;
        c.resources[RES_COURSE_DATABASE] = 1.0;
        c.resources[RES_NETWORK] = 1.0;
        caps.push_back(c);
    }

    // C10 — CheckCourseAvailability_DATABASE
    {
        Capability c = caps[1]; // Copy functional P, E, I, O from C2
        c.id = "C10";
        c.name = "CheckCourseAvailability_DATABASE";
        c.mechanismName = "SELECT availability FROM courses";
        c.type = TYPE_DATABASE;
        c.mechanism = MECH_SQL_DATABASE_QUERY;
        c.resources[RES_COURSE_DATABASE] = 1.0;
        caps.push_back(c);
    }

    // C11 — CheckCourseAvailability_FUNCTION
    {
        Capability c = caps[1]; // Copy functional P, E, I, O from C2
        c.id = "C11";
        c.name = "CheckCourseAvailability_FUNCTION";
        c.mechanismName = "localAvailabilityFunction";
        c.type = TYPE_FUNCTION;
        c.mechanism = MECH_LOCAL_FUNCTION;
        c.resources[RES_COURSE_DATABASE] = 1.0;
        caps.push_back(c);
    }

    return caps;
}

// Initial State Creator - Section 3
State createInitialState() {
    State s;
    s.set(STUDENT_AUTHENTICATED, true);
    s.set(STUDENT_EXISTS, true);
    s.set(STUDENT_ELIGIBLE, false);
    s.set(COURSE_EXISTS, true);
    s.set(COURSE_AVAILABLE, true);
    s.set(REGISTRATION_OPEN, true);
    s.set(ENROLLMENT_EXISTS, false);
    s.set(PAYMENT_COMPLETED, false);
    s.set(NOTIFICATION_SENT, false);
    s.set(REGISTRATION_CONFIRMED, false);
    s.set(REGISTRATION_REPORT_GENERATED, false);
    return s;
}

// Primary Goal Creator - Section 6
Goal createPrimaryGoal() {
    Goal g;
    g.set(ENROLLMENT_EXISTS, TRUE_VALUE);
    g.set(PAYMENT_COMPLETED, TRUE_VALUE);
    g.set(NOTIFICATION_SENT, TRUE_VALUE);
    g.set(REGISTRATION_CONFIRMED, TRUE_VALUE);
    return g;
}

// Helper to print State neatly
void printState(const State& s) {
    std::cout << "  State Vector:\n";
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        std::cout << "    [" << std::setw(2) << i << "] " 
                  << std::setw(30) << std::left << STATE_PREDICATE_NAMES[i] << ": " 
                  << (s.predicates[i] ? "TRUE  (+1)" : "FALSE (-1)") << "\n";
    }
}

// Helper to format a vector as string [v1, v2, ...]
std::string formatVector(const std::vector<double>& v, int precision = 0) {
    std::ostringstream oss;
    oss << "[";
    for (size_t i = 0; i < v.size(); ++i) {
        if (precision == 0) {
            oss << static_cast<int>(v[i]);
        } else {
            oss << std::fixed << std::setprecision(precision) << v[i];
        }
        if (i + 1 < v.size()) oss << ", ";
    }
    oss << "]";
    return oss.str();
}

// Concise Embedding Display for C3 RegisterCourse (Requirement 6)
void displayRepresentativeEmbedding(const Capability& c) {
    std::cout << "==================================================\n";
    std::cout << "REPRESENTATIVE CAPABILITY EMBEDDING: [" << c.id << "] " << c.name << "\n";
    std::cout << "==================================================\n";

    std::vector<double> p_vec, e_vec, t_vec(CAPABILITY_TYPE_COUNT, 0.0), m_vec(MECHANISM_COUNT, 0.0);
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) p_vec.push_back(static_cast<double>(c.preconditions[i]));
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) e_vec.push_back(static_cast<double>(c.effects[i]));
    t_vec[static_cast<size_t>(c.type)] = 1.0;
    m_vec[static_cast<size_t>(c.mechanism)] = 1.0;
    std::vector<double> q_vec = {c.operational.normalizedCost(), c.operational.reliability, c.operational.availability};

    std::cout << "P (11) Preconditions : " << formatVector(p_vec) << "\n";
    std::cout << "E (11) Effects       : " << formatVector(e_vec) << "\n";
    std::cout << "I ( 5) Inputs        : " << formatVector(c.inputs) << "\n";
    std::cout << "O ( 8) Outputs       : " << formatVector(c.outputs) << "\n";
    std::cout << "R ( 8) Resources     : " << formatVector(c.resources) << "\n";
    std::cout << "K ( 5) Constraints   : " << formatVector(c.constraints) << "\n";
    std::cout << "T ( 6) Type One-Hot  : " << formatVector(t_vec) << " (Type: " << CAPABILITY_TYPE_NAMES[static_cast<size_t>(c.type)] << ")\n";
    std::cout << "M ( 8) Mechanism     : " << formatVector(m_vec) << " (" << c.mechanismName << ")\n";
    std::cout << "Q ( 3) Operational   : " << formatVector(q_vec, 4) << " [Cost_norm: " << c.operational.normalizedCost() 
              << ", Rel: " << c.operational.reliability << ", Avail: " << c.operational.availability << "]\n";
    std::cout << "Full embedding dimension: " << encodeCapability(c).size() << " dimensions\n\n";
}

// ============================================================================
// 8. UNIT TESTS & ASSERTIONS (Section 39)
// ============================================================================

void runUnitTests(const std::vector<Capability>& caps, const State& s0, const Goal& goal) {
    std::cout << "==================================================\n";
    std::cout << "RUNNING SYSTEM INTEGRITY & SPECIFICATION CHECKS\n";
    std::cout << "==================================================\n";

    const Capability& C1 = caps[0];
    const Capability& C2 = caps[1];
    const Capability& C3 = caps[2];
    const Capability& C4 = caps[3];
    const Capability& C5 = caps[4];
    const Capability& C6 = caps[5];
    const Capability& C7 = caps[6];
    const Capability& C8 = caps[7];
    const Capability& C9 = caps[8];
    const Capability& C10 = caps[9];
    const Capability& C11 = caps[10];

    // 1. Initial state is correct
    assert(s0.get(STUDENT_AUTHENTICATED) == true);
    assert(s0.get(STUDENT_EXISTS) == true);
    assert(s0.get(STUDENT_ELIGIBLE) == false);
    assert(s0.get(COURSE_EXISTS) == true);
    assert(s0.get(COURSE_AVAILABLE) == true);
    assert(s0.get(REGISTRATION_OPEN) == true);
    assert(s0.get(ENROLLMENT_EXISTS) == false);
    assert(s0.get(PAYMENT_COMPLETED) == false);
    std::cout << "  [PASS] 1. Initial state correctly initialized\n";

    // 2. C1 is applicable in initial state
    assert(isApplicable(C1, s0) == true);
    std::cout << "  [PASS] 2. C1 applicable in initial state\n";

    // 3. C3 is NOT applicable before C1
    assert(isApplicable(C3, s0) == false);
    std::cout << "  [PASS] 3. C3 not applicable before prerequisites\n";

    // 4. C3 becomes applicable after C1 and C2
    State s1 = applyEffects(s0, C1);
    State s2 = applyEffects(s1, C2);
    assert(isApplicable(C3, s2) == true);
    std::cout << "  [PASS] 4. C3 becomes applicable after C1/C2\n";

    // 5. C4 is NOT applicable before C3
    assert(isApplicable(C4, s2) == false);
    std::cout << "  [PASS] 5. C4 not applicable before C3\n";

    // 6. C4 becomes applicable after C3
    State s3 = applyEffects(s2, C3);
    assert(isApplicable(C4, s3) == true);
    std::cout << "  [PASS] 6. C4 becomes applicable after C3\n";

    // 7. C5 is NOT applicable before payment
    assert(isApplicable(C5, s3) == false);
    std::cout << "  [PASS] 7. C5 not applicable before payment\n";

    // 8. C5 becomes applicable after C4
    State s4 = applyEffects(s3, C4);
    assert(isApplicable(C5, s4) == true);
    std::cout << "  [PASS] 8. C5 becomes applicable after C4\n";

    // 9. C6 becomes applicable after C4
    assert(isApplicable(C6, s4) == true);
    std::cout << "  [PASS] 9. C6 becomes applicable after C4\n";

    // 10. C4 -> C7 is invalid
    assert(canCompose(C4, C7, s3) == false);
    std::cout << "  [PASS] 10. C4 -> C7 invalid\n";

    // 11. C3 -> C4 has valid input-output dependency
    assert(inputOutputCompatibility(C3, C4) == 1.0);
    std::cout << "  [PASS] 11. C3 -> C4 input-output compatibility = 1.0\n";

    // 12. C9/C10/C11 have identical functional embeddings
    auto f9 = encodeFunctional(C9);
    auto f10 = encodeFunctional(C10);
    auto f11 = encodeFunctional(C11);
    assert(f9 == f10 && f10 == f11);
    std::cout << "  [PASS] 12. C9/C10/C11 functional embeddings identical\n";

    // 13. C8 has goal relevance 0
    assert(goalRelevance(C8, goal) == 0.0);
    std::cout << "  [PASS] 13. C8 direct goal relevance = 0\n";

    // 14. Final composition satisfies the primary goal
    State s5 = applyEffects(s4, C5);
    State s6 = applyEffects(s5, C6);
    assert(goal.isSatisfied(s6) == true);
    std::cout << "  [PASS] 14. Primary sequence satisfies goal\n";

    // 15. Every capability embedding has 65 dimensions
    for (const auto& c : caps) {
        assert(encodeCapability(c).size() == 65);
    }
    std::cout << "  [PASS] 15. Capability embeddings = 65 dimensions\n";

    // 16. Every functional embedding has 35 dimensions
    for (const auto& c : caps) {
        assert(encodeFunctional(c).size() == 35);
    }
    std::cout << "  [PASS] 16. Functional embeddings = 35 dimensions\n";
    std::cout << "All 16 specification unit assertions passed successfully!\n\n";
}

// ============================================================================
// 9. EXPERIMENTS (Sections 29-33)
// ============================================================================

void runExperiment1(const std::vector<Capability>& caps, const State& s0) {
    std::cout << "==================================================\n";
    std::cout << "EXPERIMENT 1: CAPABILITY COMPATIBILITY & COMPOSITION\n";
    std::cout << "==================================================\n";

    const Capability& C3 = caps[2]; // RegisterCourse
    const Capability& C4 = caps[3]; // MakePayment
    const Capability& C7 = caps[6]; // DropCourse

    State s2 = applyEffects(applyEffects(s0, caps[0]), caps[1]);

    std::cout << "Test Case 1A: RegisterCourse (C3) -> MakePayment (C4)\n";
    std::cout << "--------------------------------------------------\n";
    std::cout << "  C3 Preconditions : student_auth=1, eligible=1, avail=1, open=1\n";
    std::cout << "  C3 Output        : enrollment_id\n";
    std::cout << "  C4 Precondition  : enrollment_exists=1\n";
    std::cout << "  C4 Inputs        : enrollment_id, payment_details\n";
    
    double ep1 = effectPreconditionCompatibility(C3, C4);
    double io1 = inputOutputCompatibility(C3, C4);
    bool valid1 = canCompose(C3, C4, s2);
    State s3 = applyEffects(s2, C3);

    std::cout << "  Effect-Precondition Compatibility : " << std::fixed << std::setprecision(4) << ep1 << "\n";
    std::cout << "  Input-Output Compatibility        : " << io1 << "\n";
    std::cout << "  State after C3 [enrollment_exists]: " << (s3.get(ENROLLMENT_EXISTS) ? "TRUE" : "FALSE") << "\n";
    std::cout << "  C4 Applicable after C3            : " << (isApplicable(C4, s3) ? "YES" : "NO") << "\n";
    std::cout << "  State-Aware Composition (C3 -> C4): " << (valid1 ? "VALID" : "INVALID") << "\n\n";

    std::cout << "Test Case 1B: MakePayment (C4) -> DropCourse (C7)\n";
    std::cout << "--------------------------------------------------\n";
    std::cout << "  C4 Precondition  : enrollment_exists = TRUE\n";
    std::cout << "  C4 Effect        : payment_completed = TRUE\n";
    std::cout << "  C7 Preconditions : enrollment_exists = TRUE, payment_completed = FALSE\n";
    
    double ep2 = effectPreconditionCompatibility(C4, C7);
    double io2 = inputOutputCompatibility(C4, C7);
    bool valid2 = canCompose(C4, C7, s3);
    State s4 = applyEffects(s3, C4);

    std::cout << "  Effect-Precondition Compatibility : " << ep2 << "\n";
    std::cout << "  Input-Output Compatibility        : " << io2 << "\n\n";
    std::cout << "  Direct Effect Analysis:\n";
    std::cout << "    enrollment_exists:\n";
    std::cout << "      C4 does not produce this predicate (it was established earlier by C3).\n";
    std::cout << "      C7 requires TRUE.\n";
    std::cout << "    payment_completed:\n";
    std::cout << "      C4 produces TRUE.\n";
    std::cout << "      C7 requires FALSE.\n";
    std::cout << "      CONFLICT detected.\n\n";
    std::cout << "  State after C4 [payment_completed]: " << (s4.get(PAYMENT_COMPLETED) ? "TRUE" : "FALSE") << "\n";
    std::cout << "  C7 Applicable after C4            : " << (isApplicable(C7, s4) ? "YES" : "NO (Violates payment_completed == false)") << "\n";
    std::cout << "  State-Aware Composition (C4 -> C7): " << (valid2 ? "VALID" : "INVALID (Blocked by negative precondition)") << "\n\n";
}

void runExperiment2(const std::vector<Capability>& caps, const State& s0, const Goal& goal) {
    std::cout << "==================================================\n";
    std::cout << "EXPERIMENT 2: FULL CAPABILITY COMPOSITION SEQUENCE\n";
    std::cout << "==================================================\n";

    std::vector<Capability> sequence = {caps[0], caps[1], caps[2], caps[3], caps[4], caps[5]};
    State currentState = s0;

    std::cout << "Initial State S_0:\n";
    printState(currentState);
    std::cout << "\nExecuting Sequence: C1 -> C2 -> C3 -> C4 -> C5 -> C6\n";
    std::cout << "--------------------------------------------------\n";

    for (size_t i = 0; i < sequence.size(); ++i) {
        const auto& cap = sequence[i];
        bool app = isApplicable(cap, currentState);
        std::cout << "Step " << (i + 1) << ": [" << cap.id << "] " << std::setw(24) << std::left << cap.name 
                  << " | Applicable: " << (app ? "YES" : "NO ");
        
        if (!app) {
            std::cout << " -> EXECUTION HALTED!\n";
            return;
        }

        currentState = applyEffects(currentState, cap);
        std::cout << " | Applied Effects. State updated.\n";
    }

    std::cout << "\nFinal State after Execution:\n";
    printState(currentState);

    bool goalMet = goal.isSatisfied(currentState);
    std::cout << "\nPrimary Goal Satisfaction Check:\n";
    std::cout << "  Goal Satisfied: " << (goalMet ? "YES (All target predicates achieved)" : "NO") << "\n\n";

    // Synthesize Composite Capability
    Capability comp = composeSequence(sequence, s0);
    std::cout << "Composite Capability (C_registration) Synthesized Properties:\n";
    std::cout << "  Composite Cost                : " << std::fixed << std::setprecision(4) << comp.operational.cost << "\n";
    std::cout << "  Composite Reliability         : " << comp.operational.reliability << " (~" 
              << std::setprecision(1) << (comp.operational.reliability * 100.0) << "%)\n";
    std::cout << "  Composite Availability        : " << std::setprecision(4) << comp.operational.availability << "\n";
    std::cout << "  Composite Embedding Dimension : " << encodeCapability(comp).size() << " dims\n\n";
}

void runExperiment3(const std::vector<Capability>& caps) {
    std::cout << "==================================================\n";
    std::cout << "EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS\n";
    std::cout << "==================================================\n";

    const Capability& C9 = caps[8];   // API
    const Capability& C10 = caps[9];  // DATABASE
    const Capability& C11 = caps[10]; // FUNCTION

    std::cout << "Comparing three alternative implementations of CheckCourseAvailability:\n";
    std::cout << "  - C9  (API)      : Mechanism = " << C9.mechanismName << "\n";
    std::cout << "  - C10 (DATABASE) : Mechanism = " << C10.mechanismName << "\n";
    std::cout << "  - C11 (FUNCTION) : Mechanism = " << C11.mechanismName << "\n\n";

    auto sim_9_10 = blockSimilarity(C9, C10);
    auto sim_9_11 = blockSimilarity(C9, C11);
    auto sim_10_11 = blockSimilarity(C10, C11);

    std::cout << std::left << std::setw(16) << "Comparison"
              << std::setw(24) << "Functional Sim (R^35)"
              << std::setw(24) << "Full Cosine Sim (R^65)"
              << std::setw(24) << "Block Avg Sim" << "\n";
    std::cout << std::string(80, '-') << "\n";

    std::cout << std::setw(16) << "C9 vs C10"
              << std::setw(24) << std::fixed << std::setprecision(4) << sim_9_10.sim_functional
              << std::setw(24) << cosineSimilarity(encodeCapability(C9), encodeCapability(C10))
              << std::setw(24) << sim_9_10.sim_overall << "\n";

    std::cout << std::setw(16) << "C9 vs C11"
              << std::setw(24) << sim_9_11.sim_functional
              << std::setw(24) << cosineSimilarity(encodeCapability(C9), encodeCapability(C11))
              << std::setw(24) << sim_9_11.sim_overall << "\n";

    std::cout << std::setw(16) << "C10 vs C11"
              << std::setw(24) << sim_10_11.sim_functional
              << std::setw(24) << cosineSimilarity(encodeCapability(C10), encodeCapability(C11))
              << std::setw(24) << sim_10_11.sim_overall << "\n\n";

    std::cout << "Key Finding:\n";
    std::cout << "  Functional Similarity = 1.0000 (Identical inputs, outputs, preconditions, effects).\n";
    std::cout << "  Full / Block Similarity < 1.0000 (Distinct capability types, mechanisms, and resources).\n";
    std::cout << "  This cleanly separates 'What the capability does' from 'How it is implemented'.\n\n";
}

void runExperiment4(const std::vector<Capability>& caps, const State& s0, const Goal& goal) {
    std::cout << "==================================================\n";
    std::cout << "EXPERIMENT 4: IRRELEVANT CAPABILITY & GOAL RELEVANCE\n";
    std::cout << "==================================================\n";

    const Capability& C8 = caps[7]; // GenerateRegistrationReport

    std::cout << "Capability C8: GenerateRegistrationReport\n";
    std::cout << "  Preconditions : enrollment_exists = true\n";
    std::cout << "  Effects       : registration_report_generated = true\n";
    std::cout << "  Cost: 20 | Reliability: 0.95 | Availability: 1.0\n\n";

    double rel = goalRelevance(C8, goal);
    std::cout << "  Direct Goal Relevance Rel(C8, G) : " << std::fixed << std::setprecision(4) << rel << "\n";
    std::cout << "  Applicable in Initial State S_0   : " << (isApplicable(C8, s0) ? "YES" : "NO (Needs enrollment_exists)") << "\n";

    State s3 = applyEffects(applyEffects(applyEffects(s0, caps[0]), caps[1]), caps[2]);
    std::cout << "  Applicable after RegisterCourse  : " << (isApplicable(C8, s3) ? "YES (enrollment_exists = true)" : "NO") << "\n";

    std::cout << "\nGoal Relevance Comparison Across All Capabilities:\n";
    std::cout << std::left << std::setw(8) << "ID" << std::setw(28) << "Name" << std::setw(16) << "Goal Relevance" << "\n";
    std::cout << std::string(52, '-') << "\n";
    for (size_t i = 0; i < 8; ++i) {
        std::cout << std::setw(8) << caps[i].id
                  << std::setw(28) << caps[i].name
                  << std::setw(16) << std::fixed << std::setprecision(4) << goalRelevance(caps[i], goal) << "\n";
    }
    std::cout << "\nInterpretation:\n";
    std::cout << "  Applicability and Goal Relevance are orthogonal dimensions.\n";
    std::cout << "  C8 is fully executable after C3, but contributes zero progress toward the primary goal.\n\n";
}

void runExperiment5(const std::vector<Capability>& caps) {
    std::cout << "==================================================\n";
    std::cout << "EXPERIMENT 5: OPERATIONAL PROPERTIES COMPARISON\n";
    std::cout << "==================================================\n";

    const Capability& C6 = caps[5]; // ConfirmRegistration
    const Capability& C4 = caps[3]; // MakePayment
    const Capability& C8 = caps[7]; // GenerateRegistrationReport

    std::vector<Capability> selected = {C6, C4, C8};

    std::cout << std::left << std::setw(8) << "ID"
              << std::setw(28) << "Name"
              << std::setw(10) << "Cost"
              << std::setw(14) << "Norm Cost"
              << std::setw(14) << "Reliability"
              << std::setw(14) << "Availability" << "\n";
    std::cout << std::string(88, '-') << "\n";

    for (const auto& c : selected) {
        std::cout << std::setw(8) << c.id
                  << std::setw(28) << c.name
                  << std::setw(10) << std::fixed << std::setprecision(1) << c.operational.cost
                  << std::setw(14) << std::setprecision(4) << c.operational.normalizedCost()
                  << std::setw(14) << c.operational.reliability
                  << std::setw(14) << c.operational.availability << "\n";
    }

    std::cout << "\nOperational Vector Analysis:\n";
    std::cout << "  - Cost is normalized by max individual capability cost (20) into [0.0, 1.0].\n";
    std::cout << "  - Reliability and availability are preserved directly in [0.0, 1.0].\n";
    std::cout << "  - Multi-attribute evaluation enables QoS-aware selection among functionally equivalent capabilities.\n\n";
}

void printFinalSummary() {
    std::cout << "==================================================\n";
    std::cout << "FINAL SUMMARY\n";
    std::cout << "==================================================\n\n";
    std::cout << "Capability embedding dimension : 65\n";
    std::cout << "Functional embedding dimension : 35\n";
    std::cout << "State embedding dimension      : 11\n";
    std::cout << "Goal embedding dimension       : 11\n\n";

    std::cout << "Valid composition:\n";
    std::cout << "C1 -> C2 -> C3 -> C4 -> C5 -> C6\n\n";

    std::cout << "Invalid composition:\n";
    std::cout << "C4 -> C7\n\n";

    std::cout << "Alternative implementations:\n";
    std::cout << "Functional similarity is preserved (1.0000)\n";
    std::cout << "Implementation differences are represented (< 1.0000)\n\n";

    std::cout << "Irrelevant capability:\n";
    std::cout << "C8 has zero direct goal relevance (0.0000)\n\n";

    std::cout << "Operational attributes:\n";
    std::cout << "Cost, reliability and availability represented\n\n";

    std::cout << "All experiments completed successfully.\n";
    std::cout << "==================================================\n";
}

// ============================================================================
// 10. MAIN ENTRY POINT
// ============================================================================

int main() {
    std::cout << "==================================================\n";
    std::cout << "UNIVERSITY COURSE REGISTRATION\n";
    std::cout << "VECTOR EMBEDDING EXPERIMENT\n";
    std::cout << "==================================================\n\n";

    // Setup dataset, state, and goal
    std::vector<Capability> capabilities = createCapabilities();
    State initialState = createInitialState();
    Goal primaryGoal = createPrimaryGoal();

    // Print Dimension Overview
    std::cout << "Embedding Dimensions Overview:\n";
    std::cout << "  State Space Dimension        | phi_S(S) : 11  (Ternary / Boolean)\n";
    std::cout << "  Goal Space Dimension         | phi_G(G) : 11  (Ternary {-1, 0, +1})\n";
    std::cout << "  Functional Vector Dimension  | phi_F(C) : 35  [P:11, E:11, I:5, O:8]\n";
    std::cout << "  Full Capability Dimension    | phi_C(C) : 65  [P:11, E:11, I:5, O:8, R:8, K:5, T:6, M:8, Q:3]\n\n";

    // 0. Representative Embedding Display (Requirement 6)
    displayRepresentativeEmbedding(capabilities[2]); // C3 RegisterCourse

    // 1. Run Unit Tests / Assertions
    runUnitTests(capabilities, initialState, primaryGoal);

    // 2. Run Experiments 1 to 5
    runExperiment1(capabilities, initialState);
    runExperiment2(capabilities, initialState, primaryGoal);
    runExperiment3(capabilities);
    runExperiment4(capabilities, initialState, primaryGoal);
    runExperiment5(capabilities);

    // 3. Final Summary
    printFinalSummary();

    return 0;
}
