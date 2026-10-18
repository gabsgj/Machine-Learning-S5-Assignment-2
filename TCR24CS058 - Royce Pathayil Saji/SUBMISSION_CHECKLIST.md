# Assignment 2 Submission Checklist and Package Manifest

**Course:** PCCST503: Advanced Software Engineering and Systems Design  
**Project:** Assignment 2: Design of a Vector Embedding for Capability Composition  
**Student Name:** Royce P Saji  
**Registration ID:** TCR24CS058  
**Roll No:** 57  
**GitHub Repository:** [https://github.com/Royce1415/capability_embedding](https://github.com/Royce1415/capability_embedding)  
**Architecture:** Partitioned Structured Dense Vector (PSD-160)  

This document outlines the final submission package, delineating required deliverables, optional experimental artifacts, files to exclude from the submission archive, and reproduction instructions.

---

## A. Required Submission Files

These files constitute the core academic deliverables specified by the assignment prompt:

1. **Deliverable 1: Formal Embedding Design Document**
   - `report/formal_embedding_design.md`: Complete mathematical design specification defining the application model, capability model, PSD-160 partitioned vector layout, condition space, data-flow space, operational quality space, safe cosine similarity, weighted functional similarity, directional capability compatibility, and sequential composition rules.

2. **Deliverable 2: Working Implementation & Verification Tests**
   - `src/models.py`: Formal Python dataclasses and enums (`Capability`, `State`, `Goal`, `Predicate`, `IOField`, `Constraint`, `Resource`, `OperationalCost`, `CapabilityType`).
   - `src/encoder.py`: Deterministic PSD-160 vector encoder (`encode_capability`, `encode_state`, `encode_goal`, `encode_condition_predicates`, `encode_io_fields`).
   - `src/metrics.py`: Metric functions (`similarity`, `cosine_similarity`, `effect_precondition_alignment`, `output_input_alignment`, `vector_compatibility`, `validate_compatibility`, `goal_relevance`).
   - `src/composer.py`: Sequential composition engine (`compose`) with internal dependency resolution, effect overrides, and operational attribute aggregation.
   - `tests/test_encoding.py`: 12 automated unit tests for vector dimension, polarities, categoricals, numericals, determinism, and value validation.
   - `tests/test_metrics.py`: 10 automated unit tests for cosine edge cases, symmetry, directional compatibility, input matching, and availability gating.
   - `tests/test_composition.py`: 6 automated unit tests for sequential composition, effect overrides, operational aggregation, and composite similarity.
   - `tests/test_experiments.py`: 10 automated unit tests for dataset integrity, experimental reproducibility, and empirical measurements.

3. **Deliverable 3: Experimental Dataset**
   - `data/experimental_dataset.json`: Master e-commerce benchmark containing 14 formally specified capabilities, 4 application states, and 5 goals.

4. **Deliverable 4: Technical Research Report**
   - `report/technical_report.md`: Comprehensive 12-section technical research report presenting problem definition, design requirements, related approaches comparison, PSD-160 architecture, mathematical formulation, composition semantics, experimental methodology, actual empirical results, analytical interpretation, architectural limitations, and honest references.

5. **Supplementary Academic Documentation**
   - `report/README.md`: Index and guide to the report directory.
   - `report/final_requirements_audit.md`: Formal 29-item requirement verification matrix.
   - `report/final_audit_summary.md`: Audit findings and quality verification summary.
   - `requirements.txt`: Minimal dependencies (`numpy`, `pytest`, `matplotlib`).

---

## B. Optional Demonstration and Result Artifacts

These generated files demonstrate experimental execution and empirical validation:
- `experiments/run_all.py`: Master experiment runner executing all 5 required experiments.
- `experiments/results/results.json`: Full structured JSON export of all measured experimental metrics.
- `experiments/results/compatibility.csv`: Tabular results for Experiment 1 (Capability Compatibility).
- `experiments/results/composition.csv`: Tabular results for Experiment 2 (Capability Composition).
- `experiments/results/alternative_implementations.csv`: Tabular results for Experiment 3 (Alternative Implementations).
- `experiments/results/goal_relevance.csv`: Tabular results for Experiment 4 (Goal Relevance Ranking).
- `experiments/results/operational_attributes.csv`: Tabular results for Experiment 5 (Operational Vector Comparisons and Utility Scenarios).
- `experiments/results/plots/compatibility_scores.png`: High-resolution bar chart of execution compatibility scores.
- `experiments/results/plots/alternative_implementations.png`: High-resolution comparison of functional vs mechanism block similarities.
- `experiments/results/plots/goal_relevance.png`: Horizontal bar chart ranking capability relevance to target goals.
- `experiments/results/plots/operational_tradeoffs.png`: Grouped bar chart illustrating utility tradeoffs under diverse operational priorities.

---

## C. Files That Must NOT Be Submitted

When preparing the clean archive (e.g., zip or tarball) for university submission, exclude:
- Bytecode caches: `**/__pycache__/`, `**/*.pyc`
- Test framework caches: `.pytest_cache/`
- Local Git metadata: `.git/`, `**/.gitkeep` (if submitting a plain zip archive)
- OS/Editor temporary files: `.DS_Store`, `Thumbs.db`, `*.swp`, `*~`
- Local agent session logs: any temporary scratch files or conversation transcripts

---

## D. Reproduction Commands

To replicate all experimental results and verify test suites from a clean terminal:

### 1. Environment Setup
```bash
pip install -r requirements.txt
```

### 2. Run Automated Verification Test Suite (38 tests)
```bash
python3 -m pytest tests/ -v
```
Expected output: `38 passed in < 0.50s` with 0 failures and 0 errors.

### 3. Run All Five Experiments & Regenerate Artifacts
```bash
python3 experiments/run_all.py
```
Expected output: Executes Experiments 1 through 5 deterministically, logging outputs to stdout, and writes `results.json`, 5 CSV summaries, and 4 PNG figures to `experiments/results/`.

---

## E. Recommended Clean Directory Structure for Archive

```
capability_embedding_assignment2/
├── data/
│   └── experimental_dataset.json
├── experiments/
│   ├── results/
│   │   ├── plots/
│   │   │   ├── alternative_implementations.png
│   │   │   ├── compatibility_scores.png
│   │   │   ├── goal_relevance.png
│   │   │   └── operational_tradeoffs.png
│   │   ├── alternative_implementations.csv
│   │   ├── compatibility.csv
│   │   ├── composition.csv
│   │   ├── goal_relevance.csv
│   │   ├── operational_attributes.csv
│   │   └── results.json
│   └── run_all.py
├── report/
│   ├── final_audit_summary.md
│   ├── final_requirements_audit.md
│   ├── formal_embedding_design.md
│   ├── README.md
│   └── technical_report.md
├── src/
│   ├── __init__.py
│   ├── composer.py
│   ├── encoder.py
│   ├── metrics.py
│   └── models.py
├── tests/
│   ├── __init__.py
│   ├── test_composition.py
│   ├── test_encoding.py
│   ├── test_experiments.py
│   └── test_metrics.py
├── requirements.txt
└── SUBMISSION_CHECKLIST.md
```
