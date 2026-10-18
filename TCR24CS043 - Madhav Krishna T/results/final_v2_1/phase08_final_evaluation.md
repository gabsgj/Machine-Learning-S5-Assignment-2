# SCE-128 v2.1 — Final Integrated Evaluation

## Executive result
The final implementation combines the deterministic SCE-128 structured 128-D representation, explicit symbolic compatibility reasoning, hybrid goal relevance, and a leakage-free learned composition operator.

## Final metrics
| Area | Metric | Result |
|---|---|---:|
| Compatibility | Formal accuracy | 1.0000 |
| Compatibility | Vector compatibility-proxy AUC | 0.9000 |
| Composition | Held-out direct-pair mean | 0.8546 |
| Composition | Mean recursive-chain consistency | 0.8316 |
| Composition | Minimum recursive-chain consistency | 0.7929 |
| Alternative implementations | Functional gap | 0.0932 |
| Alternative implementations | Overall gap | 0.0569 |
| Goal relevance | AUC | 0.9722 |
| Goal relevance | Precision@5 | 1.0000 |
| Operational | Mean whole-vector cosine | 0.9771 |
| Operational | Mean operational-block cosine | 0.7714 |
| Operational | Mean non-operational cosine | 1.0000 |

## Interpretation
1. Compatibility: the symbolic engine reproduces all labeled compatibility relationships; the vector proxy provides an independent composability signal.
2. Composition: the learned composer generalizes to held-out direct pairs and recursively composes longer chains without receiving formal composites as inputs.
3. Alternative implementations: API, database, and GUI variants retain functional similarity while implementation information remains distinguishable, but the gap is moderate rather than perfect.
4. Goal relevance: the hybrid relevance score strongly separates labeled relevant and irrelevant capabilities on this dataset.
5. Operational attributes: controlled cost, reliability, availability, and risk perturbations affect the operational block while leaving the non-operational representation effectively unchanged.

## Important limitations
- The dataset is deliberately small and domain-specific; results are not a benchmark of general capability-embedding performance.
- The goal-relevance experiment uses symbolic backward reachability in addition to vector evidence.
- The learned composition model is intentionally low-parameter because the dataset is small; broader claims require more applications and independent datasets.

## Generated artifacts
- JSON: `C:\Users\Madhav Krishna T\Desktop\SCE128_Capability_Embedding_Final\results\final_v2_1\phase08_final_evaluation.json`
- Markdown: `C:\Users\Madhav Krishna T\Desktop\SCE128_Capability_Embedding_Final\results\final_v2_1\phase08_final_evaluation.md`
