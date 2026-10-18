"""
Encoders for Application State, Goal, and Capabilities (Section 6 & Deliverable 2).
Provides:
  - encode_state(state)
  - encode_goal(goal)
  - encode_capability(capability)
  - encode(entity) [Polymorphic unified dispatcher]
"""

from typing import Dict, Any, List, Optional, Union, Sequence
import numpy as np
import hashlib

from ..core.types import CapabilityType, VariableType
from ..core.state import State, Goal
from ..core.capability import Capability
from .vocabulary import SchemaRegistry, StateVariableRegistry
from .vector_space import SubspaceLayout, MultiFacetedEmbedding


def _hash_to_vector(text: str, dim: int) -> np.ndarray:
    """Deterministic pseudo-random projection for names and schema identifiers."""
    vec = np.zeros(dim, dtype=np.float64)
    if not text:
        return vec
    # Use sha256 to generate deterministic floating point components in [-1, 1]
    h = hashlib.sha256(text.encode("utf-8")).digest()
    for i in range(dim):
        byte_val = h[i % len(h)]
        # Map to [-1, 1]
        vec[i] = (byte_val / 127.5) - 1.0
    # Normalize to unit sphere
    norm = np.linalg.norm(vec)
    if norm > 1e-12:
        vec /= norm
    return vec


class CapabilityEmbeddingSystem:
    """
    End-to-end Embedding System for a formally specified application domain.
    Maintains schemas, variable layouts, and consistent coordinate frames.
    """

    def __init__(self, schema: Optional[SchemaRegistry] = None, io_dim: int = 16, impl_dim: int = 16):
        self.schema = schema or SchemaRegistry()
        self.io_dim = io_dim
        self.impl_dim = impl_dim
        self._cached_layout: Optional[SubspaceLayout] = None

    @property
    def layout(self) -> SubspaceLayout:
        num_vars = max(self.schema.state_vars.dimension, 1)
        num_res = max(self.schema.resources.dimension, 1)
        if self._cached_layout is None or self._cached_layout.num_state_vars != num_vars or self._cached_layout.num_resources != num_res:
            self._cached_layout = SubspaceLayout(
                num_state_vars=num_vars,
                io_dim=self.io_dim,
                num_resources=num_res,
                impl_dim=self.impl_dim
            )
        return self._cached_layout

    def _value_to_float(self, val: Any) -> float:
        """Converts arbitrary domain values to signed continuous representations."""
        if isinstance(val, bool):
            return 1.0 if val else -1.0
        elif isinstance(val, (int, float)):
            return float(val)
        elif isinstance(val, str):
            # Check standard semantic strings
            val_upper = val.upper()
            if val_upper in ("TRUE", "SUCCESS", "ACTIVE", "EXISTS", "CONFIRMED", "COMPLETED", "CREATED"):
                return 1.0
            elif val_upper in ("FALSE", "FAILURE", "INACTIVE", "NONE", "CANCELLED", "NOT_STARTED"):
                return -1.0
            else:
                # Deterministic hash to scalar in [-1, 1]
                h = int(hashlib.md5(val.encode("utf-8")).hexdigest()[:8], 16)
                return (h / 0x7FFFFFFF) - 1.0
        return 0.0

    def encode_state(self, state: State, name: str = "State") -> MultiFacetedEmbedding:
        """
        Encode an Application State (Section 3.1 & Deliverable 2).
        Represents current variable values in the state space.
        """
        layout = self.layout
        vec = np.zeros(layout.total_dim, dtype=np.float64)

        for var_name, val in state.variables.items():
            idx = self.schema.state_vars.get_index(var_name)
            if idx is None:
                idx = self.schema.state_vars.register_variable(var_name)
                layout = self.layout  # Update layout if dimension grew
                vec = np.pad(vec, (0, layout.total_dim - len(vec)))

            f_val = self._value_to_float(val)
            # In a state, current values populate the effect/current state slice
            vec[layout.eff_val_slice.start + idx] = f_val
            vec[layout.eff_mask_slice.start + idx] = 1.0

        return MultiFacetedEmbedding(vec, layout, name=name, entity_type="state")

    def encode_goal(self, goal: Goal, name: str = "Goal") -> MultiFacetedEmbedding:
        """
        Encode a Goal Specification (Section 3.2 & Deliverable 2).
        Represents target conditions and goal masks.
        """
        layout = self.layout
        vec = np.zeros(layout.total_dim, dtype=np.float64)

        for var_name, req_val in goal.conditions.items():
            idx = self.schema.state_vars.get_index(var_name)
            if idx is None:
                idx = self.schema.state_vars.register_variable(var_name)
                layout = self.layout
                vec = np.pad(vec, (0, layout.total_dim - len(vec)))

            f_val = self._value_to_float(req_val)
            # Goal sets desired target state values and active target masks
            vec[layout.eff_val_slice.start + idx] = f_val
            vec[layout.eff_mask_slice.start + idx] = 1.0
            # Also in requirement slice to allow dual matching
            vec[layout.req_val_slice.start + idx] = f_val
            vec[layout.req_mask_slice.start + idx] = 1.0

        return MultiFacetedEmbedding(vec, layout, name=name, entity_type="goal")

    def encode_capability(self, capability: Capability) -> MultiFacetedEmbedding:
        """
        Encode an Atomic or Composite Capability (Section 4 & Deliverable 2).
        Constructs the multi-faceted numerical vector:
          z_C = [z_req || z_eff || z_io || z_ops || z_impl]
        """
        layout = self.layout
        vec = np.zeros(layout.total_dim, dtype=np.float64)

        # 1. Precondition Subspace (z_req)
        for var_name, req_val in capability.preconditions.items():
            idx = self.schema.state_vars.get_index(var_name)
            if idx is None:
                idx = self.schema.state_vars.register_variable(var_name)
                layout = self.layout
                vec = np.pad(vec, (0, layout.total_dim - len(vec)))

            f_val = self._value_to_float(req_val)
            vec[layout.req_val_slice.start + idx] = f_val
            vec[layout.req_mask_slice.start + idx] = 1.0

        # 2. Effect Subspace (z_eff)
        for var_name, eff_val in capability.effects.items():
            idx = self.schema.state_vars.get_index(var_name)
            if idx is None:
                idx = self.schema.state_vars.register_variable(var_name)
                layout = self.layout
                vec = np.pad(vec, (0, layout.total_dim - len(vec)))

            f_val = self._value_to_float(eff_val)
            vec[layout.eff_val_slice.start + idx] = f_val
            vec[layout.eff_mask_slice.start + idx] = 1.0

        # 3. Input-Output Dataflow Subspace (z_io)
        io_in_vec = np.zeros(layout.io_dim, dtype=np.float64)
        for inp in capability.inputs:
            h_v = _hash_to_vector(f"{inp.name}:{inp.var_type}:{inp.domain}", layout.io_dim)
            io_in_vec += h_v * (1.5 if inp.required else 1.0)
        norm_in = np.linalg.norm(io_in_vec)
        if norm_in > 1e-12:
            io_in_vec /= norm_in
        vec[layout.io_in_slice] = io_in_vec

        io_out_vec = np.zeros(layout.io_dim, dtype=np.float64)
        for out in capability.outputs:
            h_v = _hash_to_vector(f"{out.name}:{out.var_type}:{out.domain}", layout.io_dim)
            io_out_vec += h_v
        norm_out = np.linalg.norm(io_out_vec)
        if norm_out > 1e-12:
            io_out_vec /= norm_out
        vec[layout.io_out_slice] = io_out_vec

        # 4. Operational Quality Subspace (z_ops)
        # Coordinates: [T, C_money, C_res, C_energy, -log(Rel), -log(Avail), Risk, Resources...]
        ops_vec = np.zeros(layout.ops_dim, dtype=np.float64)
        q = capability.quality
        ops_vec[0] = q.execution_time_ms
        ops_vec[1] = q.monetary_cost
        ops_vec[2] = q.resource_cost
        ops_vec[3] = q.energy_cost
        ops_vec[4] = q.log_reliability    # -log(Rel), additive
        ops_vec[5] = q.log_availability   # -log(Avail), additive
        ops_vec[6] = q.risk

        # Resource requirements multi-hot encoding
        for res in capability.resources:
            r_idx = self.schema.resources.get_index(res.name)
            if r_idx is None:
                r_idx = self.schema.resources.register_resource(res.name)
                layout = self.layout
                vec = np.pad(vec, (0, layout.total_dim - len(vec)))
                ops_vec = np.pad(ops_vec, (0, layout.ops_dim - len(ops_vec)))
            if r_idx < layout.num_resources:
                ops_vec[layout.num_ops_scalars + r_idx] = res.quantity

        vec[layout.ops_slice] = ops_vec

        # 5. Implementation Mechanism Subspace (z_impl)
        impl_vec = np.zeros(layout.impl_dim, dtype=np.float64)
        # One-hot capability type across available slots
        type_idx = self.schema.type_to_idx.get(capability.capability_type, 0)
        if type_idx < layout.impl_dim:
            impl_vec[type_idx] = 1.0

        # Hash mechanism details (endpoint, table, component, etc.)
        mech_str = f"{capability.mechanism.mechanism_type}:{sorted(capability.mechanism.details.items())}"
        mech_h = _hash_to_vector(mech_str, layout.impl_dim)
        # Blend type identity with fine mechanism details
        impl_vec = 0.7 * impl_vec + 0.3 * mech_h
        norm_impl = np.linalg.norm(impl_vec)
        if norm_impl > 1e-12:
            impl_vec /= norm_impl
        vec[layout.impl_slice] = impl_vec

        entity_type = "composite_capability" if capability.is_composite else "capability"
        return MultiFacetedEmbedding(vec, layout, name=capability.name, entity_type=entity_type)

    def encode(self, entity: Union[State, Goal, Capability, Sequence[Capability]]) -> MultiFacetedEmbedding:
        """
        Polymorphic encode method supporting:
          - encode(state)
          - encode(goal)
          - encode(capability)
          - encode([c1, c2, ...]) -> composite capability embedding
        """
        if isinstance(entity, State):
            return self.encode_state(entity)
        elif isinstance(entity, Goal):
            return self.encode_goal(entity)
        elif isinstance(entity, Capability):
            return self.encode_capability(entity)
        elif isinstance(entity, (list, tuple)):
            from ..core.composition import compose_sequence
            composed = compose_sequence(entity)
            return self.encode_capability(composed)
        else:
            raise TypeError(f"Cannot encode entity of type {type(entity)}")
