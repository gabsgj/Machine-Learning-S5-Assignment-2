from __future__ import annotations

import math
from typing import Sequence

from src.encoder import encode_capability
from src.metrics import canonical_var_name, validate_compatibility, _check_predicate_satisfaction
from src.models import (
    Capability,
    CapabilityType,
    Constraint,
    IOField,
    OperationalCost,
    Predicate,
    Resource,
)


class CompositionError(Exception):
    """Raised when an adjacent pair in a capability sequence is incompatible."""

    def __init__(self, message: str, producer_id: str, consumer_id: str, reasons: list[str]):
        super().__init__(message)
        self.producer_id = producer_id
        self.consumer_id = consumer_id
        self.reasons = reasons


def compose(capabilities: Sequence[Capability]) -> Capability:
    """
    Construct a formal composite capability from an ordered sequence [C1, C2, ..., Cn].
    
    1. Validates every adjacent pair using the formal compatibility system.
    2. Determines external preconditions (removes internally established preconditions).
    3. Determines external inputs (removes internally supplied inputs).
    4. Exposes terminal capability outputs.
    5. Combines effects where later capabilities override earlier ones on the same variable.
    6. Combines unique constraints and resources.
    7. Aggregates operational attributes (sums costs, multiplies reliabilities and availabilities).
    8. Preserves formal capability structure C = (T, I, O, P, E, K, R, Q, Rel, A, M).
    """
    if len(capabilities) < 2:
        raise ValueError("Composition requires at least two capabilities")

    # 1. Validate all adjacent pairs
    for i in range(len(capabilities) - 1):
        producer = capabilities[i]
        consumer = capabilities[i + 1]
        val_result = validate_compatibility(producer, consumer)
        if not val_result.compatible:
            reasons_str = "; ".join(val_result.reasons)
            raise CompositionError(
                f"Incompatible adjacent pair: {producer.id} -> {consumer.id}: {reasons_str}",
                producer_id=producer.id,
                consumer_id=consumer.id,
                reasons=val_result.reasons,
            )

    # 2. External Preconditions
    # Start with all preconditions of the first capability
    external_preconditions: list[Predicate] = []
    seen_pre_keys: set[tuple[str, str, str]] = set()

    for p in capabilities[0].P:
        key = (canonical_var_name(p.name), p.operator, str(p.value).strip().upper())
        if key not in seen_pre_keys:
            seen_pre_keys.add(key)
            external_preconditions.append(p)

    # For downstream capabilities, include preconditions only if not established by earlier effects
    for j in range(1, len(capabilities)):
        cap = capabilities[j]
        prior_effects = [e for c in capabilities[:j] for e in c.E]

        for p in cap.P:
            satisfied, _ = _check_predicate_satisfaction(p, prior_effects)
            if not satisfied:
                key = (canonical_var_name(p.name), p.operator, str(p.value).strip().upper())
                if key not in seen_pre_keys:
                    seen_pre_keys.add(key)
                    external_preconditions.append(p)

    # 3. External Inputs
    # Start with all inputs of the first capability
    external_inputs: list[IOField] = []
    seen_input_names: set[str] = set()

    for inp in capabilities[0].I:
        if inp.name.strip() not in seen_input_names:
            seen_input_names.add(inp.name.strip())
            external_inputs.append(inp)

    # For downstream capabilities, include inputs only if not produced by any earlier capability
    for j in range(1, len(capabilities)):
        cap = capabilities[j]
        prior_outputs = [out for c in capabilities[:j] for out in c.O]

        for inp in cap.I:
            supplied = any(
                out.name.strip() == inp.name.strip() and out.type.strip() == inp.type.strip()
                for out in prior_outputs
            )
            if not supplied and inp.name.strip() not in seen_input_names:
                seen_input_names.add(inp.name.strip())
                external_inputs.append(inp)

    # 4. Outputs: expose the terminal capability outputs
    terminal_outputs = list(capabilities[-1].O)

    # 5. Cumulative Effects: later effects override earlier ones on the same variable
    final_effects_map: dict[str, Predicate] = {}
    for cap in capabilities:
        for eff in cap.E:
            var_key = canonical_var_name(eff.name)
            final_effects_map[var_key] = eff
    final_effects = list(final_effects_map.values())

    # 6. Constraints: union of unique constraints
    unique_constraints: list[Constraint] = []
    seen_constraint_exprs: set[str] = set()
    for cap in capabilities:
        for k in cap.K:
            if k.expression.strip() not in seen_constraint_exprs:
                seen_constraint_exprs.add(k.expression.strip())
                unique_constraints.append(k)

    # 7. Resources: union of unique resources
    unique_resources: list[Resource] = []
    seen_resource_names: set[str] = set()
    for cap in capabilities:
        for r in cap.R:
            if r.name.strip() not in seen_resource_names:
                seen_resource_names.add(r.name.strip())
                unique_resources.append(r)

    # 8. Operational Attributes Aggregation
    total_time = sum(c.Q.execution_time_ms for c in capabilities)
    total_money = sum(c.Q.monetary_cost for c in capabilities)
    total_resource = sum(c.Q.resource_cost for c in capabilities)
    total_energy = sum(c.Q.energy_cost for c in capabilities)

    # Risk: 1 - product(1 - risk_i)
    comp_risk = 1.0 - math.prod(1.0 - c.Q.risk for c in capabilities)
    comp_risk = max(0.0, min(1.0, comp_risk))

    # Reliability: product(Rel_i) (assuming independent failure modes)
    comp_rel = math.prod(c.Rel for c in capabilities)
    comp_rel = max(0.0, min(1.0, comp_rel))

    # Availability: product(A_i)
    comp_avail = math.prod(c.A for c in capabilities)
    comp_avail = max(0.0, min(1.0, comp_avail))

    aggregated_cost = OperationalCost(
        execution_time_ms=round(total_time, 4),
        monetary_cost=round(total_money, 6),
        resource_cost=round(total_resource, 4),
        risk=round(comp_risk, 6),
        energy_cost=round(total_energy, 4),
    )

    # 9. Composite ID, Name, and Mechanism
    composite_id = "_".join(c.id for c in capabilities)
    composite_name = " -> ".join(c.name for c in capabilities)
    components = [c.id for c in capabilities]

    composite_mechanism = {
        "type": "SEQUENTIAL_COMPOSITION",
        "components": " -> ".join(components),
    }

    return Capability(
        id=composite_id,
        name=composite_name,
        T=CapabilityType.COMPOSITE,
        I=external_inputs,
        O=terminal_outputs,
        P=external_preconditions,
        E=final_effects,
        K=unique_constraints,
        R=unique_resources,
        Q=aggregated_cost,
        Rel=round(comp_rel, 6),
        A=round(comp_avail, 6),
        M=composite_mechanism,
        components=components,
    )
