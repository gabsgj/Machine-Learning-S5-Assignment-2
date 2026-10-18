from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from src.models.state import ApplicationState, StateVariable
from src.models.goal import GoalSpecification
from src.models.capability import Capability, CapabilityType
from src.embedding.schema import EmbeddingSchema, SubspaceSlice


@dataclass
class StateEmbedding:
    """Vector representation of an application state phi_S(S) in R^{d_state}."""
    state_id: str
    vector: np.ndarray
    schema: EmbeddingSchema

    @property
    def dim(self) -> int:
        return len(self.vector)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "dim": self.dim,
            "vector": self.vector.tolist()
        }


@dataclass
class GoalEmbedding:
    """Vector representation of a goal specification phi_G(G)."""
    goal_id: str
    val_vector: np.ndarray   # Target values in state space
    mask_vector: np.ndarray  # 1 for variables constrained by goal, 0 otherwise
    schema: EmbeddingSchema

    @property
    def vector(self) -> np.ndarray:
        """Unified 2 * d_state vector."""
        return np.concatenate([self.val_vector, self.mask_vector])

    @property
    def dim(self) -> int:
        return len(self.vector)

    def distance_to_state(self, state_emb: StateEmbedding) -> float:
        """Euclidean distance on goal-constrained dimensions."""
        diff = (state_emb.vector - self.val_vector) * self.mask_vector
        return float(np.linalg.norm(diff))

    def is_satisfied_by(self, state_emb: StateEmbedding, tol: float = 1e-4) -> bool:
        return self.distance_to_state(state_emb) <= tol


@dataclass
class CapabilityEmbedding:
    """
    Vector representation of a formal capability phi_C(C) in R^{d_C}.
    Structured partitioned space:
    [p_val || p_mask || e_val || e_mask || i || o || t || r || q || m]
    """
    capability_id: str
    vector: np.ndarray
    schema: EmbeddingSchema

    @property
    def dim(self) -> int:
        return len(self.vector)

    # Subspace sector accessors
    @property
    def pre_val(self) -> np.ndarray:
        s = self.schema.slice_pre_val
        return self.vector[s.start:s.end]

    @property
    def pre_mask(self) -> np.ndarray:
        s = self.schema.slice_pre_mask
        return self.vector[s.start:s.end]

    @property
    def eff_val(self) -> np.ndarray:
        s = self.schema.slice_eff_val
        return self.vector[s.start:s.end]

    @property
    def eff_mask(self) -> np.ndarray:
        s = self.schema.slice_eff_mask
        return self.vector[s.start:s.end]

    @property
    def input_vec(self) -> np.ndarray:
        s = self.schema.slice_in
        return self.vector[s.start:s.end]

    @property
    def output_vec(self) -> np.ndarray:
        s = self.schema.slice_out
        return self.vector[s.start:s.end]

    @property
    def type_vec(self) -> np.ndarray:
        s = self.schema.slice_type
        return self.vector[s.start:s.end]

    @property
    def resource_vec(self) -> np.ndarray:
        s = self.schema.slice_res
        return self.vector[s.start:s.end]

    @property
    def operational_vec(self) -> np.ndarray:
        s = self.schema.slice_ops
        return self.vector[s.start:s.end]

    @property
    def mechanism_vec(self) -> np.ndarray:
        s = self.schema.slice_mech
        return self.vector[s.start:s.end]

    @property
    def functional_vec(self) -> np.ndarray:
        """
        Core functional sector:
        [pre_val || pre_mask || eff_val || eff_mask || input || output]
        Excludes mechanism, resource, and operational attributes.
        """
        return np.concatenate([
            self.pre_val, self.pre_mask,
            self.eff_val, self.eff_mask,
            self.input_vec, self.output_vec
        ])

    @property
    def implementation_vec(self) -> np.ndarray:
        """Implementation details: [type || mechanism]."""
        return np.concatenate([self.type_vec, self.mechanism_vec])


class CapabilityEncoder:
    """
    Core embedding engine providing:
    - encode(state)
    - encode(goal)
    - encode(capability)
    - compose(capabilities)
    - similarity(x, y)
    """
    def __init__(self, schema: Optional[EmbeddingSchema] = None):
        self.schema = schema or EmbeddingSchema()

    def encode_state(self, state: ApplicationState) -> StateEmbedding:
        """
        phi_S : S -> R^{d_state}
        Encodes all state variables according to schema.
        """
        vec = np.zeros(self.schema.state_dim, dtype=np.float32)
        for var_name, var in self.schema.state_var_map.items():
            val = state.get(var_name, var.default_value)
            val_vec, _ = self.schema.encode_variable_value(var_name, val)
            offset = self.schema.var_offsets[var_name]
            dim = self.schema.var_dims[var_name]
            vec[offset:offset + dim] = val_vec

        return StateEmbedding(state_id=state.name, vector=vec, schema=self.schema)

    def encode_goal(self, goal: GoalSpecification) -> GoalEmbedding:
        """
        phi_G : G -> R^{2 * d_state}
        Encodes target state values and active condition masks.
        """
        val_vec = np.zeros(self.schema.state_dim, dtype=np.float32)
        mask_vec = np.zeros(self.schema.state_dim, dtype=np.float32)

        for cond in goal.conditions:
            if cond.variable in self.schema.var_offsets:
                sub_val, _ = self.schema.encode_variable_value(cond.variable, cond.target_value)
                offset = self.schema.var_offsets[cond.variable]
                dim = self.schema.var_dims[cond.variable]
                val_vec[offset:offset + dim] = sub_val
                mask_vec[offset:offset + dim] = 1.0

        return GoalEmbedding(
            goal_id=goal.name,
            val_vector=val_vec,
            mask_vector=mask_vec,
            schema=self.schema
        )

    def _hash_to_subspace(self, items: List[str], dim: int) -> np.ndarray:
        """Hashes symbolic items (names/types) into a fixed continuous subspace."""
        vec = np.zeros(dim, dtype=np.float32)
        for item in items:
            h = hash(item.strip().lower())
            idx = abs(h) % dim
            sign = 1.0 if (h // dim) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def encode_capability(self, capability: Capability) -> CapabilityEmbedding:
        """
        phi_C : C -> R^{d_C}
        Encodes the full 11-tuple:
        C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
        """
        vec = np.zeros(self.schema.capability_dim, dtype=np.float32)

        # 1. Preconditions: p_val and p_mask
        p_val = np.zeros(self.schema.state_dim, dtype=np.float32)
        p_mask = np.zeros(self.schema.state_dim, dtype=np.float32)
        for prec in capability.preconditions:
            if prec.variable in self.schema.var_offsets:
                sub_val, _ = self.schema.encode_variable_value(prec.variable, prec.expected_value)
                offset = self.schema.var_offsets[prec.variable]
                dim = self.schema.var_dims[prec.variable]
                p_val[offset:offset + dim] = sub_val
                p_mask[offset:offset + dim] = 1.0

        s_pval = self.schema.slice_pre_val
        s_pmask = self.schema.slice_pre_mask
        vec[s_pval.start:s_pval.end] = p_val
        vec[s_pmask.start:s_pmask.end] = p_mask

        # 2. Effects: e_val and e_mask
        e_val = np.zeros(self.schema.state_dim, dtype=np.float32)
        e_mask = np.zeros(self.schema.state_dim, dtype=np.float32)
        for eff in capability.effects:
            if eff.variable in self.schema.var_offsets:
                sub_val, _ = self.schema.encode_variable_value(eff.variable, eff.new_value)
                offset = self.schema.var_offsets[eff.variable]
                dim = self.schema.var_dims[eff.variable]
                e_val[offset:offset + dim] = sub_val
                e_mask[offset:offset + dim] = 1.0

        s_eval = self.schema.slice_eff_val
        s_emask = self.schema.slice_eff_mask
        vec[s_eval.start:s_eval.end] = e_val
        vec[s_emask.start:s_emask.end] = e_mask

        # 3. Inputs: i
        input_tokens = [f"{inp.name}:{inp.data_type}" for inp in capability.inputs]
        s_in = self.schema.slice_in
        vec[s_in.start:s_in.end] = self._hash_to_subspace(input_tokens, self.schema.io_dim)

        # 4. Outputs: o
        output_tokens = [f"{out.name}:{out.data_type}" for out in capability.outputs]
        s_out = self.schema.slice_out
        vec[s_out.start:s_out.end] = self._hash_to_subspace(output_tokens, self.schema.io_dim)

        # 5. Type: t (one-hot)
        s_type = self.schema.slice_type
        type_vec = np.zeros(self.schema.type_dim, dtype=np.float32)
        try:
            type_idx = self.schema.capability_types.index(capability.type)
            type_vec[type_idx] = 1.0
        except ValueError:
            pass
        vec[s_type.start:s_type.end] = type_vec

        # 6. Resources: r (multi-hot)
        s_res = self.schema.slice_res
        res_vec = np.zeros(self.schema.resource_dim, dtype=np.float32)
        for r in capability.resources:
            idx = self.schema.resource_index.get(r.lower())
            if idx is not None:
                res_vec[idx] = 1.0
        vec[s_res.start:s_res.end] = res_vec

        # 7. Operational attributes: q
        # [time, res_cost, money, risk, energy, log_rel, avail]
        q = capability.quality
        s_ops = self.schema.slice_ops
        log_rel = -np.log(max(capability.reliability, 1e-6))  # Additive under sequential composition
        ops_vec = np.array([
            q.time_ms / self.schema.time_norm,
            q.resource_cost / self.schema.res_norm,
            q.monetary_cost / self.schema.money_norm,
            q.risk,
            q.energy_cost / self.schema.energy_norm,
            log_rel,
            capability.availability
        ], dtype=np.float32)
        vec[s_ops.start:s_ops.end] = ops_vec

        # 8. Execution Mechanism: m
        s_mech = self.schema.slice_mech
        mech_tokens = [f"{capability.mechanism.mechanism_type}"]
        for k, v in capability.mechanism.details.items():
            mech_tokens.append(f"{k}={v}")
        vec[s_mech.start:s_mech.end] = self._hash_to_subspace(mech_tokens, self.schema.mech_dim)

        return CapabilityEmbedding(
            capability_id=capability.id,
            vector=vec,
            schema=self.schema
        )

    # Convenience aliases matching Deliverable 2 interface:
    def encode(self, entity: Union[ApplicationState, GoalSpecification, Capability]) -> Union[StateEmbedding, GoalEmbedding, CapabilityEmbedding]:
        if isinstance(entity, ApplicationState):
            return self.encode_state(entity)
        elif isinstance(entity, GoalSpecification):
            return self.encode_goal(entity)
        elif isinstance(entity, Capability):
            return self.encode_capability(entity)
        raise TypeError(f"Unsupported entity type for encoding: {type(entity)}")
