# Vector Embedding Architecture for Capability Composition: Technical Report

**Course:** PCCST503: Advanced Software Engineering and Systems Design  
**Topic:** Assignment 2: Design of a Vector Embedding for Capability Composition  
**Student Name:** Royce P Saji  
**Registration ID:** TCR24CS058  
**Roll No:** 57  
**GitHub Repository:** [https://github.com/Royce1415/capability_embedding](https://github.com/Royce1415/capability_embedding)  
**Architecture:** Partitioned Structured Dense Vector (PSD-160)  
**Implementation Language:** Python 3.10 / NumPy  

---

## 1. Problem Definition

In modern distributed computing, service-oriented systems, and automated workflow synthesis, systems are increasingly constructed dynamically from discrete software capabilities. A software capability represents an executable unit such as a REST API endpoint, a database stored procedure, an asynchronous message broker, or a local computation. The central challenge presented in this assignment is representing formally specified software states, goals, and capabilities in a continuous vector space while strictly preserving the mathematical relationships required for:

1. **Capability Compatibility:** Determining whether one capability can directly supply the data and preconditions required by another capability.
2. **Capability Composition:** Combining sequential chains of capabilities into composite capability representations.
3. **Goal Relevance:** Identifying which capabilities actively contribute to satisfying a target environmental goal state.
4. **Alternative Implementation Identification:** Recognizing when different software components provide functionally equivalent behavior despite differing underlying implementation mechanisms.

### 1.1 Contrast with Natural Language Word Embeddings

It is essential to distinguish capability embeddings from standard natural language text embeddings (such as Word2Vec, GloVe, or transformer text embeddings). Word embeddings map tokens based on lexical co-occurrence and distributional similarity in human text corpora. However, capability composition is governed by strict formal logic and operational causality rather than linguistic proximity:

- **Semantic Proximity vs. Operational Compatibility:** In natural language, words like "Order" and "Payment" are related concepts, but their linguistic similarity does not indicate whether a payment service can execute immediately after an order creation service. Conversely, a data validation step and a database insertion step may describe completely different domain concepts, yet be sequential partners in an executable pipeline.
- **The Similarity vs. Composability Dilemma:** Two capabilities that are highly similar (for example, two competing payment gateways like Stripe and PayPal) cannot be composed together in sequence because one does not consume the outputs or satisfy the preconditions of the other. Composability requires directional asymmetry, where the effects and outputs of the producer match the preconditions and inputs of the consumer.
- **Logical Contradictions:** Natural language models frequently project antonyms (such as "locked" and "unlocked", or "true" and "false") into nearby vector coordinates because they share identical sentence contexts. In executable software, an effect asserting `Cart.locked = true` directly contradicts a precondition requiring `Cart.locked = false`. Merging these into high-cosine representations causes catastrophic planning failures.

---

## 2. Design Requirements

To represent capabilities effectively for automated composition, an embedding architecture must satisfy nine technical requirements derived from the assignment specification:

1. **Capability Identity:** The embedding must capture the unique structural identity of each capability, including its architectural type and execution mechanism.
2. **State Awareness:** The representation must encode domain states such that environmental states, goal specifications, preconditions, and effects can be projected into a shared geometric space.
3. **Precondition-Effect Compatibility:** The vector space must provide an algebraic mechanism to determine whether a producer capability's effects satisfy the preconditions of a consumer capability.
4. **Input-Output Compatibility:** The embedding must reflect data-flow compatibility, capturing whether required input fields of a downstream service are produced by upstream services.
5. **Compositional Equivalence:** Composing two or more capabilities must produce a composite entity that can be represented within the exact same vector space as atomic capabilities, enabling recursive, hierarchical composition.
6. **Goal Relevance:** The distance or alignment between a capability vector and a goal vector must directly reflect whether invoking that capability advances the system toward the goal.
7. **Operational Awareness:** The embedding must incorporate non-functional quality attributes (execution time, monetary cost, resource demands, failure risk, reliability, and availability) without corrupting logical compatibility.
8. **Logical Consistency:** Opposite truth values on the same state variable must map to opposing vector directions, ensuring that logical contradictions produce negative inner products.
9. **Computational Efficiency:** Vector operations must rely on standard, high-speed linear algebra (dot products, vector additions, Euclidean norms) to support rapid searching across large capability catalogs.

A purely semantic text embedding fails on nearly all these requirements because it lacks signed truth polarities, treats inputs and outputs as unsegmented bags of words, and cannot distinguish non-functional costs from functional effects.

---

## 3. Related Embedding Approaches

Before finalizing our architecture, we analyzed four general embedding paradigms conceptually:

### 3.1 Sparse Symbolic Feature Vectors
- **Basic Concept:** One-hot or multi-hot binary vectors where each dimension corresponds to an exact predicate, input, or output symbol.
- **Strengths:** Perfectly preserves discrete logical truth values, prevents semantic drift, and makes contradictions explicit.
- **Limitations:** Suffers from extreme dimensional explosion as domain vocabulary grows. Vectors are completely orthogonal unless symbols match identically, preventing partial matching, soft alignment, or continuous gradient-based search.

### 3.2 Dense Learned Latent Embeddings (Unstructured)
- **Basic Concept:** Mapping entire capability descriptors (text or specifications) into an unsegmented dense latent space ($\mathbb{R}^d$) using neural encoders.
- **Strengths:** Captures latent synonymy, scales well to large vocabularies, and compresses information into compact dimensions.
- **Limitations:** Completely entangles distinct attributes. In an unstructured vector, one cannot isolate whether a high dot product was caused by shared execution protocols, similar monetary costs, or matching preconditions. Furthermore, signed logical polarities are easily lost.

### 3.3 Graph-Based Representations
- **Basic Concept:** Modeling capabilities, states, and data schemas as nodes and edges in a knowledge graph, using Graph Neural Networks (GNNs) or graph embeddings (e.g., TransE) to learn link predictions.
- **Strengths:** Naturally captures complex multi-hop dependencies and relational topology.
- **Limitations:** High computational overhead for graph traversal and inductive inference. Graph embeddings typically focus on static link existence rather than state transformations, and operational cost aggregation is awkward to represent as graph translations.

### 3.4 Structured / Block-Partitioned Embeddings
- **Basic Concept:** Allocating dedicated coordinate slices to specific functional, data-flow, and operational facets of the capability tuple.
- **Strengths:** Combines the algebraic efficiency of dense vector mathematics with the rigorous interpretability and modularity of symbolic specifications. Allows independent similarity scoring per block while supporting overall composite vectors.
- **Limitations:** Requires domain designers to establish canonical block boundaries and schema conventions.

Our proposed architecture, PSD-160, adopts the structured block-partitioned paradigm.

---

## 4. Proposed Representation: PSD-160

The Partitioned Structured Dense 160-dimensional vector space (PSD-160) allocates fixed coordinate ranges to each component of the formal capability tuple $C = (T, I, O, P, E, K, R, Q, \text{Rel}, A, M)$.

### 4.1 Vector Layout

The 160 dimensions are divided into eight dedicated blocks:

| Block Name | Slice Range | Dimensions | Mathematical Purpose |
|:---|:---:|:---:|:---|
| **Mechanism & Type** | `[0:16]` | 16 | One-hot capability type (`API`, `DB`, `GUI`, etc.) and protocol signatures |
| **Inputs** | `[16:40]` | 24 | Data-flow inputs (1.0 for required, 0.5 for optional) |
| **Outputs** | `[40:64]` | 24 | Data-flow outputs (1.0 for produced) |
| **Preconditions** | `[64:96]` | 32 | Logical propositions required prior to execution |
| **Effects** | `[96:128]` | 32 | Logical propositions established upon execution |
| **Constraints** | `[128:140]` | 12 | Invariant guard constraints and operational boundaries |
| **Resources** | `[140:152]` | 12 | Computational and system resource dependencies |
| **Operational Quality** | `[152:160]` | 8 | Normalized latency, money, compute, risk, energy, unreliability, and unavailability |

Total Vector Dimension: $16 + 24 + 24 + 32 + 32 + 12 + 12 + 8 = 160$.

### 4.2 Shared Subspaces

A central architectural feature of PSD-160 is the use of shared coordinate spaces:
- **Shared Condition Space ($\mathbb{R}^{32}$):** Application states $S$, target goals $G$, capability preconditions $P$, and capability effects $E$ are all encoded into the same 32-dimensional coordinate space. This guarantees that dot products between effects and preconditions, or between effects and goals, directly evaluate predicate alignment.
- **Shared Data-Flow Space ($\mathbb{R}^{24}$):** Inputs $I$ and outputs $O$ share a common 24-dimensional typed schema space, ensuring that output-to-input data handoffs can be computed via direct inner products.

By maintaining fixed blocks, operational variations (such as a service taking 500 ms instead of 100 ms) only modify coordinates in slice `[152:160]`, leaving the functional effect and precondition blocks completely untouched.

---

## 5. Mathematical Formulation

### 5.1 Condition Predicate Encoding ($\mathbb{R}^{32}$)

Let $\mathcal{P} = \{p_1, p_2, \dots, p_k\}$ be a set of state predicates. The 32-dimensional condition vector $v_{\text{cond}}(\mathcal{P})$ is defined deterministically:

1. **Boolean Variables (Indices 0 to 7):**
   $$v_{\text{cond}}[i] = \begin{cases} 
   +1.0 & \text{if predicate asserts } \text{Var}_i = \text{True} \\
   -1.0 & \text{if predicate asserts } \text{Var}_i = \text{False} \\
   0.0 & \text{if } \text{Var}_i \text{ is unmentioned}
   \end{cases}$$
2. **Categorical Variables (Indices 8 to 18):**
   Categorical assignments are encoded via disjoint one-hot coordinate groups (e.g., `Payment.status` maps to indices 8 for `NOT_STARTED`, 9 for `PENDING`, 10 for `SUCCESS`, and 11 for `REFUNDED`).
3. **Numerical Variables (Indices 19 to 22):**
   Numerical variables are mapped to two coordinates: normalized magnitude $\min(1.0, \max(0.0, \text{val} / 10.0))$ and operator direction ($+1.0$ for $>$ or $\ge$, $-1.0$ for $<$ or $\le$, $0.0$ for $=$).

State encoding $v(S)$ and goal encoding $v(G)$ directly invoke this condition encoder.

### 5.2 Input and Output Encoding ($\mathbb{R}^{24}$)

For a list of data fields $F$:
$$v_{\text{input}}(F)[j] = \begin{cases} 
1.0 & \text{if field } j \text{ is required} \\
0.5 & \text{if field } j \text{ is optional} \\
0.0 & \text{if field } j \text{ is absent}
\end{cases}, \quad
v_{\text{output}}(F)[j] = \begin{cases} 
1.0 & \text{if field } j \text{ is produced} \\
0.0 & \text{otherwise}
\end{cases}$$

### 5.3 Operational Vector Encoding ($\mathbb{R}^8$)

Slice `[152:160]` encodes non-functional attributes as normalized penalties:
$$v_{\text{ops}} = \begin{bmatrix}
\min(1.0, t / 1000.0) \\
\min(1.0, m / 0.10) \\
\min(1.0, r / 5.0) \\
\text{risk} \\
\min(1.0, e / 10.0) \\
1.0 - \text{Rel} \\
1.0 - A \\
c_{\text{comp}}
\end{bmatrix}$$
where $c_{\text{comp}} = \frac{1}{5}(v_{\text{ops}}[0] + v_{\text{ops}}[1] + v_{\text{ops}}[2] + v_{\text{ops}}[3] + v_{\text{ops}}[5])$.

### 5.4 Similarity Formulation

Safe cosine similarity prevents division by zero:
$$\text{cos}(a, b) = \begin{cases} 
1.0 & \text{if } \|a\| = 0 \text{ and } \|b\| = 0 \\
0.0 & \text{if } \|a\| = 0 \text{ xor } \|b\| = 0 \\
\frac{a \cdot b}{\|a\| \|b\| + \epsilon} & \text{otherwise}
\end{cases} \quad (\epsilon = 10^{-9})$$

Functional capability similarity is a weighted sum over all eight slices:
$$\text{Sim}(C_1, C_2) = \sum_{b \in \mathcal{B}} w_b \cdot \text{cos}(v(C_1)_b, v(C_2)_b)$$
with implemented weights:
$$w_{\text{effect}} = 0.25, \quad w_{\text{pre}} = 0.20, \quad w_{\text{input}} = 0.10, \quad w_{\text{output}} = 0.10$$
$$w_{\text{constraint}} = 0.10, \quad w_{\text{resource}} = 0.10, \quad w_{\text{ops}} = 0.10, \quad w_{\text{mech}} = 0.05$$
which sum exactly to $1.00$.

### 5.5 Directional Compatibility Formulation

Directional compatibility evaluates the handoff from producer $C_1$ to consumer $C_2$:
$$\text{Align}_{EP}(C_1 \to C_2) = \begin{cases} 
1.0 & \text{if } \|v(C_2)_P\|^2 = 0 \\
\frac{v(C_1)_E \cdot v(C_2)_P}{\|v(C_2)_P\|^2} & \text{otherwise}
\end{cases}$$

$$\text{Align}_{OI}(C_1 \to C_2) = \begin{cases} 
1.0 & \text{if } \|v(C_2)_I\|^2 = 0 \\
\frac{v(C_1)_O \cdot v(C_2)_I}{\|v(C_2)_I\|^2} & \text{otherwise}
\end{cases}$$

$$\text{Comp}_{vec}(C_1 \to C_2) = 0.6 \cdot \text{Align}_{EP} + 0.4 \cdot \text{Align}_{OI}$$

$$\text{Comp}_{exec}(C_1 \to C_2) = A_1 \cdot A_2 \cdot \text{Comp}_{vec}(C_1 \to C_2)$$

A candidate handoff is deemed execution-compatible if and only if $\text{Comp}_{exec} \ge 0.70$ and it passes formal verification (all required inputs produced with matching types, all preconditions satisfied, zero contradictions, and positive availability).

### 5.6 Goal Relevance Formulation

$$\text{GoalRel}(C, G) = \begin{cases} 
0.0 & \text{if } \|v(G)\|^2 = 0 \\
\frac{\max(0.0, v(C)_E \cdot v(G))}{\|v(G)\|^2} & \text{otherwise}
\end{cases}$$

---

## 6. Capability Composition Model

Given a chain of compatible capabilities $[C_1, C_2, \dots, C_n]$, sequential composition produces a unified composite capability $C_{1:n} = C_1 \circ C_2 \circ \dots \circ C_n$.

### 6.1 Sequential Composition Rules

1. **Precondition Resolution:** Preconditions of downstream capabilities that are established by earlier capabilities in the pipeline are internalized and removed from the composite's external preconditions. Preconditions that remain unsatisfied by earlier steps form the composite's external preconditions:
   $$P_{\text{comp}} = P_1 \cup \bigcup_{j=2}^n \{p \in P_j \mid \neg \text{satisfied}(p, \bigcup_{k=1}^{j-1} E_k)\}$$
2. **Input Resolution:** Inputs of downstream capabilities supplied by upstream outputs are internalized:
   $$I_{\text{comp}} = I_1 \cup \bigcup_{j=2}^n \{inp \in I_j \mid \neg \text{produced}(inp, \bigcup_{k=1}^{j-1} O_k)\}$$
3. **Terminal Outputs:** The composite exposes the terminal capability's outputs: $O_{\text{comp}} = O_n$.
4. **Cumulative Effect Override:** Effects accumulate chronologically. If capability $C_b$ ($b > a$) modifies state variable $X$, its effect overwrites the earlier effect from $C_a$.
5. **Constraint and Resource Union:** Constraints and resources are merged as set unions: $K_{\text{comp}} = \bigcup K_i$, $R_{\text{comp}} = \bigcup R_i$.
6. **Operational Attribute Aggregation:**
   - Latency: $t_{\text{comp}} = \sum_{i=1}^n t_i$
   - Monetary cost: $m_{\text{comp}} = \sum_{i=1}^n m_i$
   - Resource units: $r_{\text{comp}} = \sum_{i=1}^n r_i$
   - Risk: $\text{risk}_{\text{comp}} = 1.0 - \prod_{i=1}^n (1.0 - \text{risk}_i)$
   - Reliability: $\text{Rel}_{\text{comp}} = \prod_{i=1}^n \text{Rel}_i$ (under independent component failure modes)
   - Availability: $A_{\text{comp}} = \prod_{i=1}^n A_i$

### 6.2 Vector Re-Encoding

The composite object is an instance of the formal `Capability` dataclass. It is passed directly to `encode_capability()`, producing a 160-dimensional vector $v(C_{\text{comp}}) \in \mathbb{R}^{160}$ with zero architectural difference from an atomic capability.

---

## 7. Implementation

The implementation is written in Python 3.10 and organized into clean, modular packages:

```
ml/
├── data/
│   └── experimental_dataset.json     # Master e-commerce dataset (14 caps, 4 states, 5 goals)
├── src/
│   ├── models.py                     # Formal dataclasses and CapabilityType enum
│   ├── encoder.py                    # Deterministic PSD-160 vector encoder
│   ├── metrics.py                    # Safe cosine, similarity, compatibility, goal relevance
│   └── composer.py                   # Sequential composition engine
├── experiments/
│   ├── run_all.py                    # Master experiment runner, CSV writer, plot generator
│   └── results/
│       ├── results.json              # Full structured numerical experiment results
│       ├── *.csv                     # Five human-readable CSV summaries
│       └── plots/*.png               # Four high-resolution visualization figures
└── tests/
    ├── test_encoding.py              # 12 unit tests for PSD-160 encoder
    ├── test_metrics.py               # 10 unit tests for metrics and directional gates
    ├── test_composition.py           # 6 unit tests for sequential composition
    └── test_experiments.py           # 10 unit tests for experimental reproducibility
```

### Key Technical Aspects:
- **Dependencies:** Strictly minimal (`numpy`, `pytest`, `matplotlib`). No heavy frameworks, API servers, or pre-trained models.
- **Determinism:** All encoders are 100% deterministic. No random initializations or unseeded hashes.
- **Verification:** 38 unit tests run via pytest in under 0.50 seconds.

---

## 8. Experimental Methodology

To evaluate the PSD-160 embedding, we developed a formal benchmark dataset in the e-commerce domain containing 14 capabilities, 4 states, and 5 goals (`data/experimental_dataset.json`).

### 8.1 Capability Groups

- **Core Transaction Capabilities:**
  - `C1` (`CreateOrder`): API service consuming `cart_id`, producing `order_id`, asserting `Order.exists=true` and `Cart.locked=true`.
  - `C2` (`MakePayment`): API service consuming `order_id`, producing `payment_id`, asserting `Payment.status=SUCCESS`.
  - `C4` (`SendNotification`): Asynchronous event handler consuming `payment_id`, asserting `Notification.sent=true`.
- **Incompatible and Contradictory Capabilities:**
  - `C3` (`CancelCart`): API requiring `Order.exists=false`, asserting `Cart.status=CANCELLED`.
  - `C9` (`RefundPayment`): API service setting `Payment.status=REFUNDED`.
- **Alternative Implementations of Order Creation:**
  - `C10` (`API_CreateOrder`): REST API implementation ($t=120\text{ ms}, m=\$0.012, \text{Rel}=0.985, A=1.0$).
  - `C11` (`DB_CreateOrder`): Direct database stored procedure ($t=20\text{ ms}, m=\$0.001, \text{Rel}=0.999, A=1.0$).
  - `C12` (`GUI_CreateOrder`): Web browser automated script ($t=500\text{ ms}, m=\$0.000, \text{Rel}=0.950, A=1.0$).
- **Degraded / Unavailable Service:**
  - `C13` (`UnavailableOrderService`): Service with zero availability ($A = 0.0$).
- **Auxiliary Capabilities:**
  - `C5` (`CheckInventory`), `C6` (`ReserveInventory`), `C7` (`ShipOrder`), `C8` (`ArchiveOrder`), `C14` (`SlowExpensivePayment`).

### 8.2 Five Required Experiments

1. **Experiment 1 (Capability Compatibility):** Evaluates pairwise compatibility across compatible, contradictory, reversed, and partially matching pairs.
2. **Experiment 2 (Capability Composition):** Constructs composite $C_1 \circ C_2 \circ C_4$, verifying internal precondition/input resolution and operational aggregation.
3. **Experiment 3 (Alternative Implementations):** Compares API, DB, and GUI implementations across individual block similarities.
4. **Experiment 4 (Goal Relevance Ranking):** Evaluates capability relevance ranking against a multi-condition goal state.
5. **Experiment 5 (Operational Attributes):** Compares candidate operational representations in PSD-160 and analyzes utility tradeoffs under diverse operational priorities.

---

## 9. Results

All numerical values presented below are exact figures generated by `experiments/run_all.py` and recorded in `experiments/results/results.json`.

### 9.1 Experiment 1: Capability Compatibility

The evaluation tested six representative capability pairs:

| Capability Transition | Description / Hypothesis | Align_EP | Align_OI | Vector Score ($\text{Comp}_{vec}$) | Execution Score ($\text{Comp}_{exec}$) | Formal Decision | Failure Reasons |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **C1 $\to$ C2**<br>(`CreateOrder` $\to$ `MakePayment`) | Valid pipeline handoff | $1.0000$ | $1.0000$ | $+1.0000$ | $+1.0000$ | **COMPATIBLE** | None (Passed all checks) |
| **C1 $\to$ C3**<br>(`CreateOrder` $\to$ `CancelCart`) | Logical contradiction on `Order.exists` | $-1.0000$ | $0.0000$ | $-0.6000$ | $-0.6000$ | **INCOMPATIBLE** | Contradiction; missing input; score $< 0.70$ |
| **C2 $\to$ C1**<br>(`MakePayment` $\to$ `CreateOrder`) | Reversed execution direction | $0.0000$ | $0.0000$ | $0.0000$ | $0.0000$ | **INCOMPATIBLE** | Unmet preconditions; missing input; score $< 0.70$ |
| **C1 $\to$ C4**<br>(`CreateOrder` $\to$ `SendNotification`) | Missing intermediate step (skip C2) | $0.0000$ | $0.0000$ | $0.0000$ | $0.0000$ | **INCOMPATIBLE** | Unmet precondition `Payment.status`; missing input |
| **C2 $\to$ C4**<br>(`MakePayment` $\to$ `SendNotification`) | Valid downstream handoff | $1.0000$ | $1.0000$ | $+1.0000$ | $+1.0000$ | **COMPATIBLE** | None (Passed all checks) |
| **C1 $\to$ C8**<br>(`CreateOrder` $\to$ `ArchiveOrder`) | Partial match missing payment condition | $+0.5000$ | $+1.0000$ | $+0.7000$ | $+0.7000$ | **INCOMPATIBLE** | Precondition `Payment.status` not satisfied |

#### Critical Finding in Experiment 1:
In the transition `CreateOrder -> ArchiveOrder`, `ArchiveOrder` requires `order_id` (produced by `C1`, so $\text{Align}_{OI} = 1.0$) and requires two preconditions: `Order.exists = true` (produced by `C1`) and `Payment.status = SUCCESS` (not produced by `C1`). This yielded $\text{Align}_{EP} = 0.5000$.

The resulting continuous vector compatibility score was:
$$\text{Comp}_{vec} = 0.6(0.5) + 0.4(1.0) = 0.7000$$

Because $0.7000$ meets the numerical threshold, a purely vector-based system without execution verification would mistakenly deem this transition valid. However, our formal validation gate caught the missing payment precondition and correctly rejected the handoff. This empirical outcome demonstrates why vector alignment alone is insufficient for runtime execution safety.

Refer to the generated plot: `../experiments/results/plots/compatibility_scores.png`.

---

### 9.2 Experiment 2: Capability Composition

Sequential composition was executed on the chain $C_1 \to C_2 \to C_4$.

- **Composite ID:** `C1_C2_C4`
- **Composite Name:** `CreateOrder -> MakePayment -> SendNotification`
- **External Inputs:** `['cart_id']` (`order_id` and `payment_id` were successfully internalized)
- **External Preconditions:** `['Cart.exists', 'Inventory.available']` (`Order.exists` was satisfied by `C1` and internalized)
- **Terminal Outputs:** `['notification_id']`
- **Cumulative Final Effects:** `['Order.exists', 'Cart.locked', 'Order.status', 'Payment.status', 'Notification.sent']`

#### Similarities Between Composite and Components:
- $\text{Sim}(C_{\text{comp}}, C_1) = \mathbf{0.7144}$
- $\text{Sim}(C_{\text{comp}}, C_2) = \mathbf{0.3324}$
- $\text{Sim}(C_{\text{comp}}, C_4) = \mathbf{0.4297}$

#### Operational Attribute Aggregation:
- **Execution Time:** $100.0 + 250.0 + 60.0 = \mathbf{410.0\text{ ms}}$
- **Monetary Cost:** $\$0.010 + \$0.020 + \$0.005 = \mathbf{\$0.0350}$
- **Reliability:** $0.99 \times 0.95 \times 0.98 = \mathbf{0.92169}$
- **Availability:** $1.0 \times 1.0 \times 1.0 = \mathbf{1.0000}$

---

### 9.3 Experiment 3: Alternative Implementations

We evaluated three alternative implementations of order creation: REST API (`C10`), Database Stored Procedure (`C11`), and GUI Automation (`C12`):

| Comparison Pair | Full Similarity | Effect Sim | Precondition Sim | Input Sim | Output Sim | Mechanism Sim | Operational Sim |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **API (`C10`) vs. DB (`C11`)** | **0.9032** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **0.0000** | **0.8246** |
| **API (`C10`) vs. GUI (`C12`)** | **0.9357** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **0.0000** | **0.8572** |
| **DB (`C11`) vs. GUI (`C12`)** | **0.8907** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **0.0000** | **0.7002** |

All three implementations have exact $1.0000$ effect, precondition, input, and output similarities, establishing full functional substitutability. However, their mechanism similarity is exactly $0.0000$ (orthogonal vectors in slice `[0:16]`), and their operational similarities reflect latency and cost variations ($0.70$ to $0.86$).

Refer to the generated plot: `../experiments/results/plots/alternative_implementations.png`.

---

### 9.4 Experiment 4: Goal Relevance Ranking

Target Goal: `Goal_Master` (`Order.exists = true`, `Payment.status = SUCCESS`, `Notification.sent = true`).

| Rank | Capability ID | Capability Name | Relevance Score | Semantic Role in Plan |
|:---:|:---:|:---|:---:|:---|
| 1 | `C1` | `CreateOrder` | **0.3333** | Useful: establishes `Order.exists=true` |
| 2 | `C2` | `MakePayment` | **0.3333** | Useful: establishes `Payment.status=SUCCESS` |
| 3 | `C4` | `SendNotification` | **0.3333** | Useful: establishes `Notification.sent=true` |
| 4 | `C7` | `ShipOrder` | **0.0000** | Irrelevant: establishes `Order.status=COMPLETED` |
| 5 | `C8` | `ArchiveOrder` | **0.0000** | Irrelevant: establishes `Order.archived=true` |
| 6 | `C9` | `RefundPayment` | **0.0000** | Contradictory/Irrelevant: sets `Payment.status=REFUNDED` |
| 7 | `C5` | `CheckInventory` | **0.0000** | Irrelevant: establishes `Inventory.available=true` |
| 8 | `C3` | `CancelCart` | **0.0000** | Contradictory: establishes `Cart.status=CANCELLED` |

All three goal-advancing capabilities scored positive relevance ($0.3333$ each, summing to $1.0$), while distractor, irrelevant, and contradictory actions scored $0.0000$.

Refer to the generated plot: `../experiments/results/plots/goal_relevance.png`.

---

### 9.5 Experiment 5: Operational Attributes

#### Part A: PSD-160 Operational Vector Representations (Slice `[152:160]`)

Direct geometric comparisons across the 8-dimensional operational sub-vectors:

| Candidate Pair | Cosine Similarity | Euclidean Distance |
|:---|:---:|:---:|
| **DB (`C11`) vs. API (`C10`)** | 0.8246 | 0.1646 |
| **DB (`C11`) vs. GUI (`C12`)** | 0.7002 | 0.5776 |
| **API (`C10`) vs. GUI (`C12`)** | 0.8572 | 0.4812 |
| **DB (`C11`) vs. Unavailable (`C13`)** | 0.2230 | 1.0088 |
| **API (`C10`) vs. Unavailable (`C13`)** | 0.2555 | 1.0005 |
| **GUI (`C12`) vs. Unavailable (`C13`)** | 0.2180 | 1.1171 |

The active services share operational similarity between $0.70$ and $0.86$. The unavailable service (`C13`) exhibits extreme geometric divergence (similarity $\approx 0.22$, Euclidean distance $> 1.0$) because its unavailability coordinate ($1 - A = 1.0$) dominates the sub-vector.

#### Part B: Application-Level Utility Analysis

To demonstrate how external decision policies select among functionally equivalent candidates, we applied the utility decision policy $U(C) = w_{\text{rel}} \text{Rel} - w_{\text{time}} t_{\text{norm}} - w_{\text{cost}} m_{\text{norm}}$ with availability gating $A \cdot U(C)$:

- **Speed-Focused Profile ($w_t=0.7, w_m=0.1, w_r=0.2$):**
  1. `C11` (`DB_CreateOrder`): Effective Utility = **+0.1848** ($t=20\text{ ms}, m=\$0.001, \text{Rel}=0.999$)
  2. `C10` (`API_CreateOrder`): Effective Utility = **+0.1010** ($t=120\text{ ms}, m=\$0.012, \text{Rel}=0.985$)
  3. `C13` (`UnavailableOrderService`): Effective Utility = **0.0000** ($A=0.0$ gates raw utility $0.1180$ to zero)
  4. `C12` (`GUI_CreateOrder`): Effective Utility = **-0.1600** ($t=500\text{ ms}$ penalizes speed)
- **Reliability-Focused Profile ($w_t=0.1, w_m=0.1, w_r=0.8$):**
  1. `C11` (`DB_CreateOrder`): Effective Utility = **+0.7962**
  2. `C10` (`API_CreateOrder`): Effective Utility = **+0.7640**
  3. `C12` (`GUI_CreateOrder`): Effective Utility = **+0.7100**
  4. `C13` (`UnavailableOrderService`): Effective Utility = **0.0000**
- **Cost-Focused Profile ($w_t=0.1, w_m=0.8, w_r=0.1$):**
  1. `C11` (`DB_CreateOrder`): Effective Utility = **+0.0899**
  2. `C12` (`GUI_CreateOrder`): Effective Utility = **+0.0450** (zero monetary cost)
  3. `C13` (`UnavailableOrderService`): Effective Utility = **0.0000**
  4. `C10` (`API_CreateOrder`): Effective Utility = **-0.0095** ($\$0.012$ fee penalizes cost)

Refer to the generated plot: `../experiments/results/plots/operational_tradeoffs.png`.

---

## 10. Analysis

1. **Why `CreateOrder -> MakePayment` scores $+1.0000$:** The outputs of `C1` (`order_id`) exactly match the input requirements of `C2` ($\text{Align}_{OI} = 1.0$), and the effects of `C1` (`Order.exists=true`) satisfy the precondition of `C2` ($\text{Align}_{EP} = 1.0$). Both are fully available, yielding an execution score of $1.0$.
2. **Why `CreateOrder -> CancelCart` is rejected ($-0.6000$):** `CancelCart` requires `Order.exists=false` (encoded as $-1.0$), while `CreateOrder` produces `Order.exists=true` (encoded as $+1.0$). Their dot product is $(+1.0)(-1.0) = -1.0$, resulting in a negative alignment score and an explicit contradiction failure.
3. **Difference between continuous vector alignment and execution compatibility:** `CreateOrder -> ArchiveOrder` achieved a vector compatibility score of $+0.7000$ because $100\%$ of data inputs and $50\%$ of preconditions matched. However, missing the second precondition (`Payment.status=SUCCESS`) caused the formal validation gate to fail. This proves that continuous vector alignment acts as an efficient candidate filter, but discrete formal verification is required before execution.
4. **Why composite $C_{1:n}$ is more similar to $C_1$ ($0.7144$) than $C_2$ ($0.3324$) or $C_4$ ($0.4297$):** $C_1$ defines the external preconditions (`Cart.exists`, `Inventory.available`) and external inputs (`cart_id`) of the entire composite workflow. Because preconditions and inputs account for $30\%$ of the similarity weight, the composite shares strong structural affinity with its entry capability.
5. **Separation of functional and mechanism similarity:** The three implementations of order creation (API, DB, GUI) had exact $1.0000$ effect similarities and $0.0000$ mechanism similarities. This allows an autonomous system to identify functional substitutes while remaining aware of architectural differences.
6. **Goal relevance discrimination:** The goal relevance metric effectively assigned $0.3333$ to each of the three capabilities that establish target predicates, while zeroing out all distractor and contradictory operations.
7. **Operational representation vs. Decision policy:** PSD-160 represents raw operational metrics deterministically in slice `[152:160]`. Pairwise comparisons in this sub-vector reveal true multi-attribute proximity without assuming fixed user preferences. Application-specific trade-offs are subsequently resolved by external utility policies.
8. **Asymmetry of capability handoffs:** Compatibility is directional ($\text{Compat}(C_1 \to C_2) = 1.0$, whereas $\text{Compat}(C_2 \to C_1) = 0.0$). This asymmetry is preserved because $\text{Align}_{EP}$ and $\text{Align}_{OI}$ project producer outputs onto consumer requirements rather than computing an undirected symmetric angle.

---

## 11. Limitations

While the PSD-160 architecture successfully fulfills all assignment requirements, several technical limitations must be acknowledged:

1. **Fixed Coordinate Capacity:** The architecture assumes a predefined coordinate allocation (32 condition dimensions, 24 data-flow dimensions). While reserved slots accommodate dynamic fields via hashing, scaling to thousands of enterprise variables would introduce hash collisions.
2. **Fixed 160-Dimensional Budget:** The vector dimension is fixed at 160. Dynamic expansion requires global schema updates.
3. **Sequential Pipeline Assumption:** Composition currently supports linear sequences ($C_1 \to C_2 \to \dots \to C_n$). Complex control flow (conditional branching, concurrent parallel forks, join barriers, and loops) cannot be fully expressed in a single linear composite vector.
4. **Independent Failure Modes:** Operational reliability aggregation assumes component failures are statistically independent ($\prod \text{Rel}_i$). In production, shared infrastructure causes correlated failure modes.
5. **Coarse Discretization of Numerical Operators:** Numerical predicates are normalized over fixed intervals ($[0, 10]$) with three operator directions ($>$, $<$, $=$). Complex arithmetic expressions or non-linear constraints are not fully represented in vector space.
6. **Hand-Designed Deterministic Encoding:** The embedding is constructed through deterministic domain rules rather than learned from massive execution traces. While this ensures perfect interpretability and zero training overhead, it requires initial domain modeling.
7. **Vector Similarity Cannot Guarantee Safety Alone:** As proven by Experiment 1, continuous vector alignment can achieve high scores on partial matches. Discrete formal verification remains necessary to prevent execution failures.

---

## 12. Conclusion

In this project, we designed, implemented, and empirically evaluated PSD-160, a Partitioned Structured Dense 160-dimensional vector embedding for software capability composition. 

Our investigation yields four primary conclusions:
1. **Partitioned vectors resolve the semantic dilemma:** By segregating mechanism, data flow, preconditions, effects, constraints, resources, and operational attributes into dedicated slices, capabilities maintain functional substitutability without sacrificing operational or architectural identity.
2. **Signed polarities preserve logical consistency:** Mapping boolean states to $+1.0$ (true), $-1.0$ (false), and $0.0$ (neutral) ensures that logical contradictions produce negative vector projections, preventing invalid handoffs in vector space.
3. **Two-tier compatibility is essential:** Continuous vector alignment provides an efficient search heuristic, but formal execution gating is required to catch missing preconditions and guarantee execution correctness.
4. **Hierarchical composability is achievable:** Formally aggregating operational costs and internalizing intermediate data dependencies enables composite capabilities to be re-encoded into the exact same 160-dimensional space, supporting recursive workflow construction.

The PSD-160 architecture demonstrates that structured continuous vector spaces can bridge the gap between continuous geometric optimization and discrete software composition.

---

## 13. References

1. PCCST503 Course Specification: *Assignment 2: Design of a Vector Embedding for Capability Composition*.
2. Ghallab, M., Nau, D., and Traverso, P. (2004). *Automated Planning: Theory & Practice*. Morgan Kaufmann. (Foundational formalisms for state-transition systems, STRIPS preconditions, and cumulative state effects).
3. Dustdar, S., and Schreiner, W. (2005). *A Survey on Web Service Composition*. ACM Transactions on the Web. (Formalisms for input-output data-flow matching and QoS-aware service aggregation).

---

## 14. Automated Test Verification

The implemented codebase was subjected to automated verification using `pytest`:

```
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-9.1.1
collected 38 items

tests/test_composition.py::test_two_step_composition PASSED              [  2%]
tests/test_composition.py::test_three_step_composition PASSED            [  5%]
tests/test_composition.py::test_invalid_composition_fails PASSED         [  7%]
tests/test_composition.py::test_effect_override PASSED                   [ 10%]
tests/test_composition.py::test_operational_aggregation_exact PASSED     [ 13%]
tests/test_composition.py::test_composite_encoding_and_similarity PASSED [ 15%]
tests/test_encoding.py::test_state_vector_shape PASSED                   [ 18%]
tests/test_encoding.py::test_goal_vector_shape PASSED                    [ 21%]
tests/test_encoding.py::test_capability_vector_shape PASSED              [ 23%]
tests/test_encoding.py::test_boolean_polarity_and_contradiction PASSED   [ 26%]
tests/test_encoding.py::test_unmentioned_predicates_are_zero PASSED      [ 28%]
tests/test_encoding.py::test_categorical_one_hot_encoding PASSED         [ 31%]
tests/test_encoding.py::test_numerical_normalization_and_operator_direction PASSED [ 34%]
tests/test_encoding.py::test_input_output_encoding PASSED                [ 36%]
tests/test_encoding.py::test_operational_normalization_and_clamping PASSED [ 39%]
tests/test_encoding.py::test_deterministic_encoding PASSED               [ 42%]
tests/test_encoding.py::test_no_accidental_nan_or_inf PASSED             [ 44%]
tests/test_encoding.py::test_model_validation_rejects_invalid_values PASSED [ 47%]
tests/test_experiments.py::test_dataset_loads_correctly PASSED           [ 50%]
tests/test_experiments.py::test_required_capabilities_exist PASSED       [ 52%]
tests/test_experiments.py::test_required_goals_exist PASSED              [ 55%]
tests/test_experiments.py::test_experiment_1_compatibility_distinction PASSED [ 57%]
tests/test_experiments.py::test_experiment_2_composition_structure PASSED [ 60%]
tests/test_experiments.py::test_experiment_3_alternative_implementations PASSED [ 63%]
tests/test_experiments.py::test_experiment_4_goal_relevance_ranking PASSED [ 65%]
tests/test_experiments.py::test_experiment_5_operational_measurements PASSED [ 68%]
tests/test_experiments.py::test_experiments_are_deterministic PASSED     [ 71%]
tests/test_experiments.py::test_result_files_exist PASSED                [ 73%]
tests/test_metrics.py::test_cosine_similarity_edge_cases PASSED          [ 76%]
tests/test_metrics.py::test_similarity_weights_sum_to_one PASSED         [ 78%]
tests/test_metrics.py::test_similarity_is_symmetric PASSED               [ 81%]
tests/test_metrics.py::test_compatibility_create_order_to_make_payment_passes PASSED [ 84%]
tests/test_metrics.py::test_compatibility_create_order_to_cancel_cart_contradiction PASSED [ 86%]
tests/test_metrics.py::test_compatibility_is_directional PASSED          [ 89%]
tests/test_metrics.py::test_input_mismatch_fails_validation PASSED       [ 92%]
tests/test_metrics.py::test_goal_relevance_ranking PASSED                [ 94%]
tests/test_metrics.py::test_zero_vector_edge_cases PASSED                [ 97%]
tests/test_metrics.py::test_availability_gating PASSED                   [100%]

============================== 38 passed in 0.40s ==============================
```

These 38 tests provide automated verification that the implemented code matches the mathematical models and behavior reported in this document.
