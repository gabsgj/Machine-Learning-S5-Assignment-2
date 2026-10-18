# Assignment 2 Requirements Audit Matrix

**Course:** PCCST503: Advanced Software Engineering and Systems Design  
**Assignment:** Assignment 2: Design of a Vector Embedding for Capability Composition  
**Student Name:** Royce P Saji  
**Registration ID:** TCR24CS058  
**Roll No:** 57  
**Audit Date:** October 2026  
**Auditor:** Automated Engineering Quality Audit System  

---

## 1. Requirement-by-Requirement Verification Matrix

| # | Requirement | Status | Evidence in Codebase / Report | File / Section Reference | Notes |
|:---:|:---|:---:|:---|:---|:---|
| 1 | **Formal Application Model** | `[PASS]` | System model defined as $\mathcal{A} = (S, C, S_I, G, R, K)$ with concrete dataclasses and state variables. | `src/models.py`<br>`report/formal_embedding_design.md` Sec 1<br>`report/technical_report.md` Sec 1 & 5 | Fully covers state space, capability catalog, initial states, goals, resources, and invariant constraints. |
| 2 | **Formal Capability Model** | `[PASS]` | Capability defined as 11-tuple $C = (T, I, O, P, E, K, R, Q, \text{Rel}, A, M)$ with strict validation. | `src/models.py` (lines 78-101)<br>`report/formal_embedding_design.md` Sec 2 | All 11 elements explicitly modeled and parsed. |
| 3 | **State Representation** | `[PASS]` | `State(id, values)` encoded deterministically into 32-dimensional condition space $\mathbb{R}^{32}$. | `src/encoder.py` (`encode_state`)<br>`tests/test_encoding.py` | Variables map to canonical coordinates with signed polarities. |
| 4 | **Goal Representation** | `[PASS]` | `Goal(id, conditions)` encoded into shared 32-dimensional condition space $\mathbb{R}^{32}$. | `src/encoder.py` (`encode_goal`)<br>`tests/test_encoding.py` | Shares exact coordinates with states, preconditions, and effects. |
| 5 | **Capability Representation** | `[PASS]` | Partitioned Structured Dense vector of dimension 160 (PSD-160) partitioned into 8 slices. | `src/encoder.py` (`encode_capability`)<br>`report/formal_embedding_design.md` Sec 3 | Total dimension verified: $16+24+24+32+32+12+12+8 = 160$. |
| 6 | **Capability Identity** | `[PASS]` | One-hot capability type and execution mechanism signatures encoded in slice `[0:16]`. | `src/encoder.py` (lines 290-310)<br>`tests/test_encoding.py` | Captures architecture (`API`, `DB`, `GUI`, etc.) and protocol hints. |
| 7 | **State Awareness** | `[PASS]` | State variables directly map to precondition slice `[64:96]` and effect slice `[96:128]`. | `src/encoder.py`<br>`report/technical_report.md` Sec 4.2 | Direct dot product evaluates condition alignment. |
| 8 | **Preconditions** | `[PASS]` | Logical propositions required before invocation encoded in slice `[64:96]`. | `src/encoder.py`<br>`tests/test_encoding.py` | Supports boolean, categorical, and numerical constraints. |
| 9 | **Effects** | `[PASS]` | State transitions and assignments encoded in slice `[96:128]`. | `src/encoder.py`<br>`tests/test_encoding.py` | Distinguishes assertions, cancellations, and status updates. |
| 10 | **Input-Output Compatibility** | `[PASS]` | Typed data schema encoded in slices `[16:40]` (inputs) and `[40:64]` (outputs). Alignment measured by $\text{Align}_{OI}$. | `src/metrics.py` (`output_input_alignment`)<br>`tests/test_metrics.py` | Verified in unit tests and Experiment 1. |
| 11 | **Constraints** | `[PASS]` | Invariant execution guard expressions encoded in slice `[128:140]`. | `src/encoder.py`<br>`src/composer.py` | Merged as set union during sequential composition. |
| 12 | **Resources** | `[PASS]` | Shared and exclusive resource requirements encoded in slice `[140:152]`. | `src/encoder.py`<br>`src/composer.py` | Merged as set union during sequential composition. |
| 13 | **Operational Attributes** | `[PASS]` | Execution time, monetary cost, resource units, risk, energy, unreliability, unavailability in `[152:160]`. | `src/encoder.py` (lines 342-359)<br>`tests/test_encoding.py` | Normalized to $[0, 1]$ penalty coordinates. |
| 14 | **Similarity** | `[PASS]` | Safe cosine similarity and weighted multi-block capability similarity with weights summing to 1.0. | `src/metrics.py` (`similarity`)<br>`tests/test_metrics.py` | Symmetric; validated across identical and orthogonal vectors. |
| 15 | **Capability Compatibility** | `[PASS]` | Directional compatibility evaluating effect-precondition and output-input alignment with execution gating. | `src/metrics.py` (`vector_compatibility`, `validate_compatibility`) | Two-tier architecture separates continuous score from discrete validation gate. |
| 16 | **Directionality** | `[PASS]` | Explicitly verifies $\text{Compat}(C_1 \to C_2) \ne \text{Compat}(C_2 \to C_1)$. | `src/metrics.py`<br>`tests/test_metrics.py`<br>Exp 1 results | `C1 -> C2` scores $+1.0000$; reversed `C2 -> C1` scores $0.0000$. |
| 17 | **Composition** | `[PASS]` | Multi-step composition `compose([C1, ..., Cn])` constructing a new valid `Capability` re-encoded into PSD-160. | `src/composer.py`<br>`tests/test_composition.py`<br>Exp 2 results | Internalizes intermediate inputs and preconditions; applies effect overrides. |
| 18 | **Goal Relevance** | `[PASS]` | Continuous metric $\text{GoalRel}(C, G) = \max(0, \text{eff} \cdot g) / \|g\|^2$. | `src/metrics.py` (`goal_relevance`)<br>Exp 4 results | Validated on `Goal_Master`. |
| 19 | **Alternative Implementations** | `[PASS]` | Evaluated API (`C10`), DB (`C11`), and GUI (`C12`) order creation implementations in Experiment 3. | `experiments/run_all.py`<br>`report/technical_report.md` Sec 9.3 | High effect similarity ($1.0000$), zero mechanism similarity ($0.0000$). |
| 20 | **Irrelevant Capabilities** | `[PASS]` | Tested in Experiment 4 against `Goal_Master`. Distractors and contradictory capabilities scored $0.0000$. | `experiments/run_all.py`<br>`report/technical_report.md` Sec 9.4 | Clean separation of useful vs distractor actions. |
| 21 | **Operational Attribute Experiment** | `[PASS]` | Evaluated representation-level operational vector distances and application-level utility selection across 3 priority profiles. | `experiments/run_all.py`<br>`report/technical_report.md` Sec 9.5 | Explicitly separates raw representation from external decision policy. |
| 22 | **Experimental Dataset** | `[PASS]` | Formally specified JSON dataset with 14 capabilities, 4 states, and 5 goals in the e-commerce domain. | `data/experimental_dataset.json` | Fully populated with formal tuples matching assignment requirements. |
| 23 | **Required Experiments** | `[PASS]` | All five mandatory experiments implemented, executable via a single runner, outputting JSON, CSVs, and PNG plots. | `experiments/run_all.py`<br>`experiments/results/` | Completely automated and deterministic. |
| 24 | **Mathematical Formulation** | `[PASS]` | Complete mathematical equations documented for all encodings, similarities, alignments, gating, and aggregations. | `report/formal_embedding_design.md`<br>`report/technical_report.md` Sec 5 | All equations verified against implementation code. |
| 25 | **Formal Embedding Design** | `[PASS]` | Dedicated mathematical design specification document completed. | `report/formal_embedding_design.md` | Detailed 2,177-word document. |
| 26 | **Technical Report** | `[PASS]` | Comprehensive research report structured in 12 required sections plus references and test validation. | `report/technical_report.md` | Detailed 4,732-word document. |
| 27 | **Evaluation Criteria** | `[PASS]` | Directly answers all assignment evaluation questions in technical report analysis. | `report/technical_report.md` Sec 10 | Interprets compatibility, composition, alternatives, distractors, and costs. |
| 28 | **Limitations** | `[PASS]` | Honest assessment of architectural constraints, dimensional limits, sequential composition assumptions, and discretization. | `report/technical_report.md` Sec 11 | Lists 7 concrete technical limitations. |
| 29 | **Reproducibility** | `[PASS]` | Code, tests, and experiment runner are 100% deterministic and reproducible across repeated runs. | `tests/test_experiments.py`<br>`experiments/run_all.py` | 38/38 unit tests pass in 0.40s. |

---

## 2. Summary Audit Statistics

- **Total Requirements Audited:** 29
- **PASS:** 29
- **PARTIAL:** 0
- **FAIL:** 0
- **UNCLEAR:** 0

---

## 3. Key Observations and Architectural Notes

1. **Clean Separation of Representation vs. Utility:**  
   The project maintains a rigorous boundary between the raw PSD-160 vector representation (which deterministically encodes costs, reliability, and availability into slice `[152:160]`) and application-level utility decision policies. The utility function $U(C)$ is correctly presented as an external evaluation policy rather than an intrinsic vector coordinate.
2. **Two-Tier Compatibility Architecture:**  
   The two-tier design prevents runtime failures. In Experiment 1, `CreateOrder -> ArchiveOrder` achieved a vector alignment score of $+0.7000$ due to partial input and precondition matching, but was rejected by the formal validation gate because `Payment.status = SUCCESS` was missing. This behavior demonstrates the necessity of combining continuous search with discrete validation.
3. **Exact Reproducibility:**  
   All random seeds, unseeded hashing, and probabilistic operations were avoided in favor of deterministic linear algebra and structured coordinate indexing, ensuring identical test and experiment results across environments.
