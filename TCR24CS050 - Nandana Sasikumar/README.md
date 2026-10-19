# Vector Embedding for Capability Composition

This repository contains the complete implementation and technical report for **Assignment 2: Design of a Vector Embedding for Capability Composition**.

## Repository Structure & Deliverables

- **`capability_embedding.py` (Deliverables 1 & 2):**
  Core Python module implementing formal entities (`State`, `Goal`, `Capability`, `QoS`, `Domain`) and vector functions:
  - `encode(entity, domain)`: Universal encoder for states, goals, and capabilities
  - `similarity(c1, c2, domain, mode)`: Cosine similarity for functional equivalence vs total vector
  - `compatibility(c1, c2, domain)`: Directional precondition-effect compatibility ($C_1 \to C_2$)
  - `goal_relevance(c, goal, domain)`: Target goal contribution score
  - `compose(capabilities, domain)`: Sequential capability composition algebra ($C_2 \circ C_1$)

- **`dataset.py` (Deliverable 3):**
  The formally specified E-Commerce order fulfillment dataset from the assignment PDF, including initial state $S_I$, goal $G$, and atomic capabilities ($C_1$ to $C_7$).

- **`run_experiments.py` (Required Experiments):**
  Automated runner for the 5 experiments specified in Section 7 of the PDF:
  1. Capability compatibility ($C_1 \to C_2$ vs $C_1 \to C_3$ and asymmetry)
  2. Capability composition ($C_1 \to C_2 \to C_6$ composite vector)
  3. Alternative implementations (API vs Database vs GUI)
  4. Irrelevant capabilities (goal relevance ranking)
  5. Operational QoS trade-offs (latency, cost, reliability)
  Also generates visual summary plot `experiment_results.png`.

- **`test_capability_embedding.py`:**
  Unit test suite verifying vector encoding shapes, algebra, compatibility, and edge cases.

- **`REPORT.md` (Deliverable 4):**
  Comprehensive 12-section technical report addressing all assignment questions and evaluation criteria.

---

## How to Run

### 1. Run All 5 Experiments
```bash
python3 run_experiments.py
```

### 2. Run the Unit Tests
```bash
python3 -m unittest test_capability_embedding.py
```
