# Assignment 2: Vector Embedding for Capability Composition

**Course:** PCCST503 Machine Learning  
**Student:** Sidharth V. Jain, B.Tech., Department of Computer Science & Engineering, Semester 5, Roll No. 62

## Submission package

This project is a Python implementation of a structured vector representation for formally specified capabilities, together with state/goal encoding, compatibility, composition, goal relevance, operational evaluation, experiments, plots, tests, and a report-ready evidence set.

### Files

- `dataset.json`: formal application and capability definitions.
- `capability_embedding.py`: implementation.
- `run_experiments.py`: evaluation and plot generation.
- `test_capability_embedding.py`: automated tests.
- `artifacts/`: CSV/JSON results and figures.
- `requirements.txt`: dependencies.

## Main interfaces

The implementation provides:

- `StateGoalEncoder.encode_state(state)`
- `StateGoalEncoder.encode_goal(goal)`
- `CapabilityEncoder.encode(capability)`
- `CapabilityEncoder.similarity(a, b)`
- `compatibility(a, b)`
- `compose([c1, c2, ...])`
- `goal_relevance(capability, goal)`

## Design principle

Vector similarity and executable compatibility are deliberately separated.

Similarity measures functional/structural relatedness across five blocks:

1. identity and mechanism;
2. inputs and outputs;
3. preconditions, effects and constraints;
4. resources;
5. operational attributes.

Compatibility is calculated directly from formal effect/precondition, output/input, and constraint relationships.

## Run

```bash
pip install -r requirements.txt
python run_experiments.py
python -m unittest test_capability_embedding.py
```

The experiments produce quantitative tables and PNG figures under `artifacts/`.

---

# Technical Report (See technical_report.pdf for the final report)


## Abstract

This project develops a structured vector representation for formally specified executable capabilities. The design follows the assignment's central requirement: the representation must preserve the information required for capability identity, state and goal relevance, compatibility, and composition. Rather than treating generic semantic similarity as equivalent to executability, the implementation separates a weighted vector similarity measure from a formal compatibility function based on preconditions, effects, inputs, outputs, and constraints.

An e-commerce purchase workflow is used as the experimental application. The system represents capabilities such as `CreateOrder`, `MakePayment`, and `SendNotification`, constructs their valid composite, and distinguishes the valid sequence `CreateOrder -> MakePayment` from the invalid sequence `CreateOrder -> CancelCart`. Operational properties including execution time, resource cost, monetary cost, risk, reliability, and availability are represented explicitly.

## 1. Problem Definition

The task is to represent states, goals, and executable capabilities in a vector space while preserving the relationships required to determine whether capabilities can be composed. The capability is treated as a structured object rather than as an unstructured text label.

For a capability:

`C = (T, I, O, P, E, K, R, Q, Rel, A, M)`

the fields represent type, inputs, outputs, preconditions, effects, constraints, resources, operational properties, reliability, availability, and execution mechanism.

The application goal is:

`Order.exists = true`
`Payment.status = SUCCESS`
`Notification.sent = true`

The intended execution chain is:

`CreateOrder -> MakePayment -> SendNotification`

## 2. Design Requirements

The implementation addresses the following requirements:

- preserve capability identity;
- encode states and goals;
- encode capability inputs and outputs;
- encode preconditions and effects;
- represent constraints and resources;
- represent operational attributes;
- distinguish functional similarity from composability;
- support composition of compatible capabilities;
- identify goal-relevant capabilities;
- provide quantitative experimental evidence.

## 3. Representation

The capability vector is divided into five blocks:

`v(C) = [v_id ; v_io ; v_logic ; v_resource ; v_operation]`

The blocks respectively encode identity/mechanism, inputs/outputs, preconditions/effects/constraints, resources, and operational properties.

Each block is vectorized separately and standardized before concatenation. This prevents one numerical scale, such as milliseconds, from dominating symbolic execution structure.

## 4. Similarity

Similarity is calculated using weighted block-level cosine similarity:

`Sim(C_i,C_j) = sum_k w_k cos(v_i^k,v_j^k)`

with:

| Block | Weight |
|---|---:|
| Identity/mechanism | 0.10 |
| Inputs/outputs | 0.25 |
| Logic | 0.40 |
| Resources | 0.10 |
| Operations | 0.15 |

The relatively high logic weight reflects the importance of preconditions and effects in executable composition.

## 5. Compatibility

Similarity alone cannot determine whether one capability may follow another. The implementation therefore defines:

`Comp(A,B) = 0.55 M_EP + 0.25 M_OI + 0.20 M_K`

where `M_EP` measures effect/precondition satisfaction, `M_OI` measures output/input matching, and `M_K` checks constraint compatibility.

A pair is considered composition-ready when its compatibility score is at least `0.75`.

For example, `CreateOrder -> MakePayment` is accepted because the first capability establishes an order and provides the information required by payment. `CreateOrder -> CancelCart` is rejected because `CancelCart` requires an absent order while `CreateOrder` establishes an existing order.

## 6. Composition

For a valid sequence:

`C_1 -> C_2 -> ... -> C_n`

the implementation creates a composite capability.

The composite:

- inherits the first capability's external preconditions;
- accumulates effects in execution order;
- retains required external inputs;
- exposes the final capability's outputs;
- unions constraints and resources;
- sums time, resource and monetary cost;
- accumulates risk additively;
- multiplies reliability;
- requires all component capabilities to be available.

For the evaluated sequence:

`CreateOrder -> MakePayment -> SendNotification`

the reliability is:

`0.99 × 0.98 × 0.97 = 0.941094`

and execution time is:

`100 + 300 + 150 = 550 ms`.

## 7. State and Goal Representation

States and goals are formal key/value structures. They share a common symbolic vector space so that the representation is not tied to a single operation sequence.

The state encoder represents facts such as authentication, cart existence, inventory availability, order existence and payment status.

The goal encoder represents the desired terminal facts.

Capability goal relevance is measured by the fraction of goal conditions directly established by a capability's effects.

## 8. Experimental Method

Four evidence groups are evaluated.

### 8.1 Compatibility classification

Eight formally selected capability pairs are evaluated: four formally compatible and four formally incompatible. The compatibility threshold is `0.75`.

### 8.2 Alternative implementations

`CreateOrder` is compared with a database implementation and a GUI implementation. These alternatives should retain functional relationships while differing in mechanism/type.

### 8.3 Irrelevant capability

`CheckInventory` is compared with `CreateOrder` to examine whether the representation distinguishes a different operation from alternative implementations of the same function.

### 8.4 Operational properties

Time, resource cost, monetary cost, risk, reliability and availability are explicitly retained. A separate utility analysis demonstrates that these attributes can be used for selection without redefining compatibility.

## 9. Results

The experiment files in `artifacts/` contain the complete numerical results.

The critical compatibility outcomes are:

| Pair | Expected | Decision |
|---|---|---|
| `CreateOrder -> MakePayment` | Compatible | Compatible |
| `CreateOrder -> CancelCart` | Incompatible | Incompatible |

The composite has:

| Attribute | Value |
|---|---:|
| Execution time | 550 ms |
| Resource cost | 7 |
| Monetary cost | 0.23 |
| Accumulated risk | 0.40 |
| Reliability | 0.941094 |
| Availability | 1 |

The alternative-implementation experiment reports the structured similarity of `C1~C5` and `C1~C6`, while the irrelevant experiment reports `C1~C7`. These values are retained in `artifacts/similarity.csv` rather than being manually rounded into the report.

## 10. Analysis

The experiments demonstrate why the implementation requires two notions of relationship.

First, vector similarity is useful for identifying functional or structural relatedness. This is particularly relevant when two capabilities have different implementation mechanisms but similar inputs, outputs, preconditions and effects.

Second, formal compatibility is required for executable composition. A capability can be semantically related to another capability without satisfying its preconditions or accepting its outputs.

The composite representation also preserves operational information, allowing the system to represent not only what a capability does but some of the practical properties of executing it.

## 11. Limitations

The evaluation is a controlled prototype rather than a learned model trained from a large corpus.

The dataset is synthetic and small. Constraint reasoning covers the explicit formal patterns represented in the dataset and is not a complete theorem prover. Embedding weights are designed rather than learned. The operational utility calculation is an illustrative selection heuristic and is intentionally separate from formal compatibility.

Consequently, the results demonstrate the feasibility and structure of the representation, not general performance across arbitrary applications.

## 12. Conclusion

The implementation provides a structured capability embedding that preserves semantic, logical and operational information while explicitly separating vector similarity from executable compatibility.

The central result is that capability composition should not be reduced to ordinary cosine similarity. Instead, vector representation provides a continuous description of capability structure, while formal precondition/effect and input/output reasoning determines whether composition is executable.

The resulting system supports state and goal encoding, capability encoding, similarity, compatibility, composition and experimental evaluation.
