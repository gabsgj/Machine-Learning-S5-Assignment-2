# Assignment 2 — Vector Embedding for Capability Composition

**Course:** PCCST503  
**Topic:** Design of a Vector Embedding for Capability Composition

This project implements a **problem-specific structured vector embedding** for formally specified
states, goals, and executable capabilities. It is designed around the assignment requirements:
capability identity, state awareness, precondition/effect compatibility, input/output compatibility,
composition, goal relevance, and operational attributes.

The assignment explicitly asks for a representation designed for capability composition rather than
simply applying an existing embedding model. This project therefore uses a custom feature-space
representation built from the formal capability fields.

## Project structure

```text
capability_embedding_assignment2/
├── src/
│   └── capability_embedding.py
├── data/
│   └── dataset.json
├── experiments/
│   └── run_experiments.py
├── tests/
│   └── test_embedding.py
├── report/
│   └── technical_report.md
├── requirements.txt
└── README.md
```

## Main API

- `encode_state(state)`
- `encode_goal(goal)`
- `encode_capability(capability)`
- `compose(capabilities)`
- `similarity(x, y)`
- `compatibility(c1, c2)`

## Proposed representation

Each capability vector is constructed from:

1. Type/mechanism features
2. Input features
3. Output features
4. Preconditions
5. Effects
6. Constraints
7. Resources
8. Goal/state relevance
9. Operational attributes

The representation is deterministic and interpretable. Functional features receive higher weight
than implementation mechanism features, so an API implementation and a GUI implementation can
remain functionally related without being treated as identical.

## Running

```bash
pip install -r requirements.txt
python experiments/run_experiments.py
python -m unittest discover tests
```

The experiment script prints compatibility, composition, alternative implementation,
irrelevant-capability, and operational-attribute results.

## Assignment alignment

The assignment requires four deliverables:

1. Formal embedding design
2. Working implementation
3. Experimental dataset
4. Technical report

All four are included in this repository.

## Example

```python
from src.capability_embedding import CapabilityEmbedder, capability_from_dict

embedder = CapabilityEmbedder()

create_order = capability_from_dict({
    "name": "CreateOrder",
    "type": "API",
    "mechanism": {"method": "POST", "endpoint": "/orders"},
    "inputs": [{"name": "cart_id", "type": "UUID", "domain": "valid UUIDs", "required": True}],
    "outputs": [{"name": "order_id", "type": "UUID", "domain": "valid UUIDs"}],
    "preconditions": {"Cart.exists": True, "Cart.item_count": ">0"},
    "effects": {"Order.exists": True, "Order.status": "CREATED"},
    "constraints": ["quantity > 0"],
    "resources": ["Database", "Network"],
    "cost": {"time": 100, "resource": 2, "money": 0.01, "risk": 0.1, "energy": 1},
    "reliability": 0.99,
    "availability": 1
})

v = embedder.encode_capability(create_order)
print(v.shape)
```
