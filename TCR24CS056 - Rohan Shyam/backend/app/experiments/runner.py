from __future__ import annotations

from itertools import combinations
from typing import Any

from app.composition import compose
from app.embedding import EmbeddingEncoder, capability_similarity
from app.experiments.handlers import (
    alternative_groups,
    compatibility_experiment,
    goal_relevance_experiment,
    longest_compatible_chain,
    operational_properties,
    predicate_signature,
    skipped,
    state_and_goal_encoding,
    state_awareness,
)
from app.services.scenario import load_default_scenario
from app.models.formal import ApplicationScenario

# Keep the established private names available to callers that imported them
# while keeping the implementation in independently testable handler functions.
_compatibility_experiment = compatibility_experiment
_longest_compatible_chain = longest_compatible_chain
_alternative_groups = alternative_groups
_predicate_signature = predicate_signature
_goal_relevance_experiment = goal_relevance_experiment
_skipped = skipped


def run_all_experiments(scenario: ApplicationScenario | None = None) -> dict[str, Any]:
    scenario = scenario or load_default_scenario()
    capabilities = scenario.capabilities
    encoder = EmbeddingEncoder()
    experiments: list[dict[str, Any]] = []

    # Every group is isolated: missing inputs yield a skip entry instead of
    # preventing the other groups from producing results.
    experiments.append(compatibility_experiment(capabilities))

    chain, chain_checks = longest_compatible_chain(capabilities)
    if chain and len(chain) >= 3:
        composite, checks = compose(chain)
        experiments.append(
            {
                "id": "three_capability_composition",
                "results": {
                    "component_ids": composite.components,
                    "compatibility_checks": checks,
                    "composite": composite.model_dump(),
                    "embedding": encoder.encode_capability(composite),
                },
            }
        )
    else:
        experiments.append(
            skipped(
                "three_capability_composition",
                "needs a compatible chain of at least 3 capabilities",
            )
        )

    alternatives = alternative_groups(capabilities)
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
            pair = next(
                (
                    (left, right)
                    for left, right in combinations(capabilities, 2)
                    if {left.type, right.type} == types
                    and left.name.split()[0] == right.name.split()[0]
                ),
                None,
            )
            if pair:
                similarity[alias] = capability_similarity(encoder, *pair)
        experiments.append(
            {
                "id": "alternative_implementations",
                "results": {
                    "groups": [[cap.id for cap in group] for group in alternatives],
                    "functional_similarity": similarity,
                },
            }
        )
    else:
        experiments.append(
            skipped(
                "alternative_implementations",
                "no matching precondition/effect group with differing types",
            )
        )

    goal = scenario.goals[0] if scenario.goals else None
    if goal:
        experiments.append(goal_relevance_experiment(capabilities, goal, encoder))
    else:
        experiments.append(skipped("goal_relevance", "scenario has no goals"))

    if capabilities and (alternatives or (chain and len(chain) >= 3)):
        experiments.append(operational_properties(capabilities, chain))
    else:
        reason = (
            "scenario has no capabilities"
            if not capabilities
            else "needs alternative implementations or a three-capability chain"
        )
        experiments.append(skipped("operational_properties", reason))

    if scenario.states and goal:
        experiments.append(state_and_goal_encoding(scenario.states[0], goal, encoder))
    else:
        reason = "scenario has no states" if not scenario.states else "scenario has no goals"
        experiments.append(skipped("state_and_goal_encoding", reason))

    experiments.append(state_awareness(capabilities, scenario.states))

    dimensions = (
        set().union(*(encoder.encode_capability(cap).keys() for cap in capabilities))
        if capabilities
        else set()
    )
    return {
        "scenario_id": scenario.id,
        "experiments": experiments,
        "metrics": {
            "capability_count": len(capabilities),
            "state_count": len(scenario.states),
            "goal_count": len(scenario.goals),
            "embedding_dimensions_observed": len(dimensions),
        },
    }
