# Vector Embedding for Capability Composition

This project implements a problem-specific vector representation for formally specified
states, goals, and executable capabilities.

## Application domain

The experimental domain is a small e-commerce application.

Main capabilities:
- CreateOrder
- MakePayment
- SendNotification
- CancelCart
- UpdateProfile
- SearchProduct
- CreateOrder_Database
- CreateOrder_GUI

The implementation investigates:
1. Capability identity
2. State awareness
3. Precondition–effect compatibility
4. Input–output compatibility
5. Similarity vs composability
6. Capability composition
7. Goal relevance
8. Operational attributes

## Project structure

```text
capability_embedding_assignment/
│
├── data/
│   └── application.json
│
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── encoder.py
│   ├── composition.py
│   ├── experiments.py
│   └── main.py
│
├── results/
├── docs/
│   └── report.md
│
├── requirements.txt
└── README.md
```

## Setup in VS Code

Open this folder in VS Code.

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Linux / WSL / Ubuntu

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then run:

```bash
python -m src.main
```

The program creates:
- `results/capability_vectors.csv`
- `results/similarity_matrix.csv`
- `results/compatibility_results.csv`
- `results/experiment_results.csv`
- `results/experiment_summary.csv`
- `results/similarity_heatmap.png`
- `results/experiment_scores.png`

## Main design

A capability is represented by:

```text
C = (type, inputs, outputs, preconditions, effects,
     constraints, resources, cost, reliability, availability)
```

The vector is a concatenation of structured multi-hot feature blocks:

```text
φ(C) = [
    type,
    inputs,
    outputs,
    preconditions,
    effects,
    constraints,
    resources,
    operational_attributes
]
```

The design deliberately keeps functional properties separate from implementation
type and operational properties. This allows two implementations of a similar
function to remain functionally related without being treated as identical.

## Similarity

Cosine similarity is used for vector similarity:

similarity(x,y) = (x·y) / (||x|| ||y||)

## Compatibility

Compatibility is not decided by cosine similarity alone.

A directed compatibility test checks:

1. Effects of C1 satisfy preconditions of C2.
2. Outputs of C1 satisfy required inputs of C2.
3. C1 does not create a direct contradiction with C2's preconditions.

Thus:

```text
CreateOrder -> MakePayment       compatible
CreateOrder -> CancelCart        incompatible
```

## Composition

For a valid sequence:

```text
C1 -> C2 -> C3
```

the composite vector is constructed from the component vectors plus a
composition-structure block containing the ordered component names.

The implementation also aggregates:
- total cost
- product reliability
- minimum availability
- union of resources
- union of preconditions/effects

The composition is therefore more than an arithmetic average.


Pavithra S
TCR24CS055
