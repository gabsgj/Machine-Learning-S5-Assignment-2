"""
Vector Embedding Architecture for Capability Composition.
Dual-Faceted Partitioned Vector Space (DF-PVS).
Assignment 2: Design of a Vector Embedding for Capability Composition.
Student: Melita Mariam Mathew
Registration Number: TCCR24CS046
"""

from typing import Dict, List, Tuple, Any, Optional, Union
import numpy as np
import math

from src.models import (
    Capability,
    CompositeCapability,
    State,
    Goal,
    CapabilityType,
    ExecutionMechanism,
    OperationalAttributes,
    StateCondition,
    InputSpec,
    OutputSpec,
)


class CapabilityEmbeddingSpace:
    """
    Dual-Faceted Partitioned Vector Space (DF-PVS) for Capability Modeling.
    
    Partitions the vector space into semantically aligned, functionally dedicated subspaces:
    1. Precondition Subspace (d_state): Encodes required state assertions.
    2. Effect Subspace (d_state): Encodes state mutations/assertions produced.
    3. Input Subspace (d_io): Encodes required data types/parameters.
    4. Output Subspace (d_io): Encodes produced data types/results.
    5. Delta Subspace (d_state): Encodes net state translation vector (v_eff - v_pre).
    6. Mechanism Subspace (d_mech): Encodes capability type & execution mechanism details.
    7. Operational Subspace (d_ops): Encodes cost, latency, risk, -ln(reliability), availability.
    """

    def __init__(
        self,
        state_variables: List[str],
        io_vocab: List[str],
        type_vocab: Optional[List[str]] = None,
        max_time_ms: float = 2000.0,
        max_cost_money: float = 1.0,
        max_resource: float = 10.0,
    ):
        self.state_variables = sorted(list(set(state_variables)))
        self.state_var_to_idx = {var: i for i, var in enumerate(self.state_variables)}
        self.d_state = len(self.state_variables)

        self.io_vocab = sorted(list(set(io_vocab)))
        self.io_to_idx = {name: i for i, name in enumerate(self.io_vocab)}
        self.d_io = len(self.io_vocab)

        self.type_vocab = (
            type_vocab
            if type_vocab is not None
            else [t.value for t in CapabilityType]
        )
        self.type_to_idx = {t: i for i, t in enumerate(self.type_vocab)}
        self.d_type = len(self.type_vocab)

        # Mechanism extra features: endpoint/table/component flags (5 dimensions)
        self.d_mech_extra = 5
        self.d_mech = self.d_type + self.d_mech_extra

        # Operational subspace: [norm_time, norm_cost, norm_resource, risk, neg_log_rel, avail]
        self.d_ops = 6
        self.max_time_ms = max_time_ms
        self.max_cost_money = max_cost_money
        self.max_resource = max_resource

        # Subspace dimension offsets
        self.d_total = (
            self.d_state    # v_pre
            + self.d_state  # v_eff
            + self.d_io     # v_in
            + self.d_io     # v_out
            + self.d_state  # v_delta
            + self.d_mech   # v_mech
            + self.d_ops    # v_ops
        )

        # Precompute slice boundaries
        self.idx_pre = slice(0, self.d_state)
        self.idx_eff = slice(self.d_state, 2 * self.d_state)
        self.idx_in = slice(2 * self.d_state, 2 * self.d_state + self.d_io)
        self.idx_out = slice(2 * self.d_state + self.d_io, 2 * self.d_state + 2 * self.d_io)
        self.idx_delta = slice(2 * self.d_state + 2 * self.d_io, 3 * self.d_state + 2 * self.d_io)
        self.idx_mech = slice(3 * self.d_state + 2 * self.d_io, 3 * self.d_state + 2 * self.d_io + self.d_mech)
        self.idx_ops = slice(3 * self.d_state + 2 * self.d_io + self.d_mech, self.d_total)

    def encode_state(self, state: State) -> np.ndarray:
        """
        Encode an application state into R^(d_state).
        Boolean True: +1.0
        Boolean False: -1.0
        Numeric/count: min(val / 10.0, 1.0)
        Categorical: hash or mapped enum value in [-1, 1]
        Unset/Unknown: 0.0
        """
        vec = np.zeros(self.d_state, dtype=np.float64)
        for var, val in state.variables.items():
            if var in self.state_var_to_idx:
                idx = self.state_var_to_idx[var]
                if isinstance(val, bool):
                    vec[idx] = 1.0 if val else -1.0
                elif isinstance(val, (int, float)):
                    vec[idx] = max(-1.0, min(1.0, float(val) / 5.0))
                elif isinstance(val, str):
                    # Categorical mapped to signed range
                    if val in ["SUCCESS", "CREATED", "CUSTOMER", "AUTHENTICATED", "COMPLETED", "TRUE"]:
                        vec[idx] = 1.0
                    elif val in ["FAILED", "CANCELLED", "NOT_STARTED", "FALSE"]:
                        vec[idx] = -1.0
                    else:
                        vec[idx] = 0.5
        return vec

    def encode_goal(self, goal: Goal) -> np.ndarray:
        """
        Encode a goal specification into R^(d_state).
        Specifies target states. Variables with no goal requirement are 0.0.
        """
        vec = np.zeros(self.d_state, dtype=np.float64)
        for cond in goal.conditions:
            if cond.variable in self.state_var_to_idx:
                idx = self.state_var_to_idx[cond.variable]
                if isinstance(cond.value, bool):
                    vec[idx] = 1.0 if cond.value else -1.0
                elif isinstance(cond.value, (int, float)):
                    vec[idx] = max(-1.0, min(1.0, float(cond.value) / 5.0))
                elif isinstance(cond.value, str):
                    if cond.value in ["SUCCESS", "CREATED", "CUSTOMER", "AUTHENTICATED", "COMPLETED"]:
                        vec[idx] = 1.0
                    elif cond.value in ["FAILED", "CANCELLED", "NOT_STARTED"]:
                        vec[idx] = -1.0
                    else:
                        vec[idx] = 0.5
        return vec

    def encode_capability(self, cap: Capability) -> np.ndarray:
        """
        Encode an atomic or composite capability into R^(d_total).
        Concatenates: [v_pre, v_eff, v_in, v_out, v_delta, v_mech, v_ops].
        """
        v_pre = np.zeros(self.d_state, dtype=np.float64)
        for p in cap.preconditions:
            if p.variable in self.state_var_to_idx:
                idx = self.state_var_to_idx[p.variable]
                if isinstance(p.value, bool):
                    v_pre[idx] = 1.0 if p.value else -1.0
                elif isinstance(p.value, (int, float)):
                    v_pre[idx] = 1.0 if p.value > 0 else -1.0
                elif isinstance(p.value, str):
                    v_pre[idx] = 1.0 if p.value in ["SUCCESS", "CREATED", "CUSTOMER", "AUTHENTICATED"] else -1.0

        v_eff = np.zeros(self.d_state, dtype=np.float64)
        for e in cap.effects:
            if e.variable in self.state_var_to_idx:
                idx = self.state_var_to_idx[e.variable]
                if isinstance(e.value, bool):
                    v_eff[idx] = 1.0 if e.value else -1.0
                elif isinstance(e.value, (int, float)):
                    v_eff[idx] = 1.0 if e.value > 0 else -1.0
                elif isinstance(e.value, str):
                    v_eff[idx] = 1.0 if e.value in ["SUCCESS", "CREATED", "CUSTOMER", "AUTHENTICATED"] else -1.0

        # Input vector
        v_in = np.zeros(self.d_io, dtype=np.float64)
        for inp in cap.inputs:
            # Check by name or data_type
            if inp.name in self.io_to_idx:
                v_in[self.io_to_idx[inp.name]] = 1.0
            if inp.data_type in self.io_to_idx:
                v_in[self.io_to_idx[inp.data_type]] = 1.0

        # Output vector
        v_out = np.zeros(self.d_io, dtype=np.float64)
        for out in cap.outputs:
            if out.name in self.io_to_idx:
                v_out[self.io_to_idx[out.name]] = 1.0
            if out.data_type in self.io_to_idx:
                v_out[self.io_to_idx[out.data_type]] = 1.0

        # Delta vector: transformation operator on state
        v_delta = v_eff - v_pre

        # Mechanism vector
        v_mech = np.zeros(self.d_mech, dtype=np.float64)
        type_str = cap.type.value if hasattr(cap.type, "value") else str(cap.type)
        if type_str in self.type_to_idx:
            v_mech[self.type_to_idx[type_str]] = 1.0

        if cap.mechanism:
            details = cap.mechanism.details
            # Flag 0: POST/INSERT/WRITE
            if details.get("method") == "POST" or details.get("operation") == "INSERT" or details.get("action") == "CLICK":
                v_mech[self.d_type + 0] = 1.0
            # Flag 1: GET/SELECT/READ
            if details.get("method") == "GET" or details.get("operation") == "SELECT":
                v_mech[self.d_type + 1] = 1.0
            # Flag 2: Asynchronous / Event trigger
            if "trigger" in details or type_str == CapabilityType.EVENT.value:
                v_mech[self.d_type + 2] = 1.0
            # Flag 3: GUI interactable
            if type_str == CapabilityType.GUI.value:
                v_mech[self.d_type + 3] = 1.0
            # Flag 4: Service composite
            if "composition_pipeline" in details:
                v_mech[self.d_type + 4] = 1.0

        # Operational vector: normalized
        ops = cap.operational
        norm_time = min(ops.time_ms / self.max_time_ms, 1.0)
        norm_cost = min(ops.cost_money / self.max_cost_money, 1.0)
        norm_resource = min(ops.resource_cost / self.max_resource, 1.0)
        risk = max(0.0, min(1.0, ops.risk))
        # Negative log-reliability: -ln(Rel) in [0, inf), for Rel=0.99 => ~0.010, additive!
        rel = max(1e-5, min(1.0, ops.reliability))
        neg_log_rel = -math.log(rel)
        avail = max(0.0, min(1.0, ops.availability))

        v_ops = np.array([norm_time, norm_cost, norm_resource, risk, neg_log_rel, avail], dtype=np.float64)

        return np.concatenate([v_pre, v_eff, v_in, v_out, v_delta, v_mech, v_ops])

    # -------------------------------------------------------------------------
    # Subspace Extractors
    # -------------------------------------------------------------------------
    def get_pre(self, vec: np.ndarray) -> np.ndarray:
        return vec[self.idx_pre]

    def get_eff(self, vec: np.ndarray) -> np.ndarray:
        return vec[self.idx_eff]

    def get_in(self, vec: np.ndarray) -> np.ndarray:
        return vec[self.idx_in]

    def get_out(self, vec: np.ndarray) -> np.ndarray:
        return vec[self.idx_out]

    def get_delta(self, vec: np.ndarray) -> np.ndarray:
        return vec[self.idx_delta]

    def get_mech(self, vec: np.ndarray) -> np.ndarray:
        return vec[self.idx_mech]

    def get_ops(self, vec: np.ndarray) -> np.ndarray:
        return vec[self.idx_ops]

    # -------------------------------------------------------------------------
    # Vector-level Composition
    # -------------------------------------------------------------------------
    def compose_vectors(self, v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
        """
        Algebraic vector-level composition of two capability embeddings:
        v_comp = compose(v1, v2) representing C_comp = C2 o C1 (C1 executed first, then C2).
        
        - Effects: C2 overrides C1 where C2 produces effects; C1 effects persist otherwise.
        - Preconditions: C1 preconditions + (C2 preconditions not satisfied by C1 effects).
        - Inputs: C1 inputs + (C2 inputs not supplied by C1 outputs).
        - Outputs: Union (elementwise max/or).
        - Delta: TransE-like state transformation operator (additive with masking).
        - Mechanism: Composite service mechanism.
        - Operational: Additive for time, cost, resource, risk, neg_log_rel; min for availability.
        """
        p1, e1 = self.get_pre(v1), self.get_eff(v1)
        p2, e2 = self.get_pre(v2), self.get_eff(v2)
        in1, out1 = self.get_in(v1), self.get_out(v1)
        in2, out2 = self.get_in(v2), self.get_out(v2)
        ops1, ops2 = self.get_ops(v1), self.get_ops(v2)

        # 1. Effects: C2 effects override C1 effects
        # Mask where e2 is active (abs(e2) > 0)
        e2_active = (np.abs(e2) > 1e-4).astype(np.float64)
        e_comp = e2 + (1.0 - e2_active) * e1

        # 2. Preconditions: C1 preconditions + unmet C2 preconditions
        # A precondition in C2 is unmet if e1 does not equal p2
        # If p2 has a requirement and e1 matches it (e1 * p2 > 0), unmet is 0
        unmet_p2 = np.zeros_like(p2)
        for i in range(len(p2)):
            if abs(p2[i]) > 1e-4:
                if abs(e1[i]) > 1e-4 and (e1[i] * p2[i] > 0):
                    # C1 established this precondition!
                    unmet_p2[i] = 0.0
                else:
                    unmet_p2[i] = p2[i]
        # Union with p1 (if p1 already has it, take max)
        p_comp = np.where(np.abs(p1) > 1e-4, p1, unmet_p2)

        # 3. Inputs: C1 inputs + (C2 inputs not provided by C1 outputs)
        unmet_in2 = np.maximum(0.0, in2 - out1)
        in_comp = np.maximum(in1, unmet_in2)

        # 4. Outputs: C1 outputs + C2 outputs
        out_comp = np.maximum(out1, out2)

        # 5. Delta: e_comp - p_comp
        delta_comp = e_comp - p_comp

        # 6. Mechanism: Composite service
        mech_comp = np.zeros(self.d_mech, dtype=np.float64)
        if CapabilityType.SERVICE.value in self.type_to_idx:
            mech_comp[self.type_to_idx[CapabilityType.SERVICE.value]] = 1.0
        mech_comp[self.d_type + 4] = 1.0  # composite pipeline flag

        # 7. Operational:
        # ops = [norm_time, norm_cost, norm_resource, risk, neg_log_rel, avail]
        time_comp = min(1.0, ops1[0] + ops2[0])
        cost_comp = min(1.0, ops1[1] + ops2[1])
        res_comp = min(1.0, ops1[2] + ops2[2])
        # Joint risk: 1 - (1 - r1)*(1 - r2)
        risk_comp = 1.0 - ((1.0 - ops1[3]) * (1.0 - ops2[3]))
        # Neg log rel is perfectly additive!
        rel_log_comp = ops1[4] + ops2[4]
        # Availability is bottleneck min
        avail_comp = min(ops1[5], ops2[5])
        ops_comp = np.array([time_comp, cost_comp, res_comp, risk_comp, rel_log_comp, avail_comp], dtype=np.float64)

        return np.concatenate([p_comp, e_comp, in_comp, out_comp, delta_comp, mech_comp, ops_comp])

    # -------------------------------------------------------------------------
    # Core Evaluation Functions: Compatibility, Similarity, Goal Relevance
    # -------------------------------------------------------------------------
    def compatibility(
        self,
        c1: Union[Capability, np.ndarray],
        c2: Union[Capability, np.ndarray],
    ) -> Dict[str, Any]:
        """
        Evaluate directional composability: can C1 lead to C2? (C1 -> C2)
        
        Evaluates:
        1. Precondition Satisfaction: Does E(C1) satisfy P(C2)?
        2. Precondition Violation/Conflict: Does E(C1) contradict P(C2)?
        3. Input-Output Satisfaction: Does O(C1) provide data required by I(C2)?
        
        Returns:
            {
                "compatibility_score": float in [-1.0, 1.0],
                "precondition_match_score": float in [0.0, 1.0],
                "conflict_penalty": float in [0.0, 1.0],
                "io_satisfaction_score": float in [0.0, 1.0],
                "is_compatible": bool,
                "reasons": List[str]
            }
        """
        v1 = self.encode_capability(c1) if isinstance(c1, Capability) else c1
        v2 = self.encode_capability(c2) if isinstance(c2, Capability) else c2

        e1 = self.get_eff(v1)
        p2 = self.get_pre(v2)
        out1 = self.get_out(v1)
        in2 = self.get_in(v2)

        p2_active = np.where(np.abs(p2) > 1e-4)[0]
        in2_active = np.where(np.abs(in2) > 1e-4)[0]

        matches = 0
        conflicts = 0
        unaddressed = 0
        reasons = []

        if len(p2_active) == 0:
            pre_score = 1.0
            reasons.append("C2 has no state preconditions.")
        else:
            for idx in p2_active:
                var_name = self.state_variables[idx]
                req_val = p2[idx]
                prod_val = e1[idx]

                if abs(prod_val) > 1e-4:
                    if prod_val * req_val > 0:
                        matches += 1
                        reasons.append(f"Precondition '{var_name}' satisfied by C1 effect.")
                    else:
                        conflicts += 1
                        reasons.append(f"CONFLICT: Precondition '{var_name}' requires {'True' if req_val > 0 else 'False'}, but C1 produces {'True' if prod_val > 0 else 'False'}.")
                else:
                    unaddressed += 1

            pre_score = matches / len(p2_active) if len(p2_active) > 0 else 1.0

        # Conflict penalty
        conflict_penalty = 1.0 if conflicts > 0 else 0.0

        # I/O satisfaction score
        if len(in2_active) == 0:
            io_score = 1.0
        else:
            io_matches = np.sum((in2[in2_active] > 0) & (out1[in2_active] > 0))
            io_score = float(io_matches / len(in2_active))
            if io_score > 0:
                reasons.append(f"I/O dependencies satisfied: {int(io_matches)}/{len(in2_active)} parameters.")

        # Composite directional compatibility score:
        # If there's an explicit contradiction, score drops to negative
        if conflicts > 0:
            comp_score = -1.0 * (conflicts / max(1, len(p2_active)))
            is_compatible = False
        else:
            # Positive compatibility is a blend of state precondition enablement and I/O coupling
            # If C2 has preconditions satisfied by C1, comp_score is high
            if matches > 0:
                comp_score = 0.6 * pre_score + 0.4 * io_score
                is_compatible = True
            elif len(p2_active) == 0:
                comp_score = 0.5 + 0.5 * io_score
                is_compatible = True
            else:
                # C1 neither satisfies nor contradicts C2's preconditions (independent/weakly compatible)
                comp_score = 0.1 * io_score
                is_compatible = False

        return {
            "compatibility_score": float(np.round(comp_score, 4)),
            "precondition_match_score": float(np.round(pre_score, 4)),
            "conflict_penalty": float(np.round(conflict_penalty, 4)),
            "io_satisfaction_score": float(np.round(io_score, 4)),
            "is_compatible": is_compatible,
            "reasons": reasons,
        }

    def similarity(
        self,
        c1: Union[Capability, np.ndarray],
        c2: Union[Capability, np.ndarray],
        mode: str = "functional",
    ) -> float:
        """
        Compare two capability embeddings.
        
        CRUCIAL PRINCIPLE: Similarity != Composability.
        Two capabilities with identical effects (e.g. CreateOrder API vs CreateOrder GUI)
        have similarity ~ 1.0, but they DO NOT compose with each other.
        
        Modes:
        - 'functional': Compares effects and preconditions (outcome alignment).
        - 'mechanism': Compares execution type and operational mechanism.
        - 'total': Weighted blend of functional and mechanism similarity.
        """
        v1 = self.encode_capability(c1) if isinstance(c1, Capability) else c1
        v2 = self.encode_capability(c2) if isinstance(c2, Capability) else c2

        e1, e2 = self.get_eff(v1), self.get_eff(v2)
        p1, p2 = self.get_pre(v1), self.get_pre(v2)
        m1, m2 = self.get_mech(v1), self.get_mech(v2)

        def cosine(a: np.ndarray, b: np.ndarray) -> float:
            na = np.linalg.norm(a)
            nb = np.linalg.norm(b)
            if na < 1e-8 and nb < 1e-8:
                return 1.0
            if na < 1e-8 or nb < 1e-8:
                return 0.0
            return float(np.dot(a, b) / (na * nb))

        sim_eff = cosine(e1, e2)
        sim_pre = cosine(p1, p2)
        sim_func = 0.7 * sim_eff + 0.3 * sim_pre
        sim_mech = cosine(m1, m2)

        if mode == "functional":
            return float(np.round(sim_func, 4))
        elif mode == "mechanism":
            return float(np.round(sim_mech, 4))
        elif mode == "total":
            return float(np.round(0.75 * sim_func + 0.25 * sim_mech, 4))
        else:
            raise ValueError(f"Unknown similarity mode: {mode}")

    def goal_relevance(
        self,
        cap: Union[Capability, np.ndarray],
        goal: Union[Goal, np.ndarray],
        current_state: Optional[Union[State, np.ndarray]] = None,
    ) -> float:
        """
        Measure how effectively capability 'cap' drives state towards goal 'goal'.
        
        Only variables explicitly constrained by the goal are considered.
        Variables not in the goal have 0 weight.
        
        For each variable k in Goal:
            target = v_goal[k]
            curr = s_vec[k] (or 0 if not provided)
            gap = target - curr (if current state already satisfies, gap is 0)
            contribution = eff[k] aligned with gap
        """
        v_cap = self.encode_capability(cap) if isinstance(cap, Capability) else cap
        v_goal = self.encode_goal(goal) if isinstance(goal, Goal) else goal
        eff = self.get_eff(v_cap)

        goal_mask = np.abs(v_goal) > 1e-4
        if not np.any(goal_mask):
            return 0.0

        if current_state is not None:
            s_vec = self.encode_state(current_state) if isinstance(current_state, State) else current_state
        else:
            s_vec = np.zeros_like(v_goal)

        score = 0.0
        total_possible = 0.0

        for idx in np.where(goal_mask)[0]:
            target = v_goal[idx]
            curr = s_vec[idx]
            eff_val = eff[idx]

            # Remaining gap between target and current state
            needed_delta = target - curr
            # Weight is the magnitude of the needed change
            weight = abs(needed_delta)
            if weight < 1e-4:
                # Already satisfied in current state
                weight = 1.0  # Maintain term weight

            total_possible += abs(target) * 2.0  # Maximum possible transition scale

            if abs(eff_val) > 1e-4:
                # Check alignment with target
                if eff_val * target > 0:
                    score += abs(eff_val) * 2.0  # Positive contribution to goal
                else:
                    score -= abs(eff_val) * 2.0  # Counter-productive to goal

        return float(np.round(score / max(1e-4, total_possible), 4))

