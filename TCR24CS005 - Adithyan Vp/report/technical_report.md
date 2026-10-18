# Technical Report — Vector Embedding for Capability Composition

## 1. Problem definition

The assignment asks for a problem-specific vector representation for formally specified states,
goals, and executable capabilities. The representation must preserve functional relationships
needed to identify compatible capabilities and construct complex capabilities from smaller ones.

The application is modeled as:

`A = (S, C, S_I, G, R, K)`

where `S` is the state space, `C` is the capability set, `S_I` is the initial state, `G` is the
goal specification, `R` is the resource set, and `K` is the global constraint/policy set.

A capability is represented using type, inputs, outputs, preconditions, effects, constraints,
resources, cost, reliability, and availability.

## 2. Design requirements

The implementation addresses:

- capability identity
- state awareness
- precondition-effect compatibility
- input-output compatibility
- functional similarity versus composability
- composition
- goal relevance
- cost, reliability, availability, risk, and resources

Planning algorithms are intentionally not implemented because they are outside this assignment's
scope.

## 3. Related embedding approaches

### Word2Vec-style semantic embeddings

Distributed word representations place semantically related words near each other. They are useful
for language semantics, but a generic language embedding does not directly guarantee that an effect
satisfies a precondition.

### One-hot / feature embeddings

One-hot representations are interpretable but become sparse and do not naturally express
relationships between structured fields.

### Graph representations

Capability composition can naturally be represented as a graph whose edges express compatibility.
Graph methods are powerful, but this project uses a vector representation as the primary artifact
and computes compatibility from structured feature overlap.

### Proposed approach

The project combines structured symbolic features with a deterministic hashed feature space.
This is intentionally a custom representation rather than simply applying an existing pretrained
embedding model.

## 4. Proposed representation

For capability `C_i`, the embedding is:

`phi_C(C_i) = Normalize([F_i, 0.25 M_i, Q_i])`

where:

- `F_i` = functional feature vector
- `M_i` = mechanism feature vector
- `Q_i` = normalized operational vector

Functional features include:

- capability type
- input name/type/domain/required flag
- output name/type/domain
- preconditions
- effects
- constraints
- resources

Mechanism features include API endpoints, database operations, GUI components, event handlers,
etc.

Operational features include time, resource cost, monetary cost, risk, energy, reliability,
availability, and resource count.

The mechanism block has lower weight so that implementation details do not dominate functional
relationships.

## 5. Mathematical formulation

For a feature set `X`, a deterministic hash maps each feature to a position in a fixed-dimensional
vector:

`h(X) in R^d`

The final capability vector is:

`phi_C(C) = Normalize([h(F), 0.25 h(M), Q])`

State and goal vectors use the same deterministic feature-space idea.

Similarity is cosine similarity:

`sim(x,y) = (x dot y) / (||x|| ||y||)`

## 6. Compatibility model

For consecutive capabilities `C_i` and `C_j`, compatibility is based primarily on:

1. effect/precondition agreement
2. output/input type agreement
3. shared state-variable agreement

A simplified score is:

`Compat = 0.55 E + 0.25 IO + 0.20 S + 0.10 max(sim(C_i,C_j),0)`

with the result clipped to `[0,1]`.

This is deliberately different from pure similarity. Two capabilities can be functionally similar
without being composable.

## 7. Capability composition

For a valid chain:

`C1 : S0 -> S1`
`C2 : S1 -> S2`
`C3 : S2 -> S3`

the composite capability is:

`C123 = C3 o C2 o C1`

The implementation represents the composite vector as the normalized mean of its component vectors,
while also retaining the ordered compatibility links. The links preserve the compositional structure
that a plain average cannot preserve by itself.

## 8. Implementation

The implementation is contained in `src/capability_embedding.py`.

Supported operations:

- `encode_state(state)`
- `encode_goal(goal)`
- `encode_capability(capability)`
- `compose(capabilities)`
- `similarity(x, y)`
- `compatibility(c1, c2)`
- `goal_relevance(capability, goal)`

The dataset is stored in `data/dataset.json`.

## 9. Experimental methodology

Five experiments are included.

### Experiment 1 — Capability compatibility

`CreateOrder -> MakePayment` is expected to be compatible because `CreateOrder` produces
`Order.exists = true`, satisfying a precondition of `MakePayment`.

`CreateOrder -> CancelCart` is expected to be incompatible because `CancelCart` requires
`Order.exists = false`.

### Experiment 2 — Capability composition

The chain:

`CreateOrder -> MakePayment -> SendNotification`

is represented as the composite. `MakePayment` produces `Payment.status = SUCCESS`, which satisfies the notification precondition:

`CompletePurchase = SendNotification o MakePayment o CreateOrder`

The implementation checks each adjacent compatibility link.

### Experiment 3 — Alternative implementations

`CreateOrder`, `CreateOrderDB`, and `CreateOrderGUI` implement the same functional effect using
different mechanisms. Their functional similarity is expected to be higher than their similarity
to an unrelated capability such as `ViewProfile`.

### Experiment 4 — Irrelevant capabilities

`ViewProfile` does not contribute to the purchase goal. Goal relevance is computed from effect/goal
feature overlap.

### Experiment 5 — Operational attributes

Reliability, availability, time, money, and risk are included in the representation and reported
separately for analysis.

## 10. Results

Run:

```bash
python experiments/run_experiments.py
```

The program reports the actual compatibility scores, composition validity, alternative-implementation
similarities, goal relevance, and operational values for the supplied dataset.

The expected qualitative outcomes are:

- `CreateOrder -> MakePayment` > `CreateOrder -> CancelCart`
- `CreateOrder -> MakePayment -> SendNotification` is a valid composition
- alternative implementations of `CreateOrder` remain functionally closer to each other than to
  `ViewProfile`
- `ViewProfile` has low relevance to the purchase goal
- operational properties remain directly inspectable

## 11. Analysis

The strongest part of the representation is interpretability. Every vector component is traceable
to a formal capability attribute. This makes it possible to explain why two capabilities are similar
or compatible.

The design also separates two concepts that must not be confused:

- **similarity**: functional resemblance
- **compatibility**: whether one capability can feed another

The lower mechanism weight allows API, database, and GUI implementations to be related without
making them identical.

## 12. Limitations

1. Hashing can cause feature collisions.
2. The compatibility rules are intentionally conservative and are not a complete theorem prover.
3. The composite vector uses a mean, so ordering must be retained separately through compatibility
   links.
4. Numeric and temporal constraints are only partially interpreted.
5. The dataset is small and application-specific.
6. Learned embeddings could capture richer nonlinear relationships if a sufficiently large dataset
   were available.

## 13. Conclusion

A custom structured vector representation can encode the important functional properties of formal
capabilities. The implementation distinguishes capability identity, captures state/precondition/
effect relationships, supports input-output compatibility, represents compositions, evaluates goal
relevance, and exposes operational properties.

The central result is that capability composition should not be reduced to ordinary vector
similarity. A useful embedding must preserve the structured dependency between what a capability
requires and what it produces.

## 14. Repository usage

```bash
git add .
git commit -m "Implement Assignment 2 capability embedding"
git push
```
