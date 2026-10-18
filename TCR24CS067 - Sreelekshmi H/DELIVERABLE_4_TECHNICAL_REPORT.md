
````markdown
# Deliverable 4: Technical Report

# Design of a Vector Embedding for Capability Composition

## 1. Problem Definition

The objective of this project is to design and implement a vector
representation for formally specified application capabilities.

The representation should preserve important functional relationships
between capabilities, including:

- preconditions
- effects
- inputs
- outputs
- state relationships
- goal relevance
- cost
- reliability

The main focus is determining whether atomic capabilities can be
represented numerically and composed into meaningful composite
capabilities.

The project uses an e-commerce example containing capabilities such as
CreateOrder, MakePayment, ConfirmOrder, CancelCart, and SendEmail.

---

## 2. Design Requirements

The embedding design should support the following properties:

1. Capability identity
2. State awareness
3. Precondition-effect compatibility
4. Input-output compatibility
5. Similarity measurement
6. Capability composition
7. Goal relevance
8. Operational properties

The assignment also requires experiments that investigate capability
compatibility, composition, alternative implementations, irrelevant
capabilities, and operational attributes.

---

## 3. Related Embedding Approaches

Vector embeddings are commonly used to represent objects as numerical
vectors so that relationships between objects can be analyzed
mathematically.

The motivation for this assignment is related to the idea of semantic
embeddings such as Word2Vec, but the objective here is different.

Word embeddings focus on semantic relationships between words.

This project focuses on functional relationships between capabilities.

For example:

```text
CreateOrder → MakePayment
````

is important because the output/effect of CreateOrder can satisfy the
requirements of MakePayment.

Therefore, the proposed representation is designed specifically for
functional compatibility rather than natural-language similarity.

---

## 4. Proposed Representation

A capability is represented as:

C = (I, O, P, E, Cost, Rel)

where:

I = inputs

O = outputs

P = preconditions

E = effects

Cost = execution cost

Rel = reliability

The current baseline maps each capability to a 10-dimensional vector.

The vector contains semantic facts, input/output information, cost,
and reliability.

A state and goal are represented using a four-dimensional semantic
fact vector.

---

## 5. Mathematical Formulation

The capability embedding is represented as:

φC : C → R^10

The state embedding is:

φS : S → R^4

The goal embedding is:

φG : G → R^4

For two encoded vectors A and B, cosine similarity is calculated as:

similarity(A,B) =
(A · B) / (||A|| × ||B||)

This provides a numerical measure of feature overlap between two
representations.

---

## 6. Compatibility Model

Two capabilities are considered compatible when:

1. an effect of the first capability satisfies a precondition of the
   second capability, and

2. an output of the first capability satisfies an input requirement of
   the second capability.

Therefore:

Compatible(C1,C2) =
(E1 ∩ P2 ≠ ∅)
AND
(O1 ∩ I2 ≠ ∅)

For example:

```text
CreateOrder → MakePayment
```

is compatible because:

```text
CreateOrder effect:
order_exists

MakePayment precondition:
order_exists
```

and:

```text
CreateOrder output:
order_id

MakePayment input:
order_id
```

---

## 7. Capability Composition Model

If two capabilities are compatible:

C12 = C2 ◦ C1

The composite capability uses:

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

Composition can be applied recursively to construct larger
capabilities.

For example:

```text
CreateOrder
      ↓
MakePayment
      ↓
ConfirmOrder
```

produces:

```text
CreateOrder_MakePayment_ConfirmOrder
```

---

## 8. Implementation

The implementation is written in C++17.

The main modules are:

```text
include/
    types.hpp
    embedding.hpp
    composition.hpp
    similarity.hpp

src/
    main.cpp
    embedding.cpp
    composition.cpp
    similarity.cpp
```

The implementation provides:

```text
encodeCapability()
encodeState()
encodeGoal()
canCompose()
compose()
goalSatisfied()
cosineSimilarity()
```

These functions implement the main operations required by the
assignment.

---

## 9. Experimental Methodology

The experimental dataset contains five capabilities:

* CreateOrder
* MakePayment
* ConfirmOrder
* CancelCart
* SendEmail

The experiments investigate:

### Experiment 1: Compatibility

Compare capabilities that should and should not compose.

### Experiment 2: Composition

Construct two-step and three-step composite capabilities.

### Experiment 3: Similarity vs Composability

Compare cosine similarity with actual compatibility.

### Experiment 4: Goal Relevance

Determine whether capabilities contribute to the specified goal.

### Experiment 5: Operational Attributes

Investigate cost and reliability during composition.

---

## 10. Results

### 10.1 Compatibility Results

```text
CreateOrder → MakePayment
Compatible = Yes

CreateOrder → CancelCart
Compatible = No
```

The system successfully distinguishes these two relationships using the
implemented compatibility conditions.

### 10.2 Composition Results

The system constructs:

```text
CreateOrder_MakePayment
```

with:

```text
Cost = 0.06
Reliability = 0.9702
```

It also constructs:

```text
CreateOrder_MakePayment_ConfirmOrder
```

with:

```text
Cost = 0.08
Reliability = 0.960498
```

### 10.3 Similarity Results

The observed similarity values are:

| Capability Pair           | Similarity | Compatible |
| ------------------------- | ---------: | ---------- |
| CreateOrder - MakePayment |   0.597541 | Yes        |
| CreateOrder - CancelCart  |   0.668224 | No         |
| CreateOrder - SendEmail   |   0.443541 | No         |

The results show that similarity alone cannot be used as the
composition criterion.

For example, CreateOrder and CancelCart have a higher similarity than
CreateOrder and MakePayment, but they are not composition-compatible.

---

## 11. Analysis

The experiments demonstrate that the proposed representation can
capture several useful relationships.

The compatibility mechanism distinguishes capabilities based on
precondition-effect and input-output relationships.

The composition mechanism allows atomic capabilities to be combined
into larger capabilities.

The similarity experiment demonstrates an important distinction
between functional resemblance and composability.

A capability may have similar features to another capability without
being able to follow it in a valid composition.

Operational properties can also be propagated through compositions.

For sequential capabilities, cost is accumulated while reliability is
combined multiplicatively.

---

## 12. Limitations

The current implementation is a hand-designed baseline.

The embedding dimensions are manually defined for the selected
application domain.

Therefore, introducing new facts, inputs, or outputs may require
changes to the feature representation.

The current implementation also uses a simple cosine similarity
measure.

The JSON dataset is currently stored separately and is not automatically
loaded by the C++ program.

The current compatibility implementation also uses both semantic
effect-precondition matching and interface input-output matching.

These limitations should be considered when interpreting the results.

---

## 13. Conclusion

This project presents a baseline vector representation for formally
specified capabilities.

States, goals, and capabilities are converted into numerical
representations.

Cosine similarity is used to measure vector similarity, while explicit
precondition-effect and input-output checks are used to determine
composition compatibility.

The experiments show that atomic capabilities can be combined into
composite capabilities and that similarity and composability should be
treated as different relationships.

The implementation provides a foundation for further investigation of
vector representations for capability composition.

````

### After this

At this point you will have all **4 deliverable documents**:

```text
DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md
DELIVERABLE_2_IMPLEMENTATION.md
DELIVERABLE_3_EXPERIMENTAL_DATASET.md
DELIVERABLE_4_TECHNICAL_REPORT.md
````

