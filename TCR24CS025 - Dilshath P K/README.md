
# Capability Embedding for Functional Composition

A Python implementation exploring vector representations of application capabilities, compatibility, and composition.

## Objective

The project investigates how formally specified capabilities can be encoded as numerical vectors and combined into composite operations.

## Features

- State, goal, and capability encoding
- Capability similarity using cosine similarity
- Precondition-effect compatibility checking
- Composite capability construction
- Operational attribute modelling
- Five experimental scenarios
- CSV result generation

## Technologies

- Python
- NumPy
- Pandas
- Scikit-learn

## Project Structure

```text
capability-embedding/
├── data/
│   └── dataset.py
├── results/
├── src/
│   ├── embedding.py
│   ├── compatibility.py
│   └── composition.py
├── report/
│   └── technical_report.md
├── main.py
├── requirements.txt
└── README.md
```

## Installation

Install Python 3.10 or later.

Install the required packages:

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Experimental result tables are saved in the `results/` directory.

## Experiments

1. Capability compatibility
2. Capability composition
3. Alternative implementations
4. Goal relevance
5. Operational attributes

## Limitations

This is an experimental structured embedding, not a trained neural embedding. Similarity does not prove compatibility. The current implementation uses direct equality matching and simplified composition rules.

## Author

Dilshath P K
