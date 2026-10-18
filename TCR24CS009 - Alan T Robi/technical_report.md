# Design of a Vector Embedding for Capability Composition: Formal Representations, Compatibility, and Compositional Reasoning


**Domain**: E-Commerce & Order-Processing Capability System  

---

## Executive Summary

This technical report presents the design, implementation, and empirical evaluation of a **Hybrid Structured Capability Embedding** system for formally specified states, goals, and capabilities. Addressing the central research question—*how formally specified states, goals, and executable capabilities can be represented in a vector space such that the representation preserves relationships required for capability compatibility, composition, and application construction*—this work demonstrates that vector resemblance ($\text{Similarity}$) is fundamentally distinct from directional composability ($\text{Composability}$).

The proposed architecture encodes formal capability 11-tuples $C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)$ into a structured 167-dimensional feature space, alongside a 16-dimensional dense PCA projection (explaining 86.31% of total variance). A shared predicate canonicalization mechanism unifies semantically equivalent variable-value predicates across states, goals, preconditions, and effects (e.g., `Order.exists=true` $\equiv$ `OrderExists=true`).

Experimental evaluation across 25 formally defined capabilities indicates that directional effect-precondition and output-input matching achieves an **F1 score of 0.8333** on a constructed 12-pair evaluation set, compared to **0.2500** for an unstructured flat baseline. The representation separates functional semantics from execution mechanisms, models composite capability aggregation ($C_{comp} = C_n \circ \dots \circ C_1$), and reflects operational trade-offs without distorting functional composability.

---

## 1. Problem Definition

In modern distributed software systems and automated service composition, applications are assembled from reusable software operations termed **capabilities**. In Assignment 1, automated planners (e.g., $D^*$ Lite / $LPA^*$) searched state spaces to identify sequences of state transitions. However, classical search mechanisms treat operations as discrete, opaque labels or atomic state transition rules without continuous representation.

The objective of Assignment 2 is to move from *searching for sequences* to *formally representing the operations themselves in a continuous vector space*. The primary challenge lies in the fact that standard text embeddings (e.g., Word2Vec, BERT, Sentence-Transformers) capture natural language distributional semantics rather than formal software semantics. Words or service names with similar textual contexts may lie close in word embedding spaces, but they cannot enforce precondition satisfaction, input-output type constraints, resource availability, or state transformation safety.

Furthermore, capability composition exhibits two critical properties:
1. **Directionality**: Composition $C_1 \to C_2$ requires that effects $E_1$ satisfy preconditions $P_2$ and outputs $O_1$ satisfy inputs $I_2$. The reverse composition $C_2 \to C_1$ is generally invalid.
2. **Similarity $\neq$ Composability**: Two capabilities may be functionally similar (e.g., `CreateOrder` and `CancelCart` both manipulate cart/order entities), yet `CreateOrder` ($OrderExists=true$) actively contradicts the preconditions of `CancelCart` ($OrderExists=false$).

---

## 2. Design Requirements

To address capability composition, the vector representation must satisfy nine explicit evaluation criteria:

1. **Capability Identity**: Functionally distinct capabilities must occupy distinguishable positions in the feature space.
2. **State Awareness**: The representation must explicitly reflect state variable-value predicates and support state-space projection ($\phi_S(S)$).
3. **Precondition-Effect Compatibility**: The representation must distinguish compatible capability pairs ($E_1 \Rightarrow P_2$) from incompatible or contradictory pairs.
4. **Input-Output Compatibility**: Data dependencies ($O_1 \cap I_2 \neq \emptyset$) with matching names, types, and domains must contribute positively to composability.
5. **Composition**: Composite capabilities ($C_{comp} = C_2 \circ C_1$) must be formally constructible and representable in the same vector space.
6. **Goal Relevance**: The relationship between capability effects and desired goal conditions ($S \models G$) must be quantitatively measurable.
7. **Operational Properties**: Cost, reliability, availability, risk, and resource constraints must be incorporated without distorting functional composability.
8. **Consistency**: The representation must behave deterministically across given problem instances.
9. **Efficiency**: Feature extraction, encoding, and compatibility checking must exhibit low computational latency and storage overhead.

---

## 3. Related Embedding Approaches

Before developing the proposed model, four major representation paradigms were analyzed:

| Paradigm | Strengths | Limitations for Capability Composition |
| :--- | :--- | :--- |
| **One-Hot / Multi-Hot Encoding** | Simple, orthogonal, exact discrete matching. | High dimensionality, zero semantic generalization between related types or inputs. |
| **Textual / Distributional (Word2Vec, BERT)** | Captures rich natural language semantics and entity associations. | Insensitive to formal logic, boolean predicates, directional compatibility, and numerical operational bounds. |
| **Flat Unweighted Feature Vectors** | Integrates symbolic tokens into a single vector. | Conflates inputs, outputs, preconditions, effects, and operational attributes into one unweighted sum. Fails directional compatibility ($C_1 \to C_2$ vs $C_2 \to C_1$). |
| **Proposed Hybrid Structured Embedding** | Explicit sub-space block partition, interpretable feature alignment, directional logic matching, and numerical normalization. | Requires formal domain specification (schema definition). |

---

## 4. Proposed Representation*

We design a **Hybrid Structured Capability Embedding** that combines symbolic multi-hot feature sub-vectors with normalized numerical operational attributes.

```
FORMAL CAPABILITY Ci = (Ti, Ii, Oi, Pi, Ei, Ki, Ri, Qi, Reli, Ai, Mi)
                          |
                          v
                 FEATURE EXTRACTION
                          |
         +----------------+----------------+
         |                                 |
         v                                 v
Symbolic Sub-vectors                    Numerical Operational
(Type, Inputs, Outputs,                 Sub-vector
 Preconditions, Effects,               (Time, Resource cost, Money,
 Constraints, Resources, Mechanism)     Risk, Energy, Reliability, Availability)
         |                                 |
         +----------------+----------------+
                          |
                          v
         STRUCTURED CAPABILITY VECTOR V(Ci)  [D = 167]
                          |
         +----------------+----------------+
         |                                 |
         v                                 v
  Dense Projection                 Directional Capability Reasoning
  (PCA to d = 16)                  (Effect-Precondition & Output-Input Match)
```

The feature space is partitioned into 9 conceptual sub-space blocks:
$$\mathbf{V}(C_i) = [ \mathbf{V}_{type} \mid \mathbf{V}_{inputs} \mid \mathbf{V}_{outputs} \mid \mathbf{V}_{preconditions} \mid \mathbf{V}_{effects} \mid \mathbf{V}_{constraints} \mid \mathbf{V}_{resources} \mid \mathbf{V}_{mechanism} \mid \mathbf{V}_{operational} ]$$

In our 25-capability e-commerce dataset, the vocabulary size across all capabilities yields a total structured vector dimension $D = 167$.

### Predicate Canonicalization
To bridge syntax variations across states, goals, preconditions, and effects, a shared predicate canonicalization function maps predicate strings into normalized keys (e.g., `Order.exists=true` and `OrderExists=true` both map to `orderexists=true`).

---

## 5. Mathematical Formulation

### 5.1 Formal Capability Model
A capability $C_i$ is formally defined as:
$$C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)$$

Where:
- $T_i \in \{\text{API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE}\}$
- $I_i = \{ (n_j, t_j, d_j, r_j) \mid n_j \text{ is name}, t_j \text{ is type}, d_j \text{ is domain}, r_j \in \{\text{true, false}\} \}$
- $O_i = \{ (n_k, t_k, d_k) \}$
- $P_i = \{ p_1, p_2, \dots, p_r \}, \quad E_i = \{ e_1, e_2, \dots, e_s \}$
- $Q_i = (C_{time}, C_{resource}, C_{money}, C_{risk}, C_{energy}) \in \mathbb{R}_{\ge 0}^5$
- $Rel_i \in [0, 1], \quad A_i \in [0, 1]$

### 5.2 State and Goal Embeddings
An application state $S = \{ (x_1, v_1), \dots, (x_n, v_n) \}$ is mapped via state encoder $\phi_S(S) \in \mathbb{R}^D$ into the aligned precondition/effect feature sub-spaces. A goal specification $G = \{ g_1, \dots, g_m \}$ is mapped via goal encoder $\phi_G(G) \in \mathbb{R}^D$.

### 5.3 Vector Cosine Similarity
Vector resemblance between two capability vectors $\mathbf{x}, \mathbf{y} \in \mathbb{R}^D$ is defined as:
$$\text{Similarity}(\mathbf{x}, \mathbf{y}) = \frac{\mathbf{x} \cdot \mathbf{y}}{\|\mathbf{x}\|_2 \|\mathbf{y}\|_2}$$

### 5.4 Directional Compatibility Function
Directional compatibility for ordered sequence $C_1 \to C_2$ is defined as:
$$\text{Compat}(C_1, C_2) = w_1 \cdot \text{Match}_{EP}(E_1, P_2) + w_2 \cdot \text{Match}_{OI}(O_1, I_2)$$

Where $w_1 = 0.6, w_2 = 0.4$, and:
$$\text{Match}_{EP}(E_1, P_2) = \begin{cases} 0.0 & \text{if } \exists e \in E_1, p \in P_2 \text{ s.t. } e \text{ contradicts } p \\ \frac{|\{ p \in P_2 \mid p \in E_1 \}|}{\max(1, |P_2|)} & \text{otherwise} \end{cases}$$

$$\text{Match}_{OI}(O_1, I_2) = \frac{|\{ i \in I_2^{req} \mid \exists o \in O_1, o.\text{type} = i.\text{type} \land o.\text{name} = i.\text{name} \}|}{\max(1, |I_2^{req}|)}$$

A pair is classified as compatible if $\text{Compat}(C_1, C_2) \ge 0.5$ and no contradictions exist.

---

## 6. Capability Composition Model

Given a valid sequence of compatible capabilities $C_1 \to C_2 \dots \to C_n$, the composite capability $C_{comp} = C_n \circ \dots \circ C_1$ is constructed formally before vector encoding:

1. **Composite Inputs**: $I_{comp} = I_1 \cup \{ i \in I_k \mid i \text{ not satisfied by } \bigcup_{m < k} O_m \}$
2. **Composite Outputs**: $O_{comp} = \bigcup_{k=1}^n O_k$
3. **Composite Preconditions**: $P_{comp} = P_1 \cup \{ p \in P_k \mid p \text{ not satisfied by } \bigcup_{m < k} E_m \}$
4. **Composite Effects**: $E_{comp} = \text{Sequence-Apply}(E_1, E_2, \dots, E_n)$ (later effects overwrite earlier effects for matching variables).
5. **Operational Aggregations**:
   - $C_{time, comp} = \sum_{k=1}^n C_{time, k}$
   - $C_{money, comp} = \sum_{k=1}^n C_{money, k}$
   - $C_{risk, comp} = \max_{k=1}^n C_{risk, k}$
   - $Rel_{comp} = \prod_{k=1}^n Rel_k$
   - $A_{comp} = \min_{k=1}^n A_k$

The composite vector representation is generated via $\mathbf{V}(C_{comp}) = \text{encode\_capability}(C_{comp})$.

---

## 7. Implementation

The system is implemented in Python 3 using NumPy, Pandas, scikit-learn, and Matplotlib.

- `src/capability.py`: Defines dataclasses (`Capability`, `InputSpec`, `OutputSpec`, `CostSpec`) and JSON schema validation.
- `src/state.py`: Implements `State` and `Goal` objects with predicate satisfaction logic.
- `src/encoder.py`: Implements `CapabilityVocabulary`, `CapabilityEncoder` ($D=167$), and `CapabilityPCAEncoder` ($d=16$).
- `src/similarity.py`: Implements cosine similarity and sub-space block extraction.
- `src/compatibility.py`: Implements directional compatibility and contradiction checking.
- `src/composition.py`: Implements formal capability sequence composition engine.
- `src/evaluation.py`: Implements baseline encoders and benchmark metrics.
- `src/utils.py`: Implements shared `canonicalize_predicate` and Min-Max normalization.

---

## 8. Experimental Methodology

Five experiments were constructed using a 25-capability dataset in the e-commerce domain:

1. **Experiment 1 (Capability Compatibility)**: Evaluates $CreateOrder \to MakePayment$ vs $CreateOrder \to CancelCart$ and pairwise classification accuracy/precision/recall/F1 over a 12-pair evaluation dataset.
2. **Experiment 2 (Capability Composition)**: Constructs $CompletePurchase = SendNotification \circ MakePayment \circ CreateOrder$ and compares $V(C_{comp})$ against atomic vectors and linear vector addition ($V_1 + V_2 + V_3$).
3. **Experiment 3 (Alternative Implementations)**: Compares `CreateOrder` (API), `CreateOrderDatabase` (DB), and `CreateOrderGUI` (GUI).
4. **Experiment 4 (Irrelevant Capabilities)**: Evaluates goal relevance for target checkout goal $G$ against relevant vs unrelated capabilities (`UpdateProfile`, `CreateWishlist`, `GenerateUserReport`).
5. **Experiment 5 (Operational Attributes)**: Compares `MakePaymentPremium` (Service A) vs `MakePaymentDiscount` (Service B).

---

## 9. Results

### 9.1 Experiment 1: Capability Compatibility
Central demonstration results:

| Pair | EffectPreconditionMatch | OutputInputMatch | CompatibilityScore | HasContradiction | Classification |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `CreateOrder` $\to$ `MakePayment` | **1.0** | **0.5** | **0.8** | False | **Compatible** |
| `CreateOrder` $\to$ `CancelCart` | **0.0** | **0.0** | **0.0** | **True** | **Incompatible** |

> *Note on Output-Input Match*: `CreateOrder` produces `order_id`. `MakePayment` requires `order_id` (matched) and `payment_method` (unmatched input), yielding $\text{Match}_{OI} = 0.5$. With $\text{Match}_{EP} = 1.0$, the score is $0.6(1.0) + 0.4(0.5) = 0.8 \ge 0.5$.

Pairwise Classification Benchmark (evaluated on the 12-pair test set):

| Metric | Proposed Directional Model | Flat Unweighted Baseline |
| :--- | :---: | :---: |
| **Accuracy** | **0.8333** | 0.3333 |
| **Precision** | **1.0000** | 0.3333 |
| **Recall** | **0.7143** | 0.5000 |
| **F1 Score** | **0.8333** | **0.2500** |

*Evaluation Scope*: The F1 score of 0.8333 is measured on this specific 12-pair evaluation dataset and serves as a comparative benchmark against the baseline, not as a universal performance estimate across arbitrary unseen domains.

### 9.2 Experiment 2: Capability Composition
For $CompletePurchase = SendNotification \circ MakePayment \circ CreateOrder$:

| Vector Comparison | Cosine Similarity | Interpretation |
| :--- | :---: | :--- |
| $V(C_{comp})$ vs $V(CreateOrder)$ | **0.6052** | Step 1 contribution |
| $V(C_{comp})$ vs $V(MakePayment)$ | **0.5173** | Step 2 contribution |
| $V(C_{comp})$ vs $V(SendNotification)$ | **0.4197** | Step 3 contribution |
| $V(C_{comp})$ vs $V_1 + V_2 + V_3$ | **0.7153** | Linear structural alignment |

Aggregated operational properties: Cumulative Time = **330.0 ms**, Max Risk = **0.05**, Combined Reliability = **0.9314**, Minimum Availability = **1.0**.

### 9.3 Experiment 3: Alternative Implementations

| Implementation Pair | Type1 | Type2 | Functional Sub-space Sim | Type Sub-space Sim | Mechanism Sub-space Sim | Resource Sub-space Sim | Full Vector Sim |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `CreateOrder` vs `CreateOrderDatabase` | API | DATABASE | **1.0** | **0.0** | **0.0** | **0.7071** | **0.7404** |
| `CreateOrder` vs `CreateOrderGUI` | API | GUI | **1.0** | **0.0** | **0.0** | **0.5000** | **0.7176** |
| `CreateOrderDatabase` vs `CreateOrderGUI` | DATABASE | GUI | **1.0** | **0.0** | **0.0** | **0.0000** | **0.6606** |

### 9.4 Experiment 4: Goal Relevance
For Goal $G = \{ Order.exists=true, Payment.status=SUCCESS, Notification.sent=true \}$ (canonicalized to `orderexists=true`, `paymentstatus=success`, `notificationsent=true`):

| Capability | Category | Formal Goal Relevance | Vector Cosine Sim to Goal Vector $\mathbf{v}_G$ | Relevance Classification |
| :--- | :--- | :---: | :---: | :---: |
| `CreateOrder` | Relevant | **0.3333** | **0.1183** | Relevant |
| `MakePayment` | Relevant | **0.3333** | **0.2221** | Relevant |
| `SendNotification` | Relevant | **0.3333** | **0.2310** | Relevant |
| `GenerateInvoice` | Auxiliary | **0.0000** | **0.1235** | Irrelevant |
| `AddToCart` | Pre-checkout | **0.0000** | **0.0000** | Irrelevant |
| `UpdateProfile` | Irrelevant | **0.0000** | **0.0000** | Irrelevant |
| `CreateWishlist` | Irrelevant | **0.0000** | **0.0000** | Irrelevant |
| `GenerateUserReport` | Irrelevant | **0.0000** | **0.0000** | Irrelevant |

*Analysis of Goal Relevance vs Vector Similarity*:
Formal goal relevance measures direct logical satisfaction of explicit goal predicates ($S \models G$), returning $0.3333$ for capabilities directly producing a required goal predicate. Vector cosine similarity to $\mathbf{v}_G$ measures continuous feature overlap in precondition/effect sub-spaces. `GenerateInvoice` exhibits a non-zero vector similarity ($0.1235$) because it shares preconditions (`OrderPaid=true`, `PaymentStatus=SUCCESS`) with the goal state space, despite not producing a primary goal predicate itself. Completely unrelated capabilities (`UpdateProfile`, `CreateWishlist`, `GenerateUserReport`) yield exactly $0.0000$ for both metrics.

### 9.5 Experiment 5: Operational Attributes

| Capability Pair | Functional Sim | Operational Sub-space Sim | Full Vector Sim |
| :--- | :---: | :---: | :---: |
| `MakePaymentPremium` vs `MakePaymentDiscount` | **1.0000** | **0.7608** | **0.8174** |
| `MakePayment (Std)` vs `MakePaymentPremium` | **1.0000** | **0.9479** | **0.7851** |

*Operational Attribute Profile Comparison*:

| Capability | Service Tier | Execution Time (ms) | Monetary Cost ($) | Risk Score | Reliability | Availability |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `MakePaymentPremium` | Premium (Service A) | 50.0 | 0.025 | 0.005 | 0.999 | 1.0 |
| `MakePayment` | Standard | 150.0 | 0.010 | 0.040 | 0.980 | 1.0 |
| `MakePaymentDiscount` | Discount (Service B) | 300.0 | 0.003 | 0.100 | 0.900 | 0.95 |

*Operational Encoding Analysis*:
The operational sub-space similarity between Premium (50ms, risk=0.005, rel=99.9%) and Discount (300ms, risk=0.10, rel=90.0%) is **0.7608** (compared to **0.9479** between Standard and Premium). This occurs because reliability ($\approx 0.90 - 0.999$) and availability ($\approx 0.95 - 1.0$) form positive baseline dimensions in all operational vectors, maintaining a baseline angle projection in 7D space. However, individual normalized cost, time, and risk dimensions diverge significantly (e.g. risk score 0.0404 vs 1.0000), causing the operational similarity to drop sharply from 0.9479 down to 0.7608.

### 9.6 Efficiency & Storage Benchmarks
- **Structured Vector Dimension $D$**: 167 float64 values
- **Dense PCA Vector Dimension $d$**: 16 float64 values
- **PCA Explained Variance Ratio (16D)**: **0.8630760578** (86.31%)
- **Vector Storage Size**: 1,336 bytes per structured vector; 128 bytes per dense vector
- **Average Encoding Latency**: **0.0242 ms** per capability (or **24.2 microseconds / μs**)
- **Average Compatibility Evaluation Latency**: **0.0043 ms** per capability pair (or **4.3 microseconds / μs**)

---

## 10. Analysis

1. **Similarity vs Composability**: Experiment 1 demonstrates that cosine similarity alone is insufficient for capability composition. `CreateOrder` and `CancelCart` share cart/order entity tokens, but directional logic detection flags a hard contradiction ($OrderExists=true$ vs $OrderExists=false$), yielding $\text{Compat}=0.0$.
2. **Sub-space Disentanglement**: Experiment 3 indicates that sub-space partitioning isolates functional semantics ($\text{Sim}_{func} = 1.0$) from mechanism realization ($\text{Sim}_{mech} = 0.0$).
3. **Composite Aggregation**: Experiment 2 illustrates that formal composite capabilities ($C_{comp}$) preserve global input-output requirements and cumulative operational costs while abstracting intermediate state steps.
4. **Baseline Comparison**: The proposed directional model achieves an F1 score of **0.8333** on the 12-pair evaluation set, outperforming the flat unweighted baseline (**0.2500**).

---

## 11. Limitations

1. **Domain Vocabulary Dependency**: The feature vocabulary $\mathcal{V}$ is constructed across dataset capabilities. Adding new domain entities requires updating vocabulary bounds.
2. **Predicate Expressiveness**: The parser supports equality ($=$) and numeric inequality ($>, <, \ge, \le$). Higher-order modal logic or temporal logic predicates are outside the current parser scope.
3. **Manual Feature Schema**: Capabilities must be formally specified in JSON format. Unstructured text descriptions require manual or LLM-assisted extraction into the formal 11-tuple schema.

---

## 12. Conclusion

This project directly addresses the central research question of Assignment 2: *how formally specified states, goals, and executable capabilities can be represented in a vector space to preserve relationships required for capability compatibility, composition, and application construction.*

The experimental findings demonstrate that by constructing a **Hybrid Structured Capability Embedding** $V(C_i) \in \mathbb{R}^{167}$ with dense projection $e(C_i) \in \mathbb{R}^{16}$, formal capability specifications, state transitions, goals, and operational constraints can be mapped into a continuous vector space. Predicate canonicalization unifies state and goal syntax, while directional compatibility metrics ($E_1 \Rightarrow P_2$ and $O_1 \Rightarrow I_2$) prevent illegal compositions and evaluate operational trade-offs with microsecond-level latency.

---

## References

1. Mikolov, T., Chen, K., Corrado, G., Sutskever, I., & Dean, J. (2013). Efficient Estimation of Word Representations in Vector Space. *arXiv preprint arXiv:1301.3781*.
2. Ghallab, M., Nau, D., & Traverso, P. (2004). *Automated Planning: Theory and Practice*. Morgan Kaufmann.
3. Jolliffe, I. T., & Cadima, J. (2016). Principal component analysis: a review and recent developments. *Philosophical Transactions of the Royal Society A*, 374(2065), 20150202.


*Kindly use other tools to view the .md file if the content of the file seems confusing.
