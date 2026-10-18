SREE LEKSHMI H
TCR24CS067

````markdown
# Capability Embedding

A C++ implementation of a vector embedding framework for representing
capabilities, states, and goals, and reasoning about capability compatibility
and composition.

## Project Overview

This project implements a hand-designed vector representation for capabilities.
Each capability is represented using its preconditions, effects, inputs,
outputs, cost, and reliability.

The project demonstrates:

- Capability embedding
- State and goal representation
- Cosine similarity
- Capability compatibility
- Capability composition
- Multi-step composition
- Goal relevance
- Cost and reliability representation

## Project Structure

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
└── README.md
````

## Capability Vector

Each capability is represented using an 18-dimensional vector:

```text
[ Preconditions | Effects | Inputs | Outputs | Cost | Reliability ]
```

The representation separates preconditions from effects and inputs from
outputs so that the direction of capability interactions can be preserved.

## Example

Two capabilities used in the project are:

```text
CreateOrder
    Precondition: cart_exists
    Effect: order_exists

MakePayment
    Precondition: order_exists
    Effect: payment_success
```

Since the effect of `CreateOrder` satisfies the precondition of `MakePayment`,
the two capabilities can be composed.

```text
CreateOrder → MakePayment
```

The resulting composite capability has:

```text
Cost = 0.06
Reliability = 0.9702
```

## Experiments

The implementation evaluates:

1. Capability compatibility
2. Capability composition
3. Similarity between capabilities
4. Similarity versus composability
5. Goal relevance
6. Operational properties such as cost and reliability

One important observation is that vector similarity alone does not determine
whether two capabilities are composable.

## Technologies

* C++
* C++17
* MSYS2 UCRT64 GCC
* Standard C++ Library

## Compilation

From the project directory:

```powershell
C:\msys64\ucrt64\bin\g++.exe -std=c++17 -Iinclude src/main.cpp src/embedding.cpp src/composition.cpp src/similarity.cpp -o capability.exe
```

## Run

```powershell
.\capability.exe
```


