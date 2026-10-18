# Assignment 2 — Design of a Vector Embedding for Capability Composition

## 1. Project Overview

This project implements a problem-specific vector embedding for representing **states, goals, and executable capabilities** in a structured application environment.

The main objective is to represent capabilities as vectors so that their:

* Functional similarity
* Preconditions and effects
* Input-output compatibility
* Composability
* Goal relevance
* Operational properties

can be analyzed using numerical representations.

The implementation uses a **structured feature-based embedding** rather than directly applying a pre-trained embedding model.

---

## 2. Application Domain

The project uses an **e-commerce application** as the example environment.

The application contains capabilities related to:

* Creating orders
* Making payments
* Sending notifications
* Cancelling carts
* Database-based order creation
* GUI-based order creation
* Generating reports

This domain allows different capabilities to be compared and composed into larger workflows.

---

## 3. Formal Model

A capability is represented using properties such as:

```text
Capability =
(Type, Inputs, Outputs, Preconditions, Effects,
 Constraints, Resources, Cost, Reliability,
 Availability, Metadata)
```

The embedding converts these properties into a numerical vector.

The implementation also represents:

* Application states
* Goals
* Capability types
* Inputs and outputs
* Preconditions
* Effects
* Resources
* Operational attributes

---

## 4. Embedding Design

The vector representation contains features corresponding to the functional and operational properties of a capability.

### Capability Type

The implementation represents different capability types such as:

```text
API
DATABASE
GUI
EVENT
FUNCTION
COMPUTATION
```

### Functional Features

The embedding includes features representing:

* Inputs
* Outputs
* Preconditions
* Effects
* Resources

### Operational Features

The embedding also includes numerical values for:

* Cost
* Reliability
* Availability

This allows capabilities to be compared not only by what they do, but also by their operational characteristics.

---

## 5. Main Functions

The implementation provides the following major functions:

### `encode_state(state)`

Converts an application state into a numerical vector.

### `encode_goal(goal)`

Converts a goal specification into a numerical vector.

### `encode_capability(capability)`

Converts the complete capability description into a numerical embedding.

### `similarity(x, y)`

Calculates cosine similarity between two vectors.

### `compatibility(capability1, capability2)`

Checks whether the effects of one capability can satisfy the preconditions of another capability.

### `compose(capabilities)`

Combines multiple capabilities into a composite capability representing a larger workflow.

---

## 6. Dataset

The capability dataset is stored in:

```text
data/capabilities.json
```

The dataset contains example capabilities including:

```text
CreateOrder
MakePayment
SendNotification
CancelCart
CreateOrderDatabase
CreateOrderGUI
GenerateMonthlyReport
```

The dataset contains their functional and operational properties.

---

## 7. Experiments

The project evaluates the embedding using several experiments.

### Experiment 1 — Compatibility

The first experiment checks whether the effect of one capability satisfies the precondition of another.

Example:

```text
CreateOrder → MakePayment
```

The order created by `CreateOrder` enables the payment operation.

---

### Experiment 2 — Capability Composition

Capabilities are combined to form larger workflows.

Example:

```text
CreateOrder
      ↓
MakePayment
      ↓
SendNotification
```

This represents a simplified complete-purchase workflow.

---

### Experiment 3 — Alternative Implementations

Different implementations of similar functionality are compared.

For example:

```text
CreateOrder
CreateOrderDatabase
CreateOrderGUI
```

Although their implementation types differ, they provide related functionality.

---

### Experiment 4 — Irrelevant Capabilities

Capabilities that are unrelated to the current task are included to determine whether the embedding can distinguish relevant and irrelevant capabilities.

For example:

```text
GenerateMonthlyReport
```

is unrelated to completing a purchase.

---

### Experiment 5 — Operational Attributes

The embedding also considers operational properties such as:

```text
Cost
Reliability
Availability
```

This allows capabilities to be evaluated beyond functional similarity.

---

## 8. Results

The experimental results are stored in the `results/` directory.

```text
results/
├── compatibility_results.csv
└── composition_results.csv
```

### Compatibility Results

`compatibility_results.csv` contains the compatibility relationships between capabilities.

### Composition Results

`composition_results.csv` contains the results of combining capabilities into larger workflows, including their cost and reliability.

---

## 9. Project Structure

```text
Assignment_2/
│
├── data/
│   └── capabilities.json
│
├── results/
│   ├── compatibility_results.csv
│   └── composition_results.csv
│
├── embedding.py
├── experiments.py
├── main.py
└── README.md
```

### File Description

| File                        | Description                               |
| --------------------------- | ----------------------------------------- |
| `capabilities.json`         | Experimental capability dataset           |
| `embedding.py`              | Vector embedding and comparison functions |
| `experiments.py`            | Experimental evaluation                   |
| `main.py`                   | Main program                              |
| `compatibility_results.csv` | Capability compatibility results          |
| `composition_results.csv`   | Capability composition results            |
| `README.md`                 | Project documentation                     |

---

## 10. Technologies Used

* Python 3
* NumPy
* Pandas
* JSON
* CSV
* Cosine Similarity
* Feature-based Vector Representation

---

## 11. Conclusion

This project demonstrates a structured vector representation for capabilities in an application environment.

The proposed embedding combines functional information such as inputs, outputs, preconditions and effects with operational information such as cost, reliability and availability.

The representation can therefore be used to analyze:

```text
Capability Identity
        ↓
Functional Similarity
        ↓
Compatibility
        ↓
Composition
        ↓
Goal Relevance
```

The experiments demonstrate how capabilities can be represented and analyzed numerically while preserving information necessary for capability composition.
