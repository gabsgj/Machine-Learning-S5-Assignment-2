"""Directional compatibility and applicability logic for SCE-128."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np

from .encoder import cosine, encode_condition, encode_condition_common
from .schema import Capability, Condition, InputSpec, OutputSpec, State


@dataclass
class CompatibilityResult:
    source_id: str
    target_id: str
    effect_precondition_exact: float
    effect_precondition_vector: float
    output_input_exact: float
    output_input_vector: float
    conflict: float
    resource_overlap: float
    score: float
    compatible: bool
    reasons: List[str]


def condition_key(c: Condition) -> Tuple[str, str, Any]:
    return (c.attribute, c.operator, c.value)


def condition_matches(effect: Condition, precondition: Condition) -> bool:
    """Conservative predicate matcher for the core dataset.

    v1 supports equality, >, >=, <, <= and a small subset of direct numeric
    reasoning. Unknown operators are treated as non-matches instead of guessed.
    """
    if effect.attribute != precondition.attribute:
        return False

    ev, pv = effect.value, precondition.value
    eo, po = effect.operator, precondition.operator

    if eo == "==" and po == "==":
        return ev == pv
    if eo == "==" and po == ">":
        try:
            return float(ev) > float(pv)
        except (TypeError, ValueError):
            return False
    if eo == "==" and po == ">=":
        try:
            return float(ev) >= float(pv)
        except (TypeError, ValueError):
            return False
    if eo == "==" and po == "<":
        try:
            return float(ev) < float(pv)
        except (TypeError, ValueError):
            return False
    if eo == "==" and po == "<=":
        try:
            return float(ev) <= float(pv)
        except (TypeError, ValueError):
            return False
    return False


def condition_conflicts(effect: Condition, precondition: Condition) -> bool:
    if effect.attribute != precondition.attribute:
        return False
    # Exact opposite equality is an explicit contradiction.
    if effect.operator == "==" and precondition.operator == "==":
        return effect.value != precondition.value
    return False


def effect_precondition_scores(source: Capability, target: Capability) -> Tuple[float, float, List[str]]:
    if not target.preconditions:
        return 1.0, 1.0, ["Target has no preconditions."]

    source_effect_attributes = {e.attribute for e in source.effects}
    target_input_names = {i.name for i in target.inputs}
    dependent = [p for p in target.preconditions if p.attribute in source_effect_attributes]
    unresolved = [
        p for p in target.preconditions
        if p.attribute not in source_effect_attributes and p.attribute not in target_input_names
    ]

    # A precondition may be satisfied internally by the upstream effect, or it
    # may remain an externally supplied condition when it is also a target
    # input. It is not a composition dependency in the latter case.
    if not dependent:
        exact = 0.0 if unresolved else 1.0
        vector = 0.0
        reasons = []
        if unresolved:
            reasons.extend(
                f"Unresolved downstream precondition: {p.attribute} {p.operator} {p.value}"
                for p in unresolved
            )
        return exact, vector, reasons

    exact_hits = 0
    vector_hits: List[float] = []
    reasons: List[str] = []

    for p in dependent:
        matching = [e for e in source.effects if condition_matches(e, p)]
        conflicting = [e for e in source.effects if e.attribute == p.attribute and condition_conflicts(e, p)]
        if matching:
            exact_hits += 1
            reasons.append(f"Effect satisfies precondition: {p.attribute} {p.operator} {p.value}")
        elif conflicting:
            reasons.append(f"Effect conflicts with precondition: {p.attribute} {p.operator} {p.value}")
        else:
            reasons.append(f"No exact effect satisfies precondition: {p.attribute} {p.operator} {p.value}")

        p_vec = encode_condition_common(p)
        e_scores = [cosine(encode_condition_common(e), p_vec) for e in source.effects]
        vector_hits.append(max(e_scores) if e_scores else 0.0)

    if unresolved:
        reasons.extend(
            f"Unresolved downstream precondition: {p.attribute} {p.operator} {p.value}"
            for p in unresolved
        )
        # Keep exact PE below 1.0 so the caller treats this as non-composable.
        exact = 0.0
    else:
        exact = exact_hits / len(dependent)

    vector = max(0.0, float(np.mean(vector_hits))) if vector_hits else 0.0
    return exact, vector, reasons

def _input_output_exact(output: OutputSpec, input_spec: InputSpec) -> bool:
    return (
        output.name == input_spec.name
        and output.type == input_spec.type
        and output.domain == input_spec.domain
    )


def _input_output_compatible(output: OutputSpec, input_spec: InputSpec) -> bool:
    # v1 also permits a different variable name when type/domain are identical.
    return output.type == input_spec.type and output.domain == input_spec.domain


def output_input_scores(source: Capability, target: Capability) -> Tuple[float, float, List[str]]:
    required = [i for i in target.inputs if i.required]
    if not required:
        return 1.0, 1.0, ["Target has no required inputs."]

    exact_hits = 0
    vector_hits: List[float] = []
    reasons: List[str] = []
    for i in required:
        exact_matches = [o for o in source.outputs if _input_output_exact(o, i)]
        relaxed_matches = [o for o in source.outputs if _input_output_compatible(o, i)]
        if exact_matches:
            exact_hits += 1
            reasons.append(f"Output exactly satisfies input: {i.name}")
        elif relaxed_matches:
            exact_hits += 0.5
            reasons.append(f"Output matches input type/domain: {i.name}")
        else:
            reasons.append(f"No output satisfies input: {i.name}")

        i_vec = encode_condition_common(Condition(f"{i.name}:{i.type}", "==", i.domain))
        o_scores = [
            cosine(
                encode_condition_common(Condition(f"{o.name}:{o.type}", "==", o.domain)),
                i_vec,
            )
            for o in source.outputs
        ]
        vector_hits.append(max(o_scores) if o_scores else 0.0)

    exact = min(1.0, exact_hits / len(required))
    vector = max(0.0, float(np.mean(vector_hits)))
    return exact, vector, reasons


def compatibility(
    source: Capability,
    target: Capability,
    threshold: float = 0.60,
) -> CompatibilityResult:
    pe_exact, pe_vec, pe_reasons = effect_precondition_scores(source, target)
    io_exact, io_vec, io_reasons = output_input_scores(source, target)

    conflict_count = sum(
        1
        for e in source.effects
        for p in target.preconditions
        if condition_conflicts(e, p)
    )
    conflict = 1.0 if conflict_count > 0 else 0.0

    source_resources = set(source.resources)
    target_resources = set(target.resources)
    if not source_resources or not target_resources:
        resource_overlap = 0.0
    else:
        resource_overlap = len(source_resources & target_resources) / len(source_resources | target_resources)

    # Exact symbolic evidence receives the greatest weight. Vector evidence is
    # intentionally supplementary, not the authority for composability.
    score = (
        0.55 * pe_exact
        + 0.20 * pe_vec
        + 0.15 * io_exact
        + 0.05 * io_vec
        + 0.05 * resource_overlap
    )
    if conflict:
        score *= 0.10

    compatible = bool(pe_exact >= 1.0 and io_exact >= 0.5 and conflict == 0.0 and score >= threshold)

    return CompatibilityResult(
        source.id,
        target.id,
        float(pe_exact),
        float(pe_vec),
        float(io_exact),
        float(io_vec),
        float(conflict),
        float(resource_overlap),
        float(score),
        compatible,
        pe_reasons + io_reasons,
    )


def state_applicability(capability: Capability, state: State) -> float:
    if not capability.preconditions:
        return 1.0
    hits = 0
    for p in capability.preconditions:
        if p.attribute not in state:
            continue
        if condition_matches(Condition(p.attribute, "==", state[p.attribute]), p):
            hits += 1
    return hits / len(capability.preconditions)
