from __future__ import annotations

from typing import Iterable, List

from .compatibility import is_composable
from .embedding import StructuredEmbedder
from .models import Capability, CompositeCapability


def compose_capabilities(
    capabilities: Iterable[Capability],
    embedder: StructuredEmbedder,
    strict: bool = True,
) -> CompositeCapability:
    caps = list(capabilities)
    if not caps:
        raise ValueError("Cannot compose an empty capability sequence.")

    if strict:
        for a, b in zip(caps, caps[1:]):
            if not is_composable(a, b):
                raise ValueError(
                    f"Invalid composition: {a.name} -> {b.name}"
                )

    first = caps[0]
    last = caps[-1]

    # Inputs required by the first capability remain inputs of the composite.
    # Outputs of the last capability become outputs of the composite.
    # Preconditions/effects are exposed at the boundaries.
    composite = CompositeCapability(
        name=" ∘ ".join(c.name for c in caps),
        capability_type="COMPOSITE",
        inputs=first.inputs.copy(),
        outputs=last.outputs.copy(),
        preconditions=first.preconditions.copy(),
        effects=[x for c in caps for x in c.effects],
        constraints=[
            x for c in caps for x in c.constraints
        ],
        resources=sorted(set(x for c in caps for x in c.resources)),
        quality=type(first.quality)(
            time_ms=sum(c.quality.time_ms for c in caps),
            resource_cost=sum(c.quality.resource_cost for c in caps),
            money_cost=sum(c.quality.money_cost for c in caps),
            risk=1.0 - __import__("math").prod(1.0 - c.quality.risk for c in caps),
            energy=sum(c.quality.energy for c in caps),
        ),
        reliability=__import__("math").prod(c.reliability for c in caps),
        availability=min(c.availability for c in caps),
        mechanism={"composition": "sequential"},
        tags=["composite"],
        components=[c.name for c in caps],
    )

    return composite
