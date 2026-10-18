# PCCST503 Assignment 2

## Design of a Vector Embedding for Capability Composition

### Student details

| Field | Details |
|---|---|
| Student name | **Nayana Shaji Mekkunnel** |
| Roll number | **50** |
| Semester | **S5 CSE** |
| Course code | PCCST503 |
| Assignment | Design of a Vector Embedding for Capability Composition |

## Project overview

This project implements an interpretable, standard-library-only Python system for representing formal application states, goals, and executable capabilities. The example domain is an e-commerce purchase and fulfillment workflow.

Capabilities are modeled as operations that transform application state when their preconditions hold. The implementation provides vector encodings for states, goals, and capabilities; cosine similarity for comparing encodings; symbolic precondition/effect and typed-port compatibility checks; capability composition; direct goal relevance; and operational attribute analysis.

Similarity and composability are evaluated separately: cosine similarity describes vector resemblance, while formal predicates and ports determine whether a capability can follow another.

## Assignment deliverables

| Deliverable | File | Contents |
|---|---|---|
| 1. Formal embedding design | [`DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md`](DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md) | Formal model, embedding functions, similarity, compatibility, composition, and assumptions |
| 2. Implementation | [`capability_embedding.py`](capability_embedding.py) | Python implementation and command-line interface |
| 3. Experimental dataset | [`ecommerce_purchase_flow.json`](ecommerce_purchase_flow.json), [`DELIVERABLE_3_EXPERIMENTAL_DATASET.md`](DELIVERABLE_3_EXPERIMENTAL_DATASET.md) | Formal e-commerce problem and experiment definitions |
| 4. Technical report | [`DELIVERABLE_4_TECHNICAL_REPORT.md`](DELIVERABLE_4_TECHNICAL_REPORT.md) | Methodology, observed results, analysis, limitations, and conclusion |

## Requirements

- Python 3.10 or newer
- Windows, macOS, or Linux terminal

## Run the project

Open a terminal in this folder. On Windows, use `py -3`; on macOS or Linux, use `python3`.

Run the five assignment experiments:

```powershell
py -3 capability_embedding.py --experiments
```

Print state, goal, and capability vectors:

```powershell
py -3 capability_embedding.py --vectors
```

Print a composed purchase capability:

```powershell
py -3 capability_embedding.py --compose
```

Run all demonstrations together:

```powershell
py -3 capability_embedding.py --experiments --vectors --compose
```

If the Windows `py` launcher is unavailable, replace `py -3` with `python`. On macOS or Linux, use `python3`.

The default input is `ecommerce_purchase_flow.json`. To load a different compatible formal problem file, pass its path before the options:

```powershell
py -3 capability_embedding.py path\to\problem.json --experiments
```

## Experiments included

1. **Capability compatibility:** checks an enabling successor and a successor whose precondition is contradicted.
2. **Capability composition:** composes CreateOrder, ValidateInventory, and MakePayment and reports aggregated operational attributes.
3. **Alternative implementations:** compares API and database payment capabilities that produce the same functional effects.
4. **Irrelevant capabilities:** compares direct effects against the stated purchase goal.
5. **Operational attributes:** compares payment latency, cost, reliability, and availability.

## How the representation works

- State and goal vectors use a shared vocabulary of application variables. Boolean values map to `+1` or `-1`; missing or unspecified values map to `0`.
- Capability vectors concatenate precondition and effect features, a one-hot capability type, normalized QoS values, reliability, and availability.
- Typed ports and symbolic predicates are checked directly for compatibility.
- Sequential composition discharges preconditions established by earlier effects, rejects contradictions, merges effects in order, sums costs, multiplies reliability, and combines availability.
- Goal relevance measures the fraction of goal predicates set directly by a capability.

## Notes and limitations

The implementation is an interpretable assignment prototype, not a production workflow engine. State and goal vector coordinates currently specialize in Boolean values; categorical values such as payment status are preserved and checked symbolically, but are not expanded in those vectors. The goal relevance score measures direct effect coverage, not indirect usefulness through a longer workflow. See the technical report for the full assumptions and limitations.

## Attribution and source materials

This project was prepared from the assignment PDF and the three example archives supplied for this task. The e-commerce example is used as the main domain because it demonstrates the required composition and compatibility concepts. The assignment PDF remains the authoritative specification.
