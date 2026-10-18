from __future__ import annotations

from typing import Dict, Tuple

from .models import Capability, Condition, IOField, State


def _condition_match(produced: Condition, required: Condition) -> bool:
    if produced.variable != required.variable:
        return False

    if required.operator == "=":
        return produced.operator == "=" and produced.value == required.value

    if required.operator == "!=":
        return not (produced.operator == "=" and produced.value == required.value)

    return False


def effect_precondition_score(a: Capability, b: Capability) -> float:
    """
    Fraction of B's preconditions satisfied by A's effects.
    Empty preconditions are considered satisfied.
    """
    if not b.preconditions:
        return 1.0

    satisfied = 0
    for req in b.preconditions:
        if any(_condition_match(eff, req) for eff in a.effects):
            satisfied += 1
    return satisfied / len(b.preconditions)


def output_input_score(a: Capability, b: Capability) -> float:
    if not b.inputs:
        return 1.0

    satisfied = 0
    for req in b.inputs:
        compatible = any(
            out.type == req.type and out.name == req.name
            for out in a.outputs
        )
        if compatible:
            satisfied += 1
    return satisfied / len(b.inputs)


def resource_score(a: Capability, b: Capability) -> float:
    # Resources are not normally a composition dependency, so this is a
    # soft diagnostic rather than a hard gate.
    if not b.resources:
        return 1.0
    return len(set(a.resources) & set(b.resources)) / len(set(b.resources))


def compatibility(a: Capability, b: Capability) -> float:
    """
    Directed compatibility score a -> b.

    Preconditions/effects and output/input compatibility receive the largest
    weights because they define whether composition is functionally valid.
    """
    ep = effect_precondition_score(a, b)
    oi = output_input_score(a, b)
    operational = 0.5 * b.reliability + 0.5 * b.availability

    return float(
        0.55 * ep +
        0.30 * oi +
        0.10 * operational +
        0.05 * resource_score(a, b)
    )


def is_composable(a: Capability, b: Capability, threshold: float = 0.70) -> bool:
    return compatibility(a, b) >= threshold


def goal_relevance(cap: Capability, goal: "Goal") -> float:
    """
    Measures how many goal conditions are directly produced by a capability.
    """
    if not goal.conditions:
        return 0.0

    matched = 0
    for g in goal.conditions:
        if any(_condition_match(e, g) for e in cap.effects):
            matched += 1
    return matched / len(goal.conditions)
