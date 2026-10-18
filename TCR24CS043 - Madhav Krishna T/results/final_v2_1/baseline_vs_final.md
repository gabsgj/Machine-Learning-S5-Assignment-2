# SCE-128 v1.1 Baseline vs v2.1 Final

| Metric | v1.1 baseline | v2.1 final |
|---|---:|---:|
| Compatibility-proxy AUC | 0.9000 | 0.9000 |
| Seven-step purchase composition consistency | 0.5283 | 0.7929 |
| Mean composition consistency | 0.6880 | 0.8316 |
| Alternative-implementation overall gap | 0.0207 | 0.0569 |
| Alternative-implementation functional mean | 1.0000 | 0.8000 |
| Goal-relevance AUC | 0.8472 | 0.9722 |
| Goal-relevance Precision@5 | 0.8000 | 1.0000 |
| Mean operational-block cosine | 0.7724 | 0.7714 |
| Mean non-operational cosine | 1.0000 | 1.0000 |

## Reading the comparison
- Compatibility-proxy AUC is unchanged; the final model does not claim an improvement in this metric.
- The seven-step purchase-chain composition result uses the corrected leakage-free learned-composition evaluation.
- Goal relevance is a hybrid embedding + symbolic reachability score.
- Alternative-implementation functional similarity is lower in v2.1; the final gain is in overall separation rather than preservation of exact functional cosine.
