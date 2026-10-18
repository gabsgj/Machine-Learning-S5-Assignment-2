# Mathematical and Formal Design

## 1. Purpose

This document describes the formal representation used by the capability embedding implementation.

The design is based on the assignment model in which an application contains states, goals, executable capabilities, resources, and constraints. The purpose of the embedding is not merely to identify capabilities, but to preserve information useful for compatibility, composition, and goal relevance.

---

## 2. Application Model

An application is represented conceptually as:

```text
A = (S, C, S_I, G, R, K)
```

where:

- `S` = state space
- `C` = set of capabilities
- `S_I` = initial state
- `G` = goal specification
- `R` = resources
- `K` = constraints and policies

A state is a collection of variable-value assignments. For example:

```text
User.authenticated = true
Cart.exists = true
Order.exists = false
Payment.status = NOT_STARTED
```

A goal is a collection of conditions that must hold in a desired final state.

---

## 3. Capability Model

Each capability is represented as:

```text
C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
```

The components are:

| Component | Meaning |
|---|---|
| `T_i` | Capability type |
| `I_i` | Inputs |
| `O_i` | Outputs |
| `P_i` | Preconditions |
| `E_i` | Effects |
| `K_i` | Constraints |
| `R_i` | Required resources |
| `Q_i` | Quality and cost attributes |
| `Rel_i` | Reliability |
| `A_i` | Availability |
| `M_i` | Execution mechanism |

The implementation stores these fields explicitly rather than converting the capability into an unstructured text string.

---

## 4. Embedding Function

The capability embedding is defined as:

```text
phi_C : C -> R^80
```

where `R^80` denotes an 80-dimensional real-valued vector space.

The vector is divided into structured blocks:

```text
phi_C(C) = [phi_T, phi_I, phi_O, phi_P,
            phi_E, phi_KR, phi_OP, phi_CM]
```

where:

- `phi_T` = type and mechanism block
- `phi_I` = input block
- `phi_O` = output block
- `phi_P` = precondition block
- `phi_E` = effect block
- `phi_KR` = constraint and resource block
- `phi_OP` = operational block
- `phi_CM` = composition metadata block

The symbolic blocks use deterministic feature hashing. Numerical operational values are normalized and placed in the operational block.

The complete vector is L2-normalized before similarity calculations.

---

## 5. State Embedding

A state is mapped into the same 80-dimensional vector space:

```text
phi_S : S -> R^80
```

State variables are converted into symbolic features such as:

```text
User.authenticated=true
Order.exists=false
Payment.status=NOT_STARTED
```

This allows the representation to capture state-specific information without requiring a separate vector size for every application.

---

## 6. Goal Embedding

A goal is represented by its required conditions:

```text
phi_G : G -> R^80
```

For example, the purchase goal in the supplied dataset contains:

```text
Order.exists = true
Payment.status = SUCCESS
Notification.sent = true
```

These conditions are converted into goal features and embedded into the same fixed-dimensional space.

---

## 7. Similarity

For vectors `x` and `y`, similarity is measured using cosine similarity:

```text
similarity(x, y) = dot(x, y) / (norm(x) * norm(y))
```

Because the vectors are normalized, this is equivalent to their dot product after normalization.

The implementation exposes the operation through:

```python
StructuredEmbedder.similarity(x, y)
```

Similarity is intentionally treated as a geometric relationship rather than as a proof of composability.

---

## 8. Directed Compatibility

For two capabilities `C_i` and `C_j`, the system evaluates the transition:

```text
C_i -> C_j
```

The compatibility score is:

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

For the experiments, the composability threshold is:

```text
Comp(C_i, C_j) >= 0.70
```

The function is directional. In general:

```text
Comp(C_i, C_j) != Comp(C_j, C_i)
```

because the effects of the first capability are compared against the preconditions of the second capability.

---

## 9. Effect and Precondition Satisfaction

Suppose capability `C_i` produces:

```text
Order.exists = true
```

and capability `C_j` requires:

```text
Order.exists = true
```

The corresponding precondition is satisfied.

However, if `C_j` requires:

```text
Order.exists = false
```

then the effect of `C_i` does not satisfy the precondition.

This distinction is the main reason that ordinary vector similarity cannot be used as the complete definition of capability compatibility.

---

## 10. Input and Output Compatibility

The second major compatibility component compares outputs from the predecessor with required inputs of the successor.

For example:

```text
CreateOrder output:
order_id : UUID
```

and:

```text
MakePayment input:
order_id : UUID
```

provide a compatible interface.

The implementation computes the fraction of required successor inputs that can be supplied by predecessor outputs.

---

## 11. Composition Rule

A sequence is considered composable when all adjacent transitions satisfy the compatibility threshold:

```text
C1 -> C2 -> ... -> Cn
```

requires:

```text
Comp(C1, C2) >= 0.70
Comp(C2, C3) >= 0.70
...
Comp(Cn-1, Cn) >= 0.70
```

The implementation therefore checks local compatibility before constructing a composite capability.

---

## 12. Composite Capability

For the supplied example:

```text
CreateOrder -> MakePayment -> SendNotification
```

the composite capability is named:

```text
CompletePurchase
```

The formal composite retains the ordered component list.

Its boundary properties are derived as follows:

```text
Inputs       = inputs of the first capability
Outputs      = outputs of the final capability
Preconditions = preconditions of the first capability
Effects      = effects of the final capability
Resources    = union of component resources
```

Operational properties are aggregated as:

```text
Reliability = product of component reliabilities
Availability = minimum component availability
Time cost = sum of component time costs
Resource cost = sum of component resource costs
Money cost = sum of component money costs
Energy cost = sum of component energy costs
```

Risk is aggregated as the probability that at least one component risk occurs.

---

## 13. Composite Vector

The composite vector is constructed from the component vectors using mean aggregation followed by normalization.

Conceptually:

```text
v_composite = normalize(mean(v_1, v_2, ..., v_n))
```

This provides a compact geometric representation of the overall capability sequence.

The design deliberately keeps the exact ordered component list in the formal composite object because a simple mean vector cannot completely preserve sequence order.

---

## 14. Goal Relevance

Goal relevance is evaluated by comparing capability effects with goal conditions.

A capability whose effects satisfy more required goal conditions receives a higher relevance value than a capability whose effects are unrelated to the goal.

For the supplied purchase goal:

```text
Order.exists = true
Payment.status = SUCCESS
Notification.sent = true
```

`UpdateProfile` is unrelated because its effect concerns a user profile rather than any of the purchase conditions.

The complete three-capability sequence reaches all three target conditions and therefore receives full goal relevance in the supplied evaluation.

---

## 15. Operational Representation

Operational properties are included explicitly rather than being treated as ordinary symbolic features.

The dataset provides values such as:

- execution time
- resource cost
- monetary cost
- risk
- energy
- reliability
- availability

This allows capabilities with similar functional behaviour but different operational characteristics to remain distinguishable.

---

## 16. Design Interpretation

The representation has two complementary roles:

1. **Vector representation:** useful for geometric similarity, clustering, retrieval, and goal-oriented comparison.
2. **Explicit compatibility model:** useful for exact directed reasoning about inputs, outputs, preconditions, effects, and resources.

The combination is preferable to relying on a single similarity score for all reasoning tasks.

---

## 17. Limitations of the Mathematical Design

The current representation is a deterministic baseline.

Its main limitations are:

- feature hashing can produce collisions
- compatibility weights are manually selected
- weights are not learned from observed compositions
- the dataset is small
- mean aggregation does not fully encode sequence order
- the vector alone does not guarantee exact logical compatibility

These limitations should be considered when interpreting experimental results.

---

## 18. Future Extension

The current design can be extended by learning the representation from a larger corpus of formal capabilities and observed composition relationships.

Possible approaches include learned projection layers, graph-based embeddings, sequence models, contrastive learning, and jointly learned compatibility functions.
