"""Capability Composition Engine.

Implements formal capability composition both symbolically and algebraically in vector space:
C_12 = C_2 o C_1 (first C_1, then C_2)
C_123 = C_3 o C_2 o C_1

Preserves:
- Associativity: (C_3 o C_2) o C_1 == C_3 o (C_2 o C_1)
- State delta sequencing: E_12 = E_1 (x) E_2
- Input/Output dataflow forwarding
- Operational cost accumulation and reliability multiplication
"""

from __future__ import annotations
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from src.models.capability import Capability, CapabilityType, ExecutionMechanism, DataParameter
from src.models.state import Condition, Effect
from src.models.operational import OperationalProfile, CostProfile, ResourceRequirement
from src.embedding.schema import EmbeddingSchema


def compose_capabilities(c1: Capability, c2: Capability) -> Capability:
    """Symbolic composition: C12 = C2 o C1 (execute C1 first, then C2)."""
    # 1. Check compatibility
    compatible, info = c1.can_compose_with(c2)
    
    # 2. Sequential Preconditions: P1 + (P2 not satisfied by E1)
    e1_map = {e.variable: e for e in c1.effects}
    combined_preconditions = list(c1.preconditions)
    for p in c2.preconditions:
        # If C1's effect satisfies this precondition, do not require it in the composite's outer preconditions
        satisfied_by_e1 = False
        if p.variable in e1_map:
            eff = e1_map[p.variable]
            if eff.action == "set" and p.operator == "==" and eff.value == p.value:
                satisfied_by_e1 = True
        
        if not satisfied_by_e1:
            if not any(cp.variable == p.variable and cp.value == p.value for cp in combined_preconditions):
                combined_preconditions.append(p.model_copy())

    # 3. Sequential Effects: E1 updated by E2 (E2 overrides E1 on conflict)
    effects_map = {e.variable: e.model_copy() for e in c1.effects}
    for e in c2.effects:
        effects_map[e.variable] = e.model_copy()
    combined_effects = list(effects_map.values())

    # 4. Inputs: Inputs of C1 + inputs of C2 not produced by C1
    c1_output_names = {o.name for o in c1.outputs}
    c1_output_types = {o.data_type for o in c1.outputs}
    combined_inputs = list(c1.inputs)
    for inp in c2.inputs:
        if inp.name not in c1_output_names and inp.data_type not in c1_output_types:
            if not any(ci.name == inp.name for ci in combined_inputs):
                combined_inputs.append(inp.model_copy())

    # 5. Outputs: Union of all produced outputs
    combined_outputs = list(c1.outputs)
    c1_out_keys = {(o.name, o.data_type) for o in c1.outputs}
    for o in c2.outputs:
        if (o.name, o.data_type) not in c1_out_keys:
            combined_outputs.append(o.model_copy())

    # 6. Operational composition
    op_profile = c1.operational_profile.compose_with(c2.operational_profile)

    # 7. Sub-capabilities tracking
    sub_caps = []
    if c1.sub_capabilities:
        sub_caps.extend(c1.sub_capabilities)
    else:
        sub_caps.append(c1.name)
    if c2.sub_capabilities:
        sub_caps.extend(c2.sub_capabilities)
    else:
        sub_caps.append(c2.name)

    composite_name = f"({c1.name} >> {c2.name})"

    return Capability(
        name=composite_name,
        capability_type=CapabilityType.SERVICE,
        inputs=combined_inputs,
        outputs=combined_outputs,
        preconditions=combined_preconditions,
        effects=combined_effects,
        constraints=op_profile.constraints,
        resources=op_profile.resources,
        cost=op_profile.cost,
        reliability=op_profile.reliability,
        availability=op_profile.availability,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.SERVICE,
            details={"composition": "sequential"}
        ),
        sub_capabilities=sub_caps
    )


def compose_sequence(capabilities: List[Capability]) -> Capability:
    """Chains a sequence of capabilities C_1, C_2, ..., C_n: C_n o ... o C_2 o C_1."""
    if not capabilities:
        raise ValueError("Cannot compose an empty sequence of capabilities.")
    current = capabilities[0]
    for nxt in capabilities[1:]:
        current = compose_capabilities(current, nxt)
    return current


def compose_vectors(v1: np.ndarray, v2: np.ndarray, schema: EmbeddingSchema) -> np.ndarray:
    """Algebraic composition directly in vector space: v_12 = v_2 o v_1.
    
    Homomorphic to symbolic composition:
    phi(C_2 o C_1) approx compose_vectors(phi(C_1), phi(C_2)).
    """
    v_out = np.zeros_like(v1)

    # 1. Preconditions: Preconditions of C1, plus preconditions of C2 not fulfilled by C1's effects
    p_sl = schema.slice_preconditions
    e_sl = schema.slice_effects
    v_p1 = v1[p_sl]
    v_e1 = v1[e_sl]
    v_p2 = v2[p_sl]
    
    # Check where C1's effect satisfies C2's precondition: both non-zero and same sign
    satisfied = (v_e1 * v_p2 > 0)
    rem_p2 = np.where(satisfied, 0.0, v_p2)
    # Combine: where v_p1 is set, keep it; else take rem_p2
    v_out[p_sl] = np.where(np.abs(v_p1) > 1e-3, v_p1, rem_p2)

    # 2. Effects: Sequential override (v_e2 overrides v_e1 where v_e2 is non-zero)
    v_e2 = v2[e_sl]
    v_out[e_sl] = np.where(np.abs(v_e2) > 1e-3, v_e2, v_e1)

    # 3. Inputs: Inputs of C1 + inputs of C2 not produced by C1
    i_sl = schema.slice_inputs
    o_sl = schema.slice_outputs
    v_i1 = v1[i_sl]
    v_o1 = v1[o_sl]
    v_i2 = v2[i_sl]
    # If C1 produced it (v_o1 > 0), C2 doesn't need external input
    rem_i2 = np.where(v_o1 > 0, 0.0, v_i2)
    v_out[i_sl] = np.maximum(v_i1, rem_i2)

    # 4. Outputs: union max(vO_1, vO_2)
    v_o2 = v2[o_sl]
    v_out[o_sl] = np.maximum(v_o1, v_o2)

    # 5. Functional Semantics: Normalized linear combination
    f_sl = schema.slice_functional
    comb_f = v1[f_sl] + v2[f_sl]
    norm_f = np.linalg.norm(comb_f)
    if norm_f > 1e-6:
        v_out[f_sl] = comb_f / norm_f

    # 6. Execution Mechanism: Composite is marked as SERVICE
    m_sl = schema.slice_mechanism
    if "SERVICE" in schema.cap_type_index:
        v_out[m_sl.start + schema.cap_type_index["SERVICE"]] = 1.0

    # 7. Operational properties:
    # time (scale 1000), money (scale 10), res (scale 10), risk, energy (scale 100)
    q_sl = schema.slice_operational
    t1 = np.arctanh(np.clip(v1[q_sl.start + 0], -0.999, 0.999)) * 1000.0
    t2 = np.arctanh(np.clip(v2[q_sl.start + 0], -0.999, 0.999)) * 1000.0
    v_out[q_sl.start + 0] = np.tanh((t1 + t2) / 1000.0)

    m1 = np.arctanh(np.clip(v1[q_sl.start + 1], -0.999, 0.999)) * 10.0
    m2 = np.arctanh(np.clip(v2[q_sl.start + 1], -0.999, 0.999)) * 10.0
    v_out[q_sl.start + 1] = np.tanh((m1 + m2) / 10.0)

    r1 = np.arctanh(np.clip(v1[q_sl.start + 2], -0.999, 0.999)) * 10.0
    r2 = np.arctanh(np.clip(v2[q_sl.start + 2], -0.999, 0.999)) * 10.0
    v_out[q_sl.start + 2] = np.tanh((r1 + r2) / 10.0)

    risk1 = v1[q_sl.start + 3]
    risk2 = v2[q_sl.start + 3]
    v_out[q_sl.start + 3] = 1.0 - (1.0 - risk1) * (1.0 - risk2)

    e1 = np.arctanh(np.clip(v1[q_sl.start + 4], -0.999, 0.999)) * 100.0
    e2 = np.arctanh(np.clip(v2[q_sl.start + 4], -0.999, 0.999)) * 100.0
    v_out[q_sl.start + 4] = np.tanh((e1 + e2) / 1000.0)

    # Reliability multiplies
    v_out[q_sl.start + 5] = v1[q_sl.start + 5] * v2[q_sl.start + 5]
    # Availability is min
    v_out[q_sl.start + 6] = min(v1[q_sl.start + 6], v2[q_sl.start + 6])

    # 8. Resources: max
    r_sl = schema.slice_resources
    v_out[r_sl] = np.maximum(v1[r_sl], v2[r_sl])

    return v_out
