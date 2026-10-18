# PCCST503 Assignment 2: Capability Composition

**Name:** MUHAMMED JIYAD U  
**University Registration Number:** LTCR24CS074

Complete finite-state research implementation with a technical report, formal design,
JSON dataset, measured results, pairwise labels and actual encoded vectors.

## Run

Requires Python 3.10+ and NumPy. From this directory:

```bash
python -m pip install -r requirements.txt
python make_dataset.py
OPENBLAS_NUM_THREADS=1 python experiments.py
python -m unittest -v
```

The environment variable keeps timing comparable by using one BLAS thread;
on Windows omit it or set OPENBLAS_NUM_THREADS=1 through your shell.
No network, model weights, GPU, or planner is used at runtime.

## API example

```python
import json
from embedding import Embedding, similarity
p = json.load(open('dataset.json'))['problems'][0]
m = Embedding(p)
a, b, c = p['capabilities'][:3]
state = m.encode(p['initial_state'], 'state')
goal = m.encode(p['goal'], 'goal')
atomic = m.encode(a)
composite = m.compose([a, b, c])
assert m.encode(composite) is composite
print(m.compatibility(a, b))
print(similarity(atomic, m.encode(p['capabilities'][4])))
print(m.goal_score(composite, p['initial_state'], p['goal']))
print(m.execute(composite, p['initial_state'],
                p['available_resources'], {'request': 'valid'}))
```

`compose([a,b,c])` means execute a, then b, then c. It builds a structural
partial transformer even if current resources or availability make execution
impossible. `execute` applies those hard gates. It is a specification simulator,
not an API/GUI/database adapter and does not sample failures or generate real IDs.
Input values use finite domain membership; port types are symbolic labels.

Files:
- embedding.py: numerical representation and operations.
- dataset.json / make_dataset.py: three reproducible formal application problems.
- experiments.py: five required experiments, symbolic oracle, dense timing.
- test_embedding.py: regression checks for ordering, composition, I/O and gates.
- FORMAL_DESIGN.md: standalone mathematical specification.
- Technical_Report.pdf / Technical_Report.md: all 12 required report sections.
- results/results.json: measured outputs and environment.
- results/*_pairs.csv: all ordered pair labels and semantic cosine scores.
- results/*_vectors.npz: state basis, goal mask, atomic vectors and composite vector.

The three problems are intentionally structurally similar; they establish
renaming consistency, not broad empirical generalization. The results are from
a synthetic closed finite universe and make no claim about learned embeddings.
Dense state-space storage is the principal limitation. Read the report before
presenting the model or interpreting 100% exact correctness.

To regenerate the PDF, install requirements-report.txt and run python build_report.py. This uses existing measured results and also regenerates the Markdown report and formal design.
