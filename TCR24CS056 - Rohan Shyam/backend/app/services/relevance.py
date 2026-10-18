from __future__ import annotations

from app.embedding.encoder import EmbeddingEncoder, sparse_cosine
from app.models.formal import Capability, Goal


def matching_goal_effects(capability: Capability, goal: Goal) -> list[str]:
    """Return capability effect names that exactly satisfy goal conditions."""
    conditions = {condition.name: condition for condition in goal.conditions}
    return [
        effect.name
        for effect in capability.effects
        if effect.name in conditions
        and effect.operator == conditions[effect.name].operator
        and effect.value == conditions[effect.name].value
    ]


def goal_effect_analysis(
    capability: Capability, goal: Goal, encoder: EmbeddingEncoder
) -> dict:
    """Compute the shared goal-effect explanation used by API and experiments."""
    matched = matching_goal_effects(capability, goal)
    capability_features = encoder.encode_capability(capability)
    goal_features = {
        f"effect:{encoder.predicate_token(condition)}": encoder.weights["effect"]
        for condition in goal.conditions
    }
    capability_effect_features = {
        key: value
        for key, value in capability_features.items()
        if key.startswith("effect:")
    }
    coverage = len(matched) / len(goal.conditions) if goal.conditions else 0.0
    return {
        "matched_goal_variables": matched,
        "effect_overlap": len(matched),
        "goal_effect_coverage": round(coverage, 8),
        "relevant": bool(matched),
        "goal_effect_similarity": sparse_cosine(
            capability_effect_features, goal_features
        ),
    }
