"""
Symbolic Capability Composition Engine (Section 5).
Handles composition validation, weakest precondition propagation, effect accumulation,
and operational attribute aggregation for composite capabilities.
"""

from typing import List, Tuple, Dict, Any, Optional, Sequence
import copy

from .capability import Capability
from .types import CapabilityType, ExecutionMechanism, InputSpec, OutputSpec
from .operational import OperationalQuality, ResourceRequirement, CapabilityConstraint


class CompositionValidationError(Exception):
    """Raised when capabilities cannot be legally composed."""
    pass


def validate_composition(c1: Capability, c2: Capability) -> Tuple[bool, List[str]]:
    """
    Check if C2 o C1 is a valid composition (Section 5).
    Condition: outputs and effects of C1 must not contradict preconditions of C2,
    and any required inputs of C2 not supplied by external context should be provided by C1.
    Returns: (is_valid, list_of_reasons_or_diagnostics)
    """
    diagnostics = []
    is_valid = True

    # 1. Precondition - Effect consistency
    # If C1 produces an effect on variable v, and C2 requires variable v to have a different value:
    for var, req_val in c2.preconditions.items():
        if var in c1.effects:
            produced_val = c1.effects[var]
            if produced_val != req_val:
                diagnostics.append(
                    f"Conflict on state variable '{var}': C1 produces '{produced_val}', "
                    f"but C2 requires '{req_val}'."
                )
                is_valid = False
            else:
                diagnostics.append(
                    f"Satisfied precondition: C1 produces '{var}={produced_val}' "
                    f"satisfying C2 precondition."
                )

    # 2. Input - Output flow check
    c1_output_names = {o.name for o in c1.outputs}
    for inp in c2.inputs:
        if inp.required and inp.name in c1_output_names:
            diagnostics.append(f"Data flow matched: output '{inp.name}' of C1 feeds input of C2.")

    return is_valid, diagnostics


def compose_two(c1: Capability, c2: Capability, name: Optional[str] = None) -> Capability:
    """
    Compose two capabilities: C12 = C2 o C1 (First C1, then C2).
    Preconditions: Weakest precondition calculation:
      - All preconditions of C1 are required.
      - Any precondition of C2 that is NOT satisfied by C1's effects is also required.
      - If C1 contradicts C2, raises CompositionValidationError.
    Effects:
      - Effects of C2 take precedence over effects of C1.
      - Non-overwritten effects of C1 persist.
    Inputs/Outputs:
      - Composite inputs = C1.inputs + (C2.inputs - C1.outputs)
      - Composite outputs = C1.outputs + C2.outputs
    Operational Quality:
      - Composed via quality.compose_with(c2.quality).
    """
    is_valid, diagnostics = validate_composition(c1, c2)
    if not is_valid:
        raise CompositionValidationError(
            f"Cannot compose '{c2.name}' after '{c1.name}':\n" + "\n".join(diagnostics)
        )

    composite_name = name or f"({c2.name} o {c1.name})"

    # Weakest precondition:
    composite_preconditions = dict(c1.preconditions)
    for var, req_val in c2.preconditions.items():
        if var in c1.effects:
            # Satisfied internally by C1! Does not need to be in external preconditions
            pass
        else:
            composite_preconditions[var] = req_val

    # Cumulative effects: C1 effects updated with C2 effects
    composite_effects = dict(c1.effects)
    composite_effects.update(c2.effects)

    # Inputs: C1 inputs + C2 inputs that were not produced by C1
    c1_out_names = {o.name for o in c1.outputs}
    composite_inputs = list(c1.inputs)
    for inp in c2.inputs:
        if inp.name not in c1_out_names and not any(i.name == inp.name for i in composite_inputs):
            composite_inputs.append(inp)

    # Outputs: Union of outputs (C2 outputs can shadow C1 outputs with same name)
    composite_outputs = list(c1.outputs)
    c1_out_dict = {o.name: o for o in composite_outputs}
    for out in c2.outputs:
        c1_out_dict[out.name] = out
    composite_outputs = list(c1_out_dict.values())

    # Constraints: Union
    seen_exprs = {c.expression for c in c1.constraints}
    composite_constraints = list(c1.constraints)
    for c in c2.constraints:
        if c.expression not in seen_exprs:
            composite_constraints.append(c)

    # Resources: Combine requirements
    resource_map: Dict[str, ResourceRequirement] = {}
    for r in c1.resources:
        resource_map[r.name] = ResourceRequirement(
            name=r.name,
            resource_type=r.resource_type,
            quantity=r.quantity
        )
    for r in c2.resources:
        if r.name in resource_map:
            # Shared or additive resource
            resource_map[r.name].quantity += r.quantity
        else:
            resource_map[r.name] = ResourceRequirement(
                name=r.name,
                resource_type=r.resource_type,
                quantity=r.quantity
            )
    composite_resources = list(resource_map.values())

    # Operational quality
    composite_quality = c1.quality.compose_with(c2.quality)

    # Mechanism: Composite service
    sub_caps = []
    if c1.is_composite:
        sub_caps.extend(c1.sub_capabilities)
    else:
        sub_caps.append(c1)
    if c2.is_composite:
        sub_caps.extend(c2.sub_capabilities)
    else:
        sub_caps.append(c2)

    return Capability(
        name=composite_name,
        capability_type=CapabilityType.SERVICE,
        inputs=composite_inputs,
        outputs=composite_outputs,
        preconditions=composite_preconditions,
        effects=composite_effects,
        constraints=composite_constraints,
        resources=composite_resources,
        quality=composite_quality,
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.SERVICE,
            details={"composition_pipeline": [c.name for c in sub_caps]}
        ),
        sub_capabilities=sub_caps
    )


def compose_sequence(capabilities: Sequence[Capability], name: Optional[str] = None) -> Capability:
    """
    Compose a sequence of capabilities in order: C_n o ... o C_2 o C_1.
    List order is execution order: [C1, C2, ..., Cn].
    Section 5: 'Composition may be extended recursively: C123 = C3 o C2 o C1'
    """
    if not capabilities:
        raise ValueError("Cannot compose an empty sequence of capabilities.")
    if len(capabilities) == 1:
        return capabilities[0].clone()

    current = capabilities[0]
    for nxt in capabilities[1:]:
        current = compose_two(current, nxt)

    if name:
        current.name = name
    return current
