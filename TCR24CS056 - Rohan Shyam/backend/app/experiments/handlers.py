from __future__ import annotations

import json
from itertools import combinations
from typing import Any

from app.composition import check_compatibility, compose
from app.composition.composer import CompositionError
from app.embedding import EmbeddingEncoder
from app.models.formal import Capability, Goal, State
from app.services.applicability import capability_applicability
from app.services.formal_logic import state_satisfies_goal
from app.services.relevance import goal_effect_analysis


def skipped(experiment_id: str, reason: str) -> dict[str, Any]:
    return {"id": experiment_id, "skipped": reason}


def compatibility_experiment(capabilities: list[Capability]) -> dict[str, Any]:
    if len(capabilities) < 2:
        return skipped("compatibility", "needs at least 2 capabilities")
    checks = [
        check_compatibility(left, right)
        for left in capabilities
        for right in capabilities
        if left.id != right.id
    ]
    compatible = next((item for item in checks if item["compatible"]), None)
    incompatible = next((item for item in checks if not item["compatible"]), None)
    results: dict[str, Any] = {}
    if compatible:
        results["compatible_pair"] = compatible
    else:
        results["compatible_pair_skipped"] = "no compatible ordered pair found"
    if incompatible:
        results["incompatible_pair"] = incompatible
    else:
        results["incompatible_pair_skipped"] = "no incompatible ordered pair found"
    if compatible or incompatible:
        return {"id": "compatibility", "results": results}
    return skipped("compatibility", "no distinct capability pairs found")


def longest_compatible_chain(
    capabilities: list[Capability],
) -> tuple[list[Capability], list[dict[str, Any]]]:
    best: list[Capability] = []

    def visit(chain: list[Capability], remaining: list[Capability]) -> None:
        nonlocal best
        if len(chain) > len(best):
            best = chain
        if not remaining:
            return
        for candidate in remaining:
            needs_handoff = bool(
                candidate.preconditions
                or any(item.required for item in candidate.inputs)
            )
            if needs_handoff and check_compatibility(chain[-1], candidate)["compatible"]:
                visit(
                    chain + [candidate],
                    [item for item in remaining if item.id != candidate.id],
                )

    for start in capabilities:
        visit([start], [item for item in capabilities if item.id != start.id])
    if len(best) < 2:
        return [], []
    try:
        _, checks = compose(best)
        return best, checks
    except CompositionError:
        return [], []


def alternative_groups(capabilities: list[Capability]) -> list[list[Capability]]:
    groups: dict[tuple[Any, ...], list[Capability]] = {}
    for capability in capabilities:
        signature = (
            predicate_signature(capability.preconditions),
            predicate_signature(capability.effects),
        )
        groups.setdefault(signature, []).append(capability)
    return [group for group in groups.values() if len({item.type for item in group}) > 1]


def predicate_signature(predicates: list[Any]) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        sorted(
            (
                item.name,
                item.operator,
                json.dumps(item.value, sort_keys=True, default=str),
            )
            for item in predicates
        )
    )


def goal_relevance_experiment(
    capabilities: list[Capability], goal: Goal, encoder: EmbeddingEncoder
) -> dict[str, Any]:
    rows = []
    for capability in capabilities:
        rows.append(
            {
                "capability_id": capability.id,
                **goal_effect_analysis(capability, goal, encoder),
            }
        )
    return {
        "id": "goal_relevance",
        "results": {
            "goal_id": goal.id,
            "capabilities": rows,
            "relevant": [row["capability_id"] for row in rows if row["relevant"]],
            "irrelevant": [
                row["capability_id"] for row in rows if not row["relevant"]
            ],
        },
    }


def operational_properties(
    capabilities: list[Capability], chain: list[Capability]
) -> dict[str, Any]:
    if not capabilities:
        return skipped("operational_properties", "scenario has no capabilities")
    operational = [
        {
            "capability_id": capability.id,
            "cost_time_ms": capability.cost.time_ms,
            "reliability": capability.reliability,
            "availability": capability.availability,
        }
        for capability in capabilities
    ]
    operational_result: dict[str, Any] = {"implementations": operational}
    if len(chain) >= 2:
        composite, _ = compose(chain)
        operational_result.update(
            {
                "chain_reliability": composite.reliability,
                "chain_availability": composite.availability,
                "chain_cost": composite.cost.model_dump(),
            }
        )
    return {"id": "operational_properties", "results": operational_result}


def state_and_goal_encoding(
    state: State, goal: Goal, encoder: EmbeddingEncoder
) -> dict[str, Any]:
    encoded_state = encoder.encode_state(state)
    encoded_goal = encoder.encode_goal(goal)
    state_ok, evidence = state_satisfies_goal(state, goal.conditions)
    return {
        "id": "state_and_goal_encoding",
        "results": {
            "encoded_state": encoded_state,
            "encoded_goal": encoded_goal,
            "initial_state_satisfies_goal": state_ok,
            "condition_evidence": evidence,
        },
    }


def state_awareness(
    capabilities: list[Capability], states: list[State]
) -> dict[str, Any]:
    if not capabilities or not states:
        reason = "scenario has no capabilities" if not capabilities else "scenario has no states"
        return skipped("state_awareness", reason)
    capability = next(
        (item for item in capabilities if item.preconditions or item.constraints),
        capabilities[0],
    )
    state = states[0]
    applicable, evidence = capability_applicability(state, capability)
    return {
        "id": "state_awareness",
        "results": {
            "state_id": state.id,
            "capability_id": capability.id,
            "applicable": applicable,
            "precondition_constraint_evidence": evidence,
        },
    }
