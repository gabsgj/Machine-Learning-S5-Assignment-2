from __future__ import annotations

from app.models.formal import Capability, Predicate


def check_compatibility(producer: Capability, consumer: Capability) -> dict:
    """Check typed output/effect supply against the next operation's requirements."""
    produced = {item.name: item for item in producer.effects if item.operator == "="}
    output_types = {item.name: item.type for item in producer.outputs}
    evidence: list[dict] = []
    failures: list[str] = []
    checks: list[tuple[str, str, object]] = [("precondition", p.name, p) for p in consumer.preconditions]
    for field in consumer.inputs:
        if field.required:
            checks.append(("input", field.name, field))
    for kind, name, requirement in checks:
        supplied = produced.get(name)
        if kind == "input":
            actual_type = output_types.get(name)
            ok = actual_type == requirement.type
            evidence.append({"requirement": kind, "name": name, "expected_type": requirement.type, "provided_type": actual_type, "satisfied": ok})
            if not ok:
                failures.append(f"Required input '{name}' of type {requirement.type} is not provided with a matching type")
            continue
        assert isinstance(requirement, Predicate)
        if supplied is None:
            ok = False
            row = {"requirement": kind, "name": name, "expected": requirement.model_dump(), "provided": None, "satisfied": False}
            failures.append(f"Precondition '{name}' has no matching producer effect")
        else:
            ok = _implies(supplied, requirement)
            row = {"requirement": kind, "name": name, "expected": requirement.model_dump(), "provided": supplied.model_dump(), "satisfied": ok}
            if not ok:
                failures.append(f"Producer effect {supplied.operator} {supplied.value!r} does not satisfy consumer precondition {requirement.operator} {requirement.value!r} for '{name}'")
        evidence.append(row)
    if not checks:
        evidence.append({"requirement": "structural", "name": "no declared inputs or preconditions", "satisfied": True})
    if producer.availability <= 0 or consumer.availability <= 0:
        failures.append("One or both capabilities are unavailable")
    return {"compatible": not failures, "producer_id": producer.id, "consumer_id": consumer.id, "evidence": evidence, "reasons": failures}


def _implies(effect: Predicate, condition: Predicate) -> bool:
    if effect.name != condition.name or effect.operator != "=":
        return False
    try:
        return {
            "=": lambda: effect.value == condition.value,
            "!=": lambda: effect.value != condition.value,
            ">": lambda: effect.value > condition.value,
            ">=": lambda: effect.value >= condition.value,
            "<": lambda: effect.value < condition.value,
            "<=": lambda: effect.value <= condition.value,
            "in": lambda: effect.value in condition.value,
        }[condition.operator]()
    except (TypeError, KeyError):
        return False
