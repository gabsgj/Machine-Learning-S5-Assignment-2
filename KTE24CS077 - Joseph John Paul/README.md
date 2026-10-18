# University Course Registration Vector Embedding

## Overview
This repository contains the complete C++17 implementation and formal documentation for the university assignment **"Design of a Vector Embedding for Capability Composition"**.

The project implements a **problem-specific, deterministic, and interpretable 65-dimensional feature-vector representation** for formal states, goals, and executable capabilities within a **University Course Registration System**.

---

## Assignment Objective
To design and evaluate a structured vector embedding that preserves:
* Formal state semantics and ternary precondition applicability.
* State transitions and state-aware sequential capability composition.
* Input-output data dependencies.
* Functional similarity versus implementation diversity.
* Quality-of-Service (QoS) operational properties (cost, reliability, availability).

*Note: In accordance with assignment constraints, this project does NOT use graph search planners (BFS, DFS, A\*, D\* Lite), machine-learning models (Word2Vec, BERT), or external AI APIs.*

---

## Application Domain
* **Domain**: University Course Registration System
* **Formal Model**: $A = (S, C, S_I, G, R, K)$
* **State Predicates (11)**: Authentication, Student Existence, Eligibility, Course Existence, Availability, Registration Window, Enrollment Hold, Tuition Settlement, Notification, Confirmation, and Reporting.
* **Capabilities ($C_1 \dots C_{11}$)**: 8 core capabilities and 3 alternative implementations.

---

## Embedding Architecture

```
+-------------------------------------------------------------------------------------------------------+
|                                  Full Capability Embedding phi_C (65 dims)                           |
+-----------+-----------+---------+---------+-----------+-------------+----------+-------------+--------+
|   P (11)  |   E (11)  |  I (5)  |  O (8)  |   R (8)   |    K (5)    |  T (6)   |    M (8)    |  Q (3) |
| Preconds  |  Effects  |  Inputs | Outputs | Resources | Constraints | Type 1hot| Mech. 1-hot | QoS    |
+-----------+-----------+---------+---------+-----------+-------------+----------+-------------+--------+
|                                    Functional Embedding phi_F (35 dims)                              |
+-------------------------------------------------------------------------------------------------------+
```

* **State Vector $\phi_S(S)$**: $11$ dimensions $\in \{-1, +1\}^{11}$
* **Goal Vector $\phi_G(G)$**: $11$ dimensions $\in \{-1, 0, +1\}^{11}$
* **Functional Embedding $\phi_F(C)$**: $35$ dimensions ($P:11 + E:11 + I:5 + O:8$)
* **Full Capability Embedding $\phi_C(C)$**: $65$ dimensions ($P:11 + E:11 + I:5 + O:8 + R:8 + K:5 + T:6 + M:8 + Q:3$)

---

## Project Structure

```
UNIVERSITY_COURSE_REGISTRATION_EMBEDDING/
│
├── main.cpp                              # Complete C++17 implementation
├── embedding.exe                         # Compiled executable binary
├── README.md                             # Project overview & documentation guide
├── USAGE.md                              # Detailed build & execution instructions
│
├── data/
│   └── course_registration_dataset.json  # Complete serialized dataset
│
├── DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md
├── DELIVERABLE_2_IMPLEMENTATION.md
├── DELIVERABLE_3_EXPERIMENTAL_DATASET.md
└── DELIVERABLE_4_TECHNICAL_REPORT.md
```

---

## Requirements
* C++17 compliant compiler:
  * Windows: MinGW-w64 GCC (g++ 8.0+), MSVC (2017+), or Clang
  * Linux: GCC (`g++`) or Clang (`clang++`)
  * macOS: Apple Clang or Homebrew GCC
* Zero external third-party dependencies (Standard C++ STL only).

---

## Build Instructions

Using MinGW / GCC:
```powershell
g++ -std=c++17 main.cpp -o embedding.exe
```

Using MSVC:
```cmd
cl /std:c++17 /EHsc main.cpp /Fe:embedding.exe
```

---

## Run Instructions

```powershell
.\embedding.exe
```

---

## Experiments

1. **Experiment 1: Compatibility**: Validates $C_3 \to C_4$ and catches negative precondition conflict in $C_4 \to C_7$.
2. **Experiment 2: Composition Sequence**: Executes primary sequence $C_1 \to C_2 \to C_3 \to C_4 \to C_5 \to C_6$, verifies goal satisfaction, and synthesizes composite properties ($\text{Cost}=39.0, \text{Rel}\approx 92.2\%$).
3. **Experiment 3: Alternative Implementations**: Compares $C_9$ (API), $C_{10}$ (DATABASE), and $C_{11}$ (FUNCTION), demonstrating identical functional vectors ($\phi_F = 1.0000$) with divergent implementation coordinates ($\phi_C < 1.0000$).
4. **Experiment 4: Irrelevant Capabilities**: Demonstrates that $C_8$ has $0.0000$ direct goal relevance despite becoming applicable after $C_3$.
5. **Experiment 5: Operational QoS**: Evaluates normalized cost, reliability, and availability metrics.

---

## Expected Results
* **16/16 Unit Assertions**: `[PASS]`
* **Goal Satisfaction**: `YES`
* **Composite Cost**: `39.0000`
* **Composite Reliability**: `0.9224`

---

## Deliverables
* [DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md](file:///c:/Users/josep/OneDrive/Desktop/GIThings/New%20folder/DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md)
* [DELIVERABLE_2_IMPLEMENTATION.md](file:///c:/Users/josep/OneDrive/Desktop/GIThings/New%20folder/DELIVERABLE_2_IMPLEMENTATION.md)
* [DELIVERABLE_3_EXPERIMENTAL_DATASET.md](file:///c:/Users/josep/OneDrive/Desktop/GIThings/New%20folder/DELIVERABLE_3_EXPERIMENTAL_DATASET.md)
* [DELIVERABLE_4_TECHNICAL_REPORT.md](file:///c:/Users/josep/OneDrive/Desktop/GIThings/New%20folder/DELIVERABLE_4_TECHNICAL_REPORT.md)

---

## Limitations
* Static predicate, resource, and constraint universes.
* Independent failure assumption for sequential reliability ($\prod Rel_i$).
* Similarity is non-predictive of composability without state-aware transition verification.
