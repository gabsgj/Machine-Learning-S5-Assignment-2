Machine Learning Assignment 2

Vector Embedding for Capability Composition

Project Overview

This project designs and implements a problem-specific vector
representation for formally specified states, goals and executable
capabilities. The representation is designed for capability composition
and preserves functional information such as preconditions, effects,
inputs and outputs, together with operational attributes such as time,
monetary cost, resource cost, risk and reliability.

The implementation deliberately distinguishes vector similarity,
functional compatibility, and dependency.

Project Structure

ml_assignment_2/
├── src/
│   ├── models.py
│   ├── embedding.py
│   ├── composition.py
│   ├── experiments.py
│   └── main.py
├── data/
│   └── problems.json
└── README.md

models.py --- formal data structures.

embedding.py --- vector representation, cosine similarity and
compatibility.

composition.py --- sequential capability composition.

experiments.py --- five required experiments.

main.py --- program entry point.

problems.json --- experimental dataset.

Dataset

The dataset represents an e-commerce workflow.

States: 3

Goals: 1

Capabilities: 8

Capabilities:

CreateOrder
MakePayment_API
MakePayment_DB
MakePayment_GUI
SendNotification
CancelCart
BrowseCatalog
UpdateWishlist

Embedding Design

State and goal vectors use condition/value features:

1.0 --- specified value matches.

-1.0 --- variable is specified with another value.

0.0 --- variable is unspecified.

Dimensions:

State vector:       16
Goal vector:        16
Capability vector:  48

Capability vectors contain:

[preconditions]
[effects]
[inputs]
[outputs]
[capability type]
[time cost]
[money cost]
[resource cost]
[risk]
[reliability]

Time cost uses a logarithmic transformation to reduce domination by
large raw values.

Functional Compatibility

Compatibility is calculated from precondition/effect and input/output
relationships:

Compatibility =
    0.7 × precondition/effect score
  + 0.3 × input/output score

A separate dependency score identifies whether the second capability
actually depends on requirements supplied by the first.

Composition

For a valid sequence:

C1 → C2 → C3

the implementation constructs a composite capability containing combined
preconditions, effects, inputs, outputs, resources and operational
properties.

Experiments

Capability compatibility --- compares
CreateOrder → MakePayment_API with CreateOrder → CancelCart.

Capability composition --- constructs
CreateOrder → MakePayment_API → SendNotification.

Alternative implementations --- compares API, database and GUI
implementations of payment.

Irrelevant capabilities --- compares payment with unrelated
capabilities.

Operational attributes --- tests the influence of time, money,
resource cost, risk and reliability.

Running

From the project root:

python3 src/main.py

Key Results

Experiment 1:

CreateOrder → MakePayment_API
similarity:    0.0748
compatibility: 1.0000
dependency:    1.0000

CreateOrder → CancelCart
similarity:    0.4159
compatibility: 0.3000
dependency:    0.0000

This demonstrates that vector similarity and functional compatibility
are different relationships.

Experiment 2:

CreateOrder → MakePayment_API → SendNotification

Time cost:    225.00 ms
Money cost:   0.0650
Reliability:  0.990017

Experiment 3:

API ↔ Database:  0.9372
API ↔ GUI:       0.9383
Database ↔ GUI:  0.9368

Controlled operational experiment:

Original → Cheap/Fast:        0.998981
Original → Expensive/Slow:    0.935757
Cheap/Fast → Expensive/Slow:  0.929360

Limitations

The dataset is small and domain-specific. The feature space and
compatibility weights are manually designed. Functional compatibility is
explicitly calculated from formal relationships rather than inferred
solely from cosine similarity.

Conclusion

The implementation provides a structured vector representation for
states, goals and executable capabilities and supports capability
similarity, functional compatibility, sequential composition and
operational-property representation.