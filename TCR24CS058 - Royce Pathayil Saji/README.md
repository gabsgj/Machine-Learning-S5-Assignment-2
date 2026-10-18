# Capability Composition Vector Embedding (PSD-160)

**Course:** PCCST503: Advanced Software Engineering and Systems Design  
**Assignment:** Assignment 2: Design of a Vector Embedding for Capability Composition  
**Student Name:** Royce P Saji  
**Registration ID:** TCR24CS058  
**Roll No:** 57  
**GitHub Repository:** [https://github.com/Royce1415/capability_embedding](https://github.com/Royce1415/capability_embedding)  
**Language:** Python 3.10 / NumPy  

---

## 1. Project Overview

This repository contains our implementation and experimental evaluation of a continuous vector embedding designed for automated software capability composition. 

In distributed systems and service-oriented architectures, software capabilities (such as REST APIs, database queries, event handlers, and local routines) must be discovered, matched, and chained together into executable workflows. Traditional natural language embeddings (such as Word2Vec or BERT) map words based on text co-occurrence rather than causal execution logic: they treat antonyms like `true` and `false` as similar, cannot model directional handoffs, and ignore non-functional costs.

This project implements **PSD-160 (Partitioned Structured Dense 160-dimensional vector space)**, a deterministic embedding that represents application states, target goals, and executable capabilities in a unified metric space.

---

## 2. Assignment Objectives

The assignment requires us to:
1. Formulate a mathematical representation for software capabilities:
   $$C = (T, I, O, P, E, K, R, Q, \text{Rel}, A, M)$$
2. Map states, goals, and capabilities into vector spaces while preserving compatibility and composition semantics.
3. Distinguish functional capability similarity from directional compatibility.
4. Implement a composition engine that combines sequential capabilities, internalizes intermediate dependencies, and re-encodes the composite into the same vector space.
5. Build a formal experimental dataset in the e-commerce domain and evaluate the system across five required experiments.
6. Provide a formal design specification and comprehensive technical report.

---

## 3. Embedding Architecture: PSD-160

Instead of projecting all attributes into an unsegmented latent space, PSD-160 divides a 160-dimensional vector into eight dedicated coordinate slices:

| Block Name | Dimensions | Slice Range | Purpose |
|:---|:---:|:---:|:---|
| **Mechanism & Type** | 16 | `[0:16]` | Architectural type (`API`, `DATABASE`, `GUI`, etc.) and protocol hints |
| **Inputs** | 24 | `[16:40]` | Required ($1.0$) and optional ($0.5$) data input fields |
| **Outputs** | 24 | `[40:64]` | Produced data fields ($1.0$) |
| **Preconditions** | 32 | `[64:96]` | Logical conditions required prior to execution |
| **Effects** | 32 | `[96:128]` | State transitions established upon completion |
| **Constraints** | 12 | `[128:140]` | Invariant execution guard expressions |
| **Resources** | 12 | `[140:152]` | Shared and exclusive system resource dependencies |
| **Operational Quality** | 8 | `[152:160]` | Normalized latency, money, compute, risk, energy, unreliability, and unavailability |

Total dimensions: $16 + 24 + 24 + 32 + 32 + 12 + 12 + 8 = 160$.

### Shared Geometric Subspaces
- **Condition Space ($\mathbb{R}^{32}$):** Application states, goal conditions, capability preconditions, and capability effects share identical coordinates. Boolean variables use signed polarities ($+1.0$ for True, $-1.0$ for False, $0.0$ for neutral), allowing dot products to immediately flag logical contradictions as negative values.
- **Data-Flow Space ($\mathbb{R}^{24}$):** Inputs and outputs share a 24-dimensional typed schema space to evaluate data handoffs.

---

## 4. Key Mathematical Formulations

- **Safe Cosine Similarity:**
  $$\text{cos}(a, b) = \begin{cases} 
  1.0 & \text{if } \|a\| = 0 \text{ and } \|b\| = 0 \\
  0.0 & \text{if } \|a\| = 0 \text{ xor } \|b\| = 0 \\
  \frac{a \cdot b}{\|a\| \|b\| + \epsilon} & \text{otherwise} \quad (\epsilon = 10^{-9})
  \end{cases}$$
- **Weighted Functional Similarity:**
  $$\text{Sim}(C_1, C_2) = \sum_{b} w_b \cdot \text{cos}(v_1[b], v_2[b])$$
  Weights: effect $0.25$, precondition $0.20$, inputs $0.10$, outputs $0.10$, constraints $0.10$, resources $0.10$, operational $0.10$, mechanism $0.05$ (sum = $1.00$).
- **Directional Compatibility:**
  $$\text{Align}_{EP} = \frac{\text{eff}_1 \cdot \text{pre}_2}{\|\text{pre}_2\|^2}, \quad \text{Align}_{OI} = \frac{\text{out}_1 \cdot \text{in}_2}{\|\text{in}_2\|^2}$$
  $$\text{Comp}_{vec} = 0.6 \cdot \text{Align}_{EP} + 0.4 \cdot \text{Align}_{OI}$$
  $$\text{Comp}_{exec} = A_1 \cdot A_2 \cdot \text{Comp}_{vec}$$
  A candidate handoff requires $\text{Comp}_{exec} \ge 0.70$ and passes formal validation checks (all required inputs produced with matching types, preconditions satisfied, zero contradictions, and positive availability).
- **Goal Relevance:**
  $$\text{GoalRel}(C, G) = \frac{\max(0, \text{eff} \cdot g)}{\|g\|^2}$$

---

## 5. Repository Structure

```
.
├── data/
│   └── experimental_dataset.json    # Master e-commerce dataset (14 caps, 4 states, 5 goals)
├── experiments/
│   ├── results/
│   │   ├── plots/                   # 4 high-resolution generated figures
│   │   │   ├── alternative_implementations.png
│   │   │   ├── compatibility_scores.png
│   │   │   ├── goal_relevance.png
│   │   │   └── operational_tradeoffs.png
│   │   ├── alternative_implementations.csv
│   │   ├── compatibility.csv
│   │   ├── composition.csv
│   │   ├── goal_relevance.csv
│   │   ├── operational_attributes.csv
│   │   └── results.json             # Full raw structured experimental measurements
│   └── run_all.py                   # Master experiment runner
├── report/
│   ├── final_audit_summary.md       # Audit verification summary
│   ├── final_requirements_audit.md  # 29-requirement compliance matrix
│   ├── formal_embedding_design.md   # Deliverable 1: Mathematical specification
│   ├── README.md                    # Report directory index
│   └── technical_report.md          # Deliverable 4: 12-section technical research report
├── src/
│   ├── __init__.py
│   ├── composer.py                  # Sequential composition engine
│   ├── encoder.py                   # Deterministic PSD-160 vector encoder
│   ├── metrics.py                   # Cosine similarity, compatibility, goal relevance
│   └── models.py                    # Formal dataclasses and enums
├── tests/
│   ├── __init__.py
│   ├── test_composition.py          # 6 composition tests
│   ├── test_encoding.py             # 12 vector encoding tests
│   ├── test_experiments.py          # 10 reproducibility and measurement tests
│   └── test_metrics.py              # 10 metric, directionality, and gating tests
├── requirements.txt                 # numpy, pytest, matplotlib
├── SUBMISSION_CHECKLIST.md          # Manifest and package submission instructions
└── README.md                        # This project overview document
```

---

## 6. Installation and Setup

### Prerequisites
- Python 3.10 or higher
- `pip` package manager

### Installation
Clone the repository and install the minimal dependencies:

```bash
git clone <repository-url>
cd <repository-directory>
pip install -r requirements.txt
```

---

## 7. How to Run the Tests

Execute the automated test suite using `pytest`:

```bash
python3 -m pytest tests/ -v
```

All 38 tests run in approximately 0.35 seconds and verify vector shapes, signed polarities, categorical one-hot mappings, numerical normalization, directional compatibility, composition internalization, effect overrides, and operational aggregations.

---

## 8. How to Run the Experiments

Execute the master experiment pipeline:

```bash
python3 experiments/run_all.py
```

This script deterministically runs all five experiments, logs results to the terminal, and writes:
- `experiments/results/results.json`
- Five summary CSV files in `experiments/results/`
- Four visualization figures in `experiments/results/plots/`

---

## 9. Summary of Experimental Results

1. **Experiment 1 (Capability Compatibility):**
   - `CreateOrder -> MakePayment`: Execution Score = $+1.0000$ (COMPATIBLE).
   - `CreateOrder -> CancelCart`: Execution Score = $-0.6000$ (INCOMPATIBLE, caught contradiction on `Order.exists`).
   - `MakePayment -> CreateOrder`: Execution Score = $0.0000$ (INCOMPATIBLE, demonstrates directional asymmetry).
   - `CreateOrder -> ArchiveOrder`: Continuous vector score is $+0.7000$ (meets threshold), but rejected by the formal validation gate because `Payment.status = SUCCESS` was missing. This confirms the necessity of our two-tier architecture.
2. **Experiment 2 (Capability Composition):**
   - Composed pipeline $C_1 \circ C_2 \circ C_4$.
   - Intermediate inputs (`order_id`, `payment_id`) and preconditions (`Order.exists`) are internalized.
   - External inputs: `cart_id`. External preconditions: `Cart.exists`, `Inventory.available`.
   - Aggregated latency: $410.0$ ms, monetary cost: $\$0.035$, reliability: $0.92169$.
   - Similarities to components: vs $C_1$ ($0.7144$), vs $C_2$ ($0.3324$), vs $C_4$ ($0.4297$).
3. **Experiment 3 (Alternative Implementations):**
   - API (`C10`), DB (`C11`), and GUI (`C12`) order creation have identical effect and precondition similarities ($1.0000$), zero mechanism similarity ($0.0000$), and distinct operational similarities ($0.70$ to $0.86$).
4. **Experiment 4 (Goal Relevance Ranking):**
   - Useful capabilities for `Goal_Master` (`C1`, `C2`, `C4`) each score $0.3333$ (summing to $1.0$).
   - Irrelevant and contradictory actions (`C7`, `C8`, `C9`, `C5`, `C3`) score $0.0000$.
5. **Experiment 5 (Operational Attributes):**
   - Direct PSD-160 operational vector comparisons show active services have similarities between $0.70$ and $0.86$, while an unavailable service diverges geometrically (similarity $\approx 0.22$, distance $> 1.0$).
   - Application-level utility selection correctly picks DB under speed and cost priorities, while gating unavailable services to $0.0000$.

---

## 10. Known Limitations

1. **Fixed Coordinate Space:** The 160-dimensional layout is optimized for our domain. While reserved slots allow hashing unknown fields, very large enterprise vocabularies would require larger coordinate budgets.
2. **Sequential Composition Only:** Currently supports linear pipelines ($C_1 \to C_2 \to \dots \to C_n$). Conditional branching and parallel fork-joins are not yet represented in a single vector.
3. **Independent Failure Modes:** Multiplicative reliability assumes component failures are statistically independent.
4. **Vector Alignment Safety Gap:** As shown in Experiment 1, continuous vector alignment alone cannot guarantee execution safety without a formal validation gate.

---

## 11. Detailed Documentation

For full mathematical derivations and in-depth experimental analyses, refer to:
- **[Formal Embedding Design](report/formal_embedding_design.md):** Formal system model, capability tuple, and vector space specification.
- **[Technical Research Report](report/technical_report.md):** 12-section research report with comprehensive analysis, plots, and references.
- **[Requirements Audit Matrix](report/final_requirements_audit.md):** 29-item audit verifying complete assignment compliance.
