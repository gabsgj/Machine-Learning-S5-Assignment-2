# PCCST503 Machine Learning — Assignment 2
## Design of a Vector Embedding for Capability Composition

| | |
|---|---|
| **Name** | Surya T S |
| **Register Number** | TCR24CS069 |
| **Course** | PCCST503 Machine Learning |
| **Assignment** | Assignment 2 — Design of a Vector Embedding for Capability Composition |
| **Domain** | E-Commerce Workflow & Enterprise Transaction Processing |
| **Language** | C++14/17 · no external dependencies |

---

## Documentation

| Deliverable | File | Description |
|---|---|---|
| Formal Embedding Design | [`docs/formal_design.md`](docs/formal_design.md) | Mathematical specification of the 36-dimensional vector space |
| Implementation Notes | [`docs/implementation.md`](docs/implementation.md) | Software architecture, class APIs, and complexity analysis |
| Experimental Dataset | [`docs/experimental_dataset.md`](docs/experimental_dataset.md) | Dataset dictionary, capability specs, and experimental design |
| Technical Report | [`docs/technical_report.md`](docs/technical_report.md) | Full academic report with all 5 experiments and actual results |
| CLI Usage Manual | [`USAGE.md`](USAGE.md) | Command-line flags and usage examples |

---

## Project Structure

```
Assignment2_Capability_Embedding/
├── include/
│   ├── types.hpp              # Formal 11-tuple Capability, State, Goal, ApplicationProblem
│   ├── embedding.hpp          # VectorEmbeddingEngine — encode, similarity, compatibility, compose
│   ├── json_loader.hpp        # Lightweight JSON → C++ model binding
│   └── experiments.hpp        # Experiments 1–5 runners
├── src/
│   └── main.cpp               # CLI entry point (--all, --experiments, --vectors, --compatibility)
├── tests/
│   └── test_embedding.cpp     # 12 automated unit tests
├── data/
│   ├── ecommerce_basic.json               # Initial state, goal, core capabilities
│   └── alternative_implementations.json   # Alternative payment impls + irrelevant capabilities
├── docs/
│   ├── formal_design.md
│   ├── implementation.md
│   ├── experimental_dataset.md
│   └── technical_report.md
├── third_party/
│   └── json.hpp               # Vendored nlohmann/json (single header)
├── Makefile
├── README.md
└── USAGE.md
```

---

## Quick Start

### Compile

```bash
# Using MinGW on Windows
C:\MinGW\bin\g++.exe -std=c++14 -Wall -O2 -Iinclude -Ithird_party src/main.cpp -o capability_embedding.exe
C:\MinGW\bin\g++.exe -std=c++14 -Wall -O2 -Iinclude -Ithird_party tests/test_embedding.cpp -o test_embedding.exe

# Using make (Linux / macOS / MSYS2)
make
```

### Run

```bash
# Run all 5 experiments
./capability_embedding.exe --all

# Run automated unit tests (12 tests)
./test_embedding.exe

# Individual flags
./capability_embedding.exe --experiments     # Experiments 1-5 only
./capability_embedding.exe --vectors         # Print raw embedding vectors
./capability_embedding.exe --compatibility   # Compatibility matrix
```

---

## Embedding Design (36 Dimensions)

The capability vector `phi_C(C) in R^36` is composed of five concatenated blocks:

| Block | Symbol | Dims | Encoding |
|---|---|---|---|
| Preconditions | **p**(C) | 11 | Ternary `{-1, 0, +1}` |
| Effects | **e**(C) | 11 | Ternary `{-1, 0, +1}` |
| Capability Type | **t**(C) | 6 | One-hot: {API, DATABASE, GUI, EVENT, FUNCTION, SERVICE} |
| I/O Port Counts | **io**(C) | 2 | Normalized `[0, 1]` |
| Quality of Service | **q**(C) | 6 | Normalized {latency, cost, resource, risk, reliability, availability} |

---

## Key Experimental Results

All numbers are from actual program output (`./capability_embedding.exe --all`).

| Experiment | Finding |
|---|---|
| **1 — Compatibility** | `CreateOrder → MakePayment = +1.0000` ✅  ·  `CreateOrder → CancelCart = −1.0000` ❌ |
| **2 — Composition** | `CompletePurchase`: 250 ms · $0.065 · reliability 0.9930 · 2 preconditions pruned |
| **3 — Similarity ≠ Composability** | API ↔ DATABASE similarity = **0.8007**  ·  sequential compatibility = **0.0000** |
| **4 — Goal Relevance** | 8 GOAL-ADVANCING · 5 IRRELEVANT/PRUNED (O(d) filtering, no graph search) |
| **5 — QoS Trade-offs** | FastPayment ↔ CheapPayment: Sim = **0.9416** · divergence driven by QoS slice only |

---

## Requirements Checklist

| Requirement | File | Method / Struct | Test / Deliverable |
|:---|:---|:---|:---|
| Formal Application Model | `include/types.hpp` | `struct ApplicationProblem` | [`docs/formal_design.md`](docs/formal_design.md) |
| Formal Capability 11-Tuple | `include/types.hpp` | `struct Capability` | [`docs/formal_design.md`](docs/formal_design.md) |
| State & Goal Encoders | `include/embedding.hpp` | `encodeState()`, `encodeGoal()` | Tests 1 & 2 |
| 36-dim Capability Vector | `include/embedding.hpp` | `encodeCapability()` | Tests 3 & 4 |
| Cosine Similarity | `include/embedding.hpp` | `similarity()` | Test 5 |
| Precondition-Effect Compatibility | `include/embedding.hpp` | `compatibility()` | Tests 6 & 7 · Exp 1 |
| Input-Output Compatibility | `include/embedding.hpp` | `inputOutputCompatibility()` | Test 12 · Exp 1 |
| Capability Composition | `include/embedding.hpp` | `compose()` | Tests 8–11 · Exp 2 |
| Goal Relevance Filtering | `include/embedding.hpp` | `goalRelevance()` | Exp 4 |
| Alternative Implementations | `include/experiments.hpp` | `runExperiment3()` | Exp 3 |
| Operational Trade-offs (QoS) | `include/experiments.hpp` | `runExperiment5()` | Exp 5 |
| Technical Report | [`docs/technical_report.md`](docs/technical_report.md) | All 12 sections | Deliverable 4 |

---

## Test Results

```
======================================================================
AUTOMATED UNIT TEST SUITE: VECTOR EMBEDDING & CAPABILITY COMPOSITION
======================================================================
[PASS]  1. State encoding dimension == 11 and values in {-1, +1}
[PASS]  2. Goal encoding dimension == 11 and ternary values in {-1, 0, +1}
[PASS]  3. CreateOrder vector correctly encodes preconditions and effects
[PASS]  4. MakePayment vector correctly encodes preconditions and effects
[PASS]  5. Cosine similarity reflexivity, symmetry, and zero-vector safety
[PASS]  6. Precondition-effect compatibility: CreateOrder -> MakePayment == +1.0000
[PASS]  7. Precondition-effect incompatibility: CreateOrder -> CancelCart == -1.0000
[PASS]  8. Capability composition prunes internally satisfied preconditions
[PASS]  9. Operational reliability aggregates multiplicatively
[PASS] 10. Operational latency, monetary cost, and resources aggregate additively
[PASS] 11. Composite availability reflects conjunction of component availability
[PASS] 12. Input-output compatibility matches port signatures correctly

TEST SUMMARY: 12 PASSED, 0 FAILED
======================================================================
```

---

## Quick Start

### Build and Run Everything
```bash
# Compile both the main executable and the unit test suite
make

# Run the 12 automated unit tests
make test

# Run the complete demonstration and all 5 benchmark experiments
make run
```

---

## Project Structure

```
Assignment2_Capability_Embedding/
├── include/
│   ├── types.hpp           // Formal 11-tuple Capability, State, Goal, and Application types
│   ├── embedding.hpp       // VectorEmbeddingEngine (34-dim embedding, cosine similarity, compatibility, composition)
│   ├── json_loader.hpp     // Lightweight JSON parser binding datasets to C++ models
│   └── experiments.hpp     // Empirical evaluation suite for Experiments 1 through 5
├── src/
│   └── main.cpp            // CLI entry point supporting fine-grained flags
├── tests/
│   └── test_embedding.cpp  // 12 unit tests verifying dimensions, values, compatibility, and algebra
├── data/
│   ├── ecommerce_basic.json                 // Canonical e-commerce initial state, goal, and core capabilities
│   └── alternative_implementations.json     // Alternative payment implementations and irrelevant capabilities
├── third_party/
│   └── json.hpp            // Vendored single-header JSON parser (nlohmann/json)
├── docs/
│   ├── formal_design.md           // Deliverable 1: Formal mathematical embedding specification
│   ├── implementation.md          // Deliverable 2: Software architecture and complexity analysis
│   ├── experimental_dataset.md    // Deliverable 3: Complete dataset dictionary and experimental design
│   └── technical_report.md        // Deliverable 4: Full academic technical report with actual results
├── Makefile                // Cross-platform Makefile (Windows / Linux / macOS)
├── README.md               // Project overview and documentation
└── USAGE.md                // CLI usage manual
```

---

## Key Features

1. **Structured 34-Dimensional Vector Embedding:**
   - 11 dimensions: Preconditions $\mathbf{p}(C) \in \{-1, 0, +1\}^{11}$
   - 11 dimensions: State Effects $\mathbf{e}(C) \in \{-1, 0, +1\}^{11}$
   - 6 dimensions: Capability Type $\mathbf{t}(C) \in \{0, 1\}^6$ (One-Hot)
   - 2 dimensions: I/O Interface Port counts $\mathbf{io}(C) \in [0, 1]^2$
   - 4 dimensions: Quality of Service (QoS) $\mathbf{q}(C) \in [0, 1]^4$ (Latency, Cost, Risk, Reliability)

2. **Deterministic Causal Operations:**
   - `encodeState(S)`: Bipolar mapping $\phi_S(S) \in \{-1, +1\}^{11}$.
   - `encodeGoal(G)`: Ternary mapping $\phi_G(G) \in \{-1, 0, +1\}^{11}$.
   - `similarity(u, v)`: Cosine similarity $\in [-1, +1]$.
   - `compatibility(C1, C2)`: Precondition-effect enabling/conflict score $\in [-1, +1]$.
   - `inputOutputCompatibility(C1, C2)`: Interface port type-and-name matching $\in [0, 1]$.
   - `goalRelevance(C, G)`: Causal alignment between capability effects and target goal.
   - `compose(C1, C2)`: Sequential algebraic composition $C_2 \circ C_1$ with internal precondition reduction and QoS aggregation.

3. **Core Empirical Findings:**
   - **Precondition Compatibility:** `CreateOrder -> MakePayment = +1.0000` (Compatible) vs. `CreateOrder -> CancelCart = -1.0000` (Incompatible).
   - **Similarity $\neq$ Composability:** `MakePayment_API` and `MakePayment_DATABASE` have a high similarity of `0.7515`, yet their sequential compatibility is `0.0000` (redundant, neither enables the other).
   - **Composition Invariants:** Composite `CompletePurchase` correctly prunes internal preconditions (`order_exists`, `payment_success`) and compounds reliability ($0.999 \times 0.995 \times 0.999 = 0.993011$).
   - **Instant Goal Pruning:** Dot product goal alignment filters out irrelevant operations (`BrowseCatalog`, `UpdateWishlist`, `ViewProfile`, `ChangeTheme` score `0.00`) without graph search.

---

## Requirements Checklist

| Requirement | Implementation File | Key Class / Method | Deliverable / Test |
| :--- | :--- | :--- | :--- |
| Formal Application Model | `include/types.hpp` | `struct ApplicationProblem` | `docs/formal_design.md` |
| Formal Capability 11-Tuple | `include/types.hpp` | `struct Capability` | `docs/formal_design.md` |
| State & Goal Encoders | `include/embedding.hpp` | `encodeState()`, `encodeGoal()` | Unit Tests 1 & 2 |
| Structured Capability Vector | `include/embedding.hpp` | `encodeCapability()` (34 dims) | Unit Tests 3 & 4 |
| Cosine Similarity | `include/embedding.hpp` | `similarity()` / `cosineSimilarity()` | Unit Test 5 |
| Precondition-Effect Compatibility | `include/embedding.hpp` | `compatibility()` | Unit Tests 6 & 7 / Exp 1 |
| Input-Output Compatibility | `include/embedding.hpp` | `inputOutputCompatibility()` | Unit Test 12 / Exp 1 |
| Capability Composition | `include/embedding.hpp` | `compose()` | Unit Tests 8–11 / Exp 2 |
| Goal Relevance Filtering | `include/embedding.hpp` | `goalRelevance()` | Exp 4 |
| Alternative Implementations | `include/experiments.hpp`| `runExperiment3()` | Exp 3 |
| Operational Trade-offs | `include/experiments.hpp`| `runExperiment5()` | Exp 5 |
| Technical Report | `docs/technical_report.md`| All 12 required sections | Deliverable 4 |
