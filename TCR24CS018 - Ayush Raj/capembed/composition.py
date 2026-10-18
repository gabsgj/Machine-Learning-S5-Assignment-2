"""
Capability Composition Engine.
Implements formal algebraic composition operators both symbolically and in vector space.
Supports sequential composition (C2 o C1) and multi-capability chaining (Cn o ... o C1).
"""

from __future__ import annotations
import math
from typing import List, Tuple, Dict, Any, Optional
import numpy as np

from .core import (
    Capability,
    CapabilityType,
    InputSpec,
    OutputSpec,
    OperationalProfile,
    ExecutionMechanism,
    DomainSchema,
)
from .encoder import EncodedCapability, CapabilityEncoder


class CapabilityComposer:
    """
    Formal composition operator for capabilities.
    """
    def __init__(self, encoder: CapabilityEncoder):
        self.encoder = encoder
        self.schema = encoder.schema

    def compose_symbolic(self, c1: Capability, c2: Capability, name: Optional[str] = None) -> Capability:
        """
        Symbolic sequential composition: C12 = C2 o C1.
        C1 executes first, then C2 executes.
        """
        composite_name = name or f"({c2.name} o {c1.name})"

        # 1. Preconditions: P12 = P1 U (P2 \ E1)
        # Preconditions of C2 already satisfied by E1 are absorbed.
        combined_preconditions = dict(c1.preconditions)
        for var, req_val in c2.preconditions.items():
            if var in c1.effects:
                eff_val = c1.effects[var]
                if eff_val != req_val:
                    # Conflict: C1 sets var to something different than C2 requires
                    pass
            else:
                combined_preconditions[var] = req_val

        # 2. Effects: E12 = E1 (+) E2 (E2 overrides/augments E1)
        combined_effects = dict(c1.effects)
        combined_effects.update(c2.effects)

        # 3. Inputs: I12 = I1 U (I2 \ O1)
        # If an input of C2 matches an output of C1, it is satisfied internally.
        c1_out_names = {o.name.lower() for o in c1.outputs}
        combined_inputs = list(c1.inputs)
        for inp in c2.inputs:
            if inp.name.lower() not in c1_out_names:
                combined_inputs.append(inp)

        # 4. Outputs: O12 = O1 U O2
        seen_outs = set()
        combined_outputs = []
        for o in (c1.outputs + c2.outputs):
            key = (o.name.lower(), o.data_type)
            if key not in seen_outs:
                seen_outs.add(key)
                combined_outputs.append(o)

        # 5. Resources: R12 = R1 U R2
        combined_resources = set(c1.resources).union(c2.resources)

        # 6. Operational profile:
        # Time: sum
        # Money: sum
        # Resource cost: max or sum (sum for conservative total)
        # Risk: 1 - (1 - risk1) * (1 - risk2)
        # Energy: sum
        # Reliability: rel1 * rel2
        # Availability: min(avail1, avail2)
        op1 = c1.operational_profile
        op2 = c2.operational_profile
        comp_ops = OperationalProfile(
            execution_time_ms=op1.execution_time_ms + op2.execution_time_ms,
            monetary_cost=op1.monetary_cost + op2.monetary_cost,
            resource_cost=op1.resource_cost + op2.resource_cost,
            risk=1.0 - (1.0 - op1.risk) * (1.0 - op2.risk),
            energy_cost=op1.energy_cost + op2.energy_cost,
            reliability=op1.reliability * op2.reliability,
            availability=min(op1.availability, op2.availability),
        )

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
            cap_type=CapabilityType.SERVICE,
            inputs=combined_inputs,
            outputs=combined_outputs,
            preconditions=combined_preconditions,
            effects=combined_effects,
            constraints=list(set(c1.constraints + c2.constraints)),
            resources=combined_resources,
            operational_profile=comp_ops,
            mechanism=ExecutionMechanism(
                mechanism_type=CapabilityType.SERVICE,
                properties={"pipeline": [c.name for c in sub_caps]},
            ),
            is_composite=True,
            sub_capabilities=sub_caps,
        )

    def compose_chain_symbolic(self, capabilities: List[Capability], name: Optional[str] = None) -> Capability:
        """
        Sequentially composes a chain of capabilities: Cn o ... o C2 o C1.
        Evaluated left-to-right in execution order: (((C1 then C2) then C3) ...).
        """
        if not capabilities:
            raise ValueError("Cannot compose empty list of capabilities.")
        if len(capabilities) == 1:
            return capabilities[0]

        curr = capabilities[0]
        for next_cap in capabilities[1:]:
            curr = self.compose_symbolic(curr, next_cap)
        if name:
            curr.name = name
        return curr

    def compose_vector(
        self,
        ec1: EncodedCapability,
        ec2: EncodedCapability,
        name: Optional[str] = None,
    ) -> EncodedCapability:
        """
        Direct algebraic vector space composition: phi(C12) = phi(C2) (o) phi(C1).
        Operates directly on the partitioned vector representations.
        """
        comp_name = name or f"({ec2.name} o {ec1.name})"
        d_s = self.schema.d_state
        d_io = self.schema.d_io

        # 1. Preconditions:
        # m_pre_12 = m_pre_1 OR (m_pre_2 AND NOT m_eff_1)
        m_pre_pass = ec2.m_pre * (1.0 - ec1.m_eff)
        m_pre = np.clip(ec1.m_pre + m_pre_pass, 0.0, 1.0)
        v_pre = ec1.v_pre * ec1.m_pre + ec2.v_pre * m_pre_pass

        # 2. Effects:
        # m_eff_12 = m_eff_1 OR m_eff_2
        # v_eff_12 = v_eff_2 on m_eff_2, and v_eff_1 on (m_eff_1 AND NOT m_eff_2)
        m_eff = np.clip(ec1.m_eff + ec2.m_eff, 0.0, 1.0)
        v_eff = ec2.v_eff * ec2.m_eff + ec1.v_eff * (ec1.m_eff * (1.0 - ec2.m_eff))

        # 3. Inputs:
        # Inputs of C2 that match outputs of C1 are subtracted
        v_in_2_unmet = np.maximum(0.0, ec2.v_in - ec1.v_out)
        v_in = np.maximum(ec1.v_in, v_in_2_unmet)

        # 4. Outputs:
        # Union of produced outputs
        v_out = np.maximum(ec1.v_out, ec2.v_out)

        # 5. Type:
        # Result of composition is categorized as SERVICE (or composite computation)
        v_type = np.zeros(self.schema.d_type, dtype=np.float64)
        if "SERVICE" in self.schema.cap_type_to_idx:
            v_type[self.schema.cap_type_to_idx["SERVICE"]] = 1.0

        # 6. Mechanism:
        # Associative mechanism aggregation (feature envelope)
        v_mech = np.maximum(ec1.v_mech, ec2.v_mech)

        # 7. Resources:
        # Union of resource bits
        v_res = np.clip(ec1.v_res + ec2.v_res, 0.0, 1.0)

        # 8. Operational vector:
        # [time_norm, cost_norm, res_cost_norm, risk, energy_norm, -ln(reliability), availability]
        v_ops = np.zeros(7, dtype=np.float64)
        # Sum execution times:
        t1_ms = math.expm1(ec1.v_ops[0] * 10.0)
        t2_ms = math.expm1(ec2.v_ops[0] * 10.0)
        v_ops[0] = math.log1p(t1_ms + t2_ms) / 10.0

        # Monetary cost: additive
        v_ops[1] = ec1.v_ops[1] + ec2.v_ops[1]

        # Resource cost: additive
        v_ops[2] = ec1.v_ops[2] + ec2.v_ops[2]

        # Risk: 1 - (1 - r1)*(1 - r2)
        r1, r2 = ec1.v_ops[3], ec2.v_ops[3]
        v_ops[3] = 1.0 - (1.0 - r1) * (1.0 - r2)

        # Energy: additive
        v_ops[4] = ec1.v_ops[4] + ec2.v_ops[4]

        # Log reliability: STRICTLY ADDITIVE! -ln(Rel1 * Rel2) = -ln(Rel1) + -ln(Rel2)
        v_ops[5] = ec1.v_ops[5] + ec2.v_ops[5]

        # Availability: min (conjunction)
        v_ops[6] = min(ec1.v_ops[6], ec2.v_ops[6])

        # Also maintain symbolic backing capability
        raw_comp = self.compose_symbolic(ec1.raw_capability, ec2.raw_capability, name=comp_name)

        return EncodedCapability(
            name=comp_name,
            v_pre=v_pre,
            m_pre=m_pre,
            v_eff=v_eff,
            m_eff=m_eff,
            v_in=v_in,
            v_out=v_out,
            v_type=v_type,
            v_mech=v_mech,
            v_res=v_res,
            v_ops=v_ops,
            schema=self.schema,
            raw_capability=raw_comp,
        )

    def compose_chain_vector(
        self,
        encoded_caps: List[EncodedCapability],
        name: Optional[str] = None,
    ) -> EncodedCapability:
        """Composes a chain of encoded capabilities directly in vector space."""
        if not encoded_caps:
            raise ValueError("Cannot compose empty list of encoded capabilities.")
        if len(encoded_caps) == 1:
            return encoded_caps[0]

        curr = encoded_caps[0]
        for next_ec in encoded_caps[1:]:
            curr = self.compose_vector(curr, next_ec)
        if name:
            curr.name = name
        return curr
