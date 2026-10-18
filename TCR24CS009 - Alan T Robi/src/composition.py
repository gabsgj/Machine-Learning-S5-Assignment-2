from typing import List, Dict, Any, Optional
import numpy as np

from src.capability import Capability, InputSpec, OutputSpec, CostSpec
from src.compatibility import compatibility, CompatibilityResult
from src.encoder import CapabilityEncoder

def compose_capabilities(
    capabilities: List[Capability], 
    composite_name: Optional[str] = None
) -> Capability:
    """
    Construct a formal composite capability C_comp = C_n o ... o C_2 o C_1 from a sequence of atomic capabilities.
    Validates compatibility along the chain first.
    """
    if not capabilities:
        raise ValueError("Cannot compose an empty list of capabilities.")
    if len(capabilities) == 1:
        return capabilities[0]

    # Validate pairwise compatibility along sequence C1 -> C2 -> ... -> Cn
    for i in range(len(capabilities) - 1):
        c_curr = capabilities[i]
        c_next = capabilities[i + 1]
        res = compatibility(c_curr, c_next)
        if not res.is_compatible:
            raise ValueError(
                f"Incompatible sequence: '{c_curr.name}' -> '{c_next.name}' "
                f"(ep_score={res.effect_precondition_match:.2f}, "
                f"oi_score={res.output_input_match:.2f}, contradiction={res.has_contradiction})"
            )

    comp_name = composite_name if composite_name else f"Composite_{'_'.join(c.name for c in capabilities)}"

    # Track available outputs and produced effects as sequence progresses
    produced_outputs: List[OutputSpec] = []
    output_names = set()
    accumulated_effects: List[str] = []
    effect_var_map: Dict[str, str] = {} # var_name -> predicate string

    for c in capabilities:
        for out in c.outputs:
            if out.name not in output_names:
                produced_outputs.append(out)
                output_names.add(out.name)

        for eff in c.effects:
            accumulated_effects.append(eff)
            if "=" in eff:
                var, val = eff.split("=", 1)
                effect_var_map[var.strip()] = eff

    # Determine required composite inputs (inputs not satisfied by prior outputs)
    composite_inputs: List[InputSpec] = []
    seen_inputs = set()
    available_output_names = set()

    for c in capabilities:
        for inp in c.inputs:
            if inp.name not in available_output_names and inp.name not in seen_inputs:
                composite_inputs.append(inp)
                seen_inputs.add(inp.name)
        for out in c.outputs:
            available_output_names.add(out.name)

    # Determine required composite preconditions (preconditions not satisfied by prior effects)
    composite_preconditions: List[str] = []
    current_effect_preds: Dict[str, str] = {}

    for c in capabilities:
        for prec in c.preconditions:
            satisfied = False
            if "=" in prec:
                var, val = prec.split("=", 1)
                var = var.strip()
                val = val.strip()
                if var in current_effect_preds:
                    eff_val = current_effect_preds[var].split("=", 1)[1].strip()
                    if eff_val.lower() == val.lower():
                        satisfied = True
            if not satisfied and prec not in composite_preconditions:
                composite_preconditions.append(prec)

        for eff in c.effects:
            if "=" in eff:
                var = eff.split("=", 1)[0].strip()
                current_effect_preds[var] = eff

    # Aggregate constraints and resources
    composite_constraints = list(dict.fromkeys([k for c in capabilities for k in c.constraints]))
    composite_resources = list(dict.fromkeys([r for c in capabilities for r in c.resources]))

    # Aggregate cost attributes
    comp_time = sum(c.cost.time for c in capabilities)
    comp_res_cost = sum(c.cost.resource for c in capabilities)
    comp_money = sum(c.cost.money for c in capabilities)
    comp_risk = max(c.cost.risk for c in capabilities)
    comp_energy = sum(c.cost.energy for c in capabilities)

    comp_cost = CostSpec(
        time=comp_time,
        resource=comp_res_cost,
        money=comp_money,
        risk=comp_risk,
        energy=comp_energy
    )

    # Reliability is product of reliabilities: Rel_comp = PROD Rel_k
    comp_reliability = 1.0
    for c in capabilities:
        comp_reliability *= c.reliability

    # Availability is minimum availability: A_comp = MIN A_k
    comp_availability = min(c.availability for c in capabilities)

    # Mechanism contains structured sequence steps
    composite_mechanism = {
        "composition_type": "SEQUENTIAL",
        "step_count": len(capabilities),
        "steps": [c.mechanism for c in capabilities]
    }

    comp_cap = Capability(
        name=comp_name,
        type="SERVICE",
        inputs=composite_inputs,
        outputs=produced_outputs,
        preconditions=composite_preconditions,
        effects=list(effect_var_map.values()),
        constraints=composite_constraints,
        resources=composite_resources,
        cost=comp_cost,
        reliability=comp_reliability,
        availability=comp_availability,
        mechanism=composite_mechanism
    )
    
    comp_cap.validate()
    return comp_cap

def compose(capabilities: List[Capability], composite_name: Optional[str] = None) -> Capability:
    """Wrapper function matching assignment compose(capabilities) specification."""
    return compose_capabilities(capabilities, composite_name=composite_name)

def vector_composition_addition(vectors: List[np.ndarray]) -> np.ndarray:
    """Approximate vector composition via elementwise addition: v_comp = v1 + v2 + ... + vn."""
    return np.sum(vectors, axis=0)
