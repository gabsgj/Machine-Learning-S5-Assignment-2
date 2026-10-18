import numpy as np
from .models import CompositeCapability
from .compatibility import compatibility_score

COMPOSITION_THRESHOLD = 0.7

def can_compose(first, second):
    """Return True when first's effects/outputs satisfy second's requirements."""
    return compatibility_score(first, second) >= COMPOSITION_THRESHOLD

def compose_capabilities(capabilities):
    """Create Cn o ... o C2 o C1 from a sequence C1, C2, ..., Cn."""
    if not capabilities:
        raise ValueError("At least one capability is required.")
    for first, second in zip(capabilities, capabilities[1:]):
        score = compatibility_score(first, second)
        if score < COMPOSITION_THRESHOLD:
            raise ValueError(f"Cannot compose {first.name} -> {second.name}; score={score:.3f}")
    effects = {}
    for capability in capabilities:
        effects.update(capability.effects)
    return CompositeCapability(
        name=" o ".join(c.name for c in reversed(capabilities)),
        components=capabilities,
        preconditions=dict(capabilities[0].preconditions),
        effects=effects
    )

def compose_vectors(capabilities, encoder):
    """Simple mean composition operator used for this assignment."""
    if not capabilities: raise ValueError("No capabilities provided.")
    vectors = np.array([encoder.encode_capability(c) for c in capabilities])
    return np.mean(vectors, axis=0)
