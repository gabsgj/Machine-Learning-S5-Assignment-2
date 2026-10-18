from dataclasses import replace
from typing import Dict, List, Tuple
import numpy as np

from .models import Capability, Condition, IOField


def _condition_map(conditions):
    return {c.name: c.value for c in conditions}


def _values_equal(a, b):
    return a == b


def _condition_satisfied(effect: Condition, precondition: Condition) -> bool:
    return effect.name == precondition.name and _values_equal(effect.value, precondition.value)


def precondition_effect_compatibility(c1: Capability, c2: Capability) -> Tuple[bool, List[str]]:
    """
    Directed compatibility:
    c1 -> c2 is valid when c1's effects satisfy c2's preconditions
    and do not directly contradict them.
    """
    effects = _condition_map(c1.effects)
    reasons = []
    compatible = True

    for p in c2.preconditions:
        if p.name not in effects:
            compatible = False
            reasons.append(f"missing effect for precondition: {p.key()}")
        elif not _values_equal(effects[p.name], p.value):
            compatible = False
            reasons.append(
                f"contradiction: {c1.name} produces {p.name}={effects[p.name]}, "
                f"but {c2.name} requires {p.key()}"
            )
        else:
            reasons.append(f"satisfied: {p.key()}")

    return compatible, reasons


def input_output_compatibility(c1: Capability, c2: Capability) -> Tuple[bool, List[str]]:
    """
    Check whether outputs of c1 can supply required inputs of c2.
    Matching is based on name and type.
    """
    produced = {(x.name, x.type) for x in c1.outputs}
    reasons = []
    ok = True

    for inp in c2.inputs:
        if not inp.required:
            continue

        if (inp.name, inp.type) in produced:
            reasons.append(f"output satisfies input: {inp.name}:{inp.type}")
        else:
            ok = False
            reasons.append(f"missing output for input: {inp.name}:{inp.type}")

    return ok, reasons


def compatibility(c1: Capability, c2: Capability) -> Dict:
    pe_ok, pe_reasons = precondition_effect_compatibility(c1, c2)
    io_ok, io_reasons = input_output_compatibility(c1, c2)

    # A capability may legitimately have no explicit inputs, so input/output
    # compatibility is treated as a supporting signal. The primary directed
    # condition is precondition/effect compatibility.
    compatible = pe_ok and (io_ok or len(c2.inputs) == 0)

    return {
        "from": c1.name,
        "to": c2.name,
        "compatible": compatible,
        "precondition_effect": pe_ok,
        "input_output": io_ok,
        "precondition_effect_reasons": pe_reasons,
        "input_output_reasons": io_reasons,
    }


def compose(capabilities: List[Capability], name: str = None) -> Capability:
    """
    Construct a composite capability from an ordered list.

    Preconditions = initial requirements that are not produced internally.
    Effects = final effects of the sequence.
    Inputs/outputs = union-like external interface.
    Cost = sum.
    Reliability = product.
    Availability = minimum.
    Risk = capped sum.
    Resources/constraints = union.
    """
    if not capabilities:
        raise ValueError("At least one capability is required.")

    if name is None:
        name = "Compose(" + " -> ".join(c.name for c in capabilities) + ")"

    produced_names = set()
    all_effects = []
    all_inputs = []
    all_resources = set()
    all_constraints = set()

    for c in capabilities:
        produced_names.update(x.name for x in c.effects)
        all_effects.extend(c.effects)
        all_inputs.extend(c.inputs)
        all_resources.update(c.resources)
        all_constraints.update(c.constraints)

    first_preconditions = []
    for c in capabilities:
        for p in c.preconditions:
            # Keep conditions that are not already produced by an earlier
            # capability in the sequence.
            earlier_effect_names = {
                e.name
                for prev in capabilities[:capabilities.index(c)]
                for e in prev.effects
            }
            if p.name not in earlier_effect_names:
                first_preconditions.append(p)

    # Keep the last value for each effect variable.
    final_effect_map = {}
    for c in capabilities:
        for e in c.effects:
            final_effect_map[e.name] = e.value
    final_effects = [Condition(k, v) for k, v in final_effect_map.items()]

    # Keep unique IO fields.
    unique_inputs = {(x.name, x.type): x for x in all_inputs}
    unique_outputs = {}
    for c in capabilities:
        for x in c.outputs:
            unique_outputs[(x.name, x.type)] = x

    return Capability(
        name=name,
        type="COMPOSITE",
        inputs=list(unique_inputs.values()),
        outputs=list(unique_outputs.values()),
        preconditions=first_preconditions,
        effects=final_effects,
        constraints=sorted(all_constraints),
        resources=sorted(all_resources),
        cost=sum(c.cost for c in capabilities),
        reliability=float(np.prod([c.reliability for c in capabilities])),
        availability=min(c.availability for c in capabilities),
        risk=min(1.0, sum(c.risk for c in capabilities)),
        execution_mechanism={
            "composition": [c.name for c in capabilities]
        },
    )


def compose_vector(vectors: List[np.ndarray]) -> np.ndarray:
    """
    Vector-level composition: mean of atomic vectors.
    The semantic Capability object is composed separately and should also
    be encoded. This mean is retained as an additional compositional
    representation for comparison experiments.
    """
    if not vectors:
        raise ValueError("No vectors supplied.")
    return np.mean(np.vstack(vectors), axis=0)
