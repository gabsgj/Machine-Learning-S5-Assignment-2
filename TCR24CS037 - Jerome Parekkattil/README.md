# Assignment 2 — Vector Embedding for Capability Composition

## Structured Capability Embedding (SCE)

This repository contains an implementation and experimental evaluation for **Assignment 2: Design of a Vector Embedding for Capability Composition**.

The project investigates a central question:

> **How can formally specified states, goals, and executable capabilities be represented in a vector space such that the representation preserves the relationships required for capability compatibility, composition, and the construction of complex application functionality?**

The solution proposed here is called **Structured Capability Embedding (SCE)**.

---

# 1. Project Objective

The assignment moves the focus from Assignment 1's planning/replanning process to the representation of the operations that make up a plan.

A capability is treated as a formally specified operation with:

- inputs,
- outputs,
- preconditions,
- effects,
- constraints,
- resources,
- cost,
- reliability,
- availability,
- type, and
- execution mechanism.

The goal is to investigate whether these relationships can be encoded into vectors while retaining enough structure to reason about:

1. capability identity,
2. state awareness,
3. compatibility,
4. composition,
5. goal relevance, and
6. operational properties.

---

# 2. Important Scope Boundary

This project does **not** redesign or implement the planner from Assignment 1.

The following are outside the scope of this project:

- BFS
- DFS
- A*
- D* Lite
- LPA*
- path search
- replanning

The planner is treated only as background context.

---

# 3. Proposed Approach

SCE uses a structured vector rather than a single undifferentiated representation.

A capability is represented through the following blocks:

```text
┌─────────────────────────────────────────┐
│ Identity / Type / Mechanism             │
├─────────────────────────────────────────┤
│ Inputs                                  │
├─────────────────────────────────────────┤
│ Outputs                                 │
├─────────────────────────────────────────┤
│ Preconditions                           │
├─────────────────────────────────────────┤
│ Effects                                 │
├─────────────────────────────────────────┤
│ Resources / Constraints                 │
├─────────────────────────────────────────┤
│ Operational Quality                     │
│ time / cost / risk / reliability / etc. │
└─────────────────────────────────────────┘
```

This structure is motivated by the assignment's distinction between functional similarity and composability.

---

# 4. Similarity vs Compatibility

A major design principle is:

> **Similar capabilities do not necessarily compose.**

Cosine similarity is therefore used for functional resemblance:

```text
sim(x,y) =
    dot(x,y) / (||x|| ||y||)
```

But composition is evaluated using a separate directed compatibility measure:

```text
Comp(Ci,Cj)
    = 0.6 × cos(effect_i, precondition_j)
    + 0.4 × cos(output_i, input_j)
```

The direction matters.

For example:

```text
CreateOrder → MakePayment
```

can be compatible because CreateOrder produces:

```text
OrderExists = true
OrderStatus = CREATED
```

which satisfies requirements of MakePayment.

By contrast:

```text
CreateOrder → CancelCart
```

is incompatible in the supplied example because CancelCart requires:

```text
OrderExists = false
```

---

# 5. Repository Structure

```text
Assignment_2_Project/
│
├── README.md
├── PROJECT_ARCHITECTURE.md
├── CHANGELOG.md
├── requirements.txt
│
├── data/
│   ├── experimental_dataset.json
│   ├── capabilities.csv
│   ├── states.csv
│   ├── goals.csv
│   └── compatibility_pairs.csv
│
├── experiments/
│   ├── experiment_compatibility_results.csv
│   ├── experiment_alternative_implementations.csv
│   ├── experiment_goal_relevance.csv
│   └── experiment_operational_attributes.csv
│
├── report/
│   ├── technical_report.pdf
│   ├── technical_report.docx
│   └── formal_embedding_design.pdf
│
├── results/
│   ├── compatibility_scores.png
│   └── alternative_implementations.png
│
├── src/
│   └── capability_embedding.py
│
└── tests/
```

For a detailed explanation of the architecture, see:

```text
PROJECT_ARCHITECTURE.md
```

---

# 6. Data

The `data/` directory contains the formal application data.

### `experimental_dataset.json`

The complete machine-readable dataset.

### `capabilities.csv`

The capability catalogue.

Each capability contains formal information such as:

```text
id
name
type
mechanism
inputs
outputs
preconditions
effects
constraints
resources
execution time
monetary cost
resource cost
risk
reliability
availability
```

### `states.csv`

Formally specified application states.

### `goals.csv`

Formally specified goal conditions.

### `compatibility_pairs.csv`

Directed compatibility labels used by the compatibility experiment.

---

# 7. Source Code

The implementation is located in:

```text
src/capability_embedding.py
```

It provides:

```python
encode_state(state)
encode_goal(goal)
encode_capability(capability)
compose(capabilities)
similarity(x, y)
compatibility(capability_1, capability_2)
goal_relevance(capability, goal)
```

The implementation uses Python and NumPy and does not depend on a pretrained language model.

---

# 8. Composition

A sequence:

```text
C1 → C2 → C3
```

is converted into a composite capability.

The current implementation:

- takes inputs from the first capability,
- takes outputs from the last capability,
- combines effects,
- combines constraints,
- combines resources,
- sums costs,
- sums execution time,
- multiplies reliability,
- takes minimum availability.

The resulting composite is encoded using the same SCE representation as an atomic capability.

---

# 9. Experiments

The project evaluates the representation using five experiment categories.

## 9.1 Capability Compatibility

Tests whether compatible and incompatible directed capability pairs receive distinguishable compatibility scores.

## 9.2 Capability Composition

Tests whether a composite such as:

```text
CreateOrder → MakePayment → SendNotification
```

has a meaningful relationship with its atomic components.

## 9.3 Alternative Implementations

Tests capabilities that perform similar functions using different mechanisms:

```text
API
DATABASE
GUI
```

The goal is to preserve functional relationships without incorrectly treating the implementations as identical.

## 9.4 Goal Relevance

Tests whether capabilities can be related to desired goal conditions through their effects.

## 9.5 Operational Attributes

Investigates the influence of properties such as:

- cost,
- reliability,
- availability,
- risk,
- resource requirements.

---

# 10. Results

The supplied baseline experiments produced:

```text
Compatibility accuracy: 75%

Three-step composition alignment:
≈ 0.917
```

These values should be interpreted as **proof-of-concept results on a small synthetic dataset**, not as evidence of general superiority.

The visual experiment outputs are stored in:

```text
results/
```

---

# 11. Reports

The `report/` directory contains:

### Technical Report

```text
technical_report.pdf
technical_report.docx
```

The report covers:

1. Problem definition
2. Design requirements
3. Related approaches
4. Proposed representation
5. Mathematical formulation
6. Capability composition
7. Implementation
8. Experimental methodology
9. Results
10. Analysis
11. Limitations
12. Conclusion

### Formal Embedding Design

```text
formal_embedding_design.pdf
```

This contains the mathematical specification of the proposed representation and compatibility/composition operations.

---

# 12. Installation

Create a Python environment and install the dependencies:

```bash
pip install -r requirements.txt
```

The implementation requires:

```text
numpy
pandas
matplotlib
python-docx
reportlab
```

---

# 13. Running the Implementation

From the project root:

```bash
python src/capability_embedding.py
```

The module contains the core representation functions.

The supplied CSV files in `experiments/` contain the generated experimental outputs.

---

# 14. Testing

The `tests/` directory is reserved for automated tests.

A future test suite should verify:

```text
state encoding
goal encoding
capability encoding
similarity
directed compatibility
valid composition
invalid composition
goal relevance
operational attribute handling
```

No formal unit-test suite is currently included.

---

# 15. Reproducibility

The representation uses deterministic token-vector generation based on hashing. This means the same structured token can be mapped consistently without downloading a pretrained model.

The project separates:

```text
input data
    ↓
representation
    ↓
experiments
    ↓
results
    ↓
report
```

This makes the experiment easier to reproduce and inspect.

---

# 16. Limitations

The current implementation is a structured baseline.

Important limitations include:

- small synthetic dataset,
- deterministic rather than learned embeddings,
- simplified logical predicate representation,
- sequential composition only,
- no concurrency or branching,
- independence assumption for multiplicative reliability,
- dataset-dependent normalization constants.

A stronger future system could learn the embedding parameters from a substantially larger corpus of formally labelled capability compositions.

---

# 17. Assignment Deliverables

The assignment requires four major components:

1. **Formal embedding design**
2. **Implementation**
3. **Experimental dataset**
4. **Technical report**

All four are represented in this repository.

---

# 18. Recommended Reading Order

If reviewing the project for the first time:

```text
1. README.md
        ↓
2. PROJECT_ARCHITECTURE.md
        ↓
3. report/formal_embedding_design.pdf
        ↓
4. data/experimental_dataset.json
        ↓
5. src/capability_embedding.py
        ↓
6. experiments/
        ↓
7. results/
        ↓
8. report/technical_report.pdf
```

This follows the conceptual flow:

```text
Problem
  ↓
Architecture
  ↓
Mathematical design
  ↓
Data
  ↓
Implementation
  ↓
Experiments
  ↓
Results
  ↓
Analysis
```
