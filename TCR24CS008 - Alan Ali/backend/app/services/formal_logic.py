from __future__ import annotations

from typing import Any

from app.models.formal import Predicate, State


def satisfies(value: Any, operator: str, expected: Any) -> bool:
    try:
        return {
            "=": lambda: value == expected,
            "!=": lambda: value != expected,
            ">": lambda: value > expected,
            ">=": lambda: value >= expected,
            "<": lambda: value < expected,
            "<=": lambda: value <= expected,
            "in": lambda: value in expected,
        }[operator]()
    except (TypeError, KeyError):
        return False


def predicate_holds(state: State, predicate: Predicate) -> bool:
    return predicate.name in state.values and satisfies(state.values[predicate.name], predicate.operator, predicate.value)


def state_satisfies_goal(state: State, predicates: list[Predicate]) -> tuple[bool, list[dict[str, Any]]]:
    evidence = [{"condition": item.model_dump(), "satisfied": predicate_holds(state, item)} for item in predicates]
    return all(row["satisfied"] for row in evidence), evidence
