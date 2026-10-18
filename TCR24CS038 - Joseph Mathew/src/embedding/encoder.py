"""Encoder implementation for States, Goals, and Capabilities.

Supports:
- encode(state)
- encode(goal)
- encode(capability)
- Subspace extraction and normalization
"""

from __future__ import annotations
import hashlib
from typing import Any, Dict, List, Optional, Union
import numpy as np

from src.models.state import State, Goal, Condition, Effect
from src.models.capability import Capability, CapabilityType
from src.embedding.schema import EmbeddingSchema


class CapabilityEncoder:
    """Encodes formal entities into structured partitioned vector representations."""

    def __init__(self, schema: EmbeddingSchema):
        self.schema = schema

    def _value_to_float(self, val: Any) -> float:
        """Transforms a state variable value into a canonical signed numeric value."""
        if isinstance(val, bool):
            return 1.0 if val else -1.0
        elif isinstance(val, (int, float)):
            return float(np.tanh(val / 10.0))
        elif isinstance(val, str):
            upper = val.upper()
            if upper in ("TRUE", "SUCCESS", "CREATED", "AVAILABLE", "COMPLETED", "ACTIVE", "PAID"):
                return 1.0
            elif upper in ("FALSE", "FAILURE", "FAILED", "UNAVAILABLE", "NOT_STARTED", "INACTIVE", "CANCELLED"):
                return -1.0
            elif upper in ("PROCESSING", "PENDING", "INITIALIZED"):
                return 0.5
            else:
                h = int(hashlib.md5(val.encode()).hexdigest(), 16)
                return ((h % 1000) / 500.0) - 1.0
        elif val is None:
            return 0.0
        return 0.0

    def encode_state(self, state: State) -> np.ndarray:
        """Encode an application state S into R^{d_S}."""
        vec = np.zeros(self.schema.dim_preconditions, dtype=np.float64)
        for var_name, val in state.variables.items():
            if var_name in self.schema.var_index:
                idx = self.schema.var_index[var_name]
                vec[idx] = self._value_to_float(val)
        return vec

    def encode_goal(self, goal: Goal) -> np.ndarray:
        """Encode a goal specification G into R^{d_S}."""
        vec = np.zeros(self.schema.dim_preconditions, dtype=np.float64)
        for cond in goal.conditions:
            if cond.variable in self.schema.var_index:
                idx = self.schema.var_index[cond.variable]
                vec[idx] = self._value_to_float(cond.value)
        return vec

    def _get_canonical_intent(self, capability: Capability) -> List[str]:
        """Extracts canonical functional tokens invariant to deployment details."""
        # Strip implementation or operational suffixes like _Database, _GUI, _PremiumGateway
        name_clean = capability.name.split("_")[0]
        # If composite
        if capability.sub_capabilities:
            tokens = []
            for sub in capability.sub_capabilities:
                tokens.append(sub.split("_")[0])
            return tokens
        return [name_clean]

    def encode_capability(self, capability: Capability) -> np.ndarray:
        """Encode an atomic or composite capability C_i into partitioned vector R^D."""
        vec = np.zeros(self.schema.total_dim, dtype=np.float64)

        # 1. Precondition Subspace (v^P)
        p_slice = self.schema.slice_preconditions
        for cond in capability.preconditions:
            if cond.variable in self.schema.var_index:
                idx = p_slice.start + self.schema.var_index[cond.variable]
                vec[idx] = self._value_to_float(cond.value)

        # 2. Effect Subspace (v^E)
        e_slice = self.schema.slice_effects
        for eff in capability.effects:
            if eff.variable in self.schema.var_index:
                idx = e_slice.start + self.schema.var_index[eff.variable]
                if eff.action == "set":
                    vec[idx] = self._value_to_float(eff.value)
                elif eff.action == "increment":
                    vec[idx] = 1.0
                elif eff.action == "decrement":
                    vec[idx] = -1.0
                elif eff.action == "toggle":
                    vec[idx] = 1.0

        # 3. Input Subspace (v^I)
        i_slice = self.schema.slice_inputs
        for inp in capability.inputs:
            if inp.data_type in self.schema.type_index:
                idx = i_slice.start + self.schema.type_index[inp.data_type]
                vec[idx] = 1.0 if inp.required else 0.5
            elif inp.name in self.schema.type_index:
                idx = i_slice.start + self.schema.type_index[inp.name]
                vec[idx] = 1.0 if inp.required else 0.5

        # 4. Output Subspace (v^O)
        o_slice = self.schema.slice_outputs
        for out in capability.outputs:
            if out.data_type in self.schema.type_index:
                idx = o_slice.start + self.schema.type_index[out.data_type]
                vec[idx] = 1.0
            elif out.name in self.schema.type_index:
                idx = o_slice.start + self.schema.type_index[out.name]
                vec[idx] = 1.0

        # 5. Functional Semantics Subspace (v^F)
        # Invariant semantic intent representation
        f_slice = self.schema.slice_functional
        canonical_intents = self._get_canonical_intent(capability)
        comb_f = np.zeros(self.schema.dim_functional, dtype=np.float64)
        for token in canonical_intents:
            h = int(hashlib.sha256(token.lower().encode()).hexdigest(), 16)
            for i in range(self.schema.dim_functional):
                bit = (h >> i) & 1
                comb_f[i] += 1.0 if bit else -1.0
        
        f_norm = np.linalg.norm(comb_f)
        if f_norm > 1e-6:
            vec[f_slice] = comb_f / f_norm

        # 6. Execution Mechanism Subspace (v^M)
        m_slice = self.schema.slice_mechanism
        cap_type_name = capability.capability_type.value if hasattr(capability.capability_type, 'value') else str(capability.capability_type)
        if cap_type_name in self.schema.cap_type_index:
            t_idx = self.schema.cap_type_index[cap_type_name]
            vec[m_slice.start + t_idx] = 1.0
            
        # Only atomic capabilities hash custom mechanism details into subslots
        # For composite workflows, the mechanism is standardized as composite orchestrator
        if not capability.sub_capabilities and capability.execution_mechanism and capability.execution_mechanism.details:
            details_str = str(sorted(capability.execution_mechanism.details.items()))
            h_m = int(hashlib.md5(details_str.encode()).hexdigest(), 16)
            for k in range(8):
                idx = m_slice.start + len(self.schema.capability_types) + k
                vec[idx] = 1.0 if ((h_m >> k) & 1) else -1.0

        # 7. Operational Subspace (v^Q)
        q_slice = self.schema.slice_operational
        q_vec = capability.cost.as_vector()  # [time_ms, money, res, risk, energy]
        vec[q_slice.start + 0] = float(np.tanh(q_vec[0] / 1000.0))
        vec[q_slice.start + 1] = float(np.tanh(q_vec[1] / 10.0))
        vec[q_slice.start + 2] = float(np.tanh(q_vec[2] / 10.0))
        vec[q_slice.start + 3] = float(q_vec[3])  # risk in [0, 1]
        vec[q_slice.start + 4] = float(np.tanh(q_vec[4] / 100.0))
        vec[q_slice.start + 5] = float(capability.reliability)
        vec[q_slice.start + 6] = float(capability.availability)

        # 8. Resource Subspace (v^R)
        r_slice = self.schema.slice_resources
        for res in capability.resources:
            if res.name in self.schema.resource_index:
                r_idx = r_slice.start + self.schema.resource_index[res.name]
                vec[r_idx] = float(np.tanh(res.amount))

        return vec

    def get_subspaces(self, vec: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract partition blocks from an encoded capability vector."""
        return {
            "preconditions": vec[self.schema.slice_preconditions],
            "effects": vec[self.schema.slice_effects],
            "inputs": vec[self.schema.slice_inputs],
            "outputs": vec[self.schema.slice_outputs],
            "functional": vec[self.schema.slice_functional],
            "mechanism": vec[self.schema.slice_mechanism],
            "operational": vec[self.schema.slice_operational],
            "resources": vec[self.schema.slice_resources],
        }
