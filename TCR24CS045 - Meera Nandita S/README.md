# PCCST503 Assignment 2 — Online Course Enrollment

**Name:** Meera Nandita S  
**Registration Number:** TCR24CS045

This is a complete, submission-oriented implementation for:

**Design of a Vector Embedding for Capability Composition**

It follows the four required deliverables and includes additional consistency
and efficiency experiments.

## Folder structure

```text
Online_Course_Enrollment_Assignment_2_Level_Matched/
├── data/
│   ├── experimental_dataset.json
│   ├── problem_1_regular_enrollment.json
│   ├── problem_2_scholarship_enrollment.json
│   ├── problem_3_manual_enrollment.json
│   └── problem_4_alternative_analysis.json
├── docs/
│   ├── DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md
│   ├── DELIVERABLE_2_IMPLEMENTATION.md
│   ├── DELIVERABLE_3_EXPERIMENTAL_DATASET.md
│   └── DELIVERABLE_4_TECHNICAL_REPORT.md
├── results/
├── src/
│   ├── embedding.py
│   └── run_experiments.py
├── tests/
│   └── test_embedding.py
├── requirements.txt
└── README.md
```

## Run

```powershell
pip install -r requirements.txt
python tests/test_embedding.py
python src/run_experiments.py
```

## Main composition

```text
SelectCourse
      ↓
MakePayment
      ↓
EnrollStudent
      ↓
SendNotification
```

## Important

This project intentionally does **not** implement BFS, DFS, A*, D* Lite or a
planner. Those are outside the scope of Assignment 2. The focus is the vector
representation and capability composition.
