# PCCST503 Machine Learning Assignment 2
## Deliverable 2: Implementation Guide & Software Architecture

**Title:** Structured Capability Embedding and Composition Engine  
**Language:** C++17 (with C++14 backward-compatible support)  
**Standard Library Dependencies Only** (Vendored Header: `third_party/json.hpp`)  

---

## 1. Architectural Overview

The implementation is structured as a modular, header-centric C++ system designed for transparency, mathematical rigor, and deterministic reproducibility.

```
Assignment2_Capability_Embedding/
├── include/
│   ├── types.hpp           // Formal domain data structures (Sections 3 & 4)
│   ├── embedding.hpp       // Mathematical embedding engine & composition operators (Sections 5 & 6)
│   ├── json_loader.hpp     // JSON parsing binding formal JSON models to C++ structs
│   └── experiments.hpp     // Empirical evaluation suite for all 5 required experiments
├── src/
│   └── main.cpp            // Command-line interface and demonstration runner
├── tests/
│   └── test_embedding.cpp  // Comprehensive unit test suite (12 test cases)
├── data/
│   ├── ecommerce_basic.json                 // Canonical e-commerce initial state, goal, and core capabilities
│   └── alternative_implementations.json     // Alternative payment implementations and irrelevant capabilities
├── third_party/
│   └── json.hpp            // Vendored single-header JSON parser (nlohmann/json)
├── docs/                   // Formal Deliverables 1 through 4
├── Makefile                // Cross-platform build script
├── README.md               // Project overview and quick start
└── USAGE.md                // CLI manual and options
```

---

## 2. Core Data Structures (`include/types.hpp`)

All types are mapped directly from the formal mathematical models:

### 2.1. `Port`
Models Section 4.2 input ($I_i$) and output ($O_i$) interfaces:
```cpp
struct Port {
    std::string name;       // e.g., "order_id"
    std::string type;       // e.g., "UUID"
    std::string domain;     // e.g., "valid UUIDs"
    bool required = true;   // true for mandatory inputs
};
```

### 2.2. `Condition` & `Effect`
Model Section 4.3 state preconditions ($P_i$) and state transitions ($E_i$):
```cpp
struct Condition {
    std::string variable;   // State variable name in canonical basis
    bool expectedValue;     // Expected boolean truth value
};

struct Effect {
    std::string variable;   // State variable to update
    bool value;             // Resulting boolean value
};
```

### 2.3. `QualityAttributes`
Models Section 4.5 operational costs ($Q_i$):
```cpp
struct QualityAttributes {
    double timeCostMs = 100.0;  // Latency in milliseconds
    double moneyCost = 0.01;    // Monetary cost in USD
    double resourceCost = 1.0;  // Compute allocation units
    double risk = 0.05;         // Risk factor in [0, 1]
};
```

### 2.4. `Capability`
Implements the 11-tuple $C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, \text{Rel}_i, A_i, M_i)$:
```cpp
struct Capability {
    std::string id;
    std::string name;
    std::string description;
    std::string type;                      // T_i in {API, DATABASE, GUI, EVENT, FUNCTION, SERVICE}
    std::vector<Port> inputs;              // I_i
    std::vector<Port> outputs;             // O_i
    std::vector<Condition> preconditions;  // P_i
    std::vector<Effect> effects;           // E_i
    std::vector<std::string> constraints;  // K_i
    std::vector<std::string> resources;    // R_i
    QualityAttributes qos;                 // Q_i
    double reliability = 0.99;             // Rel_i in [0, 1]
    double availability = 1.0;             // A_i in {0, 1}
    std::string mechanism;                 // M_i (e.g., "POST /orders")
};
```

---

## 3. Embedding Engine Algorithms (`include/embedding.hpp`)

### 3.1. Vector Encodings
* **State Encoder (`encodeState`):** Iterates over the 11 fixed canonical variables; outputs $+1.0$ for `true` and $-1.0$ for `false`.
* **Goal Encoder (`encodeGoal`):** Iterates over goal conditions; outputs $+1.0$ for required true, $-1.0$ for required false, and $0.0$ for unconstrained variables.
* **Precondition Encoder (`encodePreconditions`):** Encodes capability preconditions into an 11-dimensional ternary vector $\mathbf{p} \in \{-1, 0, +1\}^{11}$.
* **Effect Encoder (`encodeEffects`):** Encodes capability state transformations into an 11-dimensional ternary vector $\mathbf{e} \in \{-1, 0, +1\}^{11}$.
* **Capability Encoder (`encodeCapability`):** Concatenates $\mathbf{p}(C)$, $\mathbf{e}(C)$, one-hot $\mathbf{t}(C)$, normalized $\mathbf{io}(C)$, and normalized $\mathbf{q}(C)$ into a single 36-dimensional dense vector.

### 3.2. Precondition-Effect Compatibility (`compatibility`)
Calculates:
$$\text{Comp}(C_1, C_2) = \frac{\mathbf{e}(C_1) \cdot \mathbf{p}(C_2)}{\|\mathbf{p}(C_2)\|_2^2 + \epsilon}$$
If $C_2$ has no preconditions, the score defaults to $1.0000$ (universally applicable).

### 3.3. Capability Composition (`compose`)
Constructs $C_{12} = C_2 \circ C_1$:
1. **Preconditions:** Retains $P(C_1)$, and adds only those $p \in P(C_2)$ that are *not* satisfied by $E(C_1)$.
2. **Effects:** Appends $E(C_1)$, then updates with $E(C_2)$ (overwriting matching variables).
3. **I/O Ports:** Accumulates remaining unresolved inputs and provides combined outputs.
4. **QoS:** Adds time, money, and compute costs; compounds risk via $1 - (1-R_1)(1-R_2)$; multiplies reliability; conjoins availability.

---

## 4. Algorithmic Complexity Analysis

Let:
* $d = 11$: Number of canonical state variables.
* $D = 36$: Total capability embedding vector dimension.
* $p = |P_i|$: Number of preconditions.
* $e = |E_i|$: Number of effects.
* $u = |I_i|, v = |O_i|$: Number of input and output ports.

| Operation | Time Complexity | Space Complexity | Explanation |
| :--- | :---: | :---: | :--- |
| `encodeState(S)` | $O(d)$ | $O(d)$ | Direct hash-map lookup per canonical state variable. |
| `encodeGoal(G)` | $O(|G| + d)$ | $O(d)$ | Single pass over goal predicates, filling an array of size $d$. |
| `encodeCapability(C)` | $O(d + |T| + |Q|)$ | $O(D)$ | Constant time $O(36)$ operations for fixed universe. |
| `cosineSimilarity(u, v)`| $O(D)$ | $O(1)$ | Single linear dot product and Euclidean norm calculation over 36 dims. |
| `compatibility(C1, C2)`| $O(d)$ | $O(d)$ | Vector dot product between $\mathbf{e}(C_1)$ and $\mathbf{p}(C_2)$. |
| `inputOutputCompatibility`| $O(u_2 \cdot v_1)$ | $O(1)$ | Pairwise string comparisons between required inputs and outputs. |
| `compose(C1, C2)` | $O(p_2 \cdot e_1 + e_1 \cdot e_2)$ | $O(p_1+p_2+e_1+e_2)$ | Set-difference and overwrite passes; bounded by small constant in practice. |
| `goalRelevance(C, G)` | $O(d)$ | $O(d)$ | Dot product of effect vector against goal vector. |

---

## 5. Verification & Testing

The project includes an automated unit test suite (`tests/test_embedding.cpp`) containing 12 unit tests:
1. `State encoding dimension == 11 and values in {-1, +1}`
2. `Goal encoding dimension == 11 and ternary values in {-1, 0, +1}`
3. `CreateOrder vector correctly encodes preconditions and effects`
4. `MakePayment vector correctly encodes preconditions and effects`
5. `Cosine similarity reflexivity, symmetry, and zero-vector safety`
6. `Precondition-effect compatibility: CreateOrder -> MakePayment == +1.0000`
7. `Precondition-effect incompatibility: CreateOrder -> CancelCart == -1.0000`
8. `Capability composition prunes internally satisfied preconditions`
9. `Operational reliability aggregates multiplicatively`
10. `Operational latency, monetary cost, and resources aggregate additively`
11. `Composite availability reflects conjunction of component availability`
12. `Input-output compatibility matches port signatures correctly`

All 12 tests execute in under 15ms and pass with zero failures.
