"""
embedding.py
============
Structured Vector Embedding System for Formal States, Goals, and Capabilities.
Implements phi_C : C -> R^d, phi_S : S -> R^ds, phi_G : G -> R^dg without black-box NLP models.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from models import (
    Capability, CompositeCapability, State, Goal,
    CapabilityType, Precondition, Effect, Resource, Constraint, QualityAttributes
)


class EmbeddingSchema:
    """
    Central deterministic feature catalog defining the dimensional layout
    and slot indices for all subspaces.
    """
    # 1. Capability Types (9 dimensions)
    CAPABILITY_TYPES: List[str] = [
        "API", "DATABASE", "GUI", "EVENT", "FUNCTION",
        "FILE", "COMPUTATION", "MESSAGE", "SERVICE"
    ]

    # 2. Data Entity Identifiers for Inputs and Outputs (17 dimensions)
    DATA_ENTITIES: List[str] = [
        "cart_id", "order_id", "payment_details", "payment_receipt",
        "customer_id", "user_id", "report_type", "report_file",
        "user_profile", "profile_data", "inventory_status",
        "notification_payload", "notification_receipt", "auth_token",
        "invoice_pdf", "audio_stream", "track_id"
    ]

    # 3. State Condition Variables (17 dimensions)
    STATE_VARIABLES: List[str] = [
        "User.authenticated",
        "User.role:ADMIN",
        "User.role:CUSTOMER",
        "Cart.exists",
        "Cart.item_count_positive",
        "Cart.locked",
        "Order.exists",
        "Order.status:CREATED",
        "Order.status:PAID",
        "Payment.status:NOT_STARTED",
        "Payment.status:SUCCESS",
        "Inventory.available",
        "Invoice.generated",
        "Notification.sent",
        "Profile.updated",
        "Report.generated",
        "Music.playing"
    ]

    # 4. System Resources (8 dimensions)
    RESOURCES: List[str] = [
        "Database", "PaymentGateway", "Network", "EmailService",
        "FileSystem", "GPU", "AuthToken", "AudioDevice"
    ]

    # 5. Domain Constraints (7 dimensions)
    CONSTRAINTS: List[str] = [
        "authenticated_user", "valid_inventory", "cart_has_items",
        "transaction_limit", "rate_limit", "valid_recipient",
        "db_connection_pool"
    ]

    # 6. Execution Mechanism Categories (10 dimensions)
    MECHANISM_TYPES: List[str] = [
        "FUNCTION_CALL", "REST_API", "MESSAGE_QUEUE",
        "DATABASE_INSERT", "MICROSERVICE", "FILE_IO",
        "UI_COMPONENT", "BATCH_JOB", "AUDIO_STREAM", "GUI_INTERACTION"
    ]

    # Operational attribute scaling bounds (6 dimensions: cost, time, res_cost, risk, rel, avail)
    MAX_MONETARY_COST = 1.0       # USD
    MAX_EXECUTION_TIME_MS = 2000.0 # ms
    MAX_RESOURCE_COST = 10.0      # units


class CapabilityEmbedder:
    """
    Deterministic mathematical encoder phi_C : C -> R^d.
    Partitions vector space into 9 interpretable subspaces:
    v = [ v_type | v_input | v_output | v_pre | v_eff | v_res | v_con | v_ops | v_mech ]
    """

    def __init__(self, schema: Optional[EmbeddingSchema] = None):
        self.schema = schema or EmbeddingSchema()

        # Compute subspace slice dimensions
        self.d_type = len(self.schema.CAPABILITY_TYPES)
        self.d_in = len(self.schema.DATA_ENTITIES)
        self.d_out = len(self.schema.DATA_ENTITIES)
        self.d_pre = len(self.schema.STATE_VARIABLES)
        self.d_eff = len(self.schema.STATE_VARIABLES)
        self.d_res = len(self.schema.RESOURCES)
        self.d_con = len(self.schema.CONSTRAINTS)
        self.d_ops = 6  # cost, time, res_cost, risk, rel, avail
        self.d_mech = len(self.schema.MECHANISM_TYPES)

        self.total_dim = (
            self.d_type + self.d_in + self.d_out + self.d_pre +
            self.d_eff + self.d_res + self.d_con + self.d_ops + self.d_mech
        )

        # Slice boundaries for easy subspace extraction
        idx = 0
        self.slice_type = slice(idx, idx + self.d_type); idx += self.d_type
        self.slice_in = slice(idx, idx + self.d_in); idx += self.d_in
        self.slice_out = slice(idx, idx + self.d_out); idx += self.d_out
        self.slice_pre = slice(idx, idx + self.d_pre); idx += self.d_pre
        self.slice_eff = slice(idx, idx + self.d_eff); idx += self.d_eff
        self.slice_res = slice(idx, idx + self.d_res); idx += self.d_res
        self.slice_con = slice(idx, idx + self.d_con); idx += self.d_con
        self.slice_ops = slice(idx, idx + self.d_ops); idx += self.d_ops
        self.slice_mech = slice(idx, idx + self.d_mech); idx += self.d_mech

    def encode_type(self, cap_type: CapabilityType) -> np.ndarray:
        """One-hot vector for capability type Ti."""
        vec = np.zeros(self.d_type, dtype=np.float64)
        type_str = cap_type.value if hasattr(cap_type, "value") else str(cap_type)
        if type_str in self.schema.CAPABILITY_TYPES:
            vec[self.schema.CAPABILITY_TYPES.index(type_str)] = 1.0
        return vec

    def encode_inputs(self, inputs: List[Any]) -> np.ndarray:
        """Multi-hot vector for input data requirements Ii (1.0 = required, 0.5 = optional)."""
        vec = np.zeros(self.d_in, dtype=np.float64)
        for inp in inputs:
            name = inp.name if hasattr(inp, "name") else str(inp)
            req = inp.required if hasattr(inp, "required") else True
            if name in self.schema.DATA_ENTITIES:
                idx = self.schema.DATA_ENTITIES.index(name)
                vec[idx] = 1.0 if req else 0.5
        return vec

    def encode_outputs(self, outputs: List[Any]) -> np.ndarray:
        """Multi-hot vector for produced output specifications Oi."""
        vec = np.zeros(self.d_out, dtype=np.float64)
        for out in outputs:
            name = out.name if hasattr(out, "name") else str(out)
            if name in self.schema.DATA_ENTITIES:
                idx = self.schema.DATA_ENTITIES.index(name)
                vec[idx] = 1.0
        return vec

    def encode_preconditions(self, preconditions: List[Precondition]) -> np.ndarray:
        """
        Signed precondition predicate vector Pi aligned with state variables:
        +1.0 if requires True, -1.0 if requires False, target encoding for categorical,
        0.0 if unconstrained.
        """
        vec = np.zeros(self.d_pre, dtype=np.float64)
        for p in preconditions:
            var = p.variable
            val = p.value
            op = p.operator

            # Boolean variable checks
            if var in self.schema.STATE_VARIABLES:
                idx = self.schema.STATE_VARIABLES.index(var)
                if op == "==":
                    vec[idx] = 1.0 if val is True else (-1.0 if val is False else 0.5)
                elif op == "!=":
                    vec[idx] = -1.0 if val is True else 1.0
            elif var == "Cart.item_count" and op in [">", ">="] and val >= 0:
                slot = "Cart.item_count_positive"
                if slot in self.schema.STATE_VARIABLES:
                    vec[self.schema.STATE_VARIABLES.index(slot)] = 1.0
            else:
                # Categorical or compound mapping
                comp_key = f"{var}:{val}"
                if comp_key in self.schema.STATE_VARIABLES:
                    idx = self.schema.STATE_VARIABLES.index(comp_key)
                    vec[idx] = 1.0 if op == "==" else -1.0
        return vec

    def encode_effects(self, effects: List[Effect]) -> np.ndarray:
        """
        State transition delta vector Delta S for effects Ei:
        +1.0 for newly activated conditions, -1.0 for deactivated conditions.
        """
        vec = np.zeros(self.d_eff, dtype=np.float64)
        for e in effects:
            var = e.variable
            val = e.value
            op = e.operation

            if op == "DELETE":
                if var in self.schema.STATE_VARIABLES:
                    vec[self.schema.STATE_VARIABLES.index(var)] = -1.0
                continue

            if var in self.schema.STATE_VARIABLES:
                idx = self.schema.STATE_VARIABLES.index(var)
                vec[idx] = 1.0 if val is True else (-1.0 if val is False else 0.5)
            elif var == "Cart.item_count":
                slot = "Cart.item_count_positive"
                if slot in self.schema.STATE_VARIABLES:
                    vec[self.schema.STATE_VARIABLES.index(slot)] = 1.0 if val > 0 else -1.0
            else:
                comp_key = f"{var}:{val}"
                if comp_key in self.schema.STATE_VARIABLES:
                    idx = self.schema.STATE_VARIABLES.index(comp_key)
                    vec[idx] = 1.0
                # If setting a categorical state (e.g. Order.status:PAID), reset opposing statuses
                if var == "Order.status":
                    for alt in ["CREATED", "PAID"]:
                        alt_key = f"Order.status:{alt}"
                        if alt_key in self.schema.STATE_VARIABLES and alt != val:
                            vec[self.schema.STATE_VARIABLES.index(alt_key)] = -0.5
                elif var == "Payment.status":
                    for alt in ["NOT_STARTED", "SUCCESS"]:
                        alt_key = f"Payment.status:{alt}"
                        if alt_key in self.schema.STATE_VARIABLES and alt != val:
                            vec[self.schema.STATE_VARIABLES.index(alt_key)] = -0.5
        return vec

    def encode_resources(self, resources: List[Resource]) -> np.ndarray:
        """Multi-hot normalized vector for required hardware/software resources Ri."""
        vec = np.zeros(self.d_res, dtype=np.float64)
        for r in resources:
            name = r.name if hasattr(r, "name") else str(r)
            if name in self.schema.RESOURCES:
                idx = self.schema.RESOURCES.index(name)
                qty = r.quantity if hasattr(r, "quantity") else 1.0
                vec[idx] = min(1.0, qty / 2.0)
        return vec

    def encode_constraints(self, constraints: List[Constraint]) -> np.ndarray:
        """Constraint vector Ki encoding applicability conditions."""
        vec = np.zeros(self.d_con, dtype=np.float64)
        for c in constraints:
            name = c.name if hasattr(c, "name") else str(c)
            if name in self.schema.CONSTRAINTS:
                idx = self.schema.CONSTRAINTS.index(name)
                vec[idx] = 1.0
        return vec

    def encode_operational(self, quality: QualityAttributes, reliability: float, availability: float) -> np.ndarray:
        """
        Normalized operational properties vector:
        [ monetary_cost_norm, exec_time_norm, resource_cost_norm, risk, reliability, availability ]
        Uses bounded log and min-max scaling to prevent single feature dominance.
        """
        # 1. Monetary cost normalized via log(1+c)/log(1+c_max)
        norm_cost = np.log1p(max(0.0, quality.monetary_cost)) / np.log1p(self.schema.MAX_MONETARY_COST)
        norm_cost = float(np.clip(norm_cost, 0.0, 1.0))

        # 2. Execution time normalized linear scale
        norm_time = float(np.clip(quality.execution_time_ms / self.schema.MAX_EXECUTION_TIME_MS, 0.0, 1.0))

        # 3. Resource cost normalized
        norm_res_cost = float(np.clip(quality.resource_cost / self.schema.MAX_RESOURCE_COST, 0.0, 1.0))

        # 4. Risk in [0, 1]
        norm_risk = float(np.clip(quality.risk, 0.0, 1.0))

        # 5. Reliability in [0, 1]
        norm_rel = float(np.clip(reliability, 0.0, 1.0))

        # 6. Availability in [0, 1]
        norm_avail = float(np.clip(availability, 0.0, 1.0))

        return np.array([norm_cost, norm_time, norm_res_cost, norm_risk, norm_rel, norm_avail], dtype=np.float64)

    def encode_mechanism(self, mechanism: Any) -> np.ndarray:
        """One-hot vector for execution mechanism type Mi."""
        vec = np.zeros(self.d_mech, dtype=np.float64)
        mech_type = getattr(mechanism, "mechanism_type", str(mechanism))
        if mech_type in self.schema.MECHANISM_TYPES:
            idx = self.schema.MECHANISM_TYPES.index(mech_type)
            vec[idx] = 1.0
        return vec

    def encode_capability(self, capability: Capability) -> np.ndarray:
        """
        Full capability embedding: phi_C : C -> R^d.
        Concatenates all 9 structured subspaces into a fixed d-dimensional vector.
        """
        v_type = self.encode_type(capability.capability_type)
        v_in = self.encode_inputs(capability.inputs)
        v_out = self.encode_outputs(capability.outputs)
        v_pre = self.encode_preconditions(capability.preconditions)
        v_eff = self.encode_effects(capability.effects)
        v_res = self.encode_resources(capability.resources)
        v_con = self.encode_constraints(capability.constraints)
        v_ops = self.encode_operational(capability.quality, capability.reliability, capability.availability)
        v_mech = self.encode_mechanism(capability.mechanism)

        return np.concatenate([
            v_type, v_in, v_out, v_pre, v_eff, v_res, v_con, v_ops, v_mech
        ]).astype(np.float64)

    def get_subspaces(self, vec: np.ndarray) -> Dict[str, np.ndarray]:
        """Extracts individual named subspaces from an encoded capability vector."""
        return {
            "type": vec[self.slice_type],
            "input": vec[self.slice_in],
            "output": vec[self.slice_out],
            "precondition": vec[self.slice_pre],
            "effect": vec[self.slice_eff],
            "resource": vec[self.slice_res],
            "constraint": vec[self.slice_con],
            "operational": vec[self.slice_ops],
            "mechanism": vec[self.slice_mech]
        }

    def get_functional_subvector(self, vec: np.ndarray) -> np.ndarray:
        """Returns functional subvector: Inputs + Outputs + Preconditions + Effects."""
        return np.concatenate([
            vec[self.slice_in],
            vec[self.slice_out],
            vec[self.slice_pre],
            vec[self.slice_eff]
        ])

    def get_operational_subvector(self, vec: np.ndarray) -> np.ndarray:
        """Returns operational subvector: Resources + Constraints + Operational Metrics."""
        return np.concatenate([
            vec[self.slice_res],
            vec[self.slice_con],
            vec[self.slice_ops]
        ])


class StateEmbedder:
    """
    Mathematical encoder phi_S : S -> R^ds.
    Maps system state variables into continuous vector space aligned with effect & precondition spaces.
    """

    def __init__(self, schema: Optional[EmbeddingSchema] = None):
        self.schema = schema or EmbeddingSchema()
        self.dim = len(self.schema.STATE_VARIABLES)

    def encode_state(self, state: State) -> np.ndarray:
        """
        Encodes state dictionary into vector:
        +1.0 for active/True condition, -1.0 for inactive/False, 0.0 if unspecified.
        """
        vec = np.zeros(self.dim, dtype=np.float64)
        for i, var_slot in enumerate(self.schema.STATE_VARIABLES):
            if ":" in var_slot:
                var_name, expected_val = var_slot.split(":", 1)
                actual_val = state.get(var_name)
                if actual_val is not None:
                    vec[i] = 1.0 if str(actual_val) == expected_val else -1.0
            elif var_slot == "Cart.item_count_positive":
                cnt = state.get("Cart.item_count", 0)
                vec[i] = 1.0 if cnt > 0 else -1.0
            else:
                val = state.get(var_slot)
                if val is not None:
                    vec[i] = 1.0 if val is True else (-1.0 if val is False else 0.0)
        return vec


class GoalEmbedder:
    """
    Mathematical encoder phi_G : G -> R^dg.
    Encodes goal specifications into vector space compatible with state and effect vectors.
    """

    def __init__(self, schema: Optional[EmbeddingSchema] = None):
        self.schema = schema or EmbeddingSchema()
        self.dim = len(self.schema.STATE_VARIABLES)

    def encode_goal(self, goal: Goal) -> np.ndarray:
        """
        Encodes goal conditions into target state vector:
        +1.0 for required positive predicates, -1.0 for required negative, 0.0 for unconstrained.
        """
        vec = np.zeros(self.dim, dtype=np.float64)
        for cond in goal.conditions:
            var = cond.variable
            val = cond.value
            op = cond.operator

            if ":" in var or (isinstance(val, str) and val not in ["True", "False"]):
                comp_key = f"{var}:{val}"
                if comp_key in self.schema.STATE_VARIABLES:
                    idx = self.schema.STATE_VARIABLES.index(comp_key)
                    vec[idx] = 1.0 if op == "==" else -1.0
            elif var in self.schema.STATE_VARIABLES:
                idx = self.schema.STATE_VARIABLES.index(var)
                if op == "==":
                    vec[idx] = 1.0 if val is True else (-1.0 if val is False else 0.5)
                elif op == "!=":
                    vec[idx] = -1.0 if val is True else 1.0
        return vec


def cosine_similarity(x: np.ndarray, y: np.ndarray, epsilon: float = 1e-12) -> float:
    """
    Safe mathematical cosine similarity:
    sim(x, y) = (x . y) / (||x||_2 ||y||_2 + eps)
    Handles zero vectors safely by returning 0.0.
    """
    norm_x = float(np.linalg.norm(x))
    norm_y = float(np.linalg.norm(y))
    if norm_x < epsilon or norm_y < epsilon:
        return 0.0
    dot_val = float(np.dot(x, y))
    sim = dot_val / (norm_x * norm_y)
    return float(np.clip(sim, -1.0, 1.0))


def compute_goal_relevance(
    capability: Capability,
    goal: Goal,
    state: State,
    cap_embedder: CapabilityEmbedder,
    goal_embedder: GoalEmbedder,
    state_embedder: StateEmbedder
) -> Tuple[float, float, float]:
    """
    Calculates goal relevance of a capability from both vector projection and symbolic effect matching:
    1. Symbolic goal coverage: fraction of unsatisfied goal predicates resolved by capability effects.
    2. Vector alignment score: cosine similarity between effect vector and remaining goal gap vector (Delta G = phi_G - phi_S).
    3. Combined goal relevance score in [0, 1].
    """
    # 1. Symbolic coverage
    unmet_goal_conditions = [c for c in goal.conditions if not c.evaluate(state.variables)]
    if not unmet_goal_conditions:
        # Goal is already fully satisfied
        return 1.0, 1.0, 1.0

    satisfied_by_cap = 0
    simulated_state = dict(state.variables)
    for eff in capability.effects:
        simulated_state = eff.apply(simulated_state)

    for cond in unmet_goal_conditions:
        if cond.evaluate(simulated_state):
            satisfied_by_cap += 1

    sym_coverage = satisfied_by_cap / len(unmet_goal_conditions)

    # 2. Vector alignment with goal gap (restricted strictly to dimensions in Goal)
    v_goal = goal_embedder.encode_goal(goal)
    v_state = state_embedder.encode_state(state)
    goal_mask = (v_goal != 0.0)
    v_gap = np.where(goal_mask, np.maximum(0.0, v_goal - v_state), 0.0)

    cap_vec = cap_embedder.encode_capability(capability)
    v_eff = cap_embedder.get_subspaces(cap_vec)["effect"]

    vec_alignment = 0.0
    if np.linalg.norm(v_gap) > 1e-6 and np.linalg.norm(v_eff) > 1e-6:
        raw_cos = cosine_similarity(v_eff, v_gap)
        vec_alignment = max(0.0, raw_cos)

    # Combined score: weighted sum of symbolic goal resolution and vector alignment
    combined_score = 0.60 * sym_coverage + 0.40 * vec_alignment
    return float(combined_score), float(sym_coverage), float(vec_alignment)
