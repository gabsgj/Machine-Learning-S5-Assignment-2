# Deliverable 1: Formal Embedding Design

## 1. Problem Definition

The objective of this project is to design a vector representation for
formally specified application capabilities.

A capability represents an operation that has:

- inputs
- outputs
- preconditions
- effects
- cost
- reliability

The embedding converts these symbolic properties into numerical vectors
so that capability relationships can be analyzed using mathematical
operations.

The main focus is capability compatibility and composition.

---

## 2. Capability Representation

A capability is represented as:

C = (I, O, P, E, Cost, Rel)

where:

- I = set of inputs
- O = set of outputs
- P = set of preconditions
- E = set of effects
- Cost = execution cost
- Rel = reliability

For example:

CreateOrder = (

    I = {cart_id},

    O = {order_id},

    P = {cart_exists},

    E = {order_exists},

    Cost = 0.01,

    Rel = 0.99
)

---

## 3. State Representation

A state is represented as a set of facts:

S = {f1, f2, ..., fn}

For example:

S = {cart_exists}

This represents a state where a cart currently exists.

The state is converted into a binary vector indicating which known
facts are present.

---

## 4. Goal Representation

A goal is represented as a set of desired facts:

G = {g1, g2, ..., gn}

For example:

G = {payment_success}

The goal is encoded using the same semantic fact space used for states.

---

## 5. Capability Embedding

A capability is mapped to a numerical vector:

φC : C → R^10

The current implementation uses a 10-dimensional hand-designed vector.

The dimensions represent:

| Dimension | Meaning |
|-----------|---------|
| 1 | cart_exists |
| 2 | order_exists |
| 3 | payment_success |
| 4 | order_cancelled |
| 5 | cart_id |
| 6 | order_id |
| 7 | payment_id |
| 8 | confirmation_id |
| 9 | cost |
| 10 | reliability |

Therefore:

φC(C) =
[f1, f2, f3, f4,
 f5, f6, f7, f8,
 cost, reliability]

The semantic features are binary:

fi ∈ {0,1}

while cost and reliability are numerical values.

---

## 6. State Embedding

A state is mapped to a four-dimensional vector:

φS : S → R^4

The dimensions represent:

[cart_exists,
 order_exists,
 payment_success,
 order_cancelled]

For example:

S = {cart_exists}

is represented as:

φS(S) = [1, 0, 0, 0]

---

## 7. Goal Embedding

A goal is mapped to the same four-dimensional semantic space:

φG : G → R^4

For example:

G = {payment_success}

is represented as:

φG(G) = [0, 0, 1, 0]

Using the same fact space allows the relationship between states,
capabilities, and goals to be investigated.

---

## 8. Similarity Measure

Cosine similarity is used to compare two embedding vectors.

For vectors A and B:

similarity(A,B) =
(A · B) / (||A|| ||B||)

where:

A · B is the dot product and

||A|| is the magnitude of vector A.

The similarity value lies between -1 and 1 for general vectors.

In the current non-negative embedding, larger values indicate greater
feature overlap.

Similarity is used to measure functional resemblance.

However, similarity alone does not determine whether two capabilities
can be composed.

---

## 9. Compatibility

Two capabilities C1 and C2 are considered composition-compatible when
the effects of C1 satisfy a precondition of C2.

Formally:

E1 ∩ P2 ≠ ∅

where:

E1 = effects of C1

P2 = preconditions of C2

The implementation additionally checks input-output compatibility:

O1 ∩ I2 ≠ ∅

where:

O1 = outputs of C1

I2 = inputs of C2

Therefore, the current implementation uses:

Compatible(C1,C2) =
(E1 ∩ P2 ≠ ∅)
AND
(O1 ∩ I2 ≠ ∅)

This provides both semantic compatibility and interface compatibility.

---

## 10. Capability Composition

If C1 and C2 are compatible, they can be composed:

C12 = C2 ◦ C1

The composite capability contains:

Inputs:
I12 = I1

Outputs:
O12 = O2

Preconditions:
P12 = P1

Effects:
E12 = E2

Cost:
Cost12 = Cost1 + Cost2

Reliability:
Rel12 = Rel1 × Rel2

For example:

CreateOrder → MakePayment

produces:

CreateOrder_MakePayment

with:

Cost = 0.01 + 0.05 = 0.06

Reliability = 0.99 × 0.98 = 0.9702

Composition can be extended recursively:

C123 = C3 ◦ C2 ◦ C1

---

## 11. Goal Relevance

A capability is considered relevant to a goal if one of its effects
matches a goal fact.

For capability C and goal G:

Relevant(C,G) = true

if:

E ∩ G ≠ ∅

For example:

MakePayment

has:

E = {payment_success}

and the goal is:

G = {payment_success}

Therefore:

Relevant(MakePayment,G) = true

---

## 12. Design Rationale

The proposed representation is a hand-designed baseline embedding.

It was selected because the assignment requires the representation to
preserve functional relationships rather than simply assigning an
arbitrary identifier to each capability.

The representation explicitly includes:

- state-related facts
- input/output information
- operational properties
- precondition/effect information

This allows compatibility, similarity, composition, and goal relevance
to be evaluated using numerical representations.

The assignment also requires investigation of alternative implementations,
irrelevant capabilities, and operational attributes. These will be
evaluated in later experiments.

---

## 13. Limitations

The current embedding is domain-specific.

Only a fixed set of facts and input/output types are represented in the
current vector dimensions.

Therefore, adding new capability types may require extending the
feature space.

The current representation is also a baseline rather than a learned
embedding. Future experiments will investigate alternative
representations and their effect on compatibility and composition.

---

## 14. Summary

The proposed embedding maps formal application entities into numerical
vectors:

State → φS(S)

Goal → φG(G)

Capability → φC(C)

The system then uses:

- cosine similarity for vector similarity
- precondition/effect matching for semantic compatibility
- input/output matching for interface compatibility
- composition rules for constructing composite capabilities

The design therefore provides a basis for evaluating whether vector
representations can preserve the relationships required for capability
composition.