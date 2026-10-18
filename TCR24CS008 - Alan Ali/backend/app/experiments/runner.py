from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import Any

from app.composition import check_compatibility, compose
from app.composition.composer import CompositionError
from app.embedding import EmbeddingEncoder, capability_similarity, sparse_cosine
from app.models.formal import ApplicationScenario, Capability, Goal
from app.services.formal_logic import satisfies, state_satisfies_goal


def load_default_scenario() -> ApplicationScenario:
    path = Path(__file__).resolve().parents[3] / "data" / "scenarios" / "commerce.json"
    return ApplicationScenario.model_validate(json.loads(path.read_text(encoding="utf-8")))


def run_all_experiments(scenario: ApplicationScenario | None = None) -> dict[str, Any]:
    scenario = scenario or load_default_scenario()
    capabilities = scenario.capabilities
    encoder = EmbeddingEncoder()
    experiments: list[dict[str, Any]] = []

    # Every group is isolated: missing inputs yield a skip entry instead of
    # preventing the other groups from producing results.
    compatibility = _compatibility_experiment(capabilities)
    experiments.append(compatibility)

    chain, chain_checks = _longest_compatible_chain(capabilities)
    if chain and len(chain) >= 3:
        composite, checks = compose(chain)
        experiments.append({"id": "three_capability_composition", "results": {
            "component_ids": composite.components, "compatibility_checks": checks,
            "composite": composite.model_dump(), "embedding": encoder.encode_capability(composite),
        }})
    else:
        experiments.append(_skipped("three_capability_composition", "needs a compatible chain of at least 3 capabilities"))

    alternatives = _alternative_groups(capabilities)
    if alternatives:
        similarity: dict[str, float] = {}
        for group in alternatives:
            for left, right in combinations(group, 2):
                key = f"{left.id}__{right.id}"
                similarity[key] = capability_similarity(encoder, left, right)
        # Keep the established report labels while discovering the matching
        # implementations by their declared type, not commerce-specific IDs.
        type_aliases = {"api_database": {"API", "DATABASE"}, "api_gui": {"API", "GUI"}}
        for alias, types in type_aliases.items():
            pair = next(((left, right) for left, right in combinations(capabilities, 2)
                         if {left.type, right.type} == types and left.name.split()[0] == right.name.split()[0]), None)
            if pair:
                similarity[alias] = capability_similarity(encoder, *pair)
        experiments.append({"id": "alternative_implementations", "results": {
            "groups": [[cap.id for cap in group] for group in alternatives],
            "functional_similarity": similarity,
        }})
    else:
        experiments.append(_skipped("alternative_implementations", "no matching precondition/effect group with differing types"))

    goal = scenario.goals[0] if scenario.goals else None
    if goal:
        experiments.append(_goal_relevance_experiment(capabilities, goal, encoder))
    else:
        experiments.append(_skipped("goal_relevance", "scenario has no goals"))

    if capabilities and (alternatives or (chain and len(chain) >= 3)):
        operational = [{"capability_id": cap.id, "cost_time_ms": cap.cost.time_ms,
                        "reliability": cap.reliability, "availability": cap.availability}
                       for cap in capabilities]
        operational_result: dict[str, Any] = {"implementations": operational}
        if chain and len(chain) >= 2:
            composite, _ = compose(chain)
            operational_result.update({"chain_reliability": composite.reliability,
                                       "chain_availability": composite.availability,
                                       "chain_cost": composite.cost.model_dump()})
        experiments.append({"id": "operational_properties", "results": operational_result})
    else:
        reason = "scenario has no capabilities" if not capabilities else "needs alternative implementations or a three-capability chain"
        experiments.append(_skipped("operational_properties", reason))

    if scenario.states and goal:
        encoded_state = encoder.encode_state(scenario.states[0])
        encoded_goal = encoder.encode_goal(goal)
        state_ok, evidence = state_satisfies_goal(scenario.states[0], goal.conditions)
        experiments.append({"id": "state_and_goal_encoding", "results": {
            "encoded_state": encoded_state, "encoded_goal": encoded_goal,
            "initial_state_satisfies_goal": state_ok, "condition_evidence": evidence,
        }})
    else:
        reason = "scenario has no states" if not scenario.states else "scenario has no goals"
        experiments.append(_skipped("state_and_goal_encoding", reason))

    if capabilities and scenario.states:
        capability = next((item for item in capabilities if item.preconditions or item.constraints), capabilities[0])
        state = scenario.states[0]
        applicability = [{"predicate": predicate.model_dump(), "satisfied": predicate.name in state.values and
                          satisfies(state.values[predicate.name], predicate.operator, predicate.value)}
                         for predicate in capability.preconditions + capability.constraints]
        experiments.append({"id": "state_awareness", "results": {
            "state_id": state.id, "capability_id": capability.id,
            "applicable": all(item["satisfied"] for item in applicability),
            "precondition_constraint_evidence": applicability,
        }})
    else:
        reason = "scenario has no capabilities" if not capabilities else "scenario has no states"
        experiments.append(_skipped("state_awareness", reason))

    dimensions = set().union(*(encoder.encode_capability(cap).keys() for cap in capabilities)) if capabilities else set()
    return {"scenario_id": scenario.id, "experiments": experiments,
            "metrics": {"capability_count": len(capabilities), "state_count": len(scenario.states),
                        "goal_count": len(scenario.goals), "embedding_dimensions_observed": len(dimensions)}}


def _compatibility_experiment(capabilities: list[Capability]) -> dict[str, Any]:
    if len(capabilities) < 2:
        return _skipped("compatibility", "needs at least 2 capabilities")
    checks = [check_compatibility(left, right) for left in capabilities for right in capabilities if left.id != right.id]
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
    return _skipped("compatibility", "no distinct capability pairs found")


def _longest_compatible_chain(capabilities: list[Capability]) -> tuple[list[Capability], list[dict[str, Any]]]:
    best: list[Capability] = []

    def visit(chain: list[Capability], remaining: list[Capability]) -> None:
        nonlocal best
        if len(chain) > len(best):
            best = chain
        if not remaining:
            return
        for candidate in remaining:
            needs_handoff = bool(candidate.preconditions or any(item.required for item in candidate.inputs))
            if needs_handoff and check_compatibility(chain[-1], candidate)["compatible"]:
                visit(chain + [candidate], [item for item in remaining if item.id != candidate.id])

    for start in capabilities:
        visit([start], [item for item in capabilities if item.id != start.id])
    if len(best) < 2:
        return [], []
    try:
        _, checks = compose(best)
        return best, checks
    except CompositionError:
        return [], []


def _alternative_groups(capabilities: list[Capability]) -> list[list[Capability]]:
    groups: dict[tuple[Any, ...], list[Capability]] = {}
    for capability in capabilities:
        signature = (_predicate_signature(capability.preconditions), _predicate_signature(capability.effects))
        groups.setdefault(signature, []).append(capability)
    return [group for group in groups.values() if len({item.type for item in group}) > 1]


def _predicate_signature(predicates: list[Any]) -> tuple[tuple[str, str, str], ...]:
    return tuple(sorted((item.name, item.operator, json.dumps(item.value, sort_keys=True, default=str)) for item in predicates))


def _goal_relevance_experiment(capabilities: list[Capability], goal: Goal, encoder: EmbeddingEncoder) -> dict[str, Any]:
    conditions = {condition.name: condition for condition in goal.conditions}
    goal_features = {f"effect:{encoder._predicate(item)}": 1.25 for item in goal.conditions}
    rows = []
    for capability in capabilities:
        feature = encoder.encode_capability(capability)
        matched = [effect.name for effect in capability.effects if effect.name in conditions and
                   effect.operator == conditions[effect.name].operator and effect.value == conditions[effect.name].value]
        effect_features = {key: value for key, value in feature.items() if key.startswith("effect:")}
        coverage = len(matched) / len(goal.conditions) if goal.conditions else 0.0
        rows.append({"capability_id": capability.id, "effect_overlap": len(matched),
                     "matched_goal_variables": matched, "goal_effect_coverage": round(coverage, 8),
                     "goal_effect_similarity": sparse_cosine(effect_features, goal_features), "relevant": bool(matched)})
    return {"id": "goal_relevance", "results": {"goal_id": goal.id, "capabilities": rows,
            "relevant": [row["capability_id"] for row in rows if row["relevant"]],
            "irrelevant": [row["capability_id"] for row in rows if not row["relevant"]]}}


def _skipped(experiment_id: str, reason: str) -> dict[str, Any]:
    return {"id": experiment_id, "skipped": reason}
