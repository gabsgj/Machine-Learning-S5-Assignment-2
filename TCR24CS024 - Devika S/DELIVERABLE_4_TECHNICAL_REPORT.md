# Deliverable 4 — Technical Report

## 1. Problem definition
The assignment asks whether formally specified states, goals and executable capabilities can be represented in a vector space while preserving relationships required for compatibility, composition and complex functionality. The selected e-commerce domain contains clear order, payment and notification transitions.

## 2. Design requirements
The design addresses capability identity, state awareness, precondition-effect compatibility, input-output compatibility, similarity versus composability, composition, goal relevance, operational properties, consistency and efficiency.

## 3. Related embedding approaches
One-hot encoding preserves identity but gives weak graded relationships. Word2Vec-style semantic embeddings are useful for natural-language similarity but do not directly encode formal preconditions, effects or typed I/O. Graph representations preserve explicit relationships but need additional numerical treatment for QoS attributes. The proposed structured embedding combines symbolic application structure with vector similarity and is therefore purpose-built for this assignment.

## 4. Proposed representation
`phi_S` and `phi_G` share the state-variable space. `phi_C` concatenates precondition, effect, type, input, output, constraint, resource and QoS subspaces. This preserves both functional and operational information.

## 5. Mathematical formulation
Cosine similarity is used for graded comparison. Compatibility is directional and evaluates successor preconditions against predecessor effects. Input-output compatibility separately checks typed port dependencies.

## 6. Capability composition model
`CompletePurchase = SendNotification o MakePayment o CreateOrder`.

CreateOrder establishes `Order.exists=true`, which satisfies MakePayment. MakePayment establishes `Payment.status=SUCCESS`, which satisfies SendNotification. The composite therefore represents a valid three-capability workflow.

## 7. Implementation
The implementation is C++17 with a JSON dataset. It provides `encode(state)`, `encode(goal)`, `encode(capability)`, recursive `compose`, `similarity`, compatibility and input-output matching. It does not implement the Assignment 1 planner because the supplied specification explicitly excludes planner redesign.

## 8. Experimental methodology
### Experiment 1 — Capability compatibility
Required pattern:
- `CreateOrder -> MakePayment`: expected compatible.
- `CreateOrder -> CancelCart`: expected incompatible.

The implementation obtains +1.00 and -1.00 respectively because the first pair has `Order.exists=true` produced/required, while the second conflicts with `Order.exists=false`.

### Experiment 2 — Capability composition
The sequence `CreateOrder -> MakePayment -> SendNotification` is composed recursively. The resulting vector is compared with each atomic capability. Operational attributes are also aggregated.

For the supplied values, the composite has:
- time = 220 ms
- monetary cost = 0.032
- serial reliability = 0.997 × 0.990 × 0.999 = 0.9860597
- serial availability = 1.0

### Experiment 3 — Alternative implementations
`CreateOrder`, `CreateOrder_DB` and `CreateOrder_GUI` share the same main functional effects but use API, database and GUI mechanisms. Effect-vector similarity is therefore high/identical while full-vector similarity can differ because type, resources and QoS are included.

### Experiment 4 — Irrelevant capabilities
`UpdateProfile` and other capabilities that do not establish goal predicates are included. Goal-effect cosine is used as a relevance signal. Intermediate capabilities may have low direct goal similarity even when they are necessary for composition; therefore goal relevance is not treated as proof of composability.

### Experiment 5 — Operational attributes
The dataset varies cost, reliability, availability and risk. The embedding contains these attributes explicitly in its QoS block, allowing the effect of changing operational conditions to be measured without changing the functional precondition/effect blocks.

## 9. Results
The compatibility experiment distinguishes the required compatible and incompatible pairs exactly. The composition experiment produces a single composite capability with aggregated effects and QoS. Alternative implementations remain functionally related without being represented as identical capabilities because implementation type, mechanism, resources and operational values are encoded. Irrelevant capabilities can be separated using goal-effect similarity. Operational perturbations alter the QoS subvector while preserving functional structure.

## 10. Analysis
Cosine similarity is useful for retrieval and graded resemblance, but it cannot replace formal composability checks. A capability can be semantically or functionally similar to another and still fail a successor precondition. Directional compatibility therefore remains the execution-level test. Separating capability subspaces also makes it possible to analyse which differences come from function and which come from implementation/QoS.

## 11. Limitations
1. The dataset is manually constructed and small.
2. Numeric and categorical encoding is deterministic rather than learned from a large corpus.
3. Compatibility is strongest for equality-style predicates; richer logical expressions need extension.
4. Sequential composition does not model concurrency.
5. QoS normalization constants are fixed and should be calibrated for a real system.
6. The implementation is an interpretable baseline rather than a learned neural model.

## 12. Conclusion
A problem-specific vector representation has been designed and implemented for formal states, goals and executable capabilities. It explicitly represents preconditions, effects, inputs, outputs, constraints, resources, type, mechanism and operational attributes. The five required experiments demonstrate compatibility, composition, alternative implementations, goal relevance and operational sensitivity. The design therefore directly addresses the assignment's research question: how formal application structure can be embedded while preserving the relationships needed for capability compatibility and composition.
