from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence
import numpy as np

from src.encoder import (
    BOOLEAN_VARS,
    CATEGORICAL_VARS,
    NUMERICAL_VARS,
    COND_DIM,
    CONSTRAINT_SLICE,
    EFFECT_SLICE,
    INPUT_SLICE,
    MECH_SLICE,
    OPS_SLICE,
    OUTPUT_SLICE,
    PRE_SLICE,
    RESOURCE_SLICE,
    TOTAL_DIM,
    encode_capability,
    encode_goal,
    _parse_bool_value,
)
from src.models import Capability, Goal, Predicate

# Block weights for functional similarity (must sum to 1.0)
BLOCK_WEIGHTS: dict[str, float] = {
    "effect": 0.25,
    "pre": 0.20,
    "input": 0.10,
    "output": 0.10,
    "constraint": 0.10,
    "resource": 0.10,
    "ops": 0.10,
    "mech": 0.05,
}

EPSILON = 1e-9


def canonical_var_name(name: str) -> str:
    """Normalize variable names to handle dot, snake, and camelCase aliases."""
    clean = name.lower().replace(".", "").replace("_", "")
    canonical_list = [
        "User.authenticated",
        "Cart.exists",
        "Cart.locked",
        "Order.exists",
        "Inventory.available",
        "Inventory.reserved",
        "Notification.sent",
        "Order.archived",
        "Payment.status",
        "Order.status",
        "User.role",
        "Cart.status",
        "Cart.item_count",
        "quantity",
    ]
    for canon in canonical_list:
        if clean == canon.lower().replace(".", "").replace("_", ""):
            return canon
    return name


def cosine_similarity(a: np.ndarray, b: np.ndarray, epsilon: float = EPSILON) -> float:
    """
    Compute safe cosine similarity between two vectors.
    Returns:
        1.0 if both vectors are zero
        0.0 if exactly one vector is zero
        dot(a, b) / (||a|| * ||b|| + epsilon) otherwise
    """
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))

    if norm_a == 0.0 and norm_b == 0.0:
        return 1.0
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    dot = float(np.dot(a, b))
    sim = dot / (norm_a * norm_b + epsilon)
    return float(np.clip(sim, -1.0, 1.0))


def similarity(cap_a: Capability | np.ndarray, cap_b: Capability | np.ndarray) -> float:
    """
    Compute symmetric functional similarity between two capabilities.
    Sim(C1, C2) = sum(w_b * cosine(block_a, block_b))
    """
    v_a = encode_capability(cap_a) if isinstance(cap_a, Capability) else cap_a
    v_b = encode_capability(cap_b) if isinstance(cap_b, Capability) else cap_b

    if len(v_a) != TOTAL_DIM or len(v_b) != TOTAL_DIM:
        raise ValueError(f"Vectors must have dimension {TOTAL_DIM}")

    slices = {
        "mech": MECH_SLICE,
        "input": INPUT_SLICE,
        "output": OUTPUT_SLICE,
        "pre": PRE_SLICE,
        "effect": EFFECT_SLICE,
        "constraint": CONSTRAINT_SLICE,
        "resource": RESOURCE_SLICE,
        "ops": OPS_SLICE,
    }

    total_sim = 0.0
    for block_name, weight in BLOCK_WEIGHTS.items():
        sl = slices[block_name]
        block_sim = cosine_similarity(v_a[sl], v_b[sl])
        total_sim += weight * block_sim

    return float(np.clip(total_sim, -1.0, 1.0))


def _extract_effect_vector(c: Capability | np.ndarray) -> np.ndarray:
    if isinstance(c, Capability):
        return encode_capability(c)[EFFECT_SLICE]
    if len(c) == TOTAL_DIM:
        return c[EFFECT_SLICE]
    if len(c) == COND_DIM:
        return c
    raise ValueError(f"Invalid effect vector dimension: {len(c)}")


def _extract_precondition_vector(c: Capability | np.ndarray) -> np.ndarray:
    if isinstance(c, Capability):
        return encode_capability(c)[PRE_SLICE]
    if len(c) == TOTAL_DIM:
        return c[PRE_SLICE]
    if len(c) == COND_DIM:
        return c
    raise ValueError(f"Invalid precondition vector dimension: {len(c)}")


def _extract_output_vector(c: Capability | np.ndarray) -> np.ndarray:
    if isinstance(c, Capability):
        return encode_capability(c)[OUTPUT_SLICE]
    if len(c) == TOTAL_DIM:
        return c[OUTPUT_SLICE]
    return c


def _extract_input_vector(c: Capability | np.ndarray) -> np.ndarray:
    if isinstance(c, Capability):
        return encode_capability(c)[INPUT_SLICE]
    if len(c) == TOTAL_DIM:
        return c[INPUT_SLICE]
    return c


def effect_precondition_alignment(
    producer: Capability | np.ndarray, consumer: Capability | np.ndarray
) -> float:
    """
    Directional effect -> precondition alignment:
    Align_EP = 1.0 if consumer precondition vector is zero
    otherwise: dot(eff_C1, pre_C2) / ||pre_C2||^2
    """
    eff = _extract_effect_vector(producer)
    pre = _extract_precondition_vector(consumer)

    norm_pre_sq = float(np.dot(pre, pre))
    if norm_pre_sq == 0.0:
        return 1.0

    dot = float(np.dot(eff, pre))
    return float(dot / norm_pre_sq)


def output_input_alignment(
    producer: Capability | np.ndarray, consumer: Capability | np.ndarray
) -> float:
    """
    Directional output -> input alignment:
    Align_OI = 1.0 if consumer input vector is zero
    otherwise: dot(out_C1, in_C2) / ||in_C2||^2
    """
    out = _extract_output_vector(producer)
    inp = _extract_input_vector(consumer)

    norm_in_sq = float(np.dot(inp, inp))
    if norm_in_sq == 0.0:
        return 1.0

    dot = float(np.dot(out, inp))
    return float(dot / norm_in_sq)


@dataclass
class CompatibilityScore:
    effect_precondition: float
    output_input: float
    vector_score: float
    availability_factor: float
    execution_score: float


@dataclass
class CompatibilityValidationResult:
    compatible: bool
    score: CompatibilityScore
    reasons: list[str] = field(default_factory=list)


def vector_compatibility(producer: Capability, consumer: Capability) -> CompatibilityScore:
    """Compute continuous vector compatibility score between producer and consumer."""
    align_ep = effect_precondition_alignment(producer, consumer)
    align_oi = output_input_alignment(producer, consumer)
    comp_vec = 0.6 * align_ep + 0.4 * align_oi
    avail_factor = float(producer.A * consumer.A)
    comp_exec = avail_factor * comp_vec

    return CompatibilityScore(
        effect_precondition=round(align_ep, 6),
        output_input=round(align_oi, 6),
        vector_score=round(comp_vec, 6),
        availability_factor=round(avail_factor, 6),
        execution_score=round(comp_exec, 6),
    )


def _check_predicate_satisfaction(
    consumer_pred: Predicate, producer_effects: list[Predicate]
) -> tuple[bool, bool]:
    """
    Check if a consumer precondition is satisfied or contradicted by producer effects.
    Returns (satisfied: bool, contradicted: bool).
    """
    c_name = canonical_var_name(consumer_pred.name)
    c_bool = _parse_bool_value(consumer_pred.value)

    matching_effects = [e for e in producer_effects if canonical_var_name(e.name) == c_name]
    if not matching_effects:
        return False, False

    for eff in matching_effects:
        e_bool = _parse_bool_value(eff.value)

        # Boolean check
        if c_bool is not None and e_bool is not None:
            if c_bool == e_bool:
                return True, False
            else:
                return False, True

        # Exact match (strings, numbers, etc.)
        if eff.operator == "=" and consumer_pred.operator == "=":
            if str(eff.value).strip().upper() == str(consumer_pred.value).strip().upper():
                return True, False
            else:
                return False, True

        # Numerical comparison
        try:
            e_num = float(eff.value)
            c_num = float(consumer_pred.value)
            op = consumer_pred.operator
            if op == ">" and e_num > c_num:
                return True, False
            if op == ">=" and e_num >= c_num:
                return True, False
            if op == "<" and e_num < c_num:
                return True, False
            if op == "<=" and e_num <= c_num:
                return True, False
            if op == "=" and e_num == c_num:
                return True, False
            return False, True
        except (ValueError, TypeError):
            pass

    return False, False


def validate_compatibility(producer: Capability, consumer: Capability) -> CompatibilityValidationResult:
    """
    Validate whether producer -> consumer handoff is execution-compatible.
    Requires:
    1. execution compatibility score >= 0.70
    2. every required consumer input present in producer outputs with matching type
    3. every consumer precondition satisfied by producer effects
    4. zero contradictory producer effects
    5. both capabilities have availability > 0
    """
    score = vector_compatibility(producer, consumer)
    reasons: list[str] = []

    # 1. Execution score check
    if score.execution_score < 0.70:
        reasons.append(f"Execution compatibility score {score.execution_score} is below threshold 0.70")

    # 2. Required inputs check
    producer_outputs = {out.name.strip(): out.type.strip() for out in producer.O}
    for inp in consumer.I:
        if inp.required:
            p_type = producer_outputs.get(inp.name.strip())
            if p_type is None:
                reasons.append(f"Required consumer input '{inp.name}' is not produced")
            elif p_type != inp.type.strip():
                reasons.append(f"Type mismatch for input '{inp.name}': expected {inp.type}, got {p_type}")

    # 3 & 4. Precondition satisfaction and contradiction check
    for pre in consumer.P:
        satisfied, contradicted = _check_predicate_satisfaction(pre, producer.E)
        if contradicted:
            reasons.append(f"Precondition '{pre.name}' is contradicted by producer effect")
        elif not satisfied:
            reasons.append(f"Precondition '{pre.name}' is not satisfied by producer effects")

    # 5. Availability check
    if producer.A <= 0.0 or consumer.A <= 0.0:
        reasons.append(f"One or both capabilities are unavailable (producer.A={producer.A}, consumer.A={consumer.A})")

    is_compatible = len(reasons) == 0
    return CompatibilityValidationResult(
        compatible=is_compatible,
        score=score,
        reasons=reasons,
    )


def goal_relevance(capability: Capability | np.ndarray, goal: Goal | np.ndarray) -> float:
    """
    Evaluate relevance of a capability to a target goal.
    GoalRel(C, G) = 0 if goal is zero
    otherwise: max(0, dot(effect, goal)) / ||goal||^2
    """
    eff = _extract_effect_vector(capability)
    g = encode_goal(goal) if isinstance(goal, Goal) else goal

    norm_g_sq = float(np.dot(g, g))
    if norm_g_sq == 0.0:
        return 0.0

    dot = float(np.dot(eff, g))
    rel = max(0.0, dot) / norm_g_sq
    return float(rel)
