"""
Vector Space Encoder for States, Goals, and Capabilities.
Produces mathematically structured embeddings with explicit subspace partitioning.
"""

from __future__ import annotations
import math
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from .core import (
    Capability,
    State,
    Goal,
    DomainSchema,
    CapabilityType,
    InputSpec,
    OutputSpec,
    OperationalProfile,
    ExecutionMechanism,
)


@dataclass
class EncodedState:
    """Vector representation of an application state S."""
    state_vector: np.ndarray  # Dimension: d_state
    mask_vector: np.ndarray   # Dimension: d_state (1 if variable is set, 0 if unknown)
    schema: DomainSchema
    raw_state: State

    @property
    def vector(self) -> np.ndarray:
        """Concatenated state and mask representation."""
        return np.concatenate([self.state_vector, self.mask_vector])


@dataclass
class EncodedGoal:
    """Vector representation of a goal specification G."""
    goal_vector: np.ndarray   # Target values in d_state
    mask_vector: np.ndarray   # 1 if variable is in goal conditions, else 0
    schema: DomainSchema
    raw_goal: Goal

    @property
    def vector(self) -> np.ndarray:
        return np.concatenate([self.goal_vector, self.mask_vector])


@dataclass
class EncodedCapability:
    """
    Structured Vector Representation of a Capability C_i:
    phi(C) = [v_pre, m_pre, v_eff, m_eff, v_in, v_out, v_type, v_mech, v_res, v_ops]^T
    """
    name: str
    v_pre: np.ndarray    # Precondition target values (d_state)
    m_pre: np.ndarray    # Precondition indicator mask (d_state)
    v_eff: np.ndarray    # Effect target values (d_state)
    m_eff: np.ndarray    # Effect modification mask (d_state)
    v_in: np.ndarray     # Input requirement vector (d_io)
    v_out: np.ndarray    # Output production vector (d_io)
    v_type: np.ndarray   # Capability type one-hot (d_type)
    v_mech: np.ndarray   # Mechanism signature vector (d_mech)
    v_res: np.ndarray    # Resource requirement mask (d_res)
    v_ops: np.ndarray    # Operational QoS vector (d_ops=7)
    
    schema: DomainSchema
    raw_capability: Capability

    @property
    def vector(self) -> np.ndarray:
        """Full concatenated embedding vector in R^D."""
        return np.concatenate([
            self.v_pre,
            self.m_pre,
            self.v_eff,
            self.m_eff,
            self.v_in,
            self.v_out,
            self.v_type,
            self.v_mech,
            self.v_res,
            self.v_ops,
        ])

    @property
    def functional_vector(self) -> np.ndarray:
        """Subvector containing purely functional behavior (pre, eff, in, out)."""
        return np.concatenate([
            self.v_pre,
            self.m_pre,
            self.v_eff,
            self.m_eff,
            self.v_in,
            self.v_out,
        ])

    @property
    def operational_vector(self) -> np.ndarray:
        """Subvector containing operational attributes (ops, res)."""
        return np.concatenate([self.v_ops, self.v_res])

    @property
    def implementation_vector(self) -> np.ndarray:
        """Subvector capturing mechanism and execution type."""
        return np.concatenate([self.v_type, self.v_mech])


class CapabilityEncoder:
    """
    Formal Encoder mapping States, Goals, and Capabilities into R^D.
    """
    def __init__(self, schema: DomainSchema):
        self.schema = schema

    def _val_to_scalar(self, val: Any) -> float:
        """Encodes primitive or categorical values to deterministic scalar coordinates."""
        if val is None:
            return 0.0
        if isinstance(val, bool):
            return 1.0 if val else -1.0
        if isinstance(val, (int, float)):
            # Numerical values scaled symmetrically
            return float(val)
        if isinstance(val, str):
            val_upper = val.upper()
            if val_upper in ("TRUE", "YES", "SUCCESS", "DONE", "COMPLETED", "CREATED"):
                return 1.0
            if val_upper in ("FALSE", "NO", "FAILED", "ERROR", "NOT_STARTED"):
                return -1.0
            # Deterministic categorical hashing to [-1, 1]
            h = int(hashlib.md5(val.encode("utf-8")).hexdigest()[:8], 16)
            return float((h % 1000) / 500.0 - 1.0)
        if isinstance(val, tuple) and len(val) == 2:
            # Predicate comparison e.g. (">", 0) -> target val + offset
            op, target = val
            base = self._val_to_scalar(target)
            offset = 0.1 if ">" in op else (-0.1 if "<" in op else 0.0)
            return base + offset
        return 1.0

    def encode_state(self, state: State) -> EncodedState:
        """phi_S: S -> R^{d_state}"""
        d = self.schema.d_state
        s_vec = np.zeros(d, dtype=np.float64)
        m_vec = np.zeros(d, dtype=np.float64)

        for var, val in state.variables.items():
            if var in self.schema.var_to_idx:
                idx = self.schema.var_to_idx[var]
                s_vec[idx] = self._val_to_scalar(val)
                m_vec[idx] = 1.0

        return EncodedState(
            state_vector=s_vec,
            mask_vector=m_vec,
            schema=self.schema,
            raw_state=state,
        )

    def encode_goal(self, goal: Goal) -> EncodedGoal:
        """phi_G: G -> R^{d_state}"""
        d = self.schema.d_state
        g_vec = np.zeros(d, dtype=np.float64)
        m_vec = np.zeros(d, dtype=np.float64)

        for var, val in goal.conditions.items():
            if var in self.schema.var_to_idx:
                idx = self.schema.var_to_idx[var]
                g_vec[idx] = self._val_to_scalar(val)
                m_vec[idx] = 1.0

        return EncodedGoal(
            goal_vector=g_vec,
            mask_vector=m_vec,
            schema=self.schema,
            raw_goal=goal,
        )

    def _encode_io(self, items: List[Any], is_input: bool = True) -> np.ndarray:
        """Encodes input or output specifications into R^{d_io}."""
        d = self.schema.d_io
        vec = np.zeros(d, dtype=np.float64)
        
        num_names = len(self.schema.data_names)
        for item in items:
            name = item.name
            dtype = item.data_type
            if name in self.schema.data_name_to_idx:
                name_idx = self.schema.data_name_to_idx[name]
                # If required input, weight higher (+1.0), else (+0.5)
                w = 1.0 if (not is_input or getattr(item, "required", True)) else 0.5
                vec[name_idx] = w
            if dtype in self.schema.type_to_idx:
                type_idx = num_names + self.schema.type_to_idx[dtype]
                vec[type_idx] = 1.0

        return vec

    def _encode_mechanism(self, mech: Optional[ExecutionMechanism]) -> np.ndarray:
        """Encodes execution mechanism properties into R^{d_mech}."""
        d = self.schema.d_mech
        vec = np.zeros(d, dtype=np.float64)
        if mech is None:
            return vec

        # Features: HTTP method / DB op / GUI action / trigger / handler
        props = mech.properties
        # 1. Action/Method feature
        action_str = str(props.get("method") or props.get("operation") or props.get("action") or props.get("trigger") or "")
        if action_str:
            h = int(hashlib.md5(action_str.encode()).hexdigest()[:4], 16) % 100
            vec[0] = (h / 50.0) - 1.0
        # 2. Target/Endpoint/Table feature
        target_str = str(props.get("endpoint") or props.get("table") or props.get("component") or props.get("handler") or "")
        if target_str:
            h = int(hashlib.md5(target_str.encode()).hexdigest()[:4], 16) % 100
            vec[1] = (h / 50.0) - 1.0
        # 3. Synchronous vs Asynchronous indicator
        is_async = 1.0 if props.get("async", False) or mech.mechanism_type in (CapabilityType.EVENT, CapabilityType.MESSAGE) else 0.0
        vec[2] = is_async
        # 4. Idempotency indicator
        is_idempotent = 1.0 if props.get("idempotent", False) or props.get("method") in ("GET", "PUT", "DELETE") else 0.0
        vec[3] = is_idempotent
        # 5-7. Property hash distribution for remaining attributes
        for i, (k, v) in enumerate(props.items()):
            pos = 4 + (i % (d - 4))
            h = int(hashlib.md5(f"{k}:{v}".encode()).hexdigest()[:4], 16) % 100
            vec[pos] = (h / 50.0) - 1.0
        return vec

    def _encode_operational(self, ops: OperationalProfile) -> np.ndarray:
        """
        Operational attributes vector (d_ops=7):
        [time_norm, cost_norm, res_cost_norm, risk, energy_norm, -ln(reliability), availability]
        """
        vec = np.zeros(7, dtype=np.float64)
        # 1. Normalized time (e.g. logarithmic / scaled by 1000ms)
        vec[0] = math.log1p(max(0.0, ops.execution_time_ms)) / 10.0
        # 2. Monetary cost
        vec[1] = max(0.0, ops.monetary_cost)
        # 3. Resource cost
        vec[2] = max(0.0, ops.resource_cost)
        # 4. Risk in [0, 1]
        vec[3] = np.clip(ops.risk, 0.0, 1.0)
        # 5. Energy cost
        vec[4] = max(0.0, ops.energy_cost)
        # 6. Additive negative log-reliability: -ln(Rel)
        rel = np.clip(ops.reliability, 1e-6, 1.0)
        vec[5] = -math.log(rel)
        # 7. Availability in [0, 1]
        vec[6] = np.clip(ops.availability, 0.0, 1.0)
        return vec

    def encode_capability(self, cap: Capability) -> EncodedCapability:
        """phi_C: C -> R^D"""
        d_s = self.schema.d_state
        
        # Preconditions
        v_pre = np.zeros(d_s, dtype=np.float64)
        m_pre = np.zeros(d_s, dtype=np.float64)
        for var, val in cap.preconditions.items():
            if var in self.schema.var_to_idx:
                idx = self.schema.var_to_idx[var]
                v_pre[idx] = self._val_to_scalar(val)
                m_pre[idx] = 1.0

        # Effects
        v_eff = np.zeros(d_s, dtype=np.float64)
        m_eff = np.zeros(d_s, dtype=np.float64)
        for var, val in cap.effects.items():
            if var in self.schema.var_to_idx:
                idx = self.schema.var_to_idx[var]
                v_eff[idx] = self._val_to_scalar(val)
                m_eff[idx] = 1.0

        # Inputs and Outputs
        v_in = self._encode_io(cap.inputs, is_input=True)
        v_out = self._encode_io(cap.outputs, is_input=False)

        # Type (one-hot)
        v_type = np.zeros(self.schema.d_type, dtype=np.float64)
        if cap.cap_type.value in self.schema.cap_type_to_idx:
            v_type[self.schema.cap_type_to_idx[cap.cap_type.value]] = 1.0

        # Mechanism
        v_mech = self._encode_mechanism(cap.mechanism)

        # Resources (multi-hot)
        v_res = np.zeros(self.schema.d_res, dtype=np.float64)
        for r in cap.resources:
            if r in self.schema.resource_to_idx:
                v_res[self.schema.resource_to_idx[r]] = 1.0

        # Operational
        v_ops = self._encode_operational(cap.operational_profile)

        return EncodedCapability(
            name=cap.name,
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
            raw_capability=cap,
        )
