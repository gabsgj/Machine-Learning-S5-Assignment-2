"""Symbolic and vector-level capability composition."""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

from .compatibility import compatibility, condition_matches
from .encoder import encode_capability, fixed_projection, l2_normalize
from .schema import Capability, Condition, InputSpec, OutputSpec, QualityAttributes


def _provided_conditions(effects: Sequence[Condition], preconditions: Sequence[Condition]) -> List[Condition]:
    return [p for p in preconditions if not any(condition_matches(e, p) for e in effects)]


def compose_two(source: Capability, target: Capability) -> Capability:
    """Build the formal composite target ◦ source.

    The function raises ValueError when the source/target pair is not safely
    composable according to the symbolic compatibility rules.
    """
    relation = compatibility(source, target)
    if not relation.compatible:
        raise ValueError(
            f"Cannot compose {source.id}->{target.id}: compatibility score={relation.score:.3f}"
        )

    provided_preconditions = _provided_conditions(source.effects, target.preconditions)
    remaining_inputs = [
        i for i in target.inputs
        if not any(
            o.type == i.type and o.domain == i.domain
            for o in source.outputs
        )
    ]

    # Source inputs remain external. Target inputs that are not supplied by
    # source remain external as well.
    merged_inputs = list(source.inputs)
    existing = {(x.name, x.type, x.domain) for x in merged_inputs}
    for i in remaining_inputs:
        key = (i.name, i.type, i.domain)
        if key not in existing:
            merged_inputs.append(i)
            existing.add(key)

    # Target effects override earlier effects for the same state attribute.
    final_effects: Dict[str, Condition] = {e.attribute: e for e in source.effects}
    for e in target.effects:
        final_effects[e.attribute] = e

    quality = QualityAttributes(
        execution_time_ms=(source.quality.execution_time_ms or 0.0) + (target.quality.execution_time_ms or 0.0),
        resource_cost=(source.quality.resource_cost or 0.0) + (target.quality.resource_cost or 0.0),
        monetary_cost=(source.quality.monetary_cost or 0.0) + (target.quality.monetary_cost or 0.0),
        risk=min(1.0, (source.quality.risk or 0.0) + (target.quality.risk or 0.0)),
        energy_cost=(source.quality.energy_cost or 0.0) + (target.quality.energy_cost or 0.0),
    )

    resources = sorted(set(source.resources) | set(target.resources))

    outputs = list(target.outputs)
    target_output_keys = {(o.name, o.type, o.domain) for o in outputs}
    for o in source.outputs:
        consumed = any(i.type == o.type and i.domain == o.domain for i in target.inputs)
        key = (o.name, o.type, o.domain)
        if not consumed and key not in target_output_keys:
            outputs.append(o)

    return Capability(
        id=f"{source.id}__{target.id}",
        name=f"{source.name}Then{target.name}",
        type="COMPOSITE",
        inputs=merged_inputs,
        outputs=outputs,
        preconditions=list(source.preconditions) + provided_preconditions,
        effects=list(final_effects.values()),
        constraints=list(source.constraints) + list(target.constraints),
        resources=resources,
        quality=quality,
        reliability=source.reliability * target.reliability,
        availability=int(bool(source.availability) and bool(target.availability)),
        mechanism={
            "composition": f"{source.id} -> {target.id}",
            "source_type": source.type,
            "target_type": target.type,
        },
    )


def compose_many(capabilities: Sequence[Capability]) -> Capability:
    if not capabilities:
        raise ValueError("At least one capability is required")
    composite = capabilities[0]
    for capability in capabilities[1:]:
        composite = compose_two(composite, capability)
    return composite


def vector_compose(source_vector: np.ndarray, target_vector: np.ndarray, relation_features: Sequence[float]) -> np.ndarray:
    """Deterministic vector-space composition operator for v1.

    v1 intentionally uses a fixed projector. A learned Compose_theta module
    can replace this once the expanded dataset is available.
    """
    rel = np.asarray(relation_features, dtype=np.float32)
    relation_vec = fixed_projection(rel, 128, "vector_composition_relation")
    mixed = (
        0.45 * source_vector.astype(np.float32)
        + 0.45 * target_vector.astype(np.float32)
        + 0.10 * relation_vec
    )
    return l2_normalize(mixed)
