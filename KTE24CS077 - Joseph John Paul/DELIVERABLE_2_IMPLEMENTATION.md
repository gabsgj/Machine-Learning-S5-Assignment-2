# Deliverable 2: Implementation Document

**Project**: University Course Registration Vector Embedding  
**Language**: C++17 (ISO/IEC 14882:2017)  
**Primary Source File**: `main.cpp`  

---

## 1. Implementation Overview

The implementation provides a complete, deterministic, and self-contained C++17 framework for vector embedding, capability representation, state-aware composition, and QoS analysis within the University Course Registration domain. It runs with zero external runtime dependencies and strictly enforces all 16 specification invariants.

---

## 2. Technology Used

* **Language**: C++17
* **Standard Library (STL)**:
  * `<vector>`, `<string>` for structured sequences and representations.
  * `<cmath>` (`std::sqrt`) for Euclidean norm and metric computations.
  * `<iomanip>`, `<iostream>` for tabular formatted console reporting.
  * `<cassert>` for compile-time and runtime integrity checks.
  * `<numeric>`, `<algorithm>` for vector operations.
* **Compiler Support**: Compatible with MinGW GCC (g++ 8+), Clang (clang++ 7+), and MSVC (2017+).

---

## 3. Project Architecture

The current workspace is organized as a streamlined, self-contained project:

```
UNIVERSITY_COURSE_REGISTRATION_EMBEDDING/
│
├── main.cpp                              # Complete implementation (Dataset, Embeddings, Engine, Tests, Experiments)
├── embedding.exe                         # Compiled executable binary
├── usage.md                              # Operational build and execution instructions
├── data/
│   └── course_registration_dataset.json  # Exported JSON dataset
│
├── DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md
├── DELIVERABLE_2_IMPLEMENTATION.md
├── DELIVERABLE_3_EXPERIMENTAL_DATASET.md
├── DELIVERABLE_4_TECHNICAL_REPORT.md
└── README.md
```

---

## 4. Data Structures

The system uses strongly typed enums and lightweight structs to represent domain primitives:

```cpp
enum StatePredicate { STUDENT_AUTHENTICATED = 0, STUDENT_EXISTS, ..., REGISTRATION_REPORT_GENERATED };
enum ConditionValue { FALSE_VALUE = -1, IRRELEVANT = 0, TRUE_VALUE = 1 };
enum InputType { IN_STUDENT_ID = 0, IN_COURSE_ID, IN_ENROLLMENT_ID, ... };
enum OutputType { OUT_ELIGIBILITY_STATUS = 0, OUT_AVAILABILITY_STATUS, ... };
enum ResourceType { RES_STUDENT_DATABASE = 0, RES_COURSE_DATABASE, ... };
enum ConstraintType { CON_AUTHENTICATION_REQUIRED = 0, ... };
enum CapabilityType { TYPE_API = 0, TYPE_DATABASE, TYPE_FUNCTION, TYPE_SERVICE, TYPE_COMPUTATION, TYPE_GUI };
enum MechanismType { MECH_LOCAL_FUNCTION = 0, MECH_SQL_DATABASE_QUERY, MECH_REST_POST_REGISTRATION, ... };
```

---

## 5. State Implementation

States are encapsulated in a 11-element boolean container:

```cpp
struct State {
    std::vector<bool> predicates;
    State() : predicates(STATE_PREDICATE_COUNT, false) {}
    bool get(StatePredicate p) const { return predicates[static_cast<size_t>(p)]; }
    void set(StatePredicate p, bool val) { predicates[static_cast<size_t>(p)] = val; }
};
```

---

## 6. Goal Implementation

Goals use ternary logic (`-1, 0, +1`) to verify whether a given state satisfies the target specification:

```cpp
struct Goal {
    std::vector<ConditionValue> conditions;
    bool isSatisfied(const State& state) const {
        for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
            if (conditions[i] == TRUE_VALUE && !state.predicates[i]) return false;
            if (conditions[i] == FALSE_VALUE && state.predicates[i]) return false;
        }
        return true;
    }
};
```

---

## 7. Capability Implementation

```cpp
struct OperationalProperties {
    double cost = 0.0;
    double reliability = 1.0;
    double availability = 1.0;
    double normalizedCost() const { return cost / 20.0; }
};

struct Capability {
    std::string id, name, mechanismName;
    CapabilityType type;
    std::vector<ConditionValue> preconditions; // 11
    std::vector<ConditionValue> effects;       // 11
    std::vector<double> inputs;                // 5
    std::vector<double> outputs;               // 8
    std::vector<double> resources;             // 8
    std::vector<double> constraints;           // 5
    MechanismType mechanism;                   // 8 (one-hot)
    OperationalProperties operational;         // 3
};
```

---

## 8. Embedding Implementation

### Full Capability Embedding $\phi_C(C) \in \mathbb{R}^{65}$
```cpp
std::vector<double> encodeCapability(const Capability& cap) {
    std::vector<double> vec;
    vec.reserve(65);
    for (auto p : cap.preconditions) vec.push_back(static_cast<double>(p));
    for (auto e : cap.effects)       vec.push_back(static_cast<double>(e));
    for (auto i : cap.inputs)        vec.push_back(i);
    for (auto o : cap.outputs)       vec.push_back(o);
    for (auto r : cap.resources)     vec.push_back(r);
    for (auto k : cap.constraints)   vec.push_back(k);
    for (size_t i = 0; i < CAPABILITY_TYPE_COUNT; ++i)
        vec.push_back(cap.type == static_cast<CapabilityType>(i) ? 1.0 : 0.0);
    for (size_t i = 0; i < MECHANISM_COUNT; ++i)
        vec.push_back(cap.mechanism == static_cast<MechanismType>(i) ? 1.0 : 0.0);
    vec.push_back(cap.operational.normalizedCost());
    vec.push_back(cap.operational.reliability);
    vec.push_back(cap.operational.availability);
    assert(vec.size() == 65);
    return vec;
}
```

### Functional Capability Embedding $\phi_F(C) \in \mathbb{R}^{35}$
```cpp
std::vector<double> encodeFunctional(const Capability& cap) {
    std::vector<double> vec;
    vec.reserve(35);
    for (auto p : cap.preconditions) vec.push_back(static_cast<double>(p));
    for (auto e : cap.effects)       vec.push_back(static_cast<double>(e));
    for (auto i : cap.inputs)        vec.push_back(i);
    for (auto o : cap.outputs)       vec.push_back(o);
    assert(vec.size() == 35);
    return vec;
}
```

---

## 9. Similarity Implementation

```cpp
double cosineSimilarity(const std::vector<double>& a, const std::vector<double>& b) {
    if (a.size() != b.size() || a.empty()) return 0.0;
    double dot = 0.0, norm_a = 0.0, norm_b = 0.0;
    for (size_t i = 0; i < a.size(); ++i) {
        dot += a[i] * b[i];
        norm_a += a[i] * a[i];
        norm_b += b[i] * b[i];
    }
    if (norm_a <= 1e-12 && norm_b <= 1e-12) return 1.0;
    if (norm_a <= 1e-12 || norm_b <= 1e-12) return 0.0;
    return dot / (std::sqrt(norm_a) * std::sqrt(norm_b));
}
```

---

## 10. Compatibility Implementation

```cpp
double effectPreconditionCompatibility(const Capability& c1, const Capability& c2) {
    int requiredCount = 0, satisfiedCount = 0;
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        if (c2.preconditions[i] != IRRELEVANT) {
            requiredCount++;
            if (c1.effects[i] == c2.preconditions[i]) satisfiedCount++;
        }
    }
    return requiredCount == 0 ? 1.0 : (double)satisfiedCount / requiredCount;
}

double inputOutputCompatibility(const Capability& c1, const Capability& c2) {
    double matched = 0.0, requiredFlowInputs = 0.0;
    if (c2.inputs[IN_ENROLLMENT_ID] > 0.0) {
        requiredFlowInputs += 1.0;
        if (c1.outputs[OUT_ENROLLMENT_ID] > 0.0) matched += 1.0;
    }
    return requiredFlowInputs <= 1e-12 ? 0.0 : matched / requiredFlowInputs;
}
```

---

## 11. State Transition Implementation

```cpp
State applyEffects(const State& state, const Capability& cap) {
    State nextState = state;
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        if (cap.effects[i] == TRUE_VALUE) nextState.predicates[i] = true;
        else if (cap.effects[i] == FALSE_VALUE) nextState.predicates[i] = false;
    }
    return nextState;
}
```

---

## 12. Composition Implementation

```cpp
bool canCompose(const Capability& c1, const Capability& c2, const State& initialState) {
    if (!isApplicable(c1, initialState)) return false;
    State s1 = applyEffects(initialState, c1);
    return isApplicable(c2, s1);
}
```

---

## 13. Goal Relevance Implementation

```cpp
double goalRelevance(const Capability& cap, const Goal& goal) {
    int goalCount = 0, matchedCount = 0;
    for (size_t i = 0; i < STATE_PREDICATE_COUNT; ++i) {
        if (goal.conditions[i] != IRRELEVANT) {
            goalCount++;
            if (cap.effects[i] == goal.conditions[i]) matchedCount++;
        }
    }
    return goalCount == 0 ? 0.0 : (double)matchedCount / goalCount;
}
```

---

## 14. Experimental Framework

The application structures the execution into five distinct experiments:
1. `runExperiment1`: Compatibility & negative precondition conflict analysis.
2. `runExperiment2`: Full primary composition ($C_1 \dots C_6$) and composite capability synthesis.
3. `runExperiment3`: Functional vs. full similarity on alternative implementations ($C_9, C_{10}, C_{11}$).
4. `runExperiment4`: Orthogonality of goal relevance and applicability on $C_8$.
5. `runExperiment5`: QoS operational vector evaluation.

---

## 15. Testing and Assertions

A dedicated test harness `runUnitTests()` enforces 16 formal specification assertions on system startup:
* Initial state assertions ($S_0$).
* Sequential applicability transitions ($C_1 \to C_6$).
* Incompatibility detection for $C_4 \to C_7$.
* Data-flow matching for $C_3 \to C_4$.
* Functional equivalence of $C_9, C_{10}, C_{11}$ ($\phi_F$).
* Zero goal relevance of $C_8$.
* Invariant dimensions: $|\phi_C| = 65$, $|\phi_F| = 35$.

---

## 16. Computational Complexity

Let:
* $n$: Number of state predicates ($n = 11$).
* $d$: Capability embedding dimension ($d = 65$).
* $l$: Composition sequence length ($l = 6$).

| Operation | Time Complexity | Space Complexity |
| :--- | :---: | :---: |
| State Encoding $\phi_S(S)$ | $\mathcal{O}(n)$ | $\mathcal{O}(n)$ |
| Capability Encoding $\phi_C(C)$ | $\mathcal{O}(d)$ | $\mathcal{O}(d)$ |
| Cosine Similarity | $\mathcal{O}(d)$ | $\mathcal{O}(1)$ |
| Applicability Check $Applicable(C, S)$ | $\mathcal{O}(n)$ | $\mathcal{O}(1)$ |
| State Transition $\text{Apply}(S, E)$ | $\mathcal{O}(n)$ | $\mathcal{O}(n)$ |
| Sequence Execution | $\mathcal{O}(l \cdot n)$ | $\mathcal{O}(n)$ |
| Composite Synthesis | $\mathcal{O}(l \cdot d)$ | $\mathcal{O}(d)$ |

---

## 17. Storage Requirements

* `Capability` instance memory footprint: $\approx 512$ bytes.
* Complete repository of 11 capabilities: $< 10$ KB in memory.
* Binary executable size: $\approx 300$ KB (standalone, statically linked standard runtime).

---

## 18. Example Execution

```powershell
g++ -std=c++17 main.cpp -o embedding.exe
.\embedding.exe
```

Output highlights:
* 16/16 Unit Assertions Passed.
* Primary sequence reaches Goal: `YES`.
* $C_9, C_{10}, C_{11}$ Functional Sim: `1.0000`, Overall Sim: `0.7452 - 0.7778`.

---

## 19. Implementation Limitations

1. **Monolithic Binary**: The current implementation is bundled within `main.cpp` for zero-dependency compilation.
2. **Fixed Dimension Allocations**: Embedding sizes are compile-time constants tailored to the Course Registration vocabulary.
3. **Discrete Metric Modeling**: Capacity thresholds are modeled discretely rather than through arithmetic interval solvers.
