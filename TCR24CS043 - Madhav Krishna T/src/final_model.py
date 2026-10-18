"""SCE-128 v2: relation-aware, block-aware, structure-guided representation.

This module deliberately keeps the v1.1 encoder unchanged and adds a second
model that addresses the weaknesses observed in Experiments 1-5:

1. Block-aware similarity instead of raw whole-vector cosine.
2. Goal relevance combines effect-goal similarity, exact goal support, and
   backward structural reachability through the formal compatibility graph.
3. Composition is structure-guided: the source/target interfaces are composed
   using the same formal precondition/effect and input/output rules, then each
   resulting block is encoded into a single 128-D vector.

No experimental labels are used as encoder inputs.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np

from .compatibility import compatibility, condition_matches
from .encoder import (
    capability_blocks,
    cosine,
    encode_capability,
    encode_condition_common,
    encode_goal,
    encode_effects_common,
    encode_io_set,
    encode_condition_set,
    encode_constraints,
    encode_resources,
    encode_mechanism,
    encode_quality,
    l2_normalize,
)
from .schema import Capability, Condition, Constraint, Goal, InputSpec, OutputSpec, QualityAttributes


V2_BLOCK_WEIGHTS = {
    "function": 0.05,
    "type": 0.05,
    "input": 0.12,
    "output": 0.12,
    "precondition": 0.12,
    "effect": 0.20,
    "constraint": 0.06,
    "resource": 0.06,
    "mechanism": 0.08,
    "operational": 0.14,
}

FUNCTIONAL_BLOCKS = (
    "function",
    "input",
    "output",
    "precondition",
    "effect",
    "constraint",
    "resource",
)
IMPLEMENTATION_BLOCKS = ("type", "mechanism")
OPERATIONAL_BLOCKS = ("operational",)


def _mean(values: Sequence[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _dedupe_conditions(conditions: Sequence[Condition]) -> List[Condition]:
    seen = set()
    out: List[Condition] = []
    for c in conditions:
        key = (c.attribute, c.operator, repr(c.value))
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def _dedupe_inputs(items: Sequence[InputSpec]) -> List[InputSpec]:
    seen = set()
    out: List[InputSpec] = []
    for item in items:
        key = (item.name, item.type, item.domain, item.required)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _dedupe_outputs(items: Sequence[OutputSpec]) -> List[OutputSpec]:
    seen = set()
    out: List[OutputSpec] = []
    for item in items:
        key = (item.name, item.type, item.domain)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _provided_by_outputs(outputs: Sequence[OutputSpec], inp: InputSpec) -> bool:
    return any(o.type == inp.type and o.domain == inp.domain and (o.name == inp.name or True) for o in outputs)


def _merge_effects(source: Sequence[Condition], target: Sequence[Condition]) -> List[Condition]:
    """Apply target effects after source effects; target wins on same attribute."""
    target_attrs = {e.attribute for e in target}
    merged = [e for e in source if e.attribute not in target_attrs]
    merged.extend(target)
    return _dedupe_conditions(merged)


def _remaining_target_preconditions(source: Capability, target: Capability) -> List[Condition]:
    remaining: List[Condition] = []
    for p in target.preconditions:
        satisfied = any(condition_matches(e, p) for e in source.effects)
        if not satisfied:
            remaining.append(p)
    return remaining


def compose_formal_v2(source: Capability, target: Capability) -> Capability:
    """Build a composite capability from two sequential capabilities.

    The composition uses formal input/output and precondition/effect semantics;
    it does not use the dataset relevance labels.
    """
    target_remaining_inputs = [
        i for i in target.inputs if i.required and not _provided_by_outputs(source.outputs, i)
    ] + [i for i in target.inputs if not i.required]
    composite_inputs = _dedupe_inputs(list(source.inputs) + target_remaining_inputs)

    consumed_names = {i.name for i in target.inputs}
    source_external_outputs = [o for o in source.outputs if o.name not in consumed_names]
    composite_outputs = _dedupe_outputs(source_external_outputs + list(target.outputs))

    composite_preconditions = _dedupe_conditions(
        list(source.preconditions) + _remaining_target_preconditions(source, target)
    )
    composite_effects = _merge_effects(source.effects, target.effects)
    composite_constraints = []
    seen_constraints = set()
    for c in list(source.constraints) + list(target.constraints):
        if c.expression not in seen_constraints:
            seen_constraints.add(c.expression)
            composite_constraints.append(c)

    resources: List[str] = []
    for resource in list(source.resources) + list(target.resources):
        if resource not in resources:
            resources.append(resource)

    q1, q2 = source.quality, target.quality
    quality = QualityAttributes(
        execution_time_ms=(q1.execution_time_ms or 0.0) + (q2.execution_time_ms or 0.0),
        resource_cost=(q1.resource_cost or 0.0) + (q2.resource_cost or 0.0),
        monetary_cost=(q1.monetary_cost or 0.0) + (q2.monetary_cost or 0.0),
        risk=min(1.0, (q1.risk or 0.0) + (q2.risk or 0.0)),
        energy_cost=(q1.energy_cost or 0.0) + (q2.energy_cost or 0.0),
    )

    mechanism = {
        "step_1_type": source.type,
        "step_1_name": source.name,
        "step_2_type": target.type,
        "step_2_name": target.name,
    }

    return Capability(
        id=f"{source.id}__{target.id}",
        name=f"{source.name}Then{target.name}",
        type="COMPOSITE",
        inputs=composite_inputs,
        outputs=composite_outputs,
        preconditions=composite_preconditions,
        effects=composite_effects,
        constraints=composite_constraints,
        resources=resources,
        quality=quality,
        reliability=max(0.0, min(1.0, source.reliability * target.reliability)),
        availability=int(bool(source.availability) and bool(target.availability)),
        mechanism=mechanism,
    )


def compose_chain_formal_v2(capabilities: Sequence[Capability]) -> Capability:
    if not capabilities:
        raise ValueError("Cannot compose an empty capability chain")
    composite = capabilities[0]
    for next_cap in capabilities[1:]:
        composite = compose_formal_v2(composite, next_cap)
    return composite


def encode_capability_v2(capability: Capability) -> np.ndarray:
    """Encode using the stable SCE-128 v1.1 encoder; v2 changes the relations."""
    return encode_capability(capability)


def blockwise_similarity_v2(a: np.ndarray, b: np.ndarray) -> float:
    ba = capability_blocks(a)
    bb = capability_blocks(b)
    return float(
        sum(V2_BLOCK_WEIGHTS[name] * cosine(ba[name], bb[name]) for name in V2_BLOCK_WEIGHTS)
    )


def functional_similarity_v2(a: np.ndarray, b: np.ndarray) -> float:
    ba = capability_blocks(a)
    bb = capability_blocks(b)
    return _mean([cosine(ba[name], bb[name]) for name in FUNCTIONAL_BLOCKS])


def implementation_similarity_v2(a: np.ndarray, b: np.ndarray) -> float:
    ba = capability_blocks(a)
    bb = capability_blocks(b)
    return _mean([cosine(ba[name], bb[name]) for name in IMPLEMENTATION_BLOCKS])


def operational_similarity_v2(a: np.ndarray, b: np.ndarray) -> float:
    ba = capability_blocks(a)
    bb = capability_blocks(b)
    return cosine(ba["operational"], bb["operational"])


def structural_relation_similarity_v2(source: Capability, target: Capability) -> float:
    """A vector-only directional relation score derived from relation blocks."""
    source_vec = encode_capability_v2(source)
    target_vec = encode_capability_v2(target)
    bs = capability_blocks(source_vec)
    bt = capability_blocks(target_vec)
    return float(
        0.30 * cosine(bs["effect"], bt["precondition"])
        + 0.30 * cosine(bs["precondition"], bt["effect"])
        + 0.20 * cosine(bs["output"], bt["input"])
        + 0.20 * cosine(bs["input"], bt["output"])
    )


def _build_goal_reachability(caps: Mapping[str, Capability], goal: Goal) -> set[str]:
    goal_keys = {(g.attribute, g.operator, repr(g.value)) for g in goal}
    sinks = {
        cid
        for cid, cap in caps.items()
        if any((e.attribute, e.operator, repr(e.value)) in goal_keys for e in cap.effects)
    }
    reverse: Dict[str, List[str]] = {cid: [] for cid in caps}
    for cid, cap in caps.items():
        for target_id, target in caps.items():
            if cid == target_id:
                continue
            if compatibility(cap, target).compatible:
                reverse[target_id].append(cid)

    reachable = set(sinks)
    stack = list(sinks)
    while stack:
        current = stack.pop()
        for predecessor in reverse[current]:
            if predecessor not in reachable:
                reachable.add(predecessor)
                stack.append(predecessor)
    return reachable


def _exact_goal_effect_coverage(capability: Capability, goal: Goal) -> float:
    if not goal:
        return 0.0
    goal_keys = {(g.attribute, g.operator, repr(g.value)) for g in goal}
    hits = {
        (e.attribute, e.operator, repr(e.value))
        for e in capability.effects
        if (e.attribute, e.operator, repr(e.value)) in goal_keys
    }
    return len(hits) / len(goal_keys)


def goal_relevance_v2(capability: Capability, goal: Goal, caps: Mapping[str, Capability]) -> Dict[str, float]:
    goal_vec = encode_goal(goal)
    effect_vec = encode_effects_common(capability)
    semantic = cosine(effect_vec, goal_vec)
    exact_support = _exact_goal_effect_coverage(capability, goal)
    reachable = capability.id in _build_goal_reachability(caps, goal)
    structural = 1.0 if reachable else 0.0
    # The score is intentionally structural: semantic effect alignment alone
    # was responsible for the CancelOrder false positive in v1.1.
    score = 0.5 * semantic + 0.2 * exact_support + 0.3 * structural
    return {
        "semantic_effect_goal": float(semantic),
        "exact_goal_effect_coverage": float(exact_support),
        "backward_goal_reachability": float(structural),
        "score": float(score),
    }


def compose_vector_v2(source: Capability, target: Capability) -> np.ndarray:
    """Structure-guided vector composition.

    The operation first applies formal input/output and precondition/effect
    composition, then encodes the resulting interface blocks. This is a
    deterministic relation-aware composition operator rather than a simple
    average of two atomic vectors.
    """
    composite = compose_formal_v2(source, target)
    return encode_capability_v2(composite)
