# PCCST503 Assignment 2 - Factored Guard-Effect Embedding
NAME : A K ASIF
REGISTRATION NUMBER: TCR24CS007
A second, independently designed solution based on finite-domain guard masks,
assignment features, typed port masks and regression-based composition.
The core representation never enumerates the Cartesian state space.

## Reproduce

Requires Python 3.10+ and NumPy:

```bash
python -m pip install -r requirements.txt
python make_dataset.py
python experiments.py
python -m unittest -v
```

Results are deterministic except timing. Eight tests include 80 seeded random
three-step compositions checked against a separate exhaustive interpreter.
To rebuild the PDF after experiments:

```bash
python -m pip install -r requirements-report.txt
python build_report.py
```

## API

```python
import json
from embedding import FactoredEmbedding, similarity
p = json.load(open('dataset.json'))['problems'][0]
m = FactoredEmbedding(p)
a, b, c = p['capabilities'][:3]
state = m.encode(p['initial_state'], 'state')
goal = m.encode(p['goal'], 'goal')
encoded = m.encode(a)
print(m.compatibility(a, b))
composite = m.compose([a, b, c])
print(composite.guards, composite.effects)
print(m.goal_satisfied(composite, p['initial_state'], p['goal']))
print(m.execute(composite, p['initial_state'],
                p['available_resources'], {'cart_id': 'valid'}))
# Compose using only numbers plus the fixed schema, without original specs:
numeric_only = [m.from_vector(m.encode(x).values.copy()) for x in [a,b,c]]
rebuilt = m.compose(numeric_only)
assert m.encode(rebuilt) is rebuilt
print(similarity(encoded, m.encode(p['capabilities'][4])))
```

compose([a,b,c]) means a then b then c. Encoded composites can be nested.
Similarity measures guard/effect resemblance; compatibility is a directional
state-and-interface check. goal_relevance counts directly established goal
restrictions; goal_satisfied simulates a given sequence from an initial state.
Neither method searches for a plan.

execute is a deterministic specification simulator, not an API/GUI/database
adapter. It enforces resource, availability and finite input-domain gates.
Declared port types are schema labels; output values are not generated or sampled.
The schema is fixed per problem and is required to interpret stored vectors.
The implementation supports conjunctions of unary finite-domain predicates and
constant assignments. It does not support cross-variable comparisons or
conditional effects. Extensional equivalence deliberately shares semantic blocks.

## Package contents

- FORMAL_DESIGN.md: standalone mathematical design.
- embedding.py: encoding, decoding, similarity, compatibility and composition.
- dataset.json / make_dataset.py: commerce, logistics and build pipeline problems.
- experiments.py: all five experiments, exhaustive oracle, scalability results.
- test_embedding.py: eight tests, including generated-case verification.
- Technical_Report.pdf / Technical_Report.md: all 12 required sections.
- results/results.json: measured results and environment.
- results/*_pairs.csv: all 283 ordered pair labels and similarity scores.
- results/*_vectors.npz: numeric atomic/state/goal/composite embeddings.
- build_report.py / requirements-report.txt: report reproduction.

The dataset is synthetic. The report distinguishes exactness for the supported
formal fragment from claims about arbitrary applications or learned prediction.
