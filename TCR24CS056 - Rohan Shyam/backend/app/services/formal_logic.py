from __future__ import annotations

from typing import Any

from app.models.formal import Predicate, State


def satisfies(value: Any, operator: str, expected: Any) -> bool:
    """Safely evaluate one supported predicate operator.

    Formal input validation normally limits operators to the model's literal
    set, but this function also serves compatibility and experiment code that
    may receive programmatically constructed values. Invalid comparisons are
    reported as a failed predicate rather than leaking a TypeError or lookup
    error to an API caller.
    """
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
    return predicate.name in state.values and satisfies(
        state.values[predicate.name], predicate.operator, predicate.value
    )


def state_satisfies_goal(
    state: State, predicates: list[Predicate]
) -> tuple[bool, list[dict[str, Any]]]:
    evidence = [
        {"condition": predicate.model_dump(), "satisfied": predicate_holds(state, predicate)}
        for predicate in predicates
    ]
    return all(row["satisfied"] for row in evidence), evidence
