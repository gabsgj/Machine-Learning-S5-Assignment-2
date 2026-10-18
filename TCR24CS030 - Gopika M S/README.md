# PCCST503 Assignment 2 — Vector Embedding for Capability Composition

## Design of a Vector Embedding for Capability Composition

This repository implements a **problem-specific vector representation** for formally specified application states, goals, and executable capabilities.

The system is designed around the assignment requirements:

- capability identity
- state awareness
- precondition–effect compatibility
- input–output compatibility
- similarity versus composability
- capability composition
- goal relevance
- operational properties such as cost, reliability, availability, risk, and resources

The implementation is intentionally **structured and explainable**. Instead of treating a capability as an arbitrary text string, it encodes its formal fields into feature groups and combines them into one vector.

---

## Repository Structure

```text
PCCST503_Assignment2_GitHub_Repo/
│
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
│
├── src/
│   ├── __init__.py
│   ├── capability_embedding.py
│   └── run_experiments.py
│
├── tests/
│   └── test_embedding.py
│
├── dataset/
│   └── capability_dataset.csv
│
├── results/
│   ├── experiment_results.csv
│   └── experiment_summary.md
│
└── report/
    └── PCCST503_Assignment2_Technical_Report.md
```

---

## 1. Main Idea

A capability is represented formally as:

```text
C = (T, I, O, P, E, K, R, Q, Rel, A, M)
```

where:

- `T` = capability type
- `I` = inputs
- `O` = outputs
- `P` = preconditions
- `E` = effects
- `K` = constraints
- `R` = resources
- `Q` = quality/cost attributes
- `Rel` = reliability
- `A` = availability
- `M` = execution mechanism

The assignment specification gives these components and asks the embedding to preserve useful functional relationships. 

This project therefore uses a structured vector with feature groups:

```text
v(C) =
[
  identity/function features,
  input features,
  output features,
  precondition features,
  effect features,
  resource features,
  mechanism features,
  operational features
]
```

A separate compatibility score is used for composition because **similarity and composability are not the same thing**.

---

## 2. Important Design Decision

A cosine similarity score answers:

> "How functionally similar are these capabilities?"

A compatibility score answers:

> "Can the first capability provide what the second capability requires?"

For example:

```text
CreateOrder -> MakePayment
```

is compatible because:

```text
CreateOrder:
    effect = Order.exists = true

MakePayment:
    precondition = Order.exists = true
```

But:

```text
CreateOrder -> CancelCart
```

is not compatible when `CancelCart` requires:

```text
Order.exists = false
```

This follows the assignment's compatibility example.

---

## 3. Installation

Python 3.9+ is recommended.

```bash
pip install -r requirements.txt
```

---

## 4. Run the Project

From the repository root:

```bash
python src/run_experiments.py
```

This performs the required experiments and writes:

```text
results/experiment_results.csv
results/experiment_summary.md
```

---

## 5. Run Tests

```bash
python -m unittest discover -s tests -v
```

---

## 6. Main Functions

The implementation supports the required operations:

```python
encode_state(state)
encode_goal(goal)
encode_capability(capability)
compose(capabilities)
similarity(x, y)
compatibility(c1, c2)
goal_relevance(capability, goal)
```

---

## 7. Experiments

The experiment suite covers:

### Experiment 1 — Capability Compatibility

Tests:

```text
CreateOrder -> MakePayment       compatible
CreateOrder -> CancelCart        incompatible
```

### Experiment 2 — Capability Composition

Tests:

```text
CreateOrder -> MakePayment -> SendNotification
```

and constructs:

```text
CompletePurchase
```

### Experiment 3 — Alternative Implementations

Compares:

```text
CreateOrderAPI
CreateOrderDatabase
CreateOrderGUI
```

They have similar functional effects but different implementation mechanisms.

### Experiment 4 — Irrelevant Capabilities

Checks whether:

```text
UpdateProfile
```

is less relevant to the purchase goal than:

```text
CreateOrder
MakePayment
SendNotification
```

### Experiment 5 — Operational Attributes

Compares capabilities using:

- reliability
- monetary cost
- availability
- risk
- resource requirements

---

## 8. Interpretation

The embedding is not intended to prove that one universal vector space exists for all software systems.

It demonstrates that a structured representation can preserve enough information to investigate:

```text
formal capability
       ↓
vector representation
       ↓
similarity
       ↓
compatibility
       ↓
composition
       ↓
goal relevance
```

---

## 9. Limitations

1. The feature vocabulary is manually designed for the demonstration application.
2. The current implementation uses symbolic feature encoding rather than a learned neural embedding.
3. Dynamic availability is represented by a scalar availability value; time-dependent availability could be extended to `A(t)`.
4. Constraints are represented using explicit feature tokens rather than a full constraint solver.
5. The experiment dataset is intentionally small because the purpose is to test the representation, not to train a production-scale model.

---

## 10. Assignment Deliverables

This repository provides:

### Deliverable 1 — Formal embedding design
See:

```text
report/PCCST503_Assignment2_Technical_Report.md
```

### Deliverable 2 — Implementation
See:

```text
src/capability_embedding.py
```

### Deliverable 3 — Experimental dataset
See:

```text
dataset/capability_dataset.csv
```

### Deliverable 4 — Technical report
See:

```text
report/PCCST503_Assignment2_Technical_Report.md
```

---

## Author

PCCST503 — Assignment 2
