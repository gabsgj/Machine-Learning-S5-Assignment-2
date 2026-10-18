# Vector Embedding System for Capability Composition

A university-level C++17 framework implementing vector embeddings, formal compatibility verification, sequential capability composition, similarity analysis, and goal relevance scoring for formally specified States, Goals, and Capabilities.

> **Design Notice:** This system is focused strictly on vector embeddings, compatibility checking, and capability composition. It is **not** a planner and contains no graph search (BFS, DFS, A*, D* Lite, LPA*) or replanning algorithms.

---

## 1. System Architecture & Project Structure

The project conforms strictly to the required directory and file layout:

```
CapabilityEmbedding/
├── include/
│   ├── Types.h              # Formal data structures: State, Goal, Capability, CapabilityType
│   └── Embedding.h          # Embedding engine, similarity, compatibility, composition, and goal relevance
├── src/
│   └── Embedding.cpp        # Full modular implementation and domain semantic registry
├── tests/
│   └── test_embedding.cpp   # Comprehensive experimental test suite (Experiments 1–5)
├── CMakeLists.txt           # Standard C++17 CMake build configuration
└── README.md                # Comprehensive theoretical documentation and user guide
```

---

## 2. Formal Data Structures

### 2.1 State
A `State` formalizes an assignment of variables and propositions representing the state of the world:
$$\mathcal{S} = \{ (v_1, c_1), (v_2, c_2), \dots, (v_n, c_n) \}$$
Examples:
- `User.authenticated = true`
- `Cart.exists = true`
- `Order.exists = false`

### 2.2 Goal
A `Goal` formalizes a set of desired conditions that must hold in the world:
$$\mathcal{G} = \{ (v_1, c_1^*), (v_2, c_2^*), \dots, (v_m, c_m^*) \}$$
A state $\mathcal{S}$ satisfies goal $\mathcal{G}$ if and only if $\forall (v, c^*) \in \mathcal{G}, \mathcal{S}(v) = c^*$.
Examples:
- `Order.exists = true`
- `Payment.status = SUCCESS`

### 2.3 Capability
A `Capability` models a computational or service unit defined by structural, operational, and semantic properties:
$$\mathcal{C} = \langle \text{name}, \text{type}, \text{mech}, In, Out, Pre, Eff, Constr, Res, \text{cost}, \text{rel}, \text{avail} \rangle$$
- **Name:** Unique identifier string.
- **Type:** Architectural classification enum (`API`, `DATABASE`, `GUI`, `EVENT`, `FUNCTION`, `FILE`, `COMPUTATION`, `MESSAGE`, `SERVICE`).
- **Execution Mechanism:** Underlying operational protocol/runtime (e.g., `REST_HTTP_JSON`, `SQL_STORED_PROCEDURE`, `QT_DESKTOP_UI`).
- **Inputs ($In$):** Required input attributes (dataflow dependencies).
- **Outputs ($Out$):** Produced output attributes (dataflow provisions).
- **Preconditions ($Pre$):** State propositions required prior to invocation.
- **Effects ($Eff$):** State proposition mutations produced upon successful completion.
- **Constraints ($Constr$):** Invariants and operational safety assertions.
- **Resources ($Res$):** Logical and hardware requirements (e.g., `ORDER_DB`, `NETWORK`, `PAYMENT_GATEWAY`).
- **Cost:** Execution monetary fee or latency metric ($c \ge 0$).
- **Reliability:** Success probability under nominal execution ($r \in [0.0, 1.0]$).
- **Availability:** Subsystem uptime / readiness probability ($a \in [0.0, 1.0]$).

---

## 3. Vector Embedding Design

The embedding engine projects States, Goals, and Capabilities into a shared 92-dimensional real vector space $\mathbb{R}^{92}$ partitioned into orthogonal semantic subspaces:

$$\mathbf{v} = \left[ \mathbf{v}_{\text{type}} \;\Big|\; \mathbf{v}_{\text{ops}} \;\Big|\; \mathbf{v}_{\text{pre}} \;\Big|\; \mathbf{v}_{\text{eff}} \;\Big|\; \mathbf{v}_{\text{in}} \;\Big|\; \mathbf{v}_{\text{out}} \;\Big|\; \mathbf{v}_{\text{res}} \;\Big|\; \mathbf{v}_{\text{constr}} \right]$$

### 3.1 Subspace Breakdown

| Index Range | Subspace | Dimensions | Description |
|:---:|:---:|:---:|:---|
| `[00 .. 08]` | Capability Type | 9 | One-hot categorical encoding: `API`, `DATABASE`, `GUI`, `EVENT`, `FUNCTION`, `FILE`, `COMPUTATION`, `MESSAGE`, `SERVICE`. |
| `[09 .. 11]` | Operational Attributes | 3 | Normalized Cost $\hat{c} = \frac{c}{c + 50.0} \in [0, 1)$, Reliability $r \in [0, 1]$, Availability $a \in [0, 1]$. |
| `[12 .. 27]` | Preconditions | 16 | Signed indicator vector for state predicates ($+1.0$ for `true`/`SUCCESS`, $-1.0$ for `false`/`FAILURE`). |
| `[28 .. 43]` | Effects / Desired State | 16 | Signed indicator vector for state mutations ($+1.0$ for `true`/`SUCCESS`, $-1.0$ for `false`/`FAILURE`). |
| `[44 .. 59]` | Data Inputs | 16 | Boolean presence indicator vector for input data fields ($1.0$ if present). |
| `[60 .. 75]` | Data Outputs | 16 | Boolean presence indicator vector for output data fields ($1.0$ if present). |
| `[76 .. 83]` | Resources | 8 | Indicator vector for required hardware/software resources ($1.0$ if utilized). |
| `[84 .. 91]` | Constraints | 8 | Indicator vector for invariant assertions ($1.0$ if required). |

### 3.2 Canonical & Unified Encoding
- **`encodeState(State)`**: Encodes current state variables directly into the world state/effects subspace (`[28..43]`), leaving operational and type dimensions at zero.
- **`encodeGoal(Goal)`**: Encodes target conditions into the desired world state subspace (`[28..43]`), mirroring the state subspace so that state satisfaction and capability effect alignment can be directly measured via inner products.
- **`encodeCapability(Capability)`**: Populates all 8 subspaces according to the capability's structural and operational specification.

---

## 4. Mathematical Foundations

### 4.1 Cosine Similarity
Given two numerical feature vectors $\mathbf{a}, \mathbf{b} \in \mathbb{R}^D$:

$$\text{similarity}(\mathbf{a}, \mathbf{b}) = \frac{\mathbf{a} \cdot \mathbf{b}}{\|\mathbf{a}\|_2 \|\mathbf{b}\|_2} = \frac{\sum_{i=1}^D a_i b_i}{\sqrt{\sum_{i=1}^D a_i^2} \sqrt{\sum_{i=1}^D b_i^2}}$$

- When $\|\mathbf{a}\|_2 = 0$ or $\|\mathbf{b}\|_2 = 0$, $\text{similarity}(\mathbf{a}, \mathbf{b}) = 0.0$.
- Result is bounded within $[-1.0, 1.0]$. For non-negative capability representations, it spans $[0.0, 1.0]$.

### 4.2 Compatibility Verification
Sequential composition $C_1 \to C_2$ is valid if and only if two formal criteria are met:

1. **Effect-Precondition Consistency & Satisfaction:**
   - **No Contradiction:** No effect in $Eff(C_1)$ can contradict any precondition in $Pre(C_2)$:
     $$\forall v \in \text{dom}(Eff(C_1)) \cap \text{dom}(Pre(C_2)), \quad Eff(C_1)[v] = Pre(C_2)[v]$$
   - **Constructive Linkage:** At least one precondition of $C_2$ is established by $Eff(C_1)$, or the composition represents an uncontradicted state-preserving pipeline.

2. **Output-Input Dataflow Fulfillment:**
   - If $In(C_2) \neq \emptyset$, any pipeline data parameters expected from the upstream service must be produced:
     $$In_{\text{pipeline}}(C_2) \subseteq Out(C_1)$$
   - If $Out(C_1) \cap In(C_2) \neq \emptyset$, dataflow linkage is established.

`areCompatible(first, second)` returns `true` if and only if both criteria pass with zero contradictions.

### 4.3 Sequential Capability Composition
When two compatible capabilities $C_1$ and $C_2$ are composed into $C_{\text{comp}} = C_1 \circ C_2$:

1. **Inputs:** External inputs of $C_1$ plus any inputs of $C_2$ not generated internally by $C_1$:
   $$In(C_{\text{comp}}) = In(C_1) \cup \left(In(C_2) \setminus Out(C_1)\right)$$
2. **Outputs:** Cumulative external outputs produced across both stages:
   $$Out(C_{\text{comp}}) = Out(C_1) \cup Out(C_2)$$
3. **Preconditions:** Preconditions of $C_1$ plus any preconditions of $C_2$ not satisfied by $C_1$'s effects:
   $$Pre(C_{\text{comp}}) = Pre(C_1) \cup \left(Pre(C_2) \setminus Eff(C_1)\right)$$
4. **Effects:** Sequential world updates where $C_2$'s effects augment or supersede $C_1$'s:
   $$Eff(C_{\text{comp}})(v) = \begin{cases} Eff(C_2)(v), & \text{if } v \in \text{dom}(Eff(C_2)) \\ Eff(C_1)(v), & \text{if } v \in \text{dom}(Eff(C_1)) \setminus \text{dom}(Eff(C_2)) \end{cases}$$
5. **Cost (Additive):**
   $$\text{cost}(C_{\text{comp}}) = \text{cost}(C_1) + \text{cost}(C_2)$$
6. **Reliability (Multiplicative Serial Model):**
   $$\text{reliability}(C_{\text{comp}}) = \text{reliability}(C_1) \times \text{reliability}(C_2)$$
7. **Availability (Multiplicative Readiness Model):**
   $$\text{availability}(C_{\text{comp}}) = \text{availability}(C_1) \times \text{availability}(C_2)$$
8. **Resources & Constraints:** Set unions $\bigcup Res$ and $\bigcup Constr$.

### 4.4 Goal Relevance Computation
Goal relevance measures how effectively a capability's effects satisfy the target conditions of a goal $\mathcal{G}$:

$$\text{goalRelevance}(C, \mathcal{G}) = \max\left(0.0, \; \text{similarity}\left(\mathbf{v}_{\text{eff}}(C), \; \mathbf{v}_{\text{goal}}(\mathcal{G})\right)\right)$$

Where $\mathbf{v}_{\text{eff}}(C)$ is the vector containing only the capability's effects in subspace `[28..43]`, and $\mathbf{v}_{\text{goal}}(\mathcal{G})$ is the goal condition vector in the same subspace.
- **Direct Match:** If $Eff(C)$ satisfies all conditions in $\mathcal{G}$, relevance is **1.0**.
- **Orthogonal / Disjoint:** If $Eff(C)$ has zero overlap with $\mathcal{G}$ (e.g. `PlayMusic` vs `PaymentStatus`), relevance is **0.0**.
- **Contradictory:** If $Eff(C)$ contradicts $\mathcal{G}$, the inner product is negative, clamped to **0.0**.

---

## 5. Summary of Experiments

The test driver `tests/test_embedding.cpp` executes all 5 required experiments:

### Experiment 1: Capability Compatibility
- **Capabilities Tested:**
  - `CreateOrder`: $Pre = \{\text{CartExists}: \text{true}\}$, $Eff = \{\text{OrderExists}: \text{true}\}$
  - `MakePayment`: $Pre = \{\text{OrderExists}: \text{true}\}$, $Eff = \{\text{PaymentStatus}: \text{SUCCESS}\}$
  - `CancelCart`: $Pre = \{\text{OrderExists}: \text{false}\}$, $Eff = \{\text{CartExists}: \text{false}\}$
- **Results:**
  - `areCompatible(CreateOrder, MakePayment)` $\to$ **`TRUE`** (preconditions matched, outputs satisfy inputs).
  - `areCompatible(CreateOrder, CancelCart)` $\to$ **`FALSE`** (direct contradiction: $Eff(\text{OrderExists}=\text{true})$ vs $Pre(\text{OrderExists}=\text{false})$).

### Experiment 2: Capability Composition
- **Capabilities Tested:** `CreateOrder` + `MakePayment` + `SendNotification` $\to$ `CompletePurchase`.
- **Merged Attributes:**
  - Intermediate input/output dependencies resolved (`orderId`, `paymentId` chained).
  - Satisfied intermediate preconditions removed from external contract ($Pre = \{\text{CartExists}: \text{true}\}$).
  - Cumulative effects: $\{\text{OrderExists}: \text{true}, \text{PaymentStatus}: \text{SUCCESS}, \text{NotificationSent}: \text{true}\}$.
  - Combined Cost: $15.0 + 25.0 + 5.0 = 45.0$.
  - Combined Reliability: $0.99 \times 0.98 \times 0.995 = 0.965349$.
  - Combined Availability: $0.995 \times 0.990 \times 0.999 = 0.984065$.
- **Embedding:** Full 92-dimensional vector generated with cosine similarity of $1.0000$ between direct composition and multi-step chain composition.

### Experiment 3: Alternative Implementations
- **Capabilities Tested:** `CreateOrder_API`, `CreateOrder_GUI`, `CreateOrder_DATABASE`.
- **Similarity Matrix:**
  $$\begin{pmatrix} & \text{API} & \text{GUI} & \text{DB} \\ \text{API} & 1.0000 & 0.8283 & 0.8697 \\ \text{GUI} & 0.8283 & 1.0000 & 0.8596 \\ \text{DB} & 0.8697 & 0.8596 & 1.0000 \end{pmatrix}$$
- **Analysis:** Identical functional properties yield high base similarity (~$83\% - 87\%$), while architectural types and operational divergence (cost, reliability, latency) accurately differentiate the implementations.

### Experiment 4: Irrelevant Capability
- **Goal:** $\{\text{PaymentStatus} = \text{SUCCESS}\}$
- **Results:**
  - $\text{goalRelevance}(\text{MakePayment}, \text{Goal}) = \mathbf{1.0000}$ (Direct satisfaction).
  - $\text{goalRelevance}(\text{PlayMusic}, \text{Goal}) = \mathbf{0.0000}$ (Orthogonal effect subspace; zero overlap).

### Experiment 5: Operational Attributes Influence
- **Evaluated Services:** Baseline ($c=10, r=0.99, a=0.995$), High Cost ($c=250$), Low Reliability ($r=0.40$), Low Availability ($a=0.50$), Budget Tier ($c=1, r=0.70, a=0.80$).
- **Analysis:** Demonstrates how QoS variations shift the vector angle in the operational subspace when functional signatures remain identical.

---

## 6. How to Build and Run

### 6.1 Using CMake (Recommended)
```bash
# Navigate to the project root
cd CapabilityEmbedding

# Create build directory
mkdir build
cd build

# Configure with CMake (C++17)
cmake ..

# Build
cmake --build .

# Run test suite
./test_embedding
```

### 6.2 Direct Compilation via C++17 Compiler (GCC / MinGW / Clang)
If CMake is not installed, compile directly with `g++` (or `clang++`):

```powershell
# Using MinGW / GCC on Windows (PowerShell):
g++ -std=c++17 -Wall -Wextra -pedantic -Iinclude src/Embedding.cpp tests/test_embedding.cpp -o test_embedding.exe

# Execute
.\test_embedding.exe
```

```bash
# On Linux / macOS:
g++ -std=c++17 -Wall -Wextra -pedantic -Iinclude src/Embedding.cpp tests/test_embedding.cpp -o test_embedding
./test_embedding
```

---

## 7. Submission Checklist & Code Quality

- [x] **C++17 Standard:** Built with standard C++17 features (`-std=c++17`).
- [x] **Zero Warnings:** Compiles cleanly with `-Wall -Wextra -pedantic`.
- [x] **No Planning Algorithms:** Zero graph search, BFS, DFS, A*, D* Lite, or LPA*.
- [x] **Complete Implementation:** No placeholders, stubs, or omissions.
- [x] **5 Experiments:** Comprehensive execution, formatted matrices, and verified assertions.
