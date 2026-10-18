# Design of a Vector Embedding for Capability Composition

**PCCST503 - Assignment 2**  
**Project:** Design of a Vector Embedding for Capability Composition. 

**Name:** NEVIN BENO

**University Register Number:** TCR24CS052

## 1. Project Overview

This project presents and implements a problem-specific vector representation for formally specified **states, goals, and executable capabilities**.

The main objective is to investigate whether structured capabilities can be represented in a vector space while preserving the relationships needed for:

- capability identity
- state awareness
- input-output compatibility
- precondition-effect compatibility
- capability similarity
- capability composition
- goal relevance
- operational properties such as cost, reliability, availability, risk, and resource usage

The implementation is intentionally different from an ordinary word-embedding system. A capability is not represented only by its name or textual description. Its functional structure is explicitly represented.

The project follows the formal capability-composition problem specified in Assignment 2 and provides the required implementation and experiments.

---

## 2. Problem Statement

A capability is an executable operation that changes an application state. Its behaviour depends on its inputs, outputs, preconditions, effects, constraints, resources, operational properties, and execution mechanism.

The central research question is:

> **How can formally specified states, goals, and executable capabilities be represented in a vector space so that the representation preserves relationships required for capability compatibility, composition, and construction of complex functionality?**

The project therefore treats capability embedding as a **structured representation problem**, rather than as ordinary natural-language semantic similarity.

---

## 3. Formal Application Model

The application is represented conceptually as:

```text
A = (S, C, S_I, G, R, K)
```

where:

| Symbol | Meaning |
|---|---|
| `S` | State space |
| `C` | Set of executable capabilities |
| `S_I` | Initial state |
| `G` | Goal specification |
| `R` | Available resources |
| `K` | Constraints and policies |

An individual capability is represented as:

```text
C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
```

where:

| Component | Meaning |
|---|---|
| `T` | Capability type |
| `I` | Inputs |
| `O` | Outputs |
| `P` | Preconditions |
| `E` | Effects |
| `K` | Constraints |
| `R` | Resources |
| `Q` | Quality and cost attributes |
| `Rel` | Reliability |
| `A` | Availability |
| `M` | Execution mechanism |

This structure is implemented directly in the project data model.

---

## 4. Project Architecture

```text
                         Formal Application
                                |
             +------------------+------------------+
             |                  |                  |
           State               Goal           Capabilities
             |                  |                  |
             v                  v                  v
      encode_state()      encode_goal()     encode_capability()
             |                  |                  |
             +------------------+------------------+
                                |
                                v
                     80-Dimensional Vector
                                |
              +-----------------+------------------+
              |                 |                  |
          Similarity       Compatibility       Composition
              |                 |                  |
              v                 v                  v
       Cosine similarity   Directed score    Composite capability
```

The design deliberately separates **geometric similarity** from **functional compatibility**. This is important because two capabilities may be similar without being executable in sequence.

---

## 5. Repository Structure

```text
capability_embedding_project/
|
+-- README.md
+-- requirements.txt
+-- run.py
|
+-- src/
|   +-- __init__.py
|   +-- models.py
|   +-- embedding.py
|   +-- compatibility.py
|   +-- composition.py
|   +-- evaluation.py
|
+-- data/
|   +-- capability_dataset.json
|
+-- experiments/
|   +-- run_experiments.py
|
+-- results/
|   +-- compatibility_results.csv
|   +-- composition_results.csv
|   +-- goal_relevance_results.csv
|   +-- operational_results.csv
|   +-- summary.json
|   +-- compatibility_matrix.png
|   +-- goal_relevance.png
|   +-- operational_effect.png
|
+-- docs/
|   +-- mathematical_design.md
|   +-- api_example.py
|
+-- report/
    +-- technical_report.md
    +-- technical_report.docx
```

---

## 6. Implementation Components

### 6.1 `src/models.py`

Defines the structured objects used by the system, including:

- `Condition`
- `IOField`
- `Quality`
- `Capability`
- `CompositeCapability`
- `State`
- `Goal`

### 6.2 `src/embedding.py`

Implements the structured 80-dimensional embedding.

### 6.3 `src/compatibility.py`

Computes the directed compatibility score between two capabilities.

### 6.4 `src/composition.py`

Constructs a composite capability from a compatible sequence and aggregates its operational properties.

### 6.5 `src/evaluation.py`

Provides evaluation functions used by the experiments.

### 6.6 `experiments/run_experiments.py`

Runs the complete experimental evaluation and generates CSV files and figures.

### 6.7 `run.py`

Provides the main entry point for running the complete project.

---

## 7. Embedding Design

The project uses an **80-dimensional structured feature-hashing representation**.

The vector is divided into the following blocks:

| Dimensions | Block | Purpose |
|---:|---|---|
| 0-7 | Type and mechanism | Represents capability type and execution mechanism |
| 8-19 | Inputs | Represents input fields and their properties |
| 20-31 | Outputs | Represents produced outputs |
| 32-43 | Preconditions | Represents conditions required before execution |
| 44-55 | Effects | Represents state changes produced by execution |
| 56-63 | Constraints and resources | Represents resource and constraint information |
| 64-71 | Operational attributes | Represents reliability, availability, cost, time, risk, and energy |
| 72-79 | Composition metadata | Represents additional structural information |

Symbolic features are mapped deterministically into their corresponding vector blocks using hashing.

Numerical operational attributes are normalized before being inserted into the operational block.

Finally, the complete vector is L2-normalized.

This design provides a fixed-size representation while retaining information from multiple parts of the formal capability definition.

---

## 8. Similarity and Composability

### 8.1 Similarity

Two vectors are compared using cosine similarity:

```text
similarity(x, y) = dot(x, y) / (norm(x) * norm(y))
```

The implementation exposes this through:

```python
StructuredEmbedder.similarity(x, y)
```

### 8.2 Why similarity is not enough

A high similarity score does not automatically mean that two capabilities can be executed consecutively.

For example:

```text
CreateOrder -> MakePayment
```

is compatible because `CreateOrder` produces the state condition:

```text
Order.exists = true
```

which satisfies the main precondition of `MakePayment`.

In contrast:

```text
CreateOrder -> CancelCart
```

is not a valid functional transition because `CancelCart` requires:

```text
Order.exists = false
```

while `CreateOrder` produces:

```text
Order.exists = true
```

Therefore, the implementation keeps **similarity** and **compatibility** as separate concepts.

---

## 9. Compatibility Model

Compatibility is directional. For a candidate transition from capability `C_i` to capability `C_j`, the implementation computes:

```text
Comp(C_i, C_j) =
    0.55 * EP
  + 0.30 * IO
  + 0.10 * OP
  + 0.05 * R
```

where:

- `EP` = effect/precondition satisfaction
- `IO` = output/input satisfaction
- `OP` = operational feasibility
- `R` = resource compatibility diagnostic

For the supplied experiments, a compatibility score of **0.70 or higher** is treated as composable.

The explicit compatibility function is used because a vector-space similarity measure alone cannot reliably represent directed precondition satisfaction.

---

## 10. Capability Composition

For a sequence:

```text
C1 -> C2 -> ... -> Cn
```

every adjacent pair must satisfy the compatibility threshold.

For the supplied dataset:

```text
CreateOrder -> MakePayment -> SendNotification
```

forms the composite capability:

```text
CompletePurchase
```

The formal composite retains the ordered list of component capabilities.

Operational properties are aggregated as follows:

```text
Reliability(composite) = product of component reliabilities
Availability(composite) = minimum component availability
Time cost(composite) = sum of component time costs
Resource cost(composite) = sum of component resource costs
Money cost(composite) = sum of component money costs
Energy cost(composite) = sum of component energy costs
```

The composite vector is formed from the normalized mean of the component vectors. The formal composite object remains available so that exact sequence and boundary information are not lost.

---

## 11. State and Goal Embeddings

The same fixed-dimensional representation is also used for application states and goals.

A state is converted into features of the form:

```text
variable=value
```

A goal is converted into features representing its required conditions.

The implementation therefore provides:

```python
encode_state(state)
encode_goal(goal)
encode_capability(capability)
```

This gives a common vector-space interface for the three major entities required by the assignment.

---

## 12. Experimental Dataset

The supplied dataset contains seven capabilities:

| Capability | Type | Purpose |
|---|---|---|
| `CreateOrder` | API | Creates an order from a cart |
| `MakePayment` | SERVICE | Processes payment for an existing order |
| `SendNotification` | MESSAGE | Sends a notification after successful payment |
| `CancelCart` | API | Cancels a cart when no order exists |
| `CreateOrderDB` | DATABASE | Database-oriented alternative implementation |
| `CreateOrderGUI` | GUI | GUI-oriented alternative implementation |
| `UpdateProfile` | DATABASE | Unrelated profile-update capability |

The initial state and goal are also defined in `data/capability_dataset.json`.

The target purchase goal is:

```text
Order.exists = true
Payment.status = SUCCESS
Notification.sent = true
```

---

## 13. Experiments

### Experiment 1 - Capability Compatibility

Tests:

```text
CreateOrder -> MakePayment
CreateOrder -> CancelCart
```

Expected behaviour:

- `CreateOrder -> MakePayment` receives a high compatibility score.
- `CreateOrder -> CancelCart` receives a substantially lower score.

### Experiment 2 - Capability Composition

Tests the three-step sequence:

```text
CreateOrder -> MakePayment -> SendNotification
```

The sequence is composed into `CompletePurchase` and its operational properties are calculated.

### Experiment 3 - Alternative Implementations

Compares:

```text
CreateOrder
CreateOrderDB
CreateOrderGUI
```

These capabilities share the broad goal of creating an order but differ in type, mechanism, resources, and operational characteristics.

The representation should therefore treat them as functionally related without making them identical.

### Experiment 4 - Irrelevant Capabilities

`UpdateProfile` is compared against the purchase goal.

Because its effect is unrelated to the required purchase conditions, its goal relevance is expected to be low.

### Experiment 5 - Operational Properties

The experiment verifies that reliability and availability affect the operational representation and that composite operational values are calculated according to the defined aggregation rules.

---

## 14. Generated Results

Running the project generates the following result files:

```text
results/compatibility_results.csv
results/composition_results.csv
results/goal_relevance_results.csv
results/operational_results.csv
results/summary.json
```

It also generates three figures:

```text
results/compatibility_matrix.png
results/goal_relevance.png
results/operational_effect.png
```

For the supplied dataset, the main recorded values are:

| Measurement | Result |
|---|---:|
| Embedding dimension | 80 |
| Number of capabilities | 7 |
| State vector dimension | 80 |
| Goal vector dimension | 80 |
| `CreateOrder -> MakePayment` compatibility | 0.9730 |
| `CreateOrder -> CancelCart` compatibility | 0.4495 |
| `CreateOrder` goal relevance | 0.3333 |
| `CompletePurchase` goal relevance | 1.0000 |
| Composite reliability | 0.9555 |
| Composite availability | 0.9800 |

These values are generated by the current implementation and are stored in `results/summary.json`.

---

## 15. Installation

### Requirements

- Python 3.9 or newer
- NumPy
- pandas
- Matplotlib

### Install dependencies

```bash
cd capability_embedding_project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the virtual environment with:

```text
.venv\\Scripts\\activate
```

---

## 16. Running the Project

From the project root:

```bash
python run.py
```

The program executes the experiments and writes the generated results into the `results/` directory.

The project can also be explored module by module using the files under `src/` and `experiments/`.

---

## 17. Basic API Example

```python
from src.embedding import StructuredEmbedder
from src.compatibility import compatibility

embedder = StructuredEmbedder()

vector_a = embedder.encode_capability(capability_a)
vector_b = embedder.encode_capability(capability_b)

similarity = embedder.similarity(vector_a, vector_b)
compatibility_score = compatibility(capability_a, capability_b)
```

Composition is available through the composition module:

```python
from src.composition import compose_capabilities

composite = compose_capabilities([
    create_order,
    make_payment,
    send_notification
])
```

A complete example is provided in `docs/api_example.py`.

---

## 18. Design Rationale

### Why feature hashing?

The formal model contains many symbolic values such as capability types, field names, state variables, operators, resources, and mechanisms. Feature hashing provides a deterministic way to map these potentially large symbolic feature sets into fixed-size vector blocks.

### Why use separate blocks?

If every feature were mixed into one undifferentiated vector, important distinctions between inputs, effects, preconditions, and operational properties could become difficult to interpret. Dedicated blocks make the representation more structured and easier to analyse.

### Why keep compatibility separate?

Compatibility is directional and depends on semantic satisfaction. A capability that produces a condition required by another capability is useful as a predecessor even if the two capabilities are not highly similar in the ordinary geometric sense.

### Why represent operational properties explicitly?

Two capabilities may perform the same broad function while having different reliability, availability, cost, execution time, resource usage, or risk. These attributes therefore need explicit representation rather than being hidden inside a generic similarity score.

---

## 19. Limitations

The current implementation is a deterministic, feature-engineered baseline rather than a learned embedding model.

Important limitations are:

1. Hash collisions are possible.
2. Compatibility weights are manually selected.
3. The weights are not learned from a training corpus.
4. The dataset is small and designed for controlled experiments.
5. The composite vector uses mean aggregation and therefore does not fully encode sequence order.
6. Exact symbolic composition information is retained in the composite object rather than entirely in the vector itself.

These limitations are appropriate for a first problem-specific implementation and provide clear directions for future research.

---

## 20. Future Work

A more advanced implementation could:

- learn embedding parameters from a larger capability corpus
- learn compatibility weights from labelled composition examples
- use graph neural networks for state-transition structure
- encode ordered composition with sequence models
- evaluate the representation on larger real-world workflows
- learn separate representations for different capability types
- jointly train goal relevance and compatibility objectives

---

## 21. Assignment Deliverables Covered

| Assignment requirement | Project component |
|---|---|
| Formal embedding design | `docs/mathematical_design.md` and `report/technical_report.md` |
| `encode(state)` | `StructuredEmbedder.encode_state()` |
| `encode(goal)` | `StructuredEmbedder.encode_goal()` |
| `encode(capability)` | `StructuredEmbedder.encode_capability()` |
| `compose(capabilities)` | `compose_capabilities()` |
| `similarity(x, y)` | `StructuredEmbedder.similarity()` |
| Compatibility experiment | `experiments/run_experiments.py` |
| Composition experiment | `experiments/run_experiments.py` |
| Alternative implementation experiment | `experiments/run_experiments.py` |
| Irrelevant capability experiment | `experiments/run_experiments.py` |
| Operational attribute experiment | `experiments/run_experiments.py` |
| Experimental dataset | `data/capability_dataset.json` |
| Technical report | `report/technical_report.md` and `report/technical_report.docx` |

---

## 22. Conclusion

This project demonstrates a structured vector representation for formally specified application capabilities.

The representation captures capability identity, inputs, outputs, preconditions, effects, constraints, resources, execution mechanisms, and operational properties. It also provides a common representation for application states and goals.

Most importantly, the project distinguishes **similarity** from **functional composability**. Vector similarity provides a useful geometric relationship, while the explicit compatibility model verifies whether the effects and outputs of one capability can satisfy the preconditions and inputs of the next capability.

The resulting implementation provides a complete baseline for studying vector representations of capability composition and can be extended toward learned representations in future work.

---

## 23. Included Documentation

The repository contains three forms of documentation:

- `README.md` - project overview, setup, architecture, experiments, results, and usage
- `docs/mathematical_design.md` - mathematical and formal representation details
- `report/technical_report.md` - submission-oriented technical report
- `report/technical_report.docx` - formatted report document