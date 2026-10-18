from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union
import numpy as np

from src.models.capability import (
    Capability, CapabilityType, ExecutionMechanism,
    Precondition, Effect, InputSpec, OutputSpec, QualityAttributes
)
from src.embedding.schema import EmbeddingSchema
from src.embedding.encoder import CapabilityEmbedding, CapabilityEncoder


@dataclass
class CompositionValidation:
    is_valid: bool
    conflicts: List[str]
    missing_preconditions: List[str]
    details: str = ""


class CapabilityComposer:
    r"""
    Implements formal capability composition both:
    1. Semantically (at the symbolic specification level)
    2. Algebraically (via vector space operator \odot_{comp})
    """
    def __init__(self, encoder: CapabilityEncoder):
        self.encoder = encoder
        self.schema = encoder.schema

    def validate_composition(self, c1: Capability, c2: Capability) -> CompositionValidation:
        """
        Validates whether c2 can execute immediately after c1.
        Composition c2 o c1 (c1 then c2).
        Checks if any effect of c1 explicitly contradicts a precondition of c2.
        """
        conflicts = []
        eff_map = {e.variable: e for e in c1.effects}
        for prec in c2.preconditions:
            if prec.variable in eff_map:
                eff = eff_map[prec.variable]
                # Check if effect value violates precondition
                if eff.new_value != prec.expected_value:
                    conflicts.append(
                        f"Effect {eff.variable}:={eff.new_value} contradicts precondition {prec.variable}=={prec.expected_value}"
                    )

        is_valid = len(conflicts) == 0
        details = "Compatible" if is_valid else f"Conflicts: {', '.join(conflicts)}"
        return CompositionValidation(
            is_valid=is_valid,
            conflicts=conflicts,
            missing_preconditions=[],
            details=details
        )

    def compose_pair(self, c1: Capability, c2: Capability, composite_id: Optional[str] = None) -> Capability:
        r"""
        Constructs composite capability C_12 = C2 o C1 (C1 executed, then C2).
        Preconditions: P12 = P1 U (P2 \ E1)
        Effects: E12 = (E1 \ TargetVars(E2)) U E2
        Inputs: I12 = I1 U (I2 \ O1)
        Outputs: O12 = O1 U O2
        Resources: R12 = R1 U R2
        Operational: Q12 = Q1 + Q2, Rel12 = Rel1 * Rel2, A12 = A1 * A2
        """
        comp_id = composite_id or f"{c1.id}_then_{c2.id}"
        comp_name = f"Composite({c1.name} -> {c2.name})"

        # 1. Preconditions
        # All preconditions of C1 are preserved
        combined_prec: List[Precondition] = list(c1.preconditions)
        c1_effect_vars = {e.variable for e in c1.effects}
        for p in c2.preconditions:
            if p.variable not in c1_effect_vars:
                # If not satisfied/modified by c1, it must be required before c1
                if not any(cp.variable == p.variable for cp in combined_prec):
                    combined_prec.append(p)

        # 2. Effects
        # Effects of C2 override effects of C1 on identical variables
        c2_effect_vars = {e.variable for e in c2.effects}
        combined_effects: List[Effect] = [e for e in c1.effects if e.variable not in c2_effect_vars]
        combined_effects.extend(c2.effects)

        # 3. Inputs & Outputs
        c1_output_names = {o.name for o in c1.outputs}
        combined_inputs: List[InputSpec] = list(c1.inputs)
        for inp in c2.inputs:
            if inp.name not in c1_output_names:
                if not any(ci.name == inp.name for ci in combined_inputs):
                    combined_inputs.append(inp)

        combined_outputs: List[OutputSpec] = list(c1.outputs)
        for out in c2.outputs:
            if not any(co.name == out.name for co in combined_outputs):
                combined_outputs.append(out)

        # 4. Resources
        combined_resources = sorted(list(set(c1.resources + c2.resources)))

        # 5. Quality Attributes
        q1, q2 = c1.quality, c2.quality
        combined_quality = QualityAttributes(
            time_ms=q1.time_ms + q2.time_ms,
            resource_cost=q1.resource_cost + q2.resource_cost,
            monetary_cost=q1.monetary_cost + q2.monetary_cost,
            risk=float(1.0 - (1.0 - q1.risk) * (1.0 - q2.risk)),
            energy_cost=q1.energy_cost + q2.energy_cost
        )

        # 6. Reliability and Availability
        combined_rel = float(c1.reliability * c2.reliability)
        combined_avail = float(c1.availability * c2.availability)

        # 7. Sub-capabilities tracking
        subs1 = c1.sub_capabilities if c1.is_composite else [c1.id]
        subs2 = c2.sub_capabilities if c2.is_composite else [c2.id]
        combined_subs = subs1 + subs2

        return Capability(
            id=comp_id,
            name=comp_name,
            type=CapabilityType.SERVICE,
            inputs=combined_inputs,
            outputs=combined_outputs,
            preconditions=combined_prec,
            effects=combined_effects,
            resources=combined_resources,
            quality=combined_quality,
            reliability=combined_rel,
            availability=combined_avail,
            mechanism=ExecutionMechanism(
                mechanism_type="COMPOSITE_PIPELINE",
                details={}
            ),
            description=f"Sequential composition of {c1.id} followed by {c2.id}",
            sub_capabilities=combined_subs
        )

    def compose_chain(self, capabilities: List[Capability], composite_id: Optional[str] = None) -> Capability:
        """Composes an ordered sequence C1 -> C2 -> ... -> Cn."""
        if not capabilities:
            raise ValueError("Cannot compose empty list of capabilities")
        if len(capabilities) == 1:
            return capabilities[0]

        current = capabilities[0]
        for next_cap in capabilities[1:]:
            current = self.compose_pair(current, next_cap)

        if composite_id:
            current.id = composite_id
        return current

    def vector_compose(self, emb1: CapabilityEmbedding, emb2: CapabilityEmbedding) -> np.ndarray:
        r"""
        Direct vector space algebraic composition operator:
        v_12 = v_2 \odot_{comp} v_1
        Computes composite vector directly from embeddings without parsing objects!
        """
        vec = np.zeros(self.schema.capability_dim, dtype=np.float32)

        # 1. Effects Sector
        # e_{val, 12} = e_{val, 2} * e_{mask, 2} + e_{val, 1} * e_{mask, 1} * (1 - e_{mask, 2})
        # e_{mask, 12} = e_{mask, 2} + e_{mask, 1} * (1 - e_{mask, 2})
        eff_mask_2 = emb2.eff_mask
        eff_val_2 = emb2.eff_val
        eff_mask_1 = emb1.eff_mask
        eff_val_1 = emb1.eff_val

        eff_mask_12 = np.clip(eff_mask_2 + eff_mask_1 * (1.0 - eff_mask_2), 0.0, 1.0)
        eff_val_12 = eff_val_2 * eff_mask_2 + eff_val_1 * eff_mask_1 * (1.0 - eff_mask_2)

        s_eval = self.schema.slice_eff_val
        s_emask = self.schema.slice_eff_mask
        vec[s_eval.start:s_eval.end] = eff_val_12
        vec[s_emask.start:s_emask.end] = eff_mask_12

        # 2. Preconditions Sector
        # Preconditions of C1 persist
        # Preconditions of C2 persist only if NOT satisfied/modified by effects of C1
        pre_mask_1 = emb1.pre_mask
        pre_val_1 = emb1.pre_val
        pre_mask_2 = emb2.pre_mask
        pre_val_2 = emb2.pre_val

        pre_mask_12 = np.clip(pre_mask_1 + pre_mask_2 * (1.0 - eff_mask_1), 0.0, 1.0)
        pre_val_12 = pre_val_1 * pre_mask_1 + pre_val_2 * pre_mask_2 * (1.0 - eff_mask_1)

        s_pval = self.schema.slice_pre_val
        s_pmask = self.schema.slice_pre_mask
        vec[s_pval.start:s_pval.end] = pre_val_12
        vec[s_pmask.start:s_pmask.end] = pre_mask_12

        # 3. IO Sectors
        # Normalized linear combination of IO signatures
        s_in = self.schema.slice_in
        s_out = self.schema.slice_out
        in_comb = emb1.input_vec + emb2.input_vec * 0.5
        norm_in = np.linalg.norm(in_comb)
        if norm_in > 0: in_comb /= norm_in
        vec[s_in.start:s_in.end] = in_comb

        out_comb = emb1.output_vec * 0.5 + emb2.output_vec
        norm_out = np.linalg.norm(out_comb)
        if norm_out > 0: out_comb /= norm_out
        vec[s_out.start:s_out.end] = out_comb

        # 4. Type Sector: Set to SERVICE
        s_type = self.schema.slice_type
        type_vec = np.zeros(self.schema.type_dim, dtype=np.float32)
        try:
            srv_idx = self.schema.capability_types.index(CapabilityType.SERVICE)
            type_vec[srv_idx] = 1.0
        except ValueError:
            pass
        vec[s_type.start:s_type.end] = type_vec

        # 5. Resource Sector: Multi-hot union (max or clip(r1 + r2))
        s_res = self.schema.slice_res
        vec[s_res.start:s_res.end] = np.clip(emb1.resource_vec + emb2.resource_vec, 0.0, 1.0)

        # 6. Operational Sector: Additive costs, log-reliability add
        # [time, res_cost, money, risk, energy, log_rel, avail]
        s_ops = self.schema.slice_ops
        ops1 = emb1.operational_vec
        ops2 = emb2.operational_vec
        ops_12 = np.zeros(self.schema.ops_dim, dtype=np.float32)
        # Additive resources, time, money, energy, and log-rel
        ops_12[0] = ops1[0] + ops2[0] # time
        ops_12[1] = ops1[1] + ops2[1] # res
        ops_12[2] = ops1[2] + ops2[2] # money
        ops_12[3] = float(1.0 - (1.0 - ops1[3]) * (1.0 - ops2[3])) # risk
        ops_12[4] = ops1[4] + ops2[4] # energy
        ops_12[5] = ops1[5] + ops2[5] # log-rel additive!
        ops_12[6] = ops1[6] * ops2[6] # avail multiplicative
        vec[s_ops.start:s_ops.end] = ops_12

        # 7. Mechanism Sector: Set to COMPOSITE_PIPELINE representation
        s_mech = self.schema.slice_mech
        vec[s_mech.start:s_mech.end] = self.encoder._hash_to_subspace(["COMPOSITE_PIPELINE"], self.schema.mech_dim)

        return vec
