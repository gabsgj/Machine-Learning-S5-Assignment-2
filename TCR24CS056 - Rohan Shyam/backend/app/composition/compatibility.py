from __future__ import annotations

from typing import Any

from app.models.formal import Capability, IOField, Predicate
from app.services.formal_logic import satisfies


def check_compatibility(producer: Capability, consumer: Capability) -> dict[str, Any]:
    """Check typed output/effect supply against the next operation's requirements."""
    produced_effects = {
        item.name: item for item in producer.effects if item.operator == "="
    }
    output_types = {item.name: item.type for item in producer.outputs}
    evidence: list[dict[str, Any]] = []
    failures: list[str] = []

    requirements = _requirements(consumer)
    for kind, name, requirement in requirements:
        if kind == "input":
            row, failure = _check_input(name, requirement, output_types)
        else:
            assert isinstance(requirement, Predicate)
            row, failure = _check_precondition(
                name, requirement, produced_effects.get(name)
            )
        evidence.append(row)
        if failure:
            failures.append(failure)

    if not requirements:
        evidence.append(
            {
                "requirement": "structural",
                "name": "no declared inputs or preconditions",
                "satisfied": True,
            }
        )
    if producer.availability <= 0 or consumer.availability <= 0:
        failures.append("One or both capabilities are unavailable")
    return {
        "compatible": not failures,
        "producer_id": producer.id,
        "consumer_id": consumer.id,
        "evidence": evidence,
        "reasons": failures,
    }


def _requirements(consumer: Capability) -> list[tuple[str, str, object]]:
    requirements: list[tuple[str, str, object]] = [
        ("precondition", predicate.name, predicate)
        for predicate in consumer.preconditions
    ]
    requirements.extend(
        ("input", field.name, field)
        for field in consumer.inputs
        if field.required
    )
    return requirements


def _check_input(
    name: str, requirement: object, output_types: dict[str, str]
) -> tuple[dict[str, Any], str | None]:
    assert isinstance(requirement, IOField)
    actual_type = output_types.get(name)
    satisfied = actual_type == requirement.type
    row = {
        "requirement": "input",
        "name": name,
        "expected_type": requirement.type,
        "provided_type": actual_type,
        "satisfied": satisfied,
    }
    failure = None
    if not satisfied:
        failure = (
            f"Required input '{name}' of type {requirement.type} is not provided "
            "with a matching type"
        )
    return row, failure


def _check_precondition(
    name: str, condition: Predicate, supplied: Predicate | None
) -> tuple[dict[str, Any], str | None]:
    if supplied is None:
        return (
            {
                "requirement": "precondition",
                "name": name,
                "expected": condition.model_dump(),
                "provided": None,
                "satisfied": False,
            },
            f"Precondition '{name}' has no matching producer effect",
        )

    satisfied = _implies(supplied, condition)
    row = {
        "requirement": "precondition",
        "name": name,
        "expected": condition.model_dump(),
        "provided": supplied.model_dump(),
        "satisfied": satisfied,
    }
    failure = None
    if not satisfied:
        failure = (
            f"Producer effect {supplied.operator} {supplied.value!r} does not satisfy "
            f"consumer precondition {condition.operator} {condition.value!r} for '{name}'"
        )
    return row, failure


def _implies(effect: Predicate, condition: Predicate) -> bool:
    if effect.name != condition.name or effect.operator != "=":
        return False
    return satisfies(effect.value, condition.operator, condition.value)
