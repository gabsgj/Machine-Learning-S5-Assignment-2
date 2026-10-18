# SCE-128 — Vector Embedding for Capability Composition

## Final cleaned implementation package

This is the submission-oriented version of the project developed for **Assignment 2: Design of a Vector Embedding for Capability Composition**.

The assignment asks for a problem-specific representation of formal states, goals, and executable capabilities that can preserve capability identity, state awareness, precondition/effect compatibility, input/output compatibility, composition, goal relevance, and operational attributes. It also requires experiments for compatibility, composition, alternative implementations, irrelevant capabilities, and operational properties.

This package keeps the successful implementation, removes obsolete prototype programs, gives every runnable experiment a clear phase name, and separates baseline results from final v2.1 results.

---

## 1. Final model

The final system is **SCE-128 v2.1**.

### Capability vector

Each capability is encoded into a normalized 128-dimensional vector:

```text
Function          4
Type              8
Input            16
Output           16
Precondition     16
Effect           16
Constraint       12
Resource         12
Mechanism         8
Operational      20
-------------------
Total            128
```

The formal capability is represented as:

```text
C = (T, I, O, P, E, K, R, Q, Reliability, Availability, M)
```

The encoder uses deterministic structured representations so that the project is reproducible without an external pretrained embedding service.

### Three reasoning layers

```text
Formal representation
        │
        ├── SCE-128 vector
        │      ├── similarity
        │      └── block-aware analysis
        │
        ├── symbolic compatibility
        │      ├── effect → precondition
        │      └── output → input
        │
        └── learned composition
               └── atomic/predicted vectors → composite vector
```

The compatibility engine is kept separate from cosine similarity because functional similarity and composability are not the same property.

---

## 2. Dataset

The final dataset contains:

- **18 capability records**
- **15 logical capabilities**
- **3 alternative implementations** of `CreateOrder`
- a formally specified initial state
- a formally specified purchase-success goal
- expected compatibility relationships
- multiple composition chains
- relevant and irrelevant capability labels used only for evaluation
- operational attributes such as cost, reliability, availability, risk, and resources

The main application chain is:

```text
AddToCart
   ↓
CheckInventory
   ↓
ReserveInventory
   ↓
CreateOrder
   ↓
MakePayment
   ↓
VerifyPayment
   ↓
SendNotification
```

Alternative implementations:

```text
CreateOrder_API
CreateOrder_DATABASE
CreateOrder_GUI
```

---

## 3. Program phases

The project is intentionally numbered in execution order.

| Phase | Program | Purpose |
|---|---|---|
| 01 | `phase01_dataset_validation` | Validate formal dataset, relations, chains, and implementation variants |
| 02 | `phase02_capability_compatibility` | Evaluate formal compatibility and vector compatibility evidence |
| 03 | `phase03_baseline_composition` | Record the v1.1 deterministic composition baseline |
| 04 | `phase04_alternative_implementations` | Test API/database/GUI functional equivalence and mechanism separation |
| 05 | `phase05_goal_relevance` | Test relevant vs irrelevant capabilities for the goal |
| 06 | `phase06_operational_attributes` | Controlled cost/reliability/availability/risk perturbations |
| 07 | `phase07_leakage_free_composition` | Train/evaluate the learned vector-only composition operator |
| 08 | `phase08_final_evaluation` | Produce the final integrated v2.1 evaluation |

There are no obsolete `v2`, `v2_main`, `exp1`, `exp2`, or `phase3_validate_dataset` programs in the final package.

---

## 4. Quick start

The project is designed to run from a clean checkout with Python and the packages listed in `requirements.txt`. The commands below use Windows PowerShell, but the module-based commands are also suitable for other platforms.

### 4.1 Clone the repository

```powershell
git clone <REPOSITORY_URL>
cd SCE128_Capability_Embedding_Final
```

> Replace `<REPOSITORY_URL>` with the URL of your Git repository.

### 4.2 Create and activate a virtual environment

Using a virtual environment keeps project dependencies isolated from the system Python installation.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution for the current session, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 4.3 Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4.4 Run the complete evaluation pipeline

This is the recommended command for reproducing the final results. It runs all numbered phases in order, executes the final integrated evaluation, and runs the regression test suite.

```powershell
python run_all.py
```

Results are written to the `results/` directory. The final v2.1 artifacts are stored under:

```text
results/final_v2_1/
```

### 4.5 Run the regression tests only

```powershell
python -m pytest
```

### 4.6 Run the final integrated evaluation only

Use this when the full dataset and model are already prepared and only the final metrics are required.

```powershell
python -m experiments.phase08_final_evaluation
```

### 4.7 Run individual phases

Each experiment is available as a Python module and can be executed independently:

```powershell
python -m experiments.phase01_dataset_validation
python -m experiments.phase02_capability_compatibility
python -m experiments.phase03_baseline_composition
python -m experiments.phase04_alternative_implementations
python -m experiments.phase05_goal_relevance
python -m experiments.phase06_operational_attributes
python -m experiments.phase07_leakage_free_composition
python -m experiments.phase08_final_evaluation
```

### 4.8 Run the project smoke test

```powershell
python -m src
```

The smoke test prints the capability/vector configuration, selected compatibility relationships, goal-relevance examples, learned-composition configuration, and the 128-dimensional block layout.

### 4.9 Generated artifacts

After execution, the main outputs are:

```text
results/
├── baseline_v1_1/
└── final_v2_1/
```

The final integrated JSON and Markdown report are:

```text
results/final_v2_1/phase08_final_evaluation.json
results/final_v2_1/phase08_final_evaluation.md
```

---

## 5. Final experimental results

The currently frozen v2.1 evaluation reports:

| Area | Metric | Result |
|---|---|---:|
| Compatibility | Formal accuracy | **1.0000** |
| Compatibility | Vector compatibility-proxy AUC | **0.9000** |
| Composition | Held-out direct-pair mean | **0.8546** |
| Composition | Mean recursive-chain consistency | **0.8316** |
| Composition | Minimum recursive-chain consistency | **0.7929** |
| Alternative implementations | Functional similarity gap | **0.0932** |
| Alternative implementations | Overall gap | **0.0569** |
| Goal relevance | AUC | **0.9722** |
| Goal relevance | Precision@5 | **1.0000** |
| Goal relevance | Precision@10 | **1.0000** |
| Operational attributes | Mean whole-vector cosine | **0.9771** |
| Operational attributes | Mean operational-block cosine | **0.7714** |
| Operational attributes | Mean non-operational cosine | **1.0000** |

### Important interpretation rules

The numbers above should be reported with the following qualifications:

1. **Compatibility accuracy is symbolic-engine accuracy.** The embedding-derived compatibility proxy is reported separately.
2. **Composition is leakage-free.** The learned composer never receives the formal composite during prediction. Formal composite vectors are independently encoded and used only as evaluation targets.
3. **Goal relevance is hybrid.** The final relevance score combines embedding evidence with symbolic backward reachability. It is not an embedding-only ranking result.
4. **The dataset is deliberately small and domain-specific.** The experiments demonstrate the proposed representation on the constructed application domain; they do not establish general-purpose embedding performance.

---

## 6. Baseline vs final model

The final package preserves the v1.1 baseline for comparison.

| Metric | v1.1 baseline | v2.1 final |
|---|---:|---:|
| Compatibility-proxy AUC | 0.9000 | 0.9000 |
| Seven-step purchase composition consistency | 0.5283 | **0.7929** |
| Mean composition consistency | 0.6880 | **0.8316** |
| Alternative-implementation overall gap | 0.0207 | **0.0569** |
| Alternative-implementation functional mean | **1.0000** | 0.8000 |
| Goal-relevance AUC | 0.8472 | **0.9722** |
| Goal-relevance Precision@5 | 0.8000 | **1.0000** |
| Operational-block mean cosine | 0.7724 | 0.7714 |
| Non-operational mean cosine | 1.0000 | 1.0000 |

The comparison intentionally keeps a regression visible: v2.1 improves overall implementation separation but does not preserve the v1.1 functional-similarity score of 1.0 for all alternative implementations.

---

## 7. Directory structure

```text
SCE128_Capability_Embedding_Final/
│
├── README.md
├── PROJECT_ARCHITECTURE.md
├── CHANGELOG.md
├── run_all.py
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── core_application.json
│   ├── expanded_application.json
│   └── composition_split.json
│
├── src/
│   ├── schema.py
│   ├── data_models.py
│   ├── dataset.py
│   ├── encoder.py
│   ├── compatibility.py
│   ├── formal_composition.py
│   ├── final_model.py
│   ├── learned_composer.py
│   ├── evaluation.py
│   └── __main__.py
│
├── experiments/
│   ├── phase01_dataset_validation.py
│   ├── phase02_capability_compatibility.py
│   ├── phase03_baseline_composition.py
│   ├── phase04_alternative_implementations.py
│   ├── phase05_goal_relevance.py
│   ├── phase06_operational_attributes.py
│   ├── phase07_leakage_free_composition.py
│   └── phase08_final_evaluation.py
│
├── tests/
│   └── regression/unit and integration tests
│
└── results/
    ├── baseline_v1_1/
    └── final_v2_1/
```

---

## 8. Reproducibility

The embedding does not require an online model or external API. Token vectors are produced from deterministic hashes and a fixed seed, and the learned composition stage uses a small ridge-regularized model.

The final learned-composition evaluation uses a fixed train/held-out split recorded in:

```text
data/composition_split.json
```

This makes the final experiments reproducible on the same Python/Numpy environment.

---

## 9. Submission readiness

Before the technical report is assembled, verify:

```powershell
python run_all.py
python -m pytest
```

The expected final result is a clean test suite and a populated `results/final_v2_1/` directory.

The next submission artifact is the technical report covering the twelve sections specified in the assignment: problem definition, requirements, related approaches, proposed representation, mathematical formulation, composition model, implementation, methodology, results, analysis, limitations, and conclusion.
