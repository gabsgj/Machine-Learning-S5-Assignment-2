# Design of a Vector Embedding for Capability Composition
## Formal Representations, Compatibility, and Compositional Reasoning

**Student Name**: Melita Mariam Mathew  
**University Registration Number**: TCR24CS046  
**Assignment**: Assignment 2 — Machine Learning  
**Implementation Repository**: `capability_vector_embedding`  

---

## Executive Summary

While natural language models like Word2Vec map words into continuous vector spaces to capture semantic analogies (e.g., $\text{king} - \text{man} + \text{woman} \approx \text{queen}$), software capabilities in real-world systems require **functional modeling**. In functional systems, the core concern is not linguistic meaning, but *operational compatibility*: what an operation requires (preconditions, inputs, resources), what it produces (effects, outputs), how it transforms system state, and how smaller capabilities algebraically compose into complex application workflows.

This repository provides a complete, mathematically grounded, and empirically validated implementation of the **Dual-Faceted Partitioned Vector Space (DF-PVS)** for capability composition.

```
       +----------------------------------------------------------------------------------+
       |             Dual-Faceted Partitioned Vector Space (DF-PVS) in R^D               |
       +------------------+------------------+---------------+---------------+------------+
       |   v_pre (R^ds)   |   v_eff (R^ds)   |  v_in (R^dio) | v_out (R^dio) |   v_ops    |
       |  Preconditions   |     Effects      |  Input Types  |  Output Types | Latency/Rel|
       +------------------+------------------+---------------+---------------+------------+
                 |                 |
                 +--------+--------+
                          | Cross-subspace asymmetric inner product
                          v
               Compatibility Score in [-1.0, 1.0]
           (+0.8000 for C1 -> C2 | -0.5000 for C1 -> C3 Conflict)
```

---

## Deliverables Checklist

| Deliverable | Description | File Location | Status |
| :--- | :--- | :--- | :--- |
| **Deliverable 1** | Formal Mathematical Embedding Design | [`formal_specification/deliverable1_formal_design.md`](formal_specification/deliverable1_formal_design.md) | **Complete** |
| **Deliverable 2** | Full Working Implementation (`encode`, `compose`, `similarity`, `compatibility`) | [`src/embedding.py`](src/embedding.py), [`src/models.py`](src/models.py), [`src/composition.py`](src/composition.py) | **Complete** |
| **Deliverable 3** | Experimental Benchmark Dataset | [`dataset/dataset.py`](dataset/dataset.py), [`dataset/benchmark_data.json`](dataset/benchmark_data.json) | **Complete** |
| **Deliverable 4** | Comprehensive Technical Report (All 12 Required Sections) | [`report/TECHNICAL_REPORT.md`](report/TECHNICAL_REPORT.md) | **Complete** |
| **Experiments** | All 5 Required Experiments + Visual Plots | [`experiments/run_experiments.py`](experiments/run_experiments.py), [`plots/`](plots/) | **Complete** |
| **Unit Tests** | 10 Automated Unit Tests covering all Section 8 criteria | [`tests/test_embedding.py`](tests/test_embedding.py) | **100% Pass** |

---

## Repository Structure

```
capability_vector_embedding/
├── README.md                           # Master project guide & student credentials
├── dataset/
│   ├── dataset.py                      # Formal dataset builder (states, goals, capabilities)
│   └── benchmark_data.json             # Serialized formal application dataset (JSON)
├── formal_specification/
│   └── deliverable1_formal_design.md   # Mathematical specification of DF-PVS
├── plots/                              # Generated high-resolution empirical plots (300 DPI)
│   ├── exp1_compatibility.png         # Compatibility & Asymmetry vs Flat Cosine
│   ├── exp2_composition.png           # Subspace Reconstruction Fidelity
│   ├── exp3_alternatives.png          # Functional Sim vs Mechanism Distance
│   ├── exp4_irrelevance.png           # Goal Relevance Separation Margin
│   └── exp5_operational.png           # Multi-Objective Pareto Trade-Offs
├── report/
│   └── TECHNICAL_REPORT.md             # Complete 12-section technical report
├── src/
│   ├── models.py                       # Domain entities: State, Goal, Capability, CompositeCapability
│   ├── embedding.py                    # CapabilityEmbeddingSpace, encoding, similarity, compatibility
│   ├── composition.py                  # Symbolic and vector composition engines
│   └── metrics.py                      # Metrics: cosine similarity, Euclidean distance, Pareto checks
├── tests/
│   └── test_embedding.py               # Unit test suite (10 test cases)
└── experiments/
    ├── exp1_compatibility.py           # Experiment 1: Compatibility (C1 -> C2 vs C1 -> C3)
    ├── exp2_composition.py             # Experiment 2: Multi-step Composition (C1 -> C2 -> C4)
    ├── exp3_alternatives.py            # Experiment 3: Alternative Implementations (API, DB, GUI)
    ├── exp4_irrelevance.py             # Experiment 4: Irrelevant Operations Filtering
    ├── exp5_operational.py             # Experiment 5: Operational Attributes Trade-offs
    └── run_experiments.py              # Master script executing all experiments and generating plots
```

---

## Quickstart & Reproduction Guide

### Prerequisites
- Python 3.9+ (tested on Python 3.13.5)
- Dependencies: `numpy`, `matplotlib`

```bash
pip install numpy matplotlib
```

### 1. Run the Full Test Suite
Verify that all 10 unit test cases pass cleanly:
```bash
python -m unittest tests/test_embedding.py
```
*Expected output*: `Ran 10 tests in 0.228s - OK`

### 2. Run All 5 Experiments & Generate High-Resolution Plots
Execute the master runner to reproduce all experimental benchmarks and generate charts in `plots/`:
```bash
python -m experiments.run_experiments
```

### 3. Generate Benchmark Dataset JSON
Regenerate `dataset/benchmark_data.json` from the formal specification:
```bash
python -m dataset.dataset
```

---

## Key Experimental Results

### Experiment 1: Capability Compatibility & Asymmetry
Testing $C_1$ (`CreateOrder`), $C_2$ (`MakePayment`), and $C_3$ (`CancelCart`):
- **$C_1 \to C_2$ Compatibility**: **`+0.8000`** (Precondition Match: `1.0000`, Conflict Penalty: `0.0000`, `is_compatible = True`).
- **$C_1 \to C_3$ Incompatibility**: **`-0.5000`** (Conflict Penalty: `1.0000` due to mutually exclusive precondition $Order.exists == \text{False}$, `is_compatible = False`).
- **Directional Asymmetry**: $\text{Score}(C_1 \to C_2) = +0.8000$ vs $\text{Score}(C_2 \to C_1) = +0.0333$ (Delta $= 0.7667$).
- **Naive Flat Cosine Failure**: A naive flat cosine similarity assigns $C_1$ and $C_3$ a score of **`0.4191`** (higher than $C_1$ and $C_2$ at `0.0625`), causing a catastrophic false positive. DF-PVS resolves this completely.

### Experiment 2: Multi-Step Capability Composition
Pipeline: $C_1$ (`CreateOrder`) $\to C_2$ (`MakePayment`) $\to C_4$ (`SendNotification`):
- **Vector Reconstruction Fidelity**: Full Vector Cosine Similarity = **`1.0000`**, L2 Reconstruction Error = **`0.0000`**.
- **Every Subspace**: Precondition, Effect, Input, Output, and Operational subspaces achieve **`1.0000`** similarity.
- **Formal State Invariance**: Step-by-step state application matches direct composite capability execution ($S_3 \equiv S_{direct}$).
- **Additive Operational Algebra**: Latency sums exactly to `550.0 ms`, cost sums to `$0.0580`, and joint reliability matches $Rel_1 \cdot Rel_2 \cdot Rel_4 = 0.97223$.

### Experiment 3: Alternative Implementations
Comparing REST API ($C_{API}$), Direct DB ($C_{DB}$), and GUI Automation ($C_{GUI}$) for `CreateOrder`:
- **Functional Similarity**: **`1.0000`** across all three implementations.
- **Mechanism Similarity**: Drops to `0.4082` - `0.5000`, preserving execution identity.
- **Euclidean Separation**: $L_2 \ge 1.4228$, guaranteeing zero collision in embedding space.
- **Downstream Composability**: All three compose identically into downstream payment ($C_2$) with score **`+0.8000`**.

### Experiment 4: Irrelevant Capability Filtering
Target Goal: $\{OrderExists = \text{True}, PaymentStatus = \text{SUCCESS}, NotificationSent = \text{True}\}$:
- **Composite Pipeline**: **`1.0000`** (100% of goal conditions satisfied).
- **Useful Atomic Steps ($C_1, C_2, C_4$)**: **`0.3333`** each.
- **Irrelevant Operations ($C_{\text{IRR1}}, C_{\text{IRR2}}, C_{\text{IRR3}}$)**: **`0.0000`**.
- **Separation Margin**: **`0.3333`** (Zero false positives, clean thresholding at $\tau = 0.15$).

### Experiment 5: Operational Attributes & Multi-Objective Trade-Offs
- **Pipeline 1 (Internal Fast DB + Wallet)**: 260.0 ms, $0.0150, Reliability 0.98205.
- **Pipeline 2 (Standard Cloud API + Gateway)**: 550.0 ms, $0.0580, Reliability 0.97223.
- **Pipeline 3 (Legacy RPA GUI + Gateway)**: 1280.0 ms, $0.1230, Reliability 0.92127.
- **Pareto Dominance**: Both P1 and P2 strictly Pareto-dominate Legacy RPA (P3). P1 provides optimal latency and cost, while P2 provides loose decoupling.

---

## Evaluation Against Assignment Criteria

| Criteria | Question Evaluated | Evaluation in DF-PVS |
| :--- | :--- | :--- |
| **Capability Representation** | Can different capabilities be represented distinctly? | **YES**: Pairwise Euclidean distances $> 0.5$ prevent coordinate collisions; type and mechanism flags preserve identity. |
| **State Relationship** | Does the representation capture relationship between capabilities and states? | **YES**: State applicability ($S \models P_i$) and state mutation ($S' = S \oplus E_i$) directly mapped to vector spaces. |
| **Precondition-Effect Compatibility**| Can composable capabilities be distinguished from incompatible ones? | **YES**: Match score $+0.8000$ vs conflict score $-0.5000$. |
| **Input-Output Compatibility** | Can dependencies between capabilities be represented? | **YES**: Dataflow parameter matching in $\mathcal{V}_{in}$ and $\mathcal{V}_{out}$. |
| **Composition** | Can complex capabilities be represented from smaller capabilities? | **YES**: Exact closed vector composition operator $\odot$ with $0.0000$ L2 reconstruction error. |
| **Goal Relevance** | Can the relationship between capabilities and goals be identified? | **YES**: Direct projection onto desired state displacement $\Delta_G$ yielding exact fractional progress. |
| **Operational Properties** | Can cost, reliability, availability, constraints be represented? | **YES**: Additive costs, series availability bottlenecks, and log-additive reliability ($-\ln Rel$). |
| **Consistency** | Does representation behave consistently across different problems? | **YES**: Preserves algebraic axioms (associativity, identity) across 15+ benchmark capabilities. |
| **Efficiency** | What are computational and storage requirements? | **YES**: Compact vector representation ($D = 75$ dimensions), sub-millisecond inner product evaluation ($0.228$s for 10 unit tests). |

---

## Author & Academic Information

- **Name**: Melita Mariam Mathew
- **University Registration Number**: TCR24CS046
- **Submission Date**: October 2026
