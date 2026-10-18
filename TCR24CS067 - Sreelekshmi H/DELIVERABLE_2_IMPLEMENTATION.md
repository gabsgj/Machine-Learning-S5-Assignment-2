````markdown
# Deliverable 2: Implementation

## 1. Implementation Overview

The proposed capability embedding system is implemented in C++17.

The implementation is divided into separate modules for:

- data representation
- embedding
- capability composition
- similarity calculation
- experimental execution

The project follows a modular structure so that the embedding and
composition methods can be modified independently.

---

## 2. Project Structure

```text
Capability-Embedding/
│
├── include/
│   ├── types.hpp
│   ├── embedding.hpp
│   ├── composition.hpp
│   └── similarity.hpp
│
├── src/
│   ├── main.cpp
│   ├── embedding.cpp
│   ├── composition.cpp
│   └── similarity.cpp
│
├── data/
│   └── capabilities.json
│
├── DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md
├── DELIVERABLE_2_IMPLEMENTATION.md
├── DELIVERABLE_3_EXPERIMENTAL_DATASET.md
├── DELIVERABLE_4_TECHNICAL_REPORT.md
├── Makefile
└── README.md
````

---

## 3. Data Representation

The `Capability` structure represents an atomic capability.

It contains:

* name
* inputs
* outputs
* preconditions
* effects
* cost
* reliability

Example:

```cpp
struct Capability {
    std::string name;

    std::vector<std::string> inputs;
    std::vector<std::string> outputs;

    std::vector<std::string> preconditions;
    std::vector<std::string> effects;

    double cost;
    double reliability;
};
```

The `State` structure stores the current state facts.

The `Goal` structure stores the desired goal facts.

---

## 4. Capability Encoding

The function:

```cpp
encodeCapability(const Capability& capability)
```

converts a capability into a numerical vector.

The current implementation produces a 10-dimensional vector.

The first dimensions represent semantic facts and input/output features.

The final two dimensions represent:

* cost
* reliability

For example:

```text
CreateOrder

[1, 1, 0, 0, 1, 1, 0, 0, 0.01, 0.99]
```

This allows symbolic capability information to be processed using
numerical operations.

---

## 5. State Encoding

The function:

```cpp
encodeState(const State& state)
```

converts an application state into a numerical vector.

The current implementation uses four dimensions:

```text
[cart_exists,
 order_exists,
 payment_success,
 order_cancelled]
```

For example:

```text
State = {cart_exists}

Vector = [1, 0, 0, 0]
```

---

## 6. Goal Encoding

The function:

```cpp
encodeGoal(const Goal& goal)
```

converts a goal specification into a numerical vector.

The same four-dimensional semantic space is used for the goal.

For example:

```text
Goal = {payment_success}

Vector = [0, 0, 1, 0]
```

Using the same semantic feature space makes it possible to compare
state and goal representations.

---

## 7. Compatibility

The function:

```cpp
canCompose(first, second)
```

checks whether two capabilities can be connected.

Two conditions are currently checked.

### Effect-precondition compatibility

An effect of the first capability must match a precondition of the
second capability.

```text
effect(first) == precondition(second)
```

### Output-input compatibility

An output of the first capability must match an input of the second
capability.

```text
output(first) == input(second)
```

The current implementation requires both conditions.

Therefore:

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

## 8. Capability Composition

The function:

```cpp
compose(first, second)
```

constructs a composite capability.

For:

```text
C1 = CreateOrder
C2 = MakePayment
```

the resulting capability is:

```text
CreateOrder_MakePayment
```

The composition combines the properties of the two capabilities.

### Inputs

The inputs of the first capability are used.

### Outputs

The outputs of the second capability are used.

### Preconditions

The preconditions of the first capability are used.

### Effects

The effects of the second capability are used.

### Cost

The costs are added:

```text
Cost = Cost1 + Cost2
```

### Reliability

The reliabilities are multiplied:

```text
Reliability = Reliability1 × Reliability2
```

For example:

```text
Cost = 0.01 + 0.05
     = 0.06

Reliability = 0.99 × 0.98
            = 0.9702
```

---

## 9. Goal Relevance

The function:

```cpp
goalSatisfied(capability, goal)
```

checks whether a capability produces a fact required by the goal.

For example:

```text
Capability:
MakePayment

Effect:
payment_success

Goal:
payment_success
```

Therefore:

```text
MakePayment → Relevant
```

---

## 10. Similarity

The function:

```cpp
cosineSimilarity(a, b)
```

compares two embedding vectors using cosine similarity.

The mathematical formula is:

```text
similarity(A,B) =
(A · B) / (||A|| × ||B||)
```

The implementation calculates:

1. dot product
2. magnitude of vector A
3. magnitude of vector B
4. final cosine similarity

If either vector has zero magnitude, the implementation returns:

```text
0
```

---

## 11. Experimental Examples

The current implementation produces the following examples.

### Compatible capabilities

```text
CreateOrder → MakePayment
Similarity = 0.597541
Compatibility = Yes
```

### Incompatible capabilities

```text
CreateOrder → CancelCart
Similarity = 0.668224
Compatibility = No
```

This is an important result.

`CreateOrder` and `CancelCart` have a relatively high similarity,
but they cannot be composed under the current compatibility rules.

Therefore:

```text
Similarity ≠ Compatibility
```

This demonstrates an important requirement of the assignment: functional
resemblance and composability are different relationships.

---

## 12. Three-Step Composition

The implementation also supports recursive composition.

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

The resulting operational attributes are:

```text
Cost = 0.08

Reliability = 0.960498
```

This demonstrates that atomic capabilities can be combined into a
larger composite capability.

---

## 13. Compilation

The project is compiled using C++17:

```powershell
C:\msys64\ucrt64\bin\g++.exe -std=c++17 -Iinclude src/main.cpp src/embedding.cpp src/composition.cpp src/similarity.cpp -o capability.exe
```

The program can then be executed using:

```powershell
.\capability.exe
```

---

## 14. Implementation Limitations

The current implementation is a baseline implementation.

The JSON dataset is currently provided as the experimental dataset,
but the C++ program does not yet automatically load the JSON file.

The feature space is also manually defined.

Therefore, new facts or input/output types require corresponding
changes to the embedding implementation.

These limitations will be considered in the experimental analysis and
technical report.

```

This document now explains **what each C++ file/function actually does**, rather than just showing code.


```
