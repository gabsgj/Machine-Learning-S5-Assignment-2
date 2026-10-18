# semantic_capability_composition
A generic vector embedding framework for representing, comparing, and composing capabilities using state, goal, preconditions, effects, and operational attributes such as cost, reliability, availability, and risk.

A C++ implementation of a problem-specific vector embedding framework for representing, comparing, and composing formally specified application capabilities.

## Overview

This project implements a vector representation for application states, goals, and executable capabilities.

The main objective is to investigate whether formally specified capabilities can be represented in a vector space while preserving useful functional relationships such as:

* Capability identity
* State awareness
* Precondition-effect compatibility
* Input-output compatibility
* Functional similarity
* Capability composition
* Goal relevance
* Operational properties such as cost, reliability, availability, and risk

The project is based on the **PCCST503 Assignment 2: Design of a Vector Embedding for Capability Composition**.

The assignment focuses on representing capabilities rather than performing path planning or replanning.

## Problem Statement

A capability is a reusable operation or service that transforms application state.

A capability is represented using information such as:

```text
Capability =
(Type,
 Inputs,
 Outputs,
 Preconditions,
 Effects,
 Constraints,
 Resources,
 Cost,
 Reliability,
 Availability,
 Execution Mechanism)
```

The system converts this structured information into a numerical vector.

The resulting vectors can then be compared and composed to study functional relationships between capabilities.

## System Architecture

```text
Formal State
     |
     v
 encode(state)
     |
     v
State Vector


Formal Goal
     |
     v
 encode(goal)
     |
     v
Goal Vector


Formal Capability
     |
     v
 encode(capability)
     |
     v
Capability Vector
     |
     +------------------+
     |                  |
     v                  v
Similarity         Compatibility
     |                  |
     +--------+---------+
              |
              v
        Capability
        Composition
              |
              v
      Composite Capability
              |
              v
      Composite Vector
```

## Core Operations

The implementation provides the following main operations:

```cpp
encode(state)
encode(goal)
encode(capability)
compose(capabilities)
similarity(x, y)
```

### `encode(state)`

Converts a formal application state into a numerical embedding.

### `encode(goal)`

Converts a goal specification into a numerical embedding.

### `encode(capability)`

Converts capability properties into a fixed-dimensional vector.

### `compose(capabilities)`

Creates a composite capability when the capabilities are compatible.

### `similarity(x, y)`

Measures the similarity between two embeddings using a normalized dot-product/cosine-style measure.

## Capability Compatibility

Two capabilities can compose when the effects produced by the first capability satisfy the preconditions required by the second capability.

For example:

```text
CreateOrder
    |
    | OrderExists = true
    v
MakePayment
```

Therefore:

```text
CreateOrder -> MakePayment
```

is compatible.

However:

```text
CreateOrder
    |
    | OrderExists = true
    v
CancelCart

Required:
OrderExists = false
```

is incompatible.

## Examples

The implementation demonstrates three application examples.

### 1. Story Orchestrator

Story-related capabilities are represented and tested for compatibility and composition.

Example:

```text
CreateCharacter
       |
       | CharacterExists = true
       v
CreateScene
```

The resulting capabilities can be represented as a composite story capability.

### 2. Arithmetic State Transition

The system represents arithmetic operations as state-transforming capabilities.

Example:

```text
Initial State
x = 5

     |
     v
   Add3

x = 8

     |
     v
 Multiply2

x = 16
```

This demonstrates the relationship between states, goals, preconditions, and effects.

### 3. E-Commerce Capability Composition

The e-commerce example demonstrates functional capability composition.

```text
CreateOrder
     |
     v
MakePayment
     |
     v
CompletePurchase
```

`CreateOrder` produces:

```text
OrderExists = true
```

which satisfies the precondition of `MakePayment`.

Therefore:

```text
CompletePurchase =
MakePayment ◦ CreateOrder
```

## Experiments

The implementation investigates the following experiments.

### 1. Capability Compatibility

Tests:

```text
CreateOrder -> MakePayment
CreateOrder -> CancelCart
```

Expected relationship:

```text
CreateOrder -> MakePayment
COMPATIBLE

CreateOrder -> CancelCart
INCOMPATIBLE
```

### 2. Capability Composition

The system creates a composite capability:

```text
CompletePurchase =
MakePayment ◦ CreateOrder
```

The composite capability is encoded and compared with the vector composition of its component capabilities.

### 3. Alternative Implementations

Functionally related capabilities are implemented using different mechanisms.

Examples include:

```text
PaymentAPI
PaymentDatabase
```

Their embeddings are compared to investigate whether functional similarity can be retained without treating different implementation mechanisms as identical.

### 4. Irrelevant Capability

An unrelated capability such as:

```text
SendEmail
```

is compared with an e-commerce capability to investigate whether irrelevant operations can be distinguished.

### 5. Operational Attributes

The influence of operational properties is investigated by varying attributes such as:

* Cost
* Reliability
* Availability
* Risk

Example:

```text
CheapPayment
ReliablePayment
```

## Project Structure

```text
capability-embedding/
│
├── include/
│   ├── State.h
│   ├── Goal.h
│   ├── Capability.h
│   ├── Embedding.h
│   └── EmbeddingSystem.h
│
├── src/
│   ├── main.cpp
│   └── EmbeddingSystem.cpp
│
├── experiments/
│   ├── story_orchestrator.txt
│   ├── arithmetic_state_transition.txt
│   └── ecommerce_capability_composition.txt
│
├── report/
│   └── Capability_Embedding_Report.pdf
│
├── output.txt
├── README.md
└── .gitignore
```

## Requirements

* C++
* GNU g++
* C++11 or later
* VS Code recommended

## Compilation

From the project root:

```bash
g++ -std=c++11 -Iinclude src/main.cpp src/EmbeddingSystem.cpp -o capability_embedding.exe
```

For the MinGW environment used during development:

```bash
g++ -std=c++11 -Iinclude -mconsole src/main.cpp src/EmbeddingSystem.cpp -o capability_embedding.exe
```

## Execution

Windows:

```powershell
.\capability_embedding.exe
```

Save the output:

```powershell
.\capability_embedding.exe > output.txt
```

## Results

The implementation successfully demonstrates:

* Formal state encoding
* Goal encoding
* Capability encoding
* Compatibility checking
* Capability composition
* Vector similarity
* Alternative implementation comparison
* Irrelevant capability comparison
* Operational attribute analysis

The final numerical results are reported in:

```text
report/Capability_Embedding_Report.pdf
```

## Limitations

The current implementation is a deterministic, problem-specific embedding rather than a learned neural embedding.

Symbolic features are converted into fixed numerical positions, so the representation does not automatically learn semantic relationships from a large dataset.

The implementation also does not perform:

* BFS
* DFS
* A*
* D* Lite
* LPA*
* Path search
* Replanning

These are outside the scope of this assignment.

## Future Work

Possible extensions include:

* Larger capability datasets
* Learned embeddings
* Graph-based capability representations
* Better semantic encoding of inputs and outputs
* Separate semantic and operational vectors
* More sophisticated composition operators
* Learned compatibility prediction
* Dynamic availability modelling

## Conclusion

This project investigates how formally specified application capabilities can be represented in a vector space while preserving relationships required for compatibility and composition.

The experiments demonstrate the use of vector representations for comparing atomic and composite capabilities across multiple application scenarios.

---

**Course:** PCCST503
**Assignment:** Assignment 2 – Design of a Vector Embedding for Capability Composition
**Implementation Language:** C++
**NAME:** AAKASH P D
**University Register number:** TCR24CS001

