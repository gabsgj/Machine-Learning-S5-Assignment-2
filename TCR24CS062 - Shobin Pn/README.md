# PCCST503 Assignment 2

## Vector Embedding for Capability Composition

This project implements a feature-based vector representation for application states, goals, and executable capabilities.

### Experiments

1. Capability compatibility
2. Capability composition
3. Alternative implementations
4. Irrelevant capabilities / goal relevance
5. Operational attributes

### Project structure

```text
PCCST503_Assignment_2/
├── common.py
├── main.py
├── requirements.txt
├── README.md
├── formal_design.md
├── report_template.md
├── data/
│   └── application_dataset.json
├── experiments/
│   ├── experiment1_compatibility.py
│   ├── experiment2_composition.py
│   ├── experiment3_alternatives.py
│   ├── experiment4_goal_relevance.py
│   └── experiment5_operational.py
└── results/
```

### Installation

```bash
pip install -r requirements.txt
```

### Run separately

```bash
python experiments/experiment1_compatibility.py
python experiments/experiment2_composition.py
python experiments/experiment3_alternatives.py
python experiments/experiment4_goal_relevance.py
python experiments/experiment5_operational.py
```

The assignment implementation uses explicit feature vectors and cosine similarity. Compatibility is handled separately using effect-precondition matching because similarity and composability are not the same.
