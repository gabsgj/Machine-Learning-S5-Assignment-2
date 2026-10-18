# Design of a Vector Embedding for Capability Composition

**PCCST503 – Machine Learning | Assignment 2**  
*Formal Representations, Vector Space Compatibility, and Compositional Reasoning*

---

## 1. Project Title & Overview
This project designs, implements, and evaluates a **problem-specific, structured vector embedding system for formally specified capabilities, states, and goals**, compliant with the official PCCST503 Machine Learning Assignment 2 specification.

Instead of applying black-box pretrained NLP models (like BERT or generic Word2Vec), this project creates a deterministic, multi-subspace mathematical vector space $\phi_C: C \to \mathbb{R}^d$ that preserves functional identity, precondition-effect compatibility, input-output data dependencies, goal relevance, and operational quality attributes (cost, reliability, availability, latency, and risk).

---

## 2. Assignment Objective
To investigate whether formally specified application components:
- States $S = \{(x_1, v_1), \dots, (x_n, v_n)\}$
- Goals $G = \{g_1, \dots, g_m\}$
- Capabilities $C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)$

can be embedded in continuous vector space while preserving:
1. **Capability Identity** (distinguishing functionally unique operations)
2. **State Awareness** (capturing state conditions and state transitions $\Delta S$)
3. **Precondition-Effect Compatibility** ($E_i \implies P_j$)
4. **Input-Output Compatibility** ($O_i \to I_j$)
5. **Similarity vs Composability Separation** (distinguishing resemblance from composability)
6. **Capability Composition** ($C_{\text{comp}} = C_n \circ \dots \circ C_1$)
7. **Goal Relevance** (directional alignment with target goal gap $\Delta G$)
8. **Operational Properties Representation** (Cost, Reliability, Availability, Risk, Latency)

---

## 3. Concept Explanation
In classical planning, transition systems search for sequences of actions. In capability embedding, we focus on **representing the operations themselves**. 
- A capability is not just an arbitrary text string; it is a formal computational contract with inputs, outputs, preconditions, effects, resources, and quality metrics.
- Vector spaces allow geometric operations (dot products, projections, distance metrics) to reason about compatibility and composability at scale.

```
       Formal Capability Model                           Partitioned Vector Space
+------------------------------------+              +--------------------------------+
| Ti  : Type (API, DB, GUI, ...)     |              | v_type (9D One-Hot)            |
| Ii  : Inputs {name, type, req}     |              | v_input (17D Multi-Hot Entity) |
| Oi  : Outputs {name, type}         |              | v_output (17D Produced Entity) |
| Pi  : Preconditions (x == val)     | phi_C : C->R^d| v_pre (17D Signed Predicates)  |
| Ei  : Effects (x := val)           | ------------>| v_eff (17D Delta-S Deltas)     |
| Ri  : Resources {DB, Net, ...}     |              | v_res (8D Resource Vector)     |
| Ki  : Constraints                  |              | v_con (7D Domain Policies)     |
| Qi  : Quality (Cost, Time, Risk)   |              | v_ops (6D Bounded Normalized)  |
| Reli: Reliability in [0, 1]        |              | v_mech (10D Mechanism Vector)  |
| Ai  : Availability in [0, 1]       |              +--------------------------------+
| Mi  : Mechanism (REST, SQL, GUI)   |                      Total Dim = 108D
+------------------------------------+
```

---

## 4. Architecture & Project Structure
The repository is modular and structured as follows:

```
vector embedding system/
│
├── main.py              # Top-level orchestrator running all experiments & evaluations
├── models.py            # Formal data classes (State, Goal, Capability, CompositeCapability)
├── embedding.py         # Subspace vector encoders (phi_C, phi_S, phi_G, cosine similarity)
├── compatibility.py     # Multi-criteria logical & vector compatibility engine
├── composition.py       # Sequential capability composition & property aggregation
├── experiments.py       # Implementation of the 5 required assignment experiments
├── evaluation.py        # Benchmark suite evaluating the 9 assignment criteria
├── visualization.py     # Matplotlib publication figure generators
├── dataset.py           # E-commerce application domain & JSON/CSV dataset exporters
├── requirements.txt     # Minimal Python dependencies (numpy, pandas, matplotlib)
├── README.md            # Comprehensive project documentation
├── REPORT_CONTENT.md    # Formal 12-section technical report with real experimental data
│
├── data/
│   ├── capabilities.json    # Full JSON export of application schema and capabilities
│   └── capabilities.csv     # Tabular capability metadata
│
├── results/
│   ├── experiment_results.csv  # Detailed metric outputs from all 5 experiments
│   └── metrics_summary.csv     # Quantitative evaluation summary across 9 properties
│
└── plots/
    ├── capability_similarity.png   # Heatmap of pairwise capability cosine similarities
    ├── compatibility_matrix.png    # Dual-panel compatibility scores & boolean decisions
    ├── composition_comparison.png  # Subspace activation profile & composite alignment
    └── operational_attributes.png  # Multi-attribute Pareto trade-offs & sensitivity
```

---

## 5. Embedding Design & Subspace Partitioning
The capability embedding operator $\phi_C(C_i) \in \mathbb{R}^{108}$ concatenates 9 disjoint subspaces:

$$\phi_C(C_i) = \left[ \mathbf{v}_{\text{type}} \;\Big|\; \mathbf{v}_{\text{in}} \;\Big|\; \mathbf{v}_{\text{out}} \;\Big|\; \mathbf{v}_{\text{pre}} \;\Big|\; \mathbf{v}_{\text{eff}} \;\Big|\; \mathbf{v}_{\text{res}} \;\Big|\; \mathbf{v}_{\text{con}} \;\Big|\; \mathbf{v}_{\text{ops}} \;\Big|\; \mathbf{v}_{\text{mech}} \right]$$

1. **Type Subspace ($\mathbf{v}_{\text{type}} \in \mathbb{R}^9$)**: One-hot vector across formal types: `[API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE]`.
2. **Input Subspace ($\mathbf{v}_{\text{in}} \in \mathbb{R}^{17}$)**: Multi-hot vector for required ($1.0$) or optional ($0.5$) data parameters.
3. **Output Subspace ($\mathbf{v}_{\text{out}} \in \mathbb{R}^{17}$)**: Binary production vector for output data entities.
4. **Precondition Subspace ($\mathbf{v}_{\text{pre}} \in \mathbb{R}^{17}$)**: Signed condition vector aligned with state variables ($+1.0$ requires True, $-1.0$ requires False, $0.0$ unconstrained).
5. **Effect Subspace ($\mathbf{v}_{\text{eff}} \in \mathbb{R}^{17}$)**: State transformation delta $\Delta S$ ($+1.0$ sets True/active, $-1.0$ sets False/inactive, $0.0$ unaffected).
6. **Resource Subspace ($\mathbf{v}_{\text{res}} \in \mathbb{R}^8$)**: Normalized multi-hot vector across hardware/software dependencies (`Database`, `PaymentGateway`, `Network`, `EmailService`, `FileSystem`, `GPU`, `AuthToken`, `AudioDevice`).
7. **Constraint Subspace ($\mathbf{v}_{\text{con}} \in \mathbb{R}^7$)**: Binary encoding of domain policy restrictions.
8. **Operational Subspace ($\mathbf{v}_{\text{ops}} \in \mathbb{R}^6$)**: Continuous normalized quality attributes:
   $$\tilde{C}_{\text{money}} = \frac{\ln(1 + C_{\text{money}})}{\ln(1 + C_{\max})}, \quad \tilde{T} = \frac{T}{T_{\max}}, \quad \tilde{R}_{\text{cost}} = \frac{R}{R_{\max}}, \quad Risk \in [0, 1], \quad Rel \in [0, 1], \quad Avail \in [0, 1]$$
9. **Mechanism Subspace ($\mathbf{v}_{\text{mech}} \in \mathbb{R}^{10}$)**: One-hot encoding of execution protocol/pattern.

---

## 6. Mathematical Formulation

### Cosine Similarity:
$$\text{Sim}(\mathbf{x}, \mathbf{y}) = \frac{\mathbf{x} \cdot \mathbf{y}}{\|\mathbf{x}\|_2 \|\mathbf{y}\|_2 + \epsilon}$$
where $\epsilon = 10^{-12}$ ensures safe zero-vector handling.

### Compatibility Engine:
Compatibility is **not** cosine similarity. A separate multi-criteria score is computed:
$$\text{Compatibility}(C_i, C_j) = w_1 \cdot \text{Score}_{E \to P} + w_2 \cdot \text{Score}_{O \to I} + w_3 \cdot \text{Score}_{\text{state}}$$
where $w_1 = 0.50, w_2 = 0.30, w_3 = 0.20$ ($\sum w_k = 1.0$).
- $\text{Score}_{E \to P} = \frac{\sum \max(0, \mathbf{v}_{\text{eff}, i} \odot \mathbf{v}_{\text{pre}, j})}{\|\mathbf{v}_{\text{pre}, j}\|_1 + \epsilon}$ (penalized to $0.0$ if any direct contradiction occurs).
- $\text{Score}_{O \to I} = \frac{\mathbf{v}_{\text{out}, i} \cdot \mathbf{v}_{\text{in}, j}}{\|\mathbf{v}_{\text{in}, j}\|_1 + \epsilon}$.
- $\text{Score}_{\text{state}} = 1.0$ if $\text{Apply}(S, E_i) \models P_j$, else fraction of satisfied conditions.
- Boolean Decision: $\text{Compatible}(C_i \to C_j) = \text{True} \iff \text{No Contradictions} \land (S' \models P_j) \land (\text{Mandatory Inputs Satisfied})$.

### Goal Relevance:
$$\text{GoalRelevance}(C_i, G, S) = 0.60 \cdot \frac{|\{g \in G \mid E(C_i) \models g\}|}{|G_{\text{unmet}}|} + 0.40 \cdot \cos(\mathbf{v}_{\text{eff}}(C_i), \Delta \mathbf{g})$$
where $\Delta \mathbf{g} = \max(0, \phi_G(G) - \phi_S(S)) \odot \mathbf{1}_{G}$ isolates unmet goal predicates.

---

## 7. Composition Model ($C_{\text{comp}} = C_n \circ \dots \circ C_1$)
For a valid pipeline sequence $C_1 \to C_2 \to \dots \to C_n$:
1. **Total Monetary Cost**: $C_{\text{total}} = \sum_{k=1}^n C_{\text{money}, k}$
2. **Total Execution Time**: $T_{\text{total}} = \sum_{k=1}^n T_{\text{exec}, k}$
3. **Composite Reliability**: $Rel_{\text{total}} = \prod_{k=1}^n Rel_k$ (Independent Bernoulli trials)
4. **Composite Availability**: $Avail_{\text{total}} = \prod_{k=1}^n Avail_k$ (Serial system availability)
5. **Combined Risk**: $Risk_{\text{total}} = 1 - \prod_{k=1}^n (1 - Risk_k)$
6. **Aggregate Preconditions**: Initial state requirements needed across the chain not fulfilled by intermediate effects.
7. **Net Effects**: State delta resulting from sequential execution $S_0 \xrightarrow{E_1} S_1 \dots \xrightarrow{E_n} S_n$.
8. **Composite Embedding**: Deterministically produced by encoding the synthesized `CompositeCapability`.

---

## 8. Dataset Description
The application domain models an **E-Commerce Order Fulfillment & Business Intelligence System**:
- Initial State $S_I$: User authenticated as Customer, Cart exists with 3 items unlocked, Order does not exist, Payment not started, Inventory available.
- Goal Specification $G$: `Order.exists == True`, `Payment.status == SUCCESS`, `Notification.sent == True`.
- Registered Capabilities:
  - `CreateOrder` (Function)
  - `MakePayment` (REST API)
  - `SendNotification` (Message Queue)
  - `CancelCart` (Function - Incompatible post-order)
  - `CheckInventory` (Microservice)
  - `GenerateInvoice` (File I/O)
  - `CreateOrderAPI`, `CreateOrderDatabase`, `CreateOrderGUI` (Alternative implementations)
  - `MakePayment_Economy`, `MakePayment_Enterprise`, `MakePayment_HighCost_LowRel` (Operational variants)
  - `UpdateProfile` (GUI - Irrelevant to purchase goal)
  - `GenerateReport` (Computation/GPU - Irrelevant to purchase goal)
  - `PlayMusic` (Audio Service - Completely irrelevant)

---

## 9. Summary of the 5 Required Experiments

| Exp # | Experiment Title | Tested Entities | Key Findings |
|---|---|---|---|
| **Exp 1** | **Capability Compatibility** | `CreateOrder` $\to$ `MakePayment` vs `CreateOrder` $\to$ `CancelCart` | $C_1 \to C_2$ is **Compatible (Score=0.7000)**. $C_1 \to C_3$ is **Incompatible (Score=0.0000)** due to 2 direct contradictions (`Order.exists` & `Cart.locked`). |
| **Exp 2** | **Capability Composition** | `CompletePurchase` = `SendNotification` $\circ$ `MakePayment` $\circ$ `CreateOrder` | Constructed valid composite: Cost=\$0.115, Rel=0.9555, Avail=0.990. Composite vector aligns with component sum vector ($\cos=0.7396$). |
| **Exp 3** | **Alternative Implementations** | `CreateOrderAPI` vs `CreateOrderDatabase` vs `CreateOrderGUI` | Functional Subspace Similarity is **1.0000 (100% equivalence)** while overall embedding similarity is $\approx 0.76 - 0.79$, preserving mechanism identity. |
| **Exp 4** | **Irrelevant Capabilities** | Relevant (`CreateOrder`, `MakePayment`, `SendNotification`) vs Irrelevant (`UpdateProfile`, `GenerateReport`, `PlayMusic`) | Relevant capabilities achieve goal relevance $0.33 - 0.43$. Irrelevant capabilities achieve **0.0000**. Perfect discrimination gap = $0.3684$. |
| **Exp 5** | **Operational Attributes** | Baseline `MakePayment` vs `Economy` vs `Enterprise` vs `HighCost_LowRel` | Functional invariant preserved ($\cos=1.0000$) while operational subspace Euclidean distance cleanly diverges ($0.16$ to $0.57$). |

---

## 10. Installation & Virtual Environment Setup

### Prerequisites
- Python 3.9+ (Python 3.10, 3.11, 3.12, 3.13, 3.14 supported)
- Standard tools (`pip`, `venv`)

### Windows Setup
```powershell
# 1. Clone or navigate to the repository directory
cd "c:\Users\govin\OneDrive\Desktop\vector embedding system"

# 2. Create Python virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
```

### Linux / macOS Setup
```bash
# 1. Navigate to directory
cd "/path/to/vector embedding system"

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 11. How to Run

Execute the complete experimental and evaluation pipeline:
```bash
python main.py
```
This single command executes all 5 experiments, runs the 9-property evaluation suite, saves CSV data to `results/`, and generates all 4 plots in `plots/`.

---

## 12. Expected Terminal Output
When executing `python main.py`, you will see:
```text
================================================================================
     PCCST503 - MACHINE LEARNING ASSIGNMENT 2: CAPABILITY EMBEDDING
        Formal Vector Embedding Design for Capability Composition
================================================================================

[1/5] Initializing Formal Application Model and Capabilities...
      - Initial State (SI): 14 variables initialized
      - Goal Specification (G): 3 target conditions
      - Capabilities Catalog (C): 15 formal capabilities registered
      - Dataset exported: data/capabilities.json & data/capabilities.csv

[2/5] Setting up Embedding, Compatibility, and Composition Engines...
      - Total Embedding Dimension: 108 features (9 Subspaces)

[3/5] Executing the 5 Required Experiments...
----------------------------------------------------------------------
EXPERIMENT 1: CAPABILITY COMPATIBILITY
----------------------------------------------------------------------
[*] Sequence 1: CreateOrder -> MakePayment: COMPATIBLE (Score: 0.7000)
[*] Sequence 2: CreateOrder -> CancelCart:  INCOMPATIBLE (Score: 0.0000)

----------------------------------------------------------------------
EXPERIMENT 2: CAPABILITY COMPOSITION
----------------------------------------------------------------------
[*] Pipeline Constructed: CreateOrder -> MakePayment -> SendNotification
    - Composite Name: CompletePurchase (Cost: $0.1150, Rel: 0.9555, Avail: 0.9900)

----------------------------------------------------------------------
EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS
----------------------------------------------------------------------
[*] Key Finding: Functional similarity is 1.0000, while overall embedding captures distinct mechanisms (API vs DB vs GUI).

----------------------------------------------------------------------
EXPERIMENT 4: IRRELEVANT CAPABILITIES
----------------------------------------------------------------------
Goal Relevance: Relevant (0.33 - 0.43) vs Irrelevant (0.0000)

----------------------------------------------------------------------
EXPERIMENT 5: OPERATIONAL ATTRIBUTES
----------------------------------------------------------------------
Operational divergence measured without altering functional identity.

======================================================================
  ALL EXPERIMENTS AND EVALUATIONS COMPLETED SUCCESSFULLY!
======================================================================
```

---

## 13. Generated Files & Artifacts
- `data/capabilities.json`: Complete serialized domain specification.
- `data/capabilities.csv`: Summary metadata for all capabilities.
- `results/experiment_results.csv`: Row-level outputs for all experiment trials.
- `results/metrics_summary.csv`: Summary of all 9 evaluation properties.
- `plots/capability_similarity.png`: Heatmap of pairwise capability cosine similarities.
- `plots/compatibility_matrix.png`: Dual heatmap comparing scores and boolean decisions.
- `plots/composition_comparison.png`: Subspace bar chart and semantic alignment.
- `plots/operational_attributes.png`: Pareto frontier, latency, and operational sensitivity plots.

---

## 14. Limitations
1. **Sequential Composition Assumption**: The current composition engine assumes sequential execution pipelines ($C_n \circ \dots \circ C_1$). Parallel (fork-join) and conditional branching composition require hypergraph or DAG vector aggregation operators.
2. **Deterministic Schema**: Feature mapping uses a structured domain schema. Expanding to open-world cross-domain capabilities requires schema ontology alignment or semantic hash encoders.
3. **Independent Failure Model**: Reliability aggregation assumes independent component failures ($Rel = \prod Rel_k$). In distributed systems with shared network/database failures, joint probability copulas would be needed.

---

## 15. Future Improvements
1. **Hypergraph Embedding Operators**: Extend vector algebra to cyclic and parallel DAG workflow compositions.
2. **Learned Metric Weights**: Train subspace weights ($w_1, w_2, w_3$) using contrastive triplet loss over ground-truth workflow traces.
3. **Dynamic Resource Scheduling**: Incorporate time-varying resource availability vectors $A_i(t)$ with temporal sine/cosine embeddings.

---

## 16. Viva Preparation Questions & Answers

**Q1: Why did you design a structured embedding instead of using Word2Vec or BERT?**  
*Answer:* Word2Vec and BERT capture linguistic co-occurrence and semantic word associations in natural text. Capabilities, however, are formal engineering artifacts governed by logical preconditions, postconditions, data types, and quality attributes. A pretrained NLP model cannot guarantee that contradictory postconditions (e.g., setting a variable to True while requiring False) produce a zero compatibility score. Our structured embedding explicitly encodes these contracts into mathematical subspaces.

**Q2: What is the difference between similarity and composability?**  
*Answer:* Similarity measures whether two capabilities share similar features (e.g. `CreateOrderAPI` and `CreateOrderDatabase` have functional similarity 1.0, but executing one after another makes no sense). Composability is an asymmetric relationship where the effects and outputs of $C_i$ satisfy the preconditions and inputs of $C_j$ ($C_i \to C_j$).

**Q3: How is a composite capability vector constructed?**  
*Answer:* We simulate sequential state progression to find net effects ($S_0 \xrightarrow{E_1} S_1 \dots \xrightarrow{E_n} S_n$), aggregate unresolved initial preconditions, chain data outputs to inputs, aggregate operational costs ($\sum$), and compute reliability ($\prod$). The resulting `CompositeCapability` is then mapped into vector space via $\phi_C$.

**Q4: How do you prevent monetary cost or latency from dominating the vector?**  
*Answer:* We apply bounded nonlinear normalization (logarithmic scaling $\frac{\ln(1+c)}{\ln(1+c_{\max})}$ for cost and bounded linear scaling for latency) so every operational feature strictly occupies $[0, 1]$.

**Q5: How does goal relevance work in vector space?**  
*Answer:* We compute the goal gap vector $\Delta \mathbf{g} = \max(0, \phi_G(G) - \phi_S(S)) \odot \mathbf{1}_G$ representing missing target conditions, and project the capability effect vector $\mathbf{v}_{\text{eff}}(C_i)$ onto $\Delta \mathbf{g}$. If a capability does not touch any goal condition, its projection is strictly 0.0.
