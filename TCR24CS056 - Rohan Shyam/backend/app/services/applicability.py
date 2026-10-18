from __future__ import annotations

from app.models.formal import Capability, Predicate, State
from app.services.formal_logic import predicate_holds


def predicate_evidence(state: State, predicates: list[Predicate]) -> list[dict]:
    """Return the stable, explainable evidence format used by API reports."""
    return [
        {"predicate": predicate.model_dump(), "satisfied": predicate_holds(state, predicate)}
        for predicate in predicates
    ]


def capability_applicability(state: State, capability: Capability) -> tuple[bool, list[dict]]:
    """Evaluate all declared preconditions and constraints for a capability."""
    predicates = capability.preconditions + capability.constraints
    evidence = predicate_evidence(state, predicates)
    return all(row["satisfied"] for row in evidence), evidence
