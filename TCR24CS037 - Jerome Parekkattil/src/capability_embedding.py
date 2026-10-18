
"""
Structured Capability Embedding (SCE)
Assignment 2: Vector Embedding for Capability Composition

The implementation deliberately does NOT redesign the planner from Assignment 1.
It encodes formal states, goals, and capabilities and provides:
    encode_state
    encode_goal
    encode_capability
    compose
    similarity
    compatibility

The representation is interpretable:
[identity | input | output | precondition | effect | resource/constraint | quality]
Each block is a fixed-width dense vector obtained from deterministic token embeddings.
"""

import hashlib, re, math
import numpy as np

BLOCK_DIM = 24
EPS = 1e-9

def _tokenize(text):
    return re.findall(r"[A-Za-z]+|[0-9]+|[><=]+", str(text).lower())

def _token_vector(token, dim=BLOCK_DIM):
    digest = hashlib.sha256(("SCE-v1|" + token).encode()).digest()
    seed = int.from_bytes(digest[:8], "big") % (2**32)
    rng = np.random.default_rng(seed)
    v = rng.normal(size=dim)
    return v / (np.linalg.norm(v) + EPS)

def _field_vector(items, dim=BLOCK_DIM):
    if not items:
        return np.zeros(dim)
    vectors = []
    for item in items:
        # Include both lexical sub-tokens and a structured raw token.
        vectors.extend(_token_vector(t, dim) for t in _tokenize(item))
        vectors.append(_token_vector("RAW:" + str(item).lower().replace(" ", "_"), dim))
    return np.mean(vectors, axis=0)

def _cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a)*np.linalg.norm(b) + EPS))

def encode_state(state):
    items = [f"{k}={v}" for k,v in state.items() if k != "state_id"]
    return _field_vector(items)

def encode_goal(goal):
    return _field_vector(goal["conditions"])

def encode_capability(c):
    identity = _field_vector([c["id"], c["name"], c["type"], c["mechanism"]])
    inp = _field_vector(c["inputs"])
    out = _field_vector(c["outputs"])
    pre = _field_vector(c["preconditions"])
    eff = _field_vector(c["effects"])
    resources = _field_vector(c["resources"] + c["constraints"])

    quality = np.array([
        c["execution_time_ms"]/500.0,
        c["money_cost"]/0.02,
        c["resource_cost"]/3.0,
        c["risk"],
        1.0-c["reliability"],
        1.0-c["availability"]
    ], dtype=float)
    quality = quality / (np.linalg.norm(quality) + EPS)

    return np.concatenate([identity, inp, out, pre, eff, resources, quality])

def _boundary_compatibility(c1, c2):
    effect_pre = _cosine(_field_vector(c1["effects"]), _field_vector(c2["preconditions"]))
    output_input = _cosine(_field_vector(c1["outputs"]), _field_vector(c2["inputs"]))
    # Directed compatibility is not the same thing as symmetric similarity.
    return 0.6*effect_pre + 0.4*output_input

def similarity(x, y):
    return _cosine(x, y)

def compose(capabilities):
    """Return a formal composite capability and its vector."""
    if not capabilities:
        raise ValueError("At least one capability is required.")
    first, last = capabilities[0], capabilities[-1]

    composite = {
        "id": "COMP_" + "_".join(c["id"] for c in capabilities),
        "name": "Composite(" + " -> ".join(c["name"] for c in capabilities) + ")",
        "type": "COMPOSITE",
        "mechanism": "SEQUENTIAL",
        "inputs": list(first["inputs"]),
        "outputs": list(last["outputs"]),
        "preconditions": list(first["preconditions"]),
        "effects": sorted(set(e for c in capabilities for e in c["effects"])),
        "constraints": sorted(set(k for c in capabilities for k in c["constraints"])),
        "resources": sorted(set(r for c in capabilities for r in c["resources"])),
        "execution_time_ms": sum(c["execution_time_ms"] for c in capabilities),
        "money_cost": sum(c["money_cost"] for c in capabilities),
        "resource_cost": sum(c["resource_cost"] for c in capabilities),
        "risk": 1.0 - math.prod(1.0-c["risk"] for c in capabilities),
        "reliability": math.prod(c["reliability"] for c in capabilities),
        "availability": min(c["availability"] for c in capabilities),
    }
    return composite, encode_capability(composite)

def compatibility(c1, c2):
    return _boundary_compatibility(c1, c2)

def goal_relevance(capability, goal):
    """Similarity between capability effects and goal conditions."""
    return _cosine(_field_vector(capability["effects"]),
                   _field_vector(goal["conditions"]))

if __name__ == "__main__":
    print("SCE module loaded.")
