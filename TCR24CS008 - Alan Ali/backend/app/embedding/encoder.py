from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from app.models.formal import Capability, Goal, Predicate, State


class EmbeddingEncoder:
    """Named, deterministic sparse features; no trained model or hidden vocabulary."""

    weights = {
        "state": 1.0,
        "goal": 1.0,
        "identity": 0.20,
        "io": 1.0,
        "condition": 1.25,
        "effect": 1.25,
        "constraint": 0.8,
        "resource": 0.55,
        "type": 0.35,
        "mechanism": 0.2,
        "operational": 0.15,
    }

    def encode_state(self, state: State) -> dict[str, float]:
        return {f"state:{key}={self._atom(value)}": 1.0 for key, value in sorted(state.values.items())}

    def encode_goal(self, goal: Goal) -> dict[str, float]:
        vector: defaultdict[str, float] = defaultdict(float)
        for item in goal.conditions:
            vector[f"goal:{self._predicate(item)}"] += 1.0
        return dict(vector)

    def encode_capability(self, capability: Capability) -> dict[str, float]:
        vector: defaultdict[str, float] = defaultdict(float)
        vector[f"identity:{capability.id}"] += 1.0
        vector[f"type:{capability.type}"] += 1.0
        for field in capability.inputs:
            prefix = f"io:input:{field.name}:{field.type}"
            vector[prefix] += 1.0
            if field.domain:
                vector[f"{prefix}:domain={field.domain}"] += 0.35
            vector[f"io:input-required:{field.required}"] += 0.2
        for field in capability.outputs:
            prefix = f"io:output:{field.name}:{field.type}"
            vector[prefix] += 1.0
            if field.domain:
                vector[f"{prefix}:domain={field.domain}"] += 0.35
        self._add_predicates(vector, "condition", capability.preconditions)
        self._add_predicates(vector, "effect", capability.effects)
        self._add_predicates(vector, "constraint", capability.constraints)
        for resource in capability.resources:
            vector[f"resource:{resource}"] += 1.0
        for key, value in sorted(capability.mechanism.items()):
            vector[f"mechanism:{key}={value}"] += 1.0
        for key, value in capability.cost.model_dump().items():
            vector[f"operational:cost:{key}"] += float(value)
        vector["operational:reliability"] += capability.reliability
        vector["operational:availability"] += capability.availability
        return self.weighted(vector)

    def weighted(self, values: dict[str, float] | defaultdict[str, float]) -> dict[str, float]:
        return {key: round(value * self.weights.get(key.split(":", 1)[0], 1.0), 8) for key, value in values.items() if value != 0}

    @staticmethod
    def _add_predicates(vector: defaultdict[str, float], section: str, items: list[Predicate]) -> None:
        for item in items:
            vector[f"{section}:{EmbeddingEncoder._predicate(item)}"] += 1.0

    @staticmethod
    def _predicate(item: Predicate) -> str:
        if item.operator == "in" and isinstance(item.value, list):
            value = "{" + ",".join(sorted(EmbeddingEncoder._atom(v) for v in item.value)) + "}"
        else:
            value = EmbeddingEncoder._atom(item.value)
        return f"{item.name}{item.operator}{value}"

    @staticmethod
    def _atom(value: Any) -> str:
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, (str, int, float)) or value is None:
            return str(value)
        return repr(value)


def sparse_cosine(left: dict[str, float], right: dict[str, float]) -> float:
    """Cosine over named sparse dimensions; zero vectors have similarity 0."""
    norm_l = math.sqrt(sum(value * value for value in left.values()))
    norm_r = math.sqrt(sum(value * value for value in right.values()))
    if norm_l == 0 or norm_r == 0:
        return 0.0
    dot = sum(value * right.get(key, 0.0) for key, value in left.items())
    return round(max(-1.0, min(1.0, dot / (norm_l * norm_r))), 8)


def capability_similarity(encoder: EmbeddingEncoder, left, right) -> dict:
    """Weighted average of within-section cosines; prevents raw units dominating."""
    left_vector = encoder.encode_capability(left)
    right_vector = encoder.encode_capability(right)
    groups = sorted({key.split(":", 1)[0] for key in left_vector} | {key.split(":", 1)[0] for key in right_vector})
    section_weights = {group: EmbeddingEncoder.weights.get(group, 1.0) for group in groups}
    breakdown = {}
    numerator = denominator = 0.0
    for group in groups:
        lpart = {key: value for key, value in left_vector.items() if key.startswith(group + ":")}
        rpart = {key: value for key, value in right_vector.items() if key.startswith(group + ":")}
        score = sparse_cosine(lpart, rpart)
        weight = section_weights[group]
        numerator += weight * score
        denominator += weight
        breakdown[group] = {"similarity": score, "weight": weight}
    score = round(numerator / denominator, 8) if denominator else 0.0
    return {"similarity": score, "metric": "weighted mean of section-wise sparse cosine",
            "section_scores": breakdown, "interpretation": "resemblance only; it does not imply composability"}
