# PCCST503 Machine Learning Assignment 2
# User Manual & CLI Specification

---

## 1. Compilation Instructions

The project is built using standard C++17 or C++14. It has no external package dependencies.

### Option A: Using `make` (or `mingw32-make` on Windows)
```bash
# Build both executable and test runner
make

# Run the 12 automated unit tests
make test

# Run full demonstration suite
make run

# Clean build artifacts
make clean
```

### Option B: Direct `g++` Command
```bash
# Compile main executable
g++ -std=c++14 -Wall -Wextra -O2 -Iinclude -Ithird_party src/main.cpp -o capability_embedding

# Compile unit tests
g++ -std=c++14 -Wall -Wextra -O2 -Iinclude -Ithird_party tests/test_embedding.cpp -o test_embedding
```

---

## 2. Command-Line Options

The binary `capability_embedding` supports simple command-line arguments:

```bash
./capability_embedding [options]
```

| Flag | Description |
| :--- | :--- |
| *(no arguments)* | Runs default execution (summary of core capabilities and all 5 benchmark experiments). |
| `--all` | Runs everything: structured vector displays, pairwise compatibility matrix, and all 5 experiments. |
| `--experiments` | Runs all five formal benchmark experiments (Sections 7.1 through 7.5). |
| `--vectors` | Displays formatted, labeled vector representations for states, goals, and capabilities. |
| `--compatibility` | Displays the full pairwise capability compatibility matrix $\text{Comp}(C_i \to C_j)$. |
| `--composition` | Displays detailed trace of sequential capability composition ($C_3 \circ C_2 \circ C_1$). |
| `--help`, `-h` | Prints usage instructions. |

---

## 3. Example Invocations & Outputs

### 3.1. Displaying Vector Representations
```bash
./capability_embedding --vectors
```
**Output Example:**
```
======================================================================
STRUCTURED VECTOR EMBEDDING REPRESENTATIONS
======================================================================

1. Canonical State Basis (Dimension: 11):
   [ 0] authenticated
   [ 1] customer_exists
   [ 2] cart_exists
   [ 3] cart_has_items
   [ 4] inventory_available
   [ 5] order_exists
   [ 6] order_created
   [ 7] payment_success
   [ 8] notification_sent
   [ 9] order_cancelled
   [10] shipment_dispatched

2. Initial State Embedding phi_S(S_I) in {-1, +1}^11:
   [+1, +1, +1, +1, +1, -1, -1, -1, -1, -1, -1]

3. Goal Specification Embedding phi_G(G) in {-1, 0, +1}^11:
   [ 0,  0,  0,  0,  0, +1,  0, +1, +1,  0,  0]

Capability: CreateOrder (Create Order)
  Preconditions: [ 0, 0,+1,+1, 0, 0, 0, 0, 0, 0, 0]
  Effects:       [ 0, 0, 0, 0, 0,+1,+1, 0, 0, 0, 0]
  Full Vector (dim=34): [0.00, 0.00, 1.00, 1.00, 0.00, ... ]
```

---

### 3.2. Pairwise Compatibility Matrix
```bash
./capability_embedding --compatibility
```
**Output Example:**
```
======================================================================
PAIRWISE CAPABILITY COMPATIBILITY MATRIX Comp(Row -> Col)
======================================================================

From \ To                CreateOrder     MakePayment  SendNotificati      CancelCart
------------------------------------------------------------------------------------
CreateOrder                     0.00            1.00            0.00           -1.00
MakePayment                     0.00            0.00            1.00            0.00
SendNotification                0.00            0.00            0.00            0.00
CancelCart                     -0.50            0.00            0.00            0.00

Legend: +1.00 = Preconditions satisfied; 0.00 = Neutral/unrelated; -1.00 = Conflict.
```

---

### 3.3. Running Benchmark Experiments
```bash
./capability_embedding --experiments
```
Executes:
* **Experiment 1 (Capability Compatibility):** Verifies $+1.0000$ enabling vs. $-1.0000$ conflict.
* **Experiment 2 (Capability Composition):** Builds `CompletePurchase` and computes operational aggregates.
* **Experiment 3 (Alternative Implementations):** Contrasts API, DB, and GUI implementations showing **Similarity $\neq$ Composability**.
* **Experiment 4 (Irrelevant Capabilities):** Calculates goal relevance to separate goal-contributing steps from irrelevant catalog browsing.
* **Experiment 5 (Operational Attributes):** Evaluates multi-attribute trade-offs between `FastPayment` and `CheapPayment`.

---

### 3.4. Running the Automated Unit Test Suite
```bash
./test_embedding
```
**Output Example:**
```
======================================================================
AUTOMATED UNIT TEST SUITE: VECTOR EMBEDDING & CAPABILITY COMPOSITION
======================================================================
[PASS] 1. State encoding dimension == 11 and values in {-1, +1}
[PASS] 2. Goal encoding dimension == 11 and ternary values in {-1, 0, +1}
[PASS] 3. CreateOrder vector correctly encodes preconditions and effects
[PASS] 4. MakePayment vector correctly encodes preconditions and effects
[PASS] 5. Cosine similarity reflexivity, symmetry, and zero-vector safety
[PASS] 6. Precondition-effect compatibility: CreateOrder -> MakePayment == +1.0000
[PASS] 7. Precondition-effect incompatibility: CreateOrder -> CancelCart == -1.0000
[PASS] 8. Capability composition prunes internally satisfied preconditions
[PASS] 9. Operational reliability aggregates multiplicatively
[PASS] 10. Operational latency, monetary cost, and resources aggregate additively
[PASS] 11. Composite availability reflects conjunction of component availability
[PASS] 12. Input-output compatibility matches port signatures correctly

======================================================================
TEST SUMMARY: 12 PASSED, 0 FAILED
======================================================================
```
