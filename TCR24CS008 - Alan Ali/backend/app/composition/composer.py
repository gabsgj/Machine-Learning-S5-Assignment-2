from __future__ import annotations

from collections.abc import Sequence

from app.composition.compatibility import check_compatibility
from app.models.formal import Capability, OperationalCost, Predicate


class CompositionError(ValueError):
    def __init__(self, message: str, diagnostics: list[dict]):
        super().__init__(message)
        self.diagnostics = diagnostics


def compose(capabilities: Sequence[Capability]) -> tuple[Capability, list[dict]]:
    if len(capabilities) < 2:
        raise CompositionError("Composition requires at least two capabilities", [])
    checks = [check_compatibility(left, right) for left, right in zip(capabilities, capabilities[1:])]
    if not all(item["compatible"] for item in checks):
        raise CompositionError("Composition failed: adjacent capabilities are not compatible", checks)

    first, last = capabilities[0], capabilities[-1]
    all_preconditions = list(first.preconditions)
    for capability in capabilities[1:]:
        for condition in capability.preconditions:
            if not _provided_before(capabilities, capability, condition):
                all_preconditions.append(condition)
    final_effects: dict[str, Predicate] = {}
    for capability in capabilities:
        for effect in capability.effects:
            final_effects[effect.name] = effect

    combined_cost = OperationalCost(**{
        field: sum(getattr(cap.cost, field) for cap in capabilities)
        for field in OperationalCost.model_fields
    })
    resources = sorted({resource for capability in capabilities for resource in capability.resources})
    composite = Capability(
        id="compose:" + "->".join(cap.id for cap in capabilities),
        name=" -> ".join(cap.name for cap in capabilities),
        type="COMPOSITE",
        mechanism={"composition": "ordered"},
        inputs=list(first.inputs),
        outputs=list(last.outputs),
        preconditions=_unique(all_preconditions),
        effects=list(final_effects.values()),
        constraints=_unique([p for cap in capabilities for p in cap.constraints]),
        resources=resources,
        cost=combined_cost,
        reliability=_product(cap.reliability for cap in capabilities),
        availability=_product(cap.availability for cap in capabilities),
        components=[cap.id for cap in capabilities],
    )
    return composite, checks


def _provided_before(chain: Sequence[Capability], current: Capability, condition: Predicate) -> bool:
    end = chain.index(current)
    return any(effect.name == condition.name and effect.operator == "=" and effect.value == condition.value
               for cap in chain[:end] for effect in cap.effects)


def _unique(items: list[Predicate]) -> list[Predicate]:
    result: dict[tuple[str, str, str], Predicate] = {}
    for item in items:
        key = (item.name, item.operator, repr(item.value))
        result[key] = item
    return list(result.values())


def _product(values) -> float:
    result = 1.0
    for value in values:
        result *= value
    return round(result, 8)
