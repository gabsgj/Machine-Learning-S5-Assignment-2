# Vector Embedding for Capability Composition

**Course:** PCCST503, Assignment 2
**Institution:** Government Engineering College Thrissur
**Submitted by:** Manasa M (Roll No. 43)

## Overview

This project designs and implements a problem-specific vector embedding for
formally specified states, goals and executable capabilities. Unlike Word2Vec,
which captures semantic similarity between words, this embedding captures
**functional relationships** between capabilities: which capabilities can work
together, what they require, what they produce, and how they change system state.

The system can:

- Encode capabilities into 32-dimensional vectors
- Check precondition–effect compatibility between capabilities
- Compose capabilities into a composite capability
- Compare capabilities using cosine similarity
- Represent cost, reliability and availability explicitly

Planning algorithms (A*, LPA*, D* Lite) are outside the scope of this assignment.

## Representation

Each capability is encoded as a vector in R^32:

| Block       | Dimensions | Content                                                   |
|-------------|------------|-----------------------------------------------------------|
| Type        | 0 – 8      | One-hot capability type (API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE) |
| Functional  | 9 – 28     | Indicators for preconditions, effects, inputs/outputs, resources |
| Operational | 29 – 31    | Cost, Reliability, Availability                           |

- **Compatibility:** Ci -> Cj is compatible when the effects of Ci satisfy the preconditions of Cj.
- **Similarity:** cosine similarity between encoded vectors (soft ranking signal only).
- **Composition:** Cost = sum of costs, Reliability = product of reliabilities, Availability = all components available.

## Capabilities Used

| Capability       | Type     | Cost  | Reliability | Availability |
|------------------|----------|-------|-------------|--------------|
| CreateOrder      | API      | 0.01  | 0.99        | 1            |
| MakePayment      | API      | 0.05  | 0.97        | 1            |
| SendNotification | SERVICE  | 0.02  | 0.98        | 1            |
| CancelCart       | FUNCTION | 0.005 | 0.99        | 1            |
| UpdateProfile    | DATABASE | 0.01  | 0.99        | 1            |
| SearchProduct    | API      | 0.01  | 0.98        | 1            |

## Requirements

- Python 3.8 or later
- NumPy

```bash
pip install numpy
```

## How to Run

```bash
python main.py
```

The program prints the encoded vectors, runs all five experiments, and saves
the experimental dataset to `dataset.json`.

## Interface

| Function                | Purpose                                              |
|-------------------------|------------------------------------------------------|
| `encode(state)`         | Encode an application state                          |
| `encode(goal)`          | Encode a goal specification                          |
| `encode(capability)`    | Encode an atomic or composite capability             |
| `compose(capabilities)` | Build a composite capability from a compatible chain |
| `similarity(x, y)`      | Cosine similarity between two encoded entities       |

## Experiments

1. **Capability compatibility:** CreateOrder -> MakePayment is compatible; CreateOrder -> CancelCart is incompatible.
2. **Capability composition:** CreateOrder -> MakePayment -> SendNotification gives total cost 0.08, combined reliability 0.9411, availability 1.
3. **Alternative implementations:** CreateOrder implemented as API, DATABASE and GUI.
4. **Irrelevant capabilities:** UpdateProfile and SearchProduct are separated from goal-relevant capabilities.
5. **Operational attributes:** cost, reliability and availability embedded and compared.

## Sample Results

| Measurement                       | Value          |
|-----------------------------------|----------------|
| CreateOrder vs MakePayment        | 0.5643         |
| CreateOrder vs CancelCart         | 0.3358         |
| MakePayment vs SendNotification   | 0.4938         |
| Encoding time                     | 7.5e-05 s      |
| Number of capabilities            | 6              |
| Vector dimension                  | 32             |

## Project Structure

```
.
├── main.py          # Embedding implementation and experiments
├── dataset.json     # Generated experimental dataset
├── README.md        # This file
└── report.docx      # Technical report
```

## Limitations

- Hand-designed symbolic features; new predicates require extending the vocabulary.
- Small experimental domain (six capabilities).
- Reliability composition assumes independent steps; availability is static.
- Goal relevance is categorical rather than a graded score.
