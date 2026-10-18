# Project Architecture

## 1. Project Overview

**Project:** Vector Embedding for Capability Composition  
**Embedding:** Structured Capability Embedding (SCE)  
**Assignment:** Assignment 2

The project investigates whether formally specified **states, goals, and executable capabilities** can be represented in a vector space while preserving the relationships required for:

- capability identity,
- state awareness,
- precondition–effect compatibility,
- input–output compatibility,
- functional similarity,
- capability composition,
- goal relevance, and
- operational properties such as cost, reliability, availability, constraints, and resources.

The architecture intentionally keeps the **planning/replanning algorithms from Assignment 1 outside the project scope**, as required by the assignment.

---

## 2. High-Level Architecture

```text
                         ┌──────────────────────────┐
                         │       data/              │
                         │                          │
                         │ States                   │
                         │ Goals                    │
                         │ Capabilities             │
                         │ Compatibility labels    │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │         src/             │
                         │                          │
                         │ Structured Capability    │
                         │ Embedding (SCE)          │
                         │                          │
                         │ encode_state()           │
                         │ encode_goal()            │
                         │ encode_capability()      │
                         │ similarity()             │
                         │ compatibility()          │
                         │ compose()                │
                         │ goal_relevance()         │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │      experiments/        │
                         │                          │
                         │ Compatibility            │
                         │ Composition              │
                         │ Alternative mechanisms   │
                         │ Goal relevance           │
                         │ Operational attributes   │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │        results/          │
                         │                          │
                         │ Experiment visualizations│
                         │ and derived figures      │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │         report/          │
                         │                          │
                         │ Formal design            │
                         │ Technical report         │
                         └──────────────────────────┘
```

---

## 3. Directory Structure

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
    └── .gitkeep
```

---

## 4. Data Layer

### `data/experimental_dataset.json`

The master machine-readable dataset. It contains the formal application data used by the experiments:

- capabilities,
- states,
- goals,
- compatibility pairs.

### `data/capabilities.csv`

Tabular representation of the capability catalogue.

Each capability contains information corresponding to the assignment's formal capability model, including:

- capability identity,
- type,
- execution mechanism,
- inputs,
- outputs,
- preconditions,
- effects,
- constraints,
- resources,
- execution time,
- monetary cost,
- resource cost,
- risk,
- reliability,
- availability.

### `data/states.csv`

Contains formally specified application states.

### `data/goals.csv`

Contains formal goal specifications.

### `data/compatibility_pairs.csv`

Contains labelled directed capability relationships used for the compatibility experiment.

The labels encode whether a source capability is expected to compose with a target capability.

---

## 5. Source Layer

### `src/capability_embedding.py`

This is the core implementation.

It implements:

```text
encode_state(state)
encode_goal(goal)
encode_capability(capability)
similarity(x, y)
compatibility(capability_1, capability_2)
compose(capabilities)
goal_relevance(capability, goal)
```

### Representation

The SCE vector is structured into blocks:

```text
[ identity
| inputs
| outputs
| preconditions
| effects
| resources + constraints
| operational quality ]
```

The operational-quality block includes:

```text
execution time
monetary cost
resource cost
risk
unreliability
unavailability
```

---

## 6. Similarity Layer

Cosine similarity is used to measure functional resemblance:

```text
sim(x,y) =
    dot(x,y) / (||x|| ||y||)
```

This relation is symmetric.

It is therefore deliberately **not** treated as the definition of capability composability.

---

## 7. Compatibility Layer

Capability composition is directional.

The implementation uses:

```text
Comp(Ci,Cj)
    = 0.6 * cos(effect_i, precondition_j)
    + 0.4 * cos(output_i, input_j)
```

The two terms represent:

1. **Effect → precondition compatibility**
2. **Output → input compatibility**

This distinction is central to the design because two capabilities can be functionally similar without being executable in sequence.

---

## 8. Composition Layer

For a valid sequence:

```text
C1 → C2 → ... → Cn
```

the composite capability is constructed from the atomic capabilities.

The current composition rule:

- takes external inputs from the first capability,
- takes external outputs from the last capability,
- uses the first capability's preconditions,
- combines effects,
- combines constraints,
- combines resources,
- sums execution time,
- sums monetary cost,
- sums resource cost,
- combines reliability multiplicatively,
- takes minimum availability.

The composite is then encoded using the same capability encoder.

---

## 9. Experiment Layer

The `experiments/` directory contains derived experiment data.

### Compatibility experiment

Tests labelled compatible and incompatible capability pairs.

### Composition experiment

Investigates:

```text
CreateOrder
      ↓
MakePayment
      ↓
SendNotification
```

and the representation of the resulting composite capability.

### Alternative implementation experiment

Tests functionally similar capabilities implemented through different mechanisms, including:

- API,
- database,
- GUI.

### Goal relevance experiment

Ranks capabilities according to the relationship between their effects and the desired goal conditions.

### Operational attribute experiment

Investigates how operational properties influence the representation.

---

## 10. Results Layer

The `results/` directory contains visual outputs derived from the experiments.

```text
compatibility_scores.png
alternative_implementations.png
```

These figures are intended to be referenced from the technical report.

---

## 11. Report Layer

The `report/` directory contains the human-readable deliverables.

### `formal_embedding_design.pdf`

Mathematical specification of:

- formal entities,
- embedding,
- similarity,
- compatibility,
- composition,
- goal relevance.

### `technical_report.pdf`

Submission-oriented technical report.

### `technical_report.docx`

Editable version of the technical report.

---

## 12. Testing Layer

The `tests/` directory is reserved for automated tests.

At the current stage, the project does not contain a formal unit-test suite. This is intentional rather than disguising experiment scripts as tests.

Recommended future tests include:

```text
test_state_encoding()
test_goal_encoding()
test_capability_encoding()
test_similarity()
test_compatibility_directionality()
test_valid_composition()
test_invalid_composition()
test_goal_relevance()
```

---

## 13. Scope Boundary

The following are intentionally **not** part of this implementation:

```text
BFS
DFS
A*
D* Lite
LPA*
path search
replanning
```

These belong to the planning/replanning context of Assignment 1 and are explicitly outside the scope of Assignment 2.

---

## 14. Data Flow

```text
Formal application specification
              │
              ▼
        Structured data
              │
              ▼
       Field-level encoding
              │
              ▼
      Capability vectors
              │
       ┌──────┼────────┐
       ▼      ▼        ▼
   similarity compatibility composition
       │      │        │
       └──────┼────────┘
              ▼
          Experiments
              │
              ▼
           Results
              │
              ▼
            Report
```

---

## 15. Architectural Principle

The architecture separates:

```text
WHAT IS REPRESENTED
        ↓
      data/

HOW IT IS REPRESENTED
        ↓
      src/

HOW IT IS EVALUATED
        ↓
   experiments/

WHAT THE EXPERIMENTS PRODUCE
        ↓
    results/

HOW THE WORK IS DOCUMENTED
        ↓
     report/
```

This separation makes the project easier to reproduce, inspect, test, and extend.
