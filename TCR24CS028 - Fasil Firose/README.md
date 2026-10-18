# Capability Embedding — Source Code

PCCST503 Assignment 2 implementation. Python 3, requires `numpy` and
`matplotlib` (`pip install numpy matplotlib`).

## Files

| File | Purpose |
|---|---|
| `capability_model.py` | Dataclasses for `State`, `Goal`, `Capability`, `IOSpec`. |
| `embedding.py` | The `Embedder` class: vocabulary construction, `encode_state`, `encode_goal`, `encode_capability`, `similarity`, `compatibility`, `goal_relevance`, `applicability`, `compose`, `compose_chain`. |
| `dataset.py` | The experimental dataset: base e-commerce capabilities plus the variants needed for each required experiment. |
| `experiments.py` | Runs all 5 required experiments with inline assertions; prints results and writes `results.json`. |
| `export_dataset.py` | Dumps the dataset to `experimental_dataset.json` (Deliverable 3, standalone of the Python object model). |
| `matrices.py` | Computes full pairwise similarity/compatibility matrices across the dataset; writes CSVs and PNG heatmaps. |
| `run_all.py` | Runs the three scripts above in sequence. |

## Run everything

```bash
pip install numpy matplotlib
python3 run_all.py
```

This prints the results of all 5 required experiments (each with an inline
`assert` so a design regression fails loudly rather than silently), then
writes:

- `results.json` — structured experiment output
- `experimental_dataset.json` — the dataset, independent of the code
- `similarity_full.csv`, `similarity_pure_function.csv`, `compatibility_score.csv` — full pairwise matrices
- `heatmap_similarity_full.png`, `heatmap_similarity_pure_function.png`, `heatmap_compatibility.png`

## Quick interactive example

```python
from dataset import build_capabilities
from embedding import Embedder

caps = build_capabilities()
emb = Embedder(list(caps.values()))

c1, c2 = caps["CreateOrder"], caps["MakePayment"]
print(emb.compatibility(c1, c2))          # directed compatibility score
print(emb.similarity(emb.encode_capability(c1), emb.encode_capability(c2)))  # cosine similarity

composite = emb.compose(c1, c2, new_id="CreateAndPay")
print(composite.effects, composite.reliability)
```

## Design notes

- Vectors are a concatenation of blocks: `type | mechanism | precondition |
  effect | input | output | constraint | resource | operational`.
  `Embedder.layout.slices()` gives the exact index ranges.
- `similarity(v1, v2, block=...)` supports four comparison modes:
  `"full"`, `"functional"` (excludes operational attributes),
  `"pure_function"` (excludes type/mechanism too — "same function regardless
  of implementation"), and `"implementation"` (type/mechanism only).
- `compatibility(Ci, Cj)` is a directed, non-cosine measure: it checks
  whether `Ci`'s effects entail `Cj`'s preconditions and whether `Ci`'s
  outputs satisfy `Cj`'s required inputs. It also detects direct
  contradictions (same variable, opposite required value).
- `compose(Ci, Cj)` raises `ValueError` if composing would contradict a
  precondition — composition is only defined for compatible pairs.
