# Technical Report

## Design of a Vector Embedding for Capability Composition

**Course:** PCCST503  
**Assignment:** Assignment 2  
**Project:** Design of a Vector Embedding for Capability Composition

---

# Abstract

This project develops a problem-specific vector representation for formally specified application states, goals, and executable capabilities. The representation is designed for a setting in which a capability is defined not only by its name, but also by its type, inputs, outputs, preconditions, effects, constraints, resources, operational properties, and execution mechanism.

An 80-dimensional structured embedding is implemented using deterministic feature hashing for symbolic information and normalized numerical features for operational attributes. Cosine similarity is used to measure geometric similarity. Because similarity alone cannot determine whether one capability can validly follow another, a separate directed compatibility function is implemented using effect-precondition satisfaction, output-input compatibility, operational feasibility, and resource information.

The implementation is evaluated on five required scenarios: capability compatibility, multi-step composition, alternative implementations, irrelevant capabilities, and operational properties. In the supplied dataset, `CreateOrder -> MakePayment` obtains a compatibility score of 0.9730, while `CreateOrder -> CancelCart` obtains 0.4495. The three-step sequence `CreateOrder -> MakePayment -> SendNotification` is successfully composed into `CompletePurchase`, with composite reliability 0.9555 and availability 0.9800.

The project demonstrates that a structured hybrid representation can provide useful geometric relationships while retaining explicit symbolic reasoning for functional compatibility and composition.

---

# 1. Problem Definition

The objective of the assignment is to design a numerical representation for formally specified states, goals, and executable capabilities such that important functional relationships are preserved.

This problem differs from ordinary semantic word embedding. In a conventional language representation, two terms may be considered similar because they occur in similar linguistic contexts. In capability composition, however, functional relationships depend on explicit structure.

For example, a capability may:

- require an authenticated user
- consume a cart identifier
- produce an order identifier
- require that inventory is available
- create an order
- use a database and network
- have a particular execution time and reliability
- be implemented through an API, GUI, database operation, event, or service

The central research question is:

> **How can formally specified states, goals, and executable capabilities be represented in a vector space so that the representation preserves relationships required for capability compatibility, composition, and construction of complex functionality?**

The implementation therefore treats the problem as a structured representation task.

---

# 2. Design Requirements

The proposed representation addresses the following requirements.

## 2.1 Capability identity

Different capabilities must remain distinguishable even when they perform related functions.

## 2.2 State awareness

The representation must be able to represent application state information and goal conditions.

## 2.3 Precondition-effect compatibility

The system must represent whether the effects of one capability can satisfy the preconditions of another.

## 2.4 Input-output compatibility

The representation must capture whether outputs produced by one capability can supply inputs required by another.

## 2.5 Similarity versus composability

A similarity measure should not be treated as an exact substitute for directed functional compatibility.

## 2.6 Composition

Compatible capabilities must be combinable into a composite capability.

## 2.7 Goal relevance

Capabilities should be comparable with respect to their contribution to a specified goal.

## 2.8 Operational properties

Reliability, availability, execution time, resource cost, monetary cost, energy, and risk should be represented explicitly.

The assignment also requires experiments covering compatibility, composition, alternative implementations, irrelevant capabilities, and operational properties.

---

# 3. Related Representation Approaches

## 3.1 Distributional embeddings

Word2Vec is an example of a distributional embedding approach in which representations are learned from contextual word usage.

Such representations are useful for semantic relationships in natural language. However, functional capability composition requires explicit reasoning about state transitions, inputs, outputs, preconditions, and effects. Textual similarity alone does not provide those guarantees.

## 3.2 One-hot representation

One-hot encoding provides an exact identity for each item, but it does not naturally represent relationships between structured capabilities. Two different capabilities receive unrelated vectors even when they share inputs, effects, or mechanisms.

## 3.3 Feature hashing

Feature hashing maps symbolic features into a fixed-dimensional vector. It is deterministic and computationally simple, making it suitable for a controlled first implementation of a structured capability embedding.

## 3.4 Proposed hybrid approach

The project combines:

1. structured feature hashing for symbolic capability information
2. numerical representation for operational attributes
3. an explicit compatibility function for directed composability
4. a composition mechanism for constructing composite capabilities

This combination is intended to provide both geometric representation and explicit functional reasoning.

---

# 4. Formal Application Model

The application model is represented conceptually as:

```text
A = (S, C, S_I, G, R, K)
```

where:

| Symbol | Meaning |
|---|---|
| `S` | State space |
| `C` | Set of capabilities |
| `S_I` | Initial state |
| `G` | Goal specification |
| `R` | Resources |
| `K` | Constraints and policies |

The capability model is:

```text
C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
```

where:

| Component | Meaning |
|---|---|
| `T_i` | Capability type |
| `I_i` | Inputs |
| `O_i` | Outputs |
| `P_i` | Preconditions |
| `E_i` | Effects |
| `K_i` | Constraints |
| `R_i` | Resources |
| `Q_i` | Quality and cost attributes |
| `Rel_i` | Reliability |
| `A_i` | Availability |
| `M_i` | Execution mechanism |

The implementation stores these properties explicitly in the capability data model.

---

# 5. Proposed Representation

## 5.1 Overview

The project maps capabilities into an 80-dimensional real-valued vector.

The representation is divided into blocks so that different functional aspects of a capability are represented separately.

| Dimensions | Block | Information represented |
|---:|---|---|
| 0-7 | Type and mechanism | Capability type and execution mechanism |
| 8-19 | Inputs | Input names, types, domains, and required status |
| 20-31 | Outputs | Output names, types, domains, and required status |
| 32-43 | Preconditions | Required state conditions |
| 44-55 | Effects | State changes produced by the capability |
| 56-63 | Constraints and resources | Constraints and required resources |
| 64-71 | Operational attributes | Time, cost, risk, energy, reliability, availability |
| 72-79 | Composition metadata | Additional structural information |

Symbolic features are deterministically hashed into their designated blocks. Numerical operational values are normalized before inclusion.

The final vector is L2-normalized.

## 5.2 State representation

States are represented using features derived from variable-value assignments. For example:

```text
User.authenticated=true
Cart.exists=true
Order.exists=false
Payment.status=NOT_STARTED
```

The state is encoded into the same 80-dimensional space.

## 5.3 Goal representation

Goals are represented by their required conditions. For the purchase example, the target conditions are:

```text
Order.exists=true
Payment.status=SUCCESS
Notification.sent=true
```

The goal is also represented in the 80-dimensional space.

---

# 6. Mathematical Formulation

## 6.1 Capability embedding

The capability embedding is defined as:

```text
phi_C : C -> R^80
```

Conceptually, the vector is:

```text
phi_C(C) = [phi_T, phi_I, phi_O, phi_P,
            phi_E, phi_KR, phi_OP, phi_CM]
```

where each block corresponds to a different part of the formal capability definition.

## 6.2 Similarity

For two vectors `x` and `y`, cosine similarity is defined as:

```text
similarity(x, y) = dot(x, y) / (norm(x) * norm(y))
```

The implementation exposes this through:

```python
StructuredEmbedder.similarity(x, y)
```

## 6.3 Directed compatibility

For a candidate transition from `C_i` to `C_j`:

```text
Comp(C_i, C_j) =
    0.55 * EP
  + 0.30 * IO
  + 0.10 * OP
  + 0.05 * R
```

where:

- `EP` = effect/precondition satisfaction
- `IO` = output/input satisfaction
- `OP` = operational feasibility
- `R` = resource compatibility diagnostic

The supplied experiments use a threshold of 0.70.

Thus:

```text
Comp(C_i, C_j) >= 0.70
```

is treated as a composable transition.

The function is directional because the effects of the first capability are compared with the preconditions of the second capability.

---

# 7. Capability Composition Model

A sequence:

```text
C1 -> C2 -> ... -> Cn
```

is composable when every adjacent pair satisfies the compatibility threshold.

For the supplied dataset:

```text
CreateOrder -> MakePayment -> SendNotification
```

is composed into:

```text
CompletePurchase
```

## 7.1 Composite interface

The composite capability uses the boundary information of the sequence:

```text
Inputs        = inputs of the first capability
Outputs       = outputs of the final capability
Preconditions = preconditions of the first capability
Effects       = effects of the final capability
Resources     = union of component resources
```

## 7.2 Operational aggregation

For a sequence of capabilities:

```text
Reliability = product of component reliabilities
Availability = minimum component availability
Time cost = sum of component time costs
Resource cost = sum of component resource costs
Money cost = sum of component money costs
Energy cost = sum of component energy costs
```

Risk is aggregated as the probability that at least one component risk occurs.

## 7.3 Composite vector

The vector representation of a composite capability is the normalized mean of the component vectors:

```text
v_composite = normalize(mean(v_1, v_2, ..., v_n))
```

The exact ordered list of component capabilities remains stored in the formal composite object. This is necessary because mean aggregation does not completely encode sequence order.

---

# 8. Implementation

The implementation is written in Python using NumPy, pandas, and Matplotlib.

The main interfaces are:

```python
encode_state(state)
encode_goal(goal)
encode_capability(capability)
compose_capabilities(capabilities)
StructuredEmbedder.similarity(x, y)
compatibility(a, b)
```

The dataset is stored as JSON. This separates the experimental data from the embedding implementation and allows additional capabilities to be added without changing the core representation code.

## 8.1 Repository modules

| File | Responsibility |
|---|---|
| `src/models.py` | Formal data structures |
| `src/embedding.py` | State, goal, and capability embeddings |
| `src/compatibility.py` | Directed compatibility calculation |
| `src/composition.py` | Composite capability construction |
| `src/evaluation.py` | Evaluation utilities |
| `experiments/run_experiments.py` | Required experiments |
| `data/capability_dataset.json` | Experimental dataset |
| `run.py` | Main execution entry point |

---

# 9. Experimental Methodology

The evaluation is designed around the five scenarios required by the assignment.

## 9.1 Experiment 1 - Capability Compatibility

The first experiment evaluates:

```text
CreateOrder -> MakePayment
CreateOrder -> CancelCart
```

`CreateOrder` produces:

```text
Order.exists=true
```

`MakePayment` requires:

```text
Order.exists=true
```

Therefore the state condition is satisfied.

`CancelCart`, however, requires:

```text
Order.exists=false
```

which conflicts with the effect of `CreateOrder`.

The experiment therefore tests whether the compatibility representation distinguishes a valid transition from an invalid one.

## 9.2 Experiment 2 - Capability Composition

The second experiment evaluates:

```text
CreateOrder -> MakePayment -> SendNotification
```

The expected result is a valid composite capability named `CompletePurchase`.

The experiment also evaluates its aggregate reliability, availability, and other operational properties.

## 9.3 Experiment 3 - Alternative Implementations

The dataset contains three order-creation implementations:

```text
CreateOrder
CreateOrderDB
CreateOrderGUI
```

They share the broad functional purpose of creating an order but differ in capability type, mechanism, resources, and operational attributes.

The experiment checks whether the representation keeps these capabilities related without making them identical.

## 9.4 Experiment 4 - Irrelevant Capability

`UpdateProfile` is unrelated to the purchase goal.

The experiment measures its goal relevance and compares it with the relevance of the complete purchase composition.

## 9.5 Experiment 5 - Operational Properties

The final experiment examines the role of reliability and availability and verifies their aggregation in a composed capability.

---

# 10. Results

The project was executed using:

```bash
python run.py
```

The generated results are stored in the `results/` directory.

## 10.1 Summary of measured values

| Measurement | Value |
|---|---:|
| Embedding dimension | 80 |
| Number of capabilities | 7 |
| State vector dimension | 80 |
| Goal vector dimension | 80 |
| `CreateOrder -> MakePayment` compatibility | 0.9730 |
| `CreateOrder -> CancelCart` compatibility | 0.4495 |
| `CreateOrder` goal relevance | 0.3333 |
| `CompletePurchase` goal relevance | 1.0000 |
| Composite reliability | 0.9555 |
| Composite availability | 0.9800 |

## 10.2 Compatibility result

The compatibility score for `CreateOrder -> MakePayment` is 0.9730, which is above the 0.70 composition threshold.

The compatibility score for `CreateOrder -> CancelCart` is 0.4495, which is below the threshold.

This demonstrates the intended distinction between a transition whose effects satisfy the next capability's requirements and a transition whose state conditions conflict.

## 10.3 Composition result

The valid sequence:

```text
CreateOrder -> MakePayment -> SendNotification
```

produces the composite capability:

```text
CompletePurchase
```

Its measured reliability is 0.9555 and its availability is 0.9800.

The reliability value is consistent with the product of the three component reliabilities:

```text
0.99 * 0.97 * 0.995 = 0.9555 approximately
```

The availability value is the minimum of the three component availability values:

```text
min(1.00, 0.99, 0.98) = 0.98
```

## 10.4 Goal relevance

The complete purchase composition receives a goal relevance of 1.0000 because its final effects satisfy all three target conditions in the supplied goal.

`CreateOrder` alone receives a lower value of 0.3333 because it establishes only one of the three required goal conditions.

`UpdateProfile` is unrelated to the purchase goal and is therefore treated as irrelevant to the target functionality.

## 10.5 Alternative implementations

`CreateOrderDB` and `CreateOrderGUI` represent alternative ways of producing an order. They share important functional information with `CreateOrder` but retain different mechanism and operational features.

This demonstrates why the embedding includes both functional and mechanism information.

---

# 11. Analysis

## 11.1 Structured representation is necessary

The experiments show why the capability name alone is insufficient. Functional compatibility depends on conditions and interfaces. For example, the important relationship between `CreateOrder` and `MakePayment` is not simply that both are related to purchasing. The relationship arises because the first capability establishes a state condition required by the second and provides an appropriate identifier output.

## 11.2 Similarity and compatibility serve different purposes

A vector similarity score is useful for geometric comparison, retrieval, and identifying related capabilities. It is not sufficient to prove that one capability can follow another.

The explicit compatibility calculation therefore complements the embedding rather than replacing it.

## 11.3 Operational attributes should remain visible

Operational attributes can differentiate capabilities that perform related functions. A database operation, API call, and GUI action may all create an order but have different execution times, resource requirements, reliability, availability, and risks.

Keeping these attributes in a dedicated block prevents them from being treated as if they were identical to semantic identity.

## 11.4 Composition requires preserving formal information

The composite vector provides a compact representation, but mean aggregation can lose sequence information. The implementation addresses this by retaining the ordered component list and exact aggregate properties in the formal `CompositeCapability` object.

Thus, the system uses the vector for geometric representation and the structured object for exact composition information.

---

# 12. Limitations

The current project is a deterministic, feature-engineered baseline.

### 12.1 Hash collisions

Different symbolic features may map to the same hashed dimension. This is an inherent property of feature hashing.

### 12.2 Manually selected compatibility weights

The values 0.55, 0.30, 0.10, and 0.05 are design choices rather than learned parameters.

### 12.3 Small controlled dataset

The experiments use a small synthetic dataset designed to demonstrate the required relationships. It is not intended to establish performance on large real-world workflows.

### 12.4 Sequence information in the vector

Mean aggregation does not completely preserve ordering. The exact ordered sequence is therefore retained separately in the composite object.

### 12.5 No learned embedding

The current system does not learn vector representations from a large training corpus. It is a structured baseline intended to demonstrate the representation principles and required experiments.

---

# 13. Future Work

Future versions could extend the baseline in several directions:

1. Learn the compatibility weights from labelled composition examples.
2. Learn the embedding from a large corpus of formal capabilities.
3. Use graph-based representations for state-transition structure.
4. Use sequence models to preserve ordered composition information.
5. Use contrastive learning to bring compatible capabilities closer in vector space while separating incompatible pairs.
6. Evaluate the system on larger and more realistic workflow datasets.
7. Jointly learn goal relevance, compatibility, and composition quality.

These extensions would move the implementation from a deterministic engineered representation toward a learned capability embedding model.

---

# 14. Conclusion

This project implements a problem-specific vector representation for formally specified states, goals, and executable capabilities.

The representation explicitly captures capability identity, inputs, outputs, preconditions, effects, constraints, resources, execution mechanisms, and operational properties. States and goals are also mapped into the same fixed-dimensional vector space.

The experimental results demonstrate the central design principle: **geometric similarity and functional composability should not be treated as the same relationship**. The embedding provides a structured geometric representation, while the directed compatibility model evaluates whether one capability can validly follow another based on effects, preconditions, outputs, inputs, operational feasibility, and resources.

The supplied experiments successfully distinguish the valid `CreateOrder -> MakePayment` transition from the invalid `CreateOrder -> CancelCart` transition, construct the multi-step `CompletePurchase` capability, represent alternative order-creation mechanisms, identify an irrelevant profile-update capability, and aggregate operational properties across a composition.

The implementation therefore provides a complete baseline for studying vector representations of capability composition and offers a clear foundation for future learned and graph-based approaches.

---

# 15. Reproducibility

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

The execution produces the CSV files, JSON summary, and figures under `results/`.

---

# 16. Project Deliverables

The repository contains:

- formal embedding design: `docs/mathematical_design.md`
- implementation: `src/`
- experimental dataset: `data/capability_dataset.json`
- experiment runner: `experiments/run_experiments.py`
- generated results: `results/`
- technical report: `report/technical_report.md`
- formatted technical report: `report/technical_report.docx`
- project documentation: `README.md`

