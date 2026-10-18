# Design of a Vector Embedding for Capability Composition
## Formal Representations, Compatibility, and Compositional Reasoning
### PCCST503 – Assignment 2

**Submitted by:** Ayush Raj — TCR24CS018  
**Date:** October 2026  
**Repository & Codebase:** `capembed`  

---

## Abstract
In computational software engineering and autonomous systems, services and operations—termed **capabilities**—interact according to strict *functional* and *state-transformative* contracts rather than lexical or semantic co-occurrence. Crucially, **functional resemblance and composability are not the same**: two alternative payment capabilities (e.g., Stripe and PayPal) are functionally nearly identical yet cannot compose together, while an order creation capability and a payment processing capability share virtually no semantic similarity yet compose seamlessly.

This report presents the mathematical design, software implementation (`capembed`), and empirical evaluation of a **Structured Dual-Subspace Partitioned Tensor Embedding** for formally specified states, goals, and executable capabilities. The vector representation supports closed-form algebraic composition operators ($\mathbf{c}_{12} = \mathbf{c}_2 \odot \mathbf{c}_1$), directional compatibility evaluation ($\Gamma_{PE}, \Gamma_{IO}$), multi-attribute Quality of Service (QoS) preservation, and goal-relevance projection. The framework is empirically verified across three distinct application domains (E-Commerce, Cloud DevOps CI/CD, and Healthcare Clinical Care), demonstrating strict associativity, non-commutativity, zero-leakage precondition absorption, and exact discrimination of composable chains versus conflicting operations.

---

## 1. Problem Definition

In modern distributed architectures, service meshes, and automated task execution pipelines, systems are described by formal transitions over application states. An application environment is modeled as a 6-tuple:
$$\mathcal{A} = (\mathcal{S}, \mathcal{C}, S_I, \mathcal{G}, \mathcal{R}, \mathcal{K})$$
where:
- $\mathcal{S}$ is the state space of the application, where any state $S \in \mathcal{S}$ is an assignment of values to state variables: $S = \{(x_1, v_1), (x_2, v_2), \dots, (x_n, v_n)\}$.
- $\mathcal{C} = \{C_1, C_2, \dots, C_k\}$ is the universe of available atomic and composite executable capabilities.
- $S_I \in \mathcal{S}$ represents the initial condition of the system.
- $\mathcal{G} = \{g_1, g_2, \dots, g_m\}$ is the target goal specification; a state $S$ satisfies the goal ($S \models \mathcal{G}$) when all specified goal constraints hold.
- $\mathcal{R}$ denotes the set of shared resources (e.g., databases, network interfaces, payment gateways, compute clusters).
- $\mathcal{K}$ represents global constraints and organizational policies (e.g., transaction limits, role-based access controls).

Each capability $C_i \in \mathcal{C}$ is formally defined as an 11-tuple:
$$C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)$$
capturing its operational type $T_i \in \{\text{API}, \text{DATABASE}, \text{GUI}, \text{EVENT}, \text{FUNCTION}, \text{FILE}, \text{COMPUTATION}, \text{MESSAGE}, \text{SERVICE}\}$, data contracts ($I_i, O_i$), logical state contracts ($P_i, E_i$), constraints $K_i$, resource demands $R_i$, operational QoS attributes $Q_i$, reliability $Rel_i \in [0, 1]$, availability $A_i \in \{0, 1\}$, and execution mechanism $M_i$.

### The Core Research Question
> *How can formally specified states, goals, and executable capabilities be represented in a continuous vector space such that the representation preserves the algebraic, logical, and operational relationships required for capability compatibility, composition, and the construction of complex application functionality?*

---

## 2. Design Requirements

To preserve the semantics of capability reasoning in continuous vector spaces, the embedding system must fulfill eight mandatory structural properties:

1. **Capability Identity**: Distinct capabilities must map to distinguishable points in the embedding space ($\|\phi_C(C_a) - \phi_C(C_b)\|_2 > 0$ for $a \neq b$).
2. **State Awareness & Applicability**: The representation must encode whether a capability is applicable to a given system state ($S \models P_i$).
3. **Precondition–Effect Compatibility**: The embedding must evaluate whether $E_i \implies P_j$, enabling directional transition $C_i \to C_j$, while penalizing contradictions.
4. **Input–Output Compatibility**: The embedding must determine whether the produced outputs $O_i$ fulfill the required input signatures $I_j$ ($O_i \supseteq I_j$).
5. **Decoupling of Similarity and Composability**: The system must explicitly separate *functional similarity* ($\text{Sim}(C_a, C_b)$, symmetric) from *composability* ($\text{Comp}(C_i, C_j)$, asymmetric and directional).
6. **Closed Algebraic Composition Operator**: The space must support an operator $\odot$ such that $\phi_C(C_j \circ C_i) = \phi_C(C_j) \odot \phi_C(C_i)$, preserving condition absorption and associativity.
7. **Goal Relevance**: The embedding must measure how effectively a capability or composite chain moves the system toward goal $\mathcal{G}$.
8. **Operational Profile Awareness**: Additive costs (latency, money, resource units), multiplicative failure rates (reliability), and boolean availability must be preserved without polluting logical compatibility.

---

## 3. Related Embedding Approaches and Their Limitations

| Approach | Representative Models | Strengths | Fundamental Flaws for Capability Composition |
| :--- | :--- | :--- | :--- |
| **Distributional Text & Token Embeddings** | GloVe, FastText, Dense Sentence Embeddings | Dense representations; vector offsets encode lexical or textual similarity. | **Conflates similarity with composability.** Substitutable operations (e.g., Stripe vs. PayPal) cluster together ($\cos(\theta) \to 1$), falsely predicting they should compose, while complementary operations (Order $\to$ Pay) have low cosine similarity. Symmetric distance metrics fail to capture directional execution. |
| **Knowledge Graph Embeddings** | TransE (Bordes et al., 2013), ComplEx, RotatE | Models relations as geometric translations ($\mathbf{h} + \mathbf{r} \approx \mathbf{t}$). | Designed for static relational triples, not multi-variable state transformations with conditional applicability, precondition absorption, or dynamic QoS attributes. |
| **Action Embeddings in RL & Planning** | Action-space embeddings (Dulac-Arnold et al., 2015), Plan-Net | Encodes discrete actions in continuous control. | Relies on opaque learned latent spaces without formal safety verification, exact precondition checking, or deterministic I/O dataflow contracts. |
| **Semantic Web Service Descriptions** | OWL-S, WSDL, OpenAPI / Swagger | Rigorous formal specifications of preconditions, effects, inputs, outputs. | Purely symbolic; lacks continuous algebraic operators for fast nearest-neighbor retrieval, continuous relaxation, or vector space composition. |

### Conclusion on Existing Methods
Merely applying standard unstructured dense embeddings or general textual representations fails because capability interaction is fundamentally asymmetric, contract-driven, and multi-faceted. A domain-tailored, partitioned structured tensor space is essential.

---

## 4. Proposed Representation: The Structured Dual-Subspace Partitioned Tensor

We formulate a partitioned vector space $\mathcal{V} \cong \mathbb{R}^D$ where functional contracts, execution mechanics, resource locks, and operational QoS metrics occupy dedicated, semantically orthogonal subspaces:

$$
\phi_C(C) = \left[ \mathbf{v}_{\text{pre}}, \, \mathbf{m}_{\text{pre}}, \, \mathbf{v}_{\text{eff}}, \, \mathbf{m}_{\text{eff}}, \, \mathbf{v}_{\text{in}}, \, \mathbf{v}_{\text{out}}, \, \mathbf{v}_{\text{type}}, \, \mathbf{v}_{\text{mech}}, \, \mathbf{v}_{\text{res}}, \, \mathbf{v}_{\text{ops}} \right]^T \in \mathbb{R}^D
$$

### Subspace Dimensionality Decomposition
Given domain schema $\mathcal{D} = (d_{\text{state}}, d_{\text{io}}, d_{\text{type}}, d_{\text{mech}}, d_{\text{res}}, d_{\text{ops}})$:
- **Preconditions**: Target values $\mathbf{v}_{\text{pre}} \in \mathbb{R}^{d_{\text{state}}}$ and indicator mask $\mathbf{m}_{\text{pre}} \in \{0, 1\}^{d_{\text{state}}}$.
- **Effects**: Target values $\mathbf{v}_{\text{eff}} \in \mathbb{R}^{d_{\text{state}}}$ and modification mask $\mathbf{m}_{\text{eff}} \in \{0, 1\}^{d_{\text{state}}}$.
- **Dataflow (I/O)**: Input schema $\mathbf{v}_{\text{in}} \in \mathbb{R}^{d_{\text{io}}}$ and output schema $\mathbf{v}_{\text{out}} \in \mathbb{R}^{d_{\text{io}}}$.
- **Execution Modality**: Capability type one-hot $\mathbf{v}_{\text{type}} \in \{0, 1\}^{d_{\text{type}}}$ and mechanism signature $\mathbf{v}_{\text{mech}} \in \mathbb{R}^{d_{\text{mech}}}$.
- **Resource Footprint**: Multi-hot resource bitmask $\mathbf{v}_{\text{res}} \in \{0, 1\}^{d_{\text{res}}}$.
- **Operational Profile**: Real vector $\mathbf{v}_{\text{ops}} \in \mathbb{R}^7$.

Total vector dimension:
$$D = 4 \cdot d_{\text{state}} + 2 \cdot d_{\text{io}} + d_{\text{type}} + d_{\text{mech}} + d_{\text{res}} + 7$$

For our E-Commerce benchmark ($d_{\text{state}}=14, d_{\text{io}}=15, d_{\text{type}}=9, d_{\text{mech}}=8, d_{\text{res}}=7, d_{\text{ops}}=7$), the representation has dimension $D = 117$.

---

## 5. Mathematical Formulation

### 5.1 State and Goal Embeddings
Let variable values be mapped to scalar coordinates through canonical quantization $\psi: \mathcal{V}_{\text{val}} \to [-1, 1]$:
- Boolean: $\psi(\text{True}) = +1.0$, $\psi(\text{False}) = -1.0$.
- Categorical: Deterministic cryptographic hash projection $\psi(s) = \frac{\text{hash}(s) \pmod{1000}}{500} - 1.0$.
- Numeric: Min-max scaled normalization.

**State Embedding $\phi_S(S) \in \mathbb{R}^{2 \cdot d_{\text{state}}}$**:
$$\phi_S(S) = [\mathbf{s}_{\text{val}}, \, \mathbf{s}_{\text{mask}}]^T$$
where $s_{\text{val}}[k] = \psi(S(x_k))$ and $s_{\text{mask}}[k] = \mathbf{1}[x_k \in \text{dom}(S)]$.

**Goal Embedding $\phi_G(G) \in \mathbb{R}^{2 \cdot d_{\text{state}}}$**:
$$\phi_G(G) = [\mathbf{g}_{\text{val}}, \, \mathbf{g}_{\text{mask}}]^T$$
where $g_{\text{val}}[k] = \psi(G(x_k))$ and $g_{\text{mask}}[k] = \mathbf{1}[x_k \in \text{conditions}(G)]$.

### 5.2 Directional Precondition–Effect Compatibility (Gamma_PE)
For transition $C_i \to C_j$, does $C_i$'s effect satisfy $C_j$'s preconditions?
Let the overlapping mask be $\mathbf{m}_{ij}^{\text{overlap}} = \mathbf{m}_{\text{eff}, i} \odot \mathbf{m}_{\text{pre}, j}$.
$$\Gamma_{PE}(C_i, C_j) = \frac{\sum_{k=1}^{d_{\text{state}}} m_{ij}^{\text{overlap}}[k] \cdot \text{sgn}\left(v_{\text{eff}, i}[k] \cdot v_{\text{pre}, j}[k]\right)}{\sum_{k=1}^{d_{\text{state}}} m_{ij}^{\text{overlap}}[k] + \epsilon}$$
- $\Gamma_{PE} = +1.0$: Complete agreement on all overlapping state variables.
- $\Gamma_{PE} = -1.0$: Severe contradiction (e.g., $E_i$ produces $X=\text{True}$ while $P_j$ requires $X=\text{False}$).
- If $\sum m_{ij}^{\text{overlap}} = 0$, $\Gamma_{PE} = 1.0$ if $\sum \mathbf{m}_{\text{pre}, j} = 0$, else $0.0$ (neutral; preconditions must be met by prior state).

### 5.3 Input–Output Dataflow Compatibility (Gamma_IO)
$$\Gamma_{IO}(C_i, C_j) = \frac{\sum_{k=1}^{d_{\text{io}}} \min\left(v_{\text{out}, i}[k], \, v_{\text{in}, j}[k]\right)}{\sum_{k=1}^{d_{\text{io}}} v_{\text{in}, j}[k] + \epsilon}$$
If $C_j$ requires no inputs ($\sum v_{\text{in}, j} = 0$), $\Gamma_{IO} = 1.0$.

### 5.4 Total Directional Composability Score (Comp)
$$\text{Comp}(C_i, C_j) = \begin{cases}
\Gamma_{PE}(C_i, C_j) & \text{if } \Gamma_{PE}(C_i, C_j) < 0 \\
w_{PE} \cdot \Gamma_{PE}(C_i, C_j) + w_{IO} \cdot \Gamma_{IO}(C_i, C_j) & \text{if } \Gamma_{PE}(C_i, C_j) \ge 0
\end{cases}$$
Default weights: $w_{PE} = 0.6, w_{IO} = 0.4$. Note that $\text{Comp}(C_i, C_j) \neq \text{Comp}(C_j, C_i)$ (strictly asymmetric).

### 5.5 Functional vs. Implementation Similarity
- **Functional Similarity**:
  $$\text{Sim}_{\text{func}}(C_i, C_j) = \cos(\mathbf{v}_{\text{func}, i}, \mathbf{v}_{\text{func}, j})$$
  where $\mathbf{v}_{\text{func}} = [\mathbf{v}_{\text{pre}}, \mathbf{m}_{\text{pre}}, \mathbf{v}_{\text{eff}}, \mathbf{m}_{\text{eff}}, \mathbf{v}_{\text{in}}, \mathbf{v}_{\text{out}}]^T$.
- **Implementation Similarity**:
  $$\text{Sim}_{\text{impl}}(C_i, C_j) = \cos([\mathbf{v}_{\text{type}, i}, \mathbf{v}_{\text{mech}, i}], [\mathbf{v}_{\text{type}, j}, \mathbf{v}_{\text{mech}, j}])$$

### 5.6 Goal Relevance (Rel)
$$\text{Rel}(C_i, \mathcal{G}) = \frac{\sum_{k=1}^{d_{\text{state}}} g_{\text{mask}}[k] \cdot m_{\text{eff}, i}[k] \cdot \text{sgn}\left(v_{\text{eff}, i}[k] \cdot g_{\text{val}}[k]\right)}{\sum_{k=1}^{d_{\text{state}}} g_{\text{mask}}[k] + \epsilon}$$

### 5.7 Operational QoS Subspace & Log-Reliability Additivity
The operational subvector is encoded as:
$$\mathbf{v}_{\text{ops}} = \left[ \tfrac{1}{10} \ln(1 + C_{\text{time}}), \, C_{\text{money}}, \, C_{\text{resource}}, \, C_{\text{risk}}, \, C_{\text{energy}}, \, -\ln(Rel), \, \text{Availability} \right]^T$$

**Mathematical Theorem (Additivity of Reliability in Vector Space):**
For independent failure rates, the reliability of a sequential chain $C_{1..k} = C_k \circ \dots \circ C_1$ satisfies $Rel_{1..k} = \prod_{i=1}^k Rel_i$. Taking negative natural logarithms:
$$-\ln(Rel_{1..k}) = -\ln\left(\prod_{i=1}^k Rel_i\right) = \sum_{i=1}^k -\ln(Rel_i)$$
Hence, in the 6th dimension of $\mathbf{v}_{\text{ops}}$, sequential composition is strictly linear and additive!

---

## 6. Capability Composition Model

For sequential composition $C_{12} = C_2 \circ C_1$ ($C_1$ followed by $C_2$):

### 6.1 Algebraic Vector Composition Rules
1. **Preconditions**:
   $$\mathbf{m}_{\text{pre}, 12} = \mathbf{m}_{\text{pre}, 1} + \mathbf{m}_{\text{pre}, 2} \odot (\mathbf{1} - \mathbf{m}_{\text{eff}, 1})$$
   $$\mathbf{v}_{\text{pre}, 12} = \mathbf{v}_{\text{pre}, 1} \odot \mathbf{m}_{\text{pre}, 1} + \mathbf{v}_{\text{pre}, 2} \odot \mathbf{m}_{\text{pre}, 2} \odot (\mathbf{1} - \mathbf{m}_{\text{eff}, 1})$$
   *Semantic intuition*: Preconditions of $C_2$ that are produced by $C_1$'s effects ($\mathbf{m}_{\text{eff}, 1}=1$) are absorbed internally and cleared from the composite interface.
2. **Effects**:
   $$\mathbf{m}_{\text{eff}, 12} = \mathbf{m}_{\text{eff}, 1} \lor \mathbf{m}_{\text{eff}, 2} = \mathbf{m}_{\text{eff}, 1} + \mathbf{m}_{\text{eff}, 2} - \mathbf{m}_{\text{eff}, 1} \odot \mathbf{m}_{\text{eff}, 2}$$
   $$\mathbf{v}_{\text{eff}, 12} = \mathbf{v}_{\text{eff}, 2} \odot \mathbf{m}_{\text{eff}, 2} + \mathbf{v}_{\text{eff}, 1} \odot \mathbf{m}_{\text{eff}, 1} \odot (\mathbf{1} - \mathbf{m}_{\text{eff}, 2})$$
   *Semantic intuition*: Effects of $C_2$ override effects of $C_1$ where both modify the same variable; non-overridden effects of $C_1$ persist.
3. **Dataflow Inputs**:
   $$\mathbf{v}_{\text{in}, 12} = \max\left(\mathbf{v}_{\text{in}, 1}, \, \max(0, \, \mathbf{v}_{\text{in}, 2} - \mathbf{v}_{\text{out}, 1})\right)$$
4. **Dataflow Outputs**:
   $$\mathbf{v}_{\text{out}, 12} = \max(\mathbf{v}_{\text{out}, 1}, \, \mathbf{v}_{\text{out}, 2})$$
5. **Resources**:
   $$\mathbf{v}_{\text{res}, 12} = \min(\mathbf{1}, \, \mathbf{v}_{\text{res}, 1} + \mathbf{v}_{\text{res}, 2})$$
6. **Mechanisms**:
   $$\mathbf{v}_{\text{mech}, 12} = \max(\mathbf{v}_{\text{mech}, 1}, \, \mathbf{v}_{\text{mech}, 2})$$
   Using element-wise maximum guarantees strict algebraic associativity: $\max(\max(\mathbf{a}, \mathbf{b}), \mathbf{c}) = \max(\mathbf{a}, \max(\mathbf{b}, \mathbf{c}))$.
7. **Operational Attributes**:
   - $v_{\text{ops}, 12}[0] = \frac{1}{10} \ln(1 + \Delta t_1 + \Delta t_2)$
   - $v_{\text{ops}, 12}[1] = v_{\text{ops}, 1}[1] + v_{\text{ops}, 2}[1]$ (monetary cost sum)
   - $v_{\text{ops}, 12}[3] = 1 - (1 - v_{\text{ops}, 1}[3])(1 - v_{\text{ops}, 2}[3])$ (risk combination)
   - $v_{\text{ops}, 12}[5] = v_{\text{ops}, 1}[5] + v_{\text{ops}, 2}[5]$ (additive log-reliability)
   - $v_{\text{ops}, 12}[6] = \min(v_{\text{ops}, 1}[6], v_{\text{ops}, 2}[6])$ (availability conjunction)

### 6.2 Formal Properties of the Composition Operator
- **Non-Commutativity**: In general, $C_2 \circ C_1 \neq C_1 \circ C_2$, as execution order determines which preconditions are checked against the initial environment.
- **Associativity**: $((C_3 \circ C_2) \circ C_1) \equiv (C_3 \circ (C_2 \circ C_1))$. Proven both symbolically and in vector space ($\| \mathbf{v}_{\text{left}} - \mathbf{v}_{\text{right}} \|_2 = 0.00\text{e}+00$).

---

## 7. Implementation

The system is implemented as the `capembed` Python package:
```
capembed/
├── core.py         # Capability, State, Goal, Input/Output, QoS definitions
├── encoder.py      # Vector space projection into R^D
├── composition.py  # Symbolic and direct vector-space composition engines
├── metrics.py      # Gamma_PE, Gamma_IO, Composability, Sim_func, Sim_impl, Relevance
└── pipeline.py     # Unified high-level API: encode(), compose(), similarity(), compatibility()
```

### High-Level API Conformance (Deliverable 2)
The five functions required by Section 9 of the assignment are implemented directly:
1. `encode(state) -> EncodedState`
2. `encode(goal) -> EncodedGoal`
3. `encode(capability) -> EncodedCapability`
4. `compose(capabilities) -> EncodedCapability`
5. `similarity(x, y, mode="functional") -> float`

---

## 8. Experimental Methodology

To rigorously validate the embedding, experiments were performed across three diverse application domains:
1. **E-Commerce Order-to-Fulfillment**: 10 capabilities covering checkout, payment processing, inventory reservation, customer notification, order cancellation, and profile updates.
2. **Cloud DevOps CI/CD Pipeline**: 9 capabilities modeling git checkout, code linting, unit testing, Docker image packaging, container registry push, Kubernetes cluster deployment, and smoke testing.
3. **Healthcare Clinical Care Pathway**: 8 capabilities modeling identity validation, vital triage, lab blood panels, medical diagnosis, electronic prescription, pharmacy dispensing, and insurance billing.

---

## 9. Results

### Experiment 1: Capability Compatibility
Evaluating C1 -> C2 (CreateOrder -> MakePayment) versus C1 -> C3 (CreateOrder -> CancelCart):

| Transition | Gamma_PE | Gamma_IO | Composability (Comp) | Functional Similarity (Sim_func) | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **C1 -> C2** (CreateOrder -> MakePayment) | **+1.0000** | **+1.0000** | **+1.0000** | 0.0821 | **Compatible Chain** |
| **C1 -> C3** (CreateOrder -> CancelCart) | **-1.0000** | 0.0000 | **-1.0000** | 0.3162 | **Contradiction Conflict** |
| **C2 -> C1** (MakePayment -> CreateOrder) | 0.0000 | 0.0000 | **0.0000** | 0.0821 | **Asymmetric Directional Rejection** |

![Figure 1: Directional Composability vs. Symmetric Functional Similarity](file:///home/ayush/Ayush/assignment2/figures/fig1_composability_vs_similarity.png)

### Experiment 2: Capability Composition
For chain C1 -> C2 -> C5 (CreateOrder -> MakePayment -> SendNotification):
- **Associativity Distance**: `|| ((C5 o C2) o C1) - (C5 o (C2 o C1)) ||_2 = 0.000000e+00`.
- **Precondition Absorption**: Original preconditions required `Order.exists=True` (for C2) and `Payment.status=SUCCESS` (for C5). In the composite capability C125, both are internalized and absorbed. The external precondition requires only `{ User.authenticated: True, Cart.exists: True }`.
- **State Transition Parity**:
  $$\text{Apply}(S_0, C_{125}) \equiv \text{Apply}\left(\text{Apply}\left(\text{Apply}(S_0, C_1), C_2\right), C_5\right)$$
  Variable states after execution are 100% bitwise identical.

### Experiment 3: Alternative Implementations
Comparing three implementations of `CreateOrder`: API (POST /orders), Database (INSERT orders), and GUI (CLICK submit_button):

| Metric | API vs. DB | API vs. GUI | DB vs. GUI |
| :--- | :---: | :---: | :---: |
| **Functional Similarity (Sim_func)** | **1.0000** | **1.0000** | **1.0000** |
| **Implementation Similarity (Sim_impl)** | 0.0814 | 0.4863 | 0.0381 |
| **Full Vector Euclidean Distance (||phi_A - phi_B||_2)** | **2.3961** | **2.0933** | **2.9818** |
| **Execution Latency** | 85.0 ms vs 15.0 ms | 85.0 ms vs 650.0 ms | 15.0 ms vs 650.0 ms |

![Figure 2: Functional Equivalence vs. Implementation Distinguishability](file:///home/ayush/Ayush/assignment2/figures/fig2_alternatives_comparison.png)

### Experiment 4: Irrelevant Capabilities Screening
Goal: `Order.exists=True`, `Payment.status=SUCCESS`, `Inventory.reserved=True`, `Notification.sent=True`.

| Capability | Category | Goal Relevance (Rel) | System Action |
| :--- | :--- | :---: | :--- |
| **CreateOrder** | Contributing Core | **+0.2500** | Included (Rank 1) |
| **MakePayment** | Contributing Core | **+0.2500** | Included (Rank 2) |
| **ReserveInventory** | Contributing Core | **+0.2500** | Included (Rank 3) |
| **SendNotification** | Contributing Core | **+0.2500** | Included (Rank 4) |
| **CancelCart** | Contradictory | **0.0000** | Filtered Out |
| **UpdateUserProfile** | Irrelevant | **0.0000** | Filtered Out |
| **SubmitProductReview** | Irrelevant | **0.0000** | Filtered Out |

*Margin of Separation*: +0.2500. All non-contributing capabilities are cleanly separated from useful ones.

![Figure 3: Capability Discrimination and Goal Relevance Ranking](file:///home/ayush/Ayush/assignment2/figures/fig3_goal_relevance.png)

### Experiment 5: Operational Attributes & QoS Preservation

| Chain Length (k) | Multiplicative Reliability (Product Rel_i) | Vector -ln(Rel) Dimension | Theoretical Value | Absolute Error |
| :---: | :---: | :---: | :---: | :---: |
| 1 | 0.99500 | 0.005013 | 0.005013 | 0.00e+00 |
| 2 | 0.98505 | 0.015063 | 0.015063 | 5.20e-18 |
| 3 | 0.98308 | 0.017065 | 0.017065 | 2.43e-17 |
| 4 | 0.96833 | 0.032179 | 0.032179 | 0.00e+00 |

![Figure 4: Operational QoS Preservation Under Sequential Composition](file:///home/ayush/Ayush/assignment2/figures/fig4_operational_scaling.png)

---

## 10. Evaluation Against All Criteria

| Evaluation Question (Section 8) | Assessment & Findings | Score / Status |
| :--- | :--- | :---: |
| **Capability Representation**<br>*Can different capabilities be represented distinctly?* | Every distinct capability produces a non-zero vector with Euclidean distance >= 0.5 from any other capability. | **PASSED (100%)** |
| **State Relationship**<br>*Does the representation capture state applicability?* | Applicable states score +1.0; states violating preconditions score <= -0.5. | **PASSED (100%)** |
| **Precondition–Effect Compatibility**<br>*Can composable capabilities be distinguished from incompatible ones?* | C1 -> C2 scores +1.0000; C1 -> C3 scores -1.0000. Perfect discrimination. | **PASSED (100%)** |
| **Input–Output Compatibility**<br>*Can data dependencies be represented?* | Output production vector overlap matches required input schema (0.0 <= Gamma_IO <= 1.0). | **PASSED (100%)** |
| **Composition**<br>*Can complex capabilities be represented from smaller ones?* | Closed-form vector operator preserves condition absorption, state transformation parity, and associativity (diff = 0). | **PASSED (100%)** |
| **Goal Relevance**<br>*Can the relationship between capabilities and goals be identified?* | Contributing operations achieve +0.25 per satisfied goal condition; irrelevant operations score 0.0. | **PASSED (100%)** |
| **Operational Properties**<br>*Can cost, reliability, availability, constraints be represented appropriately?* | Costs are additive, log-reliability is strictly additive in R^D (error < 1e-16), availability is conjunctive. | **PASSED (100%)** |
| **Consistency**<br>*Does the representation behave consistently across different problems?* | Tested across E-Commerce, Cloud DevOps, and Healthcare domains with identical invariant satisfaction. | **PASSED (100%)** |
| **Efficiency**<br>*What are the computational and storage requirements?* | Encoding time: 0.12 ms; Composition time: 0.18 ms; Memory: 117 floats (< 1 KB per capability). | **PASSED (100%)** |

---

## 11. Analysis and Discussion

### Why Semantic Similarity Fails for Execution Pipelines
Traditional NLP embeddings measure distributional co-occurrence: words appearing in similar contexts are mapped to close vectors. When applied naively to services, two database engines (`MySQL_Insert` and `Postgres_Insert`) will have high cosine similarity. However:
1. **Competition vs. Cooperation**: Substitutes cannot be chained together sequentially.
2. **Directionality**: In vector space with standard cosine similarity, $\cos(\mathbf{u}, \mathbf{v}) \equiv \cos(\mathbf{v}, \mathbf{u})$. But composition is strictly directional: `CreateOrder` $\to$ `MakePayment` is valid, whereas `MakePayment` $\to$ `CreateOrder` is invalid because an order must exist before funds are charged.
3. **Partitioned Subspaces Solve This**: By separating the precondition subspace, effect subspace, and implementation subspace, `capembed` computes asymmetric projection tensors that evaluate directional validity without losing symmetric functional equivalence.

---

## 12. Limitations and Future Work

1. **Continuous Relaxation for Neural Planners**: The current model uses deterministic partitioned vectors. Future work will investigate using this structured embedding as an inductive bias for training continuous neural policy networks or GNN-based graph planners.
2. **First-Order Predicate Logic**: Currently, variables are propositionally bound or attribute-keyed. Extending to full first-order logic with universal ($\forall$) and existential ($\exists$) quantifiers will enable reasoning over arbitrary dynamic object graphs.
3. **Stochastic and Non-Deterministic Effects**: While operational reliability models probability of overall success ($Rel \in [0, 1]$), branching effects (e.g., probability $p$ of `InStock` vs. $1-p$ of `Backordered`) can be modeled using probabilistic mixture tensors or density matrices in quantum-inspired embedding spaces.

---

## 13. Conclusion

This project designed, implemented, and empirically verified a formal vector embedding architecture for capability composition. By decoupling functional resemblance from directional composability, preserving algebraic associativity, absorbing internal preconditions, and linearly encoding multiplicative reliability via logarithmic coordinate mapping, `capembed` bridges symbolic software engineering contracts and continuous vector representations. The system provides a mathematically sound foundation for automated service synthesis, capability discovery, and compositional reasoning in autonomous systems.
