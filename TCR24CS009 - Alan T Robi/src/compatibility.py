from dataclasses import dataclass
from typing import Tuple, List, Dict, Any, Optional
from src.capability import Capability, InputSpec, OutputSpec
from src.utils import canonicalize_predicate

@dataclass
class CompatibilityResult:
    c1_name: str
    c2_name: str
    effect_precondition_match: float
    output_input_match: float
    compatibility_score: float
    has_contradiction: bool
    is_compatible: bool

def check_effect_precondition_match(c1: Capability, c2: Capability) -> Tuple[float, bool]:
    """
    Evaluate Precondition-Effect match for directional composition C1 -> C2.
    Returns: (match_score in [0, 1], has_contradiction)
    """
    p2_list = c2.preconditions
    if not p2_list:
        return (1.0, False)

    e1_canon_set = set(canonicalize_predicate(e) for e in c1.effects)
    satisfied_count = 0
    has_contradiction = False

    for p in p2_list:
        cp = canonicalize_predicate(p)
        # Check direct match
        if cp in e1_canon_set:
            satisfied_count += 1
            continue

        # Check contradiction (e.g. orderexists=true vs orderexists=false)
        if "=" in cp:
            var, val = cp.split("=", 1)
            opp_val = "false" if val.strip().lower() == "true" else ("true" if val.strip().lower() == "false" else None)
            if opp_val:
                contradictory_pred = f"{var.strip()}={opp_val}"
                if contradictory_pred in e1_canon_set:
                    has_contradiction = True

    if has_contradiction:
        return (0.0, True)

    match_score = satisfied_count / len(p2_list)
    return (float(match_score), False)


def check_output_input_match(c1: Capability, c2: Capability) -> float:
    """
    Evaluate Input-Output match for directional composition C1 -> C2.
    Checks if C1 outputs satisfy C2's required inputs.
    """
    req_inputs = [i for i in c2.inputs if i.required]
    if not req_inputs:
        return 1.0

    c1_outputs = c1.outputs
    if not c1_outputs:
        return 0.0

    matched_count = 0
    for inp in req_inputs:
        # Match by name, type, and domain
        match_found = False
        for out in c1_outputs:
            if out.name == inp.name and out.type == inp.type:
                match_found = True
                break
            elif out.type == inp.type and (out.name in inp.name or inp.name in out.name):
                match_found = True
                break
        if match_found:
            matched_count += 1

    return float(matched_count / len(req_inputs))


def compatibility(
    c1: Capability, 
    c2: Capability, 
    w_ep: float = 0.6, 
    w_oi: float = 0.4, 
    threshold: float = 0.5
) -> CompatibilityResult:
    """
    Compute directional compatibility score between C1 and C2 for C1 -> C2 sequence:
    Compat(C1, C2) = w_ep * Match_EP(E1, P2) + w_oi * Match_OI(O1, I2)
    """
    ep_score, contradiction = check_effect_precondition_match(c1, c2)
    oi_score = check_output_input_match(c1, c2)

    if contradiction:
        score = 0.0
        is_comp = False
    else:
        score = w_ep * ep_score + w_oi * oi_score
        is_comp = (score >= threshold) and (ep_score > 0.0 or not c2.preconditions)

    return CompatibilityResult(
        c1_name=c1.name,
        c2_name=c2.name,
        effect_precondition_match=ep_score,
        output_input_match=oi_score,
        compatibility_score=score,
        has_contradiction=contradiction,
        is_compatible=is_comp
    )
