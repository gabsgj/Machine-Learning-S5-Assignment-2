# Deliverable 2 — Implementation

## Environment

- Python 3.10+
- NumPy

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
python src/run_experiments.py
```

Run tests:

```bash
python tests/test_embedding.py
```

## API

```python
encode_state(state)
encode_goal(goal)
encode_capability(capability)
compose(capabilities)
similarity(x, y)
compatibility(c1, c2)
```

The implementation is intentionally deterministic and reproducible. The
vocabulary is constructed from the experimental dataset, and all vector
construction uses explicit weights.

## Files

- `src/embedding.py`: core representation
- `src/run_experiments.py`: all required experiments + consistency/efficiency
- `tests/test_embedding.py`: sanity tests
- `data/*.json`: formal application problems
- `results/*.csv`: generated measurements

## Design choice

A pretrained text embedding is deliberately not used. The assignment asks for
a representation designed specifically for capability composition. Structured
features allow the report to explain exactly why two capabilities are similar,
why they are composable, and how operational properties alter their vectors.
