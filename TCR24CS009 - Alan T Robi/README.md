# Vector Embedding for Capability Composition

**Alan T. Robi**

TCR24CS009

A formal, interpretable **Hybrid Structured Capability Embedding** system implemented in Python.

---

## 1. Project Purpose & Overview

In software architectures and automated planning systems, applications are composed of reusable operations termed **capabilities**. While traditional natural language embeddings (e.g. Word2Vec, BERT) capture text semantics, they cannot reason over formal pre/post-conditions, input-output type constraints, or operational properties. Furthermore, semantic resemblance does not imply composability ($\text{Similarity} \neq \text{Composability}$).

This project designs, implements, and evaluates a domain-specific vector space representation $V(C_i) \in \mathbb{R}^D$ and compact dense projection $e(C_i) \in \mathbb{R}^{16}$ for formally specified capabilities, states, and goals. It explicitly separates **cosine vector similarity** from **directional capability compatibility** and **sequence composition**.

---

## 2. Key Mathematical Design

Each formal capability is represented as an 11-tuple:
$$C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)$$

Where:
- $T_i$: Capability type $\in \{\text{API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE}\}$
- $I_i, O_i$: Formal input and output specifications $\{(name, type, domain, required)\}$
- $P_i, E_i$: Precondition and effect variable-value state predicates
- $K_i, R_i$: Constraint and resource requirement sets
- $Q_i$: Operational costs $(C_{time}, C_{resource}, C_{money}, C_{risk}, C_{energy})$
- $Rel_i, A_i$: Reliability $\in [0, 1]$ and Availability $\in [0, 1]$
- $M_i$: Execution mechanism details (e.g. `{method: POST, endpoint: /orders}`)

### Structured Vector Encodings*
1. **Capability Vector**: Concatenation of sub-vectors:
   $$
   V(C_i) = [ V_{type} \mid V_{inputs} \mid V_{outputs} \mid V_{preconditions} \mid V_{effects} \mid V_{constraints} \mid V_{resources} \mid V_{mechanism} \mid V_{operational} ]
   $$
2. **Dense Embedding**: $\mathbf{e}(C_i) = \text{PCA}_{16}(V(C_i))$
3. **Directional Compatibility Score**:
   $$
   \text{Compat}(C_1, C_2) = w_1 \cdot \text{Match}_{EP}(E_1, P_2) + w_2 \cdot \text{Match}_{OI}(O_1, I_2)
   $$
   where explicit contradictions (e.g., $OrderExists=true$ vs $OrderExists=false$) enforce $\text{Compat}(C_1, C_2) = 0$.

---

## 3. Directory & Project Structure

```
VectorRep/
│
├── data/
│   └── capabilities.json                 # 25 formally specified capabilities
│
├── src/
│   ├── capability.py                     # Dataclasses & JSON loader for C_i tuple
│   ├── state.py                          # Formal State S and Goal G representations
│   ├── encoder.py                        # Structured vector & PCA dense encoder
│   ├── similarity.py                     # Cosine & sub-space similarity metrics
│   ├── compatibility.py                  # Directional compatibility engine
│   ├── composition.py                    # Capability sequence composition engine
│   ├── evaluation.py                     # Baselines (Textual/Flat) & metric utilities
│   └── utils.py                          # File I/O and normalization helpers
│
├── experiments/
│   ├── run_experiments.py                # Master runner for all 5 experiments
│   ├── experiment_1_compatibility.py     # Experiment 1: Compatibility testing
│   ├── experiment_2_composition.py       # Experiment 2: Capability composition
│   ├── experiment_3_implementations.py   # Experiment 3: Alternative implementations
│   ├── experiment_4_irrelevant.py        # Experiment 4: Irrelevant capabilities
│   └── experiment_5_operational.py       # Experiment 5: Operational attributes
│
├── results/
│   ├── tables/                           # CSV and JSON result metrics
│   └── plots/                            # PNG visualization plots
│
├── tests/
│   └── test_core.py                      # Pytest/Unittest suite
│
├── README.md                             # Project instructions and documentation
├── requirements.txt                      # Python dependencies
├── technical_report.md                   # Formal 12-section technical report
└── PROJECT_SUMMARY.md                    # High-level summary of findings
```

---

## 4. Environment & Installation

### Environment Requirements
- Python 3.9+
- Standard packages: NumPy, Pandas, scikit-learn, Matplotlib

### Installation Steps
```bash
# 1. Clone or navigate to the workspace directory (working directory may not be VectorRep. Below is an example using the working directory as VectorRep. Kindly use your working directory which contains all the files in the repository)
cd VectorRep

# 2. Install dependencies
pip install -r requirements.txt
```

---

## 5. How to Run Experiments & Tests

### Run Unit Tests
```bash
python -m unittest discover -s tests
```

### Run All Experiments
```bash
python experiments/run_experiments.py
```

Running the experiment runner will execute all 5 required assignment experiments, calculate efficiency benchmarks, save CSV tables in `results/tables/`, and save 6 visualization plots in `results/plots/`.

---

## 6. Generated Results & Artifacts

- **PCA Embeddings Plot**: `results/plots/plot_pca_embeddings.png`
- **Compatibility Scores Plot**: `results/plots/plot_compatibility_scores.png`
- **Composition Plot**: `results/plots/plot_composite_similarity.png`
- **Alternative Implementation Plot**: `results/plots/plot_alternative_implementations.png`
- **Goal Relevance Plot**: `results/plots/plot_goal_relevance.png`
- **Operational Trade-off Plot**: `results/plots/plot_operational_tradeoff.png`
- **Full Report**: `technical_report.md`


*Kindly use other tools to view the .md file correctly if any symbols in the content of file seems confusing.
