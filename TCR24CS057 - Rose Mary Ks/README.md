# Capability Embedding for Capability Composition

PCCST503 - Machine Learning — Assignment 2

NAME: ROSE MARY K S

REGISTER NUMBER:TCR24CS057

## Overview

This project demonstrates a vector-based representation of application capabilities and how smaller capabilities can be composed into a larger workflow.

An online shopping application is used as the example. The selected workflow is:

`CreateOrder → MakePayment → SendNotification`

Each capability is represented using its type, inputs, outputs, preconditions, effects, and resources. The project creates feature-based vectors, calculates cosine similarity, checks compatibility, simulates execution, and evaluates operational attributes.

## Objectives

* Represent application capabilities in a structured format.
* Convert capability features into numerical vectors.
* Measure similarity using cosine similarity.
* Check compatibility between capabilities.
* Compose atomic capabilities into a workflow.
* Simulate the workflow and verify goal satisfaction.
* Evaluate latency, reliability, risk, and cost.

## Project Structure

```text
CAPABILITY_EMBED/
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── results/
│   ├── alternative_implementations.csv
│   ├── alternative_implementations.png
│   ├── capability_latency.png
│   ├── capability_reliability.png
│   ├── embeddings.json
│   ├── goal_relevance.csv
│   ├── goal_relevance.png
│   ├── operational_attributes.csv
│   └── summary.json
└── report/
    └── Capability_Embedding_Assignment_Report.pdf
```

*Note: The files inside `results/` are generated when the program runs. Their exact names depend on the final code version.*

## Technologies Used

* **Python** – Main programming language
* **NumPy** – Numerical operations and vector processing
* **Pandas** – Tabular data handling
* **Matplotlib** – Data visualization
* **Scikit-learn** – Cosine similarity calculation

## Requirements

* Python 3
* NumPy
* Pandas
* Matplotlib
* Scikit-learn

Install the required libraries using:

```bash
python -m pip install -r requirements.txt
```

## Setup and Execution

### 1. Open the project

Open the `CAPABILITY_EMBED` folder in VS Code.

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows PowerShell:**

```powershell
venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```cmd
venv\Scripts\activate.bat
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Run the program

```bash
python main.py
```

The program displays the execution summary and generates experiment outputs in the `results/` directory.

## Capability Dataset

The example dataset contains eight capabilities:

1. `CreateOrder`
2. `MakePayment`
3. `SendNotification`
4. `CancelCart`
5. `CreateOrderDB`
6. `CreateOrderGUI`
7. `RefundPayment`
8. `TrackDelivery`

The initial state specifies that the user is authenticated and has a non-empty cart. The goal is to create an order, complete payment, and send a notification.

## Methodology

### 1. Capability Representation

Each capability is described using features such as:

* Type
* Inputs
* Outputs
* Preconditions
* Effects
* Resources

### 2. Vector Embedding

A shared feature vocabulary is used to encode each capability as a multi-hot vector. Each vector represents the features associated with that capability.

### 3. Similarity Measurement

Cosine similarity is used to measure the similarity between capability vectors.

### 4. Compatibility Checking

Symbolic checks are used to identify links between capabilities, such as an output from one capability matching an input or precondition of another.

### 5. Capability Composition

Atomic capabilities are arranged into an ordered sequence to form a larger workflow:

`CreateOrder → MakePayment → SendNotification`

### 6. Workflow Execution

The program simulates the workflow by checking preconditions, updating the application state, and verifying whether the final goal is satisfied.

## Experiments

The project includes experiments for:

* Capability compatibility
* Capability composition and execution
* Comparison of alternative implementations
* Goal relevance using cosine similarity
* Operational attribute analysis

## Generated Results

The program generates files such as:

| File                              | Description                                |
| --------------------------------- | ------------------------------------------ |
| `embeddings.json`                 | Capability feature vectors                 |
| `summary.json`                    | Composition and execution summary          |
| `goal_relevance.csv`              | Goal similarity results                    |
| `alternative_implementations.csv` | Comparison of alternative capabilities     |
| `operational_attributes.csv`      | Operational attribute values               |
| PNG files                         | Graphical comparison of experiment results |

Refer to the generated files for the exact numerical results of a run.

## Limitations

* The dataset is small and manually specified.
* The vectors are feature-based and are not learned from training data.
* Compatibility checking is simplified and requires stronger validation of all inputs, preconditions, constraints, and resources.
* Reliability and risk calculations use simplifying assumptions.
* More application domains and larger datasets are needed for broader evaluation.

## Report

The detailed assignment report is available in:

`report/Capability_Embedding_Assignment_Report.pdf`

## Notes

* Do not upload the `venv/` folder to GitHub.
* Keep `requirements.txt` so that dependencies can be installed on another system.
* Include the generated results and report that are required for your submission.
