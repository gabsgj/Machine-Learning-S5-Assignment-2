# PCCST503 Assignment 2
## Design of a Vector Embedding for

 Capability Composition

Name:Amrutha K S
Roll No:11

This project implements a structured, problem-specific vector representation for application capabilities. It is based on the formal capability model in the assignment brief.

## Run

Open a terminal in this folder and run:

```bash
pip install -r requirements.txt
python main.py
```

The program automatically creates the CSV files and PNG graphs in `results/`.

## Main files

- `data/capabilities.json`: experimental dataset.
- `src/models.py`: formal state, goal and capability data structures.
- `src/encoder.py`: vector embedding.
- `src/compatibility.py`: similarity and functional compatibility.
- `src/composition.py`: capability composition and composite vectors.
- `src/experiments.py`: required experiments and result generation.
- `main.py`: runs the complete experiment.
- `report.md`: technical report.
