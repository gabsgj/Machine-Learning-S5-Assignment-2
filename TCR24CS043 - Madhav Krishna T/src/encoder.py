"""SCE-128 structured embedding encoder.

This v1 implementation follows the architecture from Phase 2 but keeps the
encoder deterministic and dependency-light.  Token vectors are generated
from stable hashes; field blocks are pooled and projected into fixed-size
vectors.  This gives us reproducible embeddings before we introduce learned
parameters using a larger training dataset.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np

from .schema import Capability, Condition, Goal, InputSpec, OutputSpec, State


EPS = 1e-12


# ----------------------------- basic utilities -----------------------------


def l2_normalize(x: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(x))
    if norm <= EPS:
        return np.zeros_like(x, dtype=np.float32)
    return (x / norm).astype(np.float32)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= EPS:
        return 0.0
    return float(np.dot(a, b) / denom)


def stable_seed(text: str, seed: int = 1729) -> int:
    digest = hashlib.sha256(f"{seed}|{text}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little", signed=False) % (2**32 - 1)


def token_vector(text: Any, dim: int = 32, seed: int = 1729) -> np.ndarray:
    """Create a deterministic dense token representation."""
    rng = np.random.default_rng(stable_seed(str(text), seed))
    return rng.normal(0.0, 1.0, size=dim).astype(np.float32) / math.sqrt(dim)


def numeric_vector(value: Any, dim: int = 8) -> np.ndarray:
    """Encode numeric/bool values with explicit sign and scale features."""
    out = np.zeros(dim, dtype=np.float32)
    if isinstance(value, bool):
        sign = 1.0 if value else -1.0
        # Opposite boolean values deliberately occupy opposing directions.
        basis = np.array([1.0, 0.75, 0.5, 0.25], dtype=np.float32) * sign
        out[: min(4, dim)] = basis[: min(4, dim)]
        return out
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        x = float(value)
        scaled = math.tanh(x)
        log_scaled = math.tanh(math.copysign(math.log1p(abs(x)), x))
        out[0] = scaled
        out[1] = log_scaled
        out[2] = 1.0 if x > 0 else (-1.0 if x < 0 else 0.0)
        out[3] = math.tanh(abs(x))
        if dim > 4:
            out[4] = math.tanh(x * x)
        return out
    return out


def value_vector(value: Any, dim: int = 16, seed: int = 1729) -> np.ndarray:
    """Encode values while preserving strong polarity for contradictory booleans."""
    out = np.zeros(dim, dtype=np.float32)
    if isinstance(value, bool):
        sign = 1.0 if value else -1.0
        basis = np.array([1.0, 0.85, 0.70, 0.55, 0.40, 0.25], dtype=np.float32) * sign
        out[: min(len(basis), dim)] = basis[: min(len(basis), dim)]
        if dim > 6:
            # Keep a shared categorical/value component so true/false remain the
            # same variable domain while their polarity stays distinct.
            out[6] = 0.35
        return l2_normalize(out)

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        n = numeric_vector(value, dim=min(8, dim))
        out[: len(n)] = n
        if dim > 8:
            out[8:] = token_vector(f"value:{value}", dim=dim - 8, seed=seed)
        return l2_normalize(out)

    # Categorical/string values retain token identity.
    return l2_normalize(token_vector(f"value:{value}", dim=dim, seed=seed))

def mean_pool(vectors: Sequence[np.ndarray], dim: int) -> np.ndarray:
    if not vectors:
        return np.zeros(dim, dtype=np.float32)
    stacked = np.vstack(vectors).astype(np.float32)
    return np.mean(stacked, axis=0).astype(np.float32)


def fixed_projection(x: np.ndarray, out_dim: int, label: str, seed: int = 1729) -> np.ndarray:
    """Deterministic tanh projection used as the v1 field projector."""
    in_dim = int(x.shape[0])
    rng = np.random.default_rng(stable_seed(label, seed))
    scale = 1.0 / math.sqrt(max(in_dim, 1))
    w = rng.normal(0.0, scale, size=(out_dim, in_dim)).astype(np.float32)
    b = rng.normal(0.0, 0.02, size=(out_dim,)).astype(np.float32)
    y = np.tanh(w @ x + b).astype(np.float32)
    return l2_normalize(y)


# ----------------------------- predicate encoders --------------------------


def encode_condition_raw(condition: Condition, seed: int = 1729) -> np.ndarray:
    a = token_vector(f"attribute:{condition.attribute}", dim=24, seed=seed)
    o = token_vector(f"operator:{condition.operator}", dim=12, seed=seed)
    v = value_vector(condition.value, dim=20, seed=seed)
    return np.concatenate([a, o, v]).astype(np.float32)


def encode_condition(condition: Condition, role: str, out_dim: int = 16, seed: int = 1729) -> np.ndarray:
    raw = encode_condition_raw(condition, seed=seed)
    projected = fixed_projection(raw, out_dim, f"condition:{role}", seed=seed)
    return projected




def encode_condition_common(condition: Condition, out_dim: int = 24, seed: int = 1729) -> np.ndarray:
    """Encode predicates into one shared relation space.

    The common space explicitly separates attribute/operator/value. Boolean
    values use opposite directions so predicates such as x=True and x=False
    remain strongly distinguishable while sharing the same attribute identity.
    """
    if out_dim != 24:
        raise ValueError("SCE-128 v1.1 common predicate dimension is fixed at 24")

    attribute = token_vector(f"attribute:{condition.attribute}", dim=12, seed=seed)
    operator = token_vector(f"operator:{condition.operator}", dim=4, seed=seed)
    value = value_vector(condition.value, dim=8, seed=seed)
    return l2_normalize(np.concatenate([attribute, operator, value]).astype(np.float32))


def encode_condition_set_common(
    conditions: Sequence[Condition], out_dim: int = 64, seed: int = 1729
) -> np.ndarray:
    vectors = [encode_condition_common(c, out_dim=24, seed=seed) for c in conditions]
    pooled = mean_pool(vectors, 24)
    raw = np.concatenate([pooled, np.array([math.tanh(len(conditions))], dtype=np.float32)])
    return fixed_projection(raw, out_dim, "set:common", seed=seed)

def encode_condition_set(
    conditions: Sequence[Condition],
    role: str,
    out_dim: int = 16,
    seed: int = 1729,
) -> np.ndarray:
    vectors = [encode_condition(c, role=role, out_dim=out_dim, seed=seed) for c in conditions]
    pooled = mean_pool(vectors, out_dim)
    # Add a size signal so empty/small/large condition sets are distinguishable.
    size_signal = np.array(
        [math.tanh(len(conditions)), math.tanh(math.log1p(len(conditions)))],
        dtype=np.float32,
    )
    raw = np.concatenate([pooled, size_signal])
    return fixed_projection(raw, out_dim, f"set:{role}", seed=seed)


# ----------------------------- I/O encoders --------------------------------


def encode_input(item: InputSpec, out_dim: int = 16, seed: int = 1729) -> np.ndarray:
    parts = [
        token_vector(f"input_name:{item.name}", 20, seed),
        token_vector(f"input_type:{item.type}", 12, seed),
        token_vector(f"input_domain:{item.domain}", 16, seed),
        np.array([1.0 if item.required else 0.0], dtype=np.float32),
    ]
    return fixed_projection(np.concatenate(parts), out_dim, "input", seed)


def encode_output(item: OutputSpec, out_dim: int = 16, seed: int = 1729) -> np.ndarray:
    parts = [
        token_vector(f"output_name:{item.name}", 20, seed),
        token_vector(f"output_type:{item.type}", 12, seed),
        token_vector(f"output_domain:{item.domain}", 16, seed),
    ]
    return fixed_projection(np.concatenate(parts), out_dim, "output", seed)


def encode_io_set(items: Sequence[Any], role: str, out_dim: int = 16, seed: int = 1729) -> np.ndarray:
    if role == "input":
        vectors = [encode_input(x, out_dim=out_dim, seed=seed) for x in items]
    else:
        vectors = [encode_output(x, out_dim=out_dim, seed=seed) for x in items]
    pooled = mean_pool(vectors, out_dim)
    raw = np.concatenate([pooled, np.array([math.tanh(len(items))], dtype=np.float32)])
    return fixed_projection(raw, out_dim, f"set:{role}", seed=seed)


# ----------------------------- capability encoding -------------------------


def encode_resources(resources: Sequence[str], out_dim: int = 12, seed: int = 1729) -> np.ndarray:
    vectors = [token_vector(f"resource:{r}", out_dim, seed) for r in resources]
    pooled = mean_pool(vectors, out_dim)
    raw = np.concatenate([pooled, np.array([math.tanh(len(resources))], dtype=np.float32)])
    return fixed_projection(raw, out_dim, "resources", seed)


def encode_constraints(constraints: Sequence[Any], out_dim: int = 12, seed: int = 1729) -> np.ndarray:
    vectors = [token_vector(f"constraint:{c.expression}", out_dim, seed) for c in constraints]
    pooled = mean_pool(vectors, out_dim)
    raw = np.concatenate([pooled, np.array([math.tanh(len(constraints))], dtype=np.float32)])
    return fixed_projection(raw, out_dim, "constraints", seed)


def encode_mechanism(mechanism: Dict[str, str], capability_type: str, out_dim: int = 8, seed: int = 1729) -> np.ndarray:
    tokens = [token_vector(f"type:{capability_type}", 16, seed)]
    tokens.extend(token_vector(f"mechanism:{k}={v}", 16, seed) for k, v in sorted(mechanism.items()))
    pooled = mean_pool(tokens, 16)
    return fixed_projection(pooled, out_dim, "mechanism", seed)


def encode_quality(capability: Capability, out_dim: int = 20, seed: int = 1729) -> np.ndarray:
    """Explicit 20-D operational representation for SCE-128 v1.1.

    The block contains normalized primary attributes, squared terms, and
    selected interactions. It intentionally excludes capability-name tokens so
    operational sensitivity comes from operational properties themselves.
    """
    if out_dim != 20:
        raise ValueError("SCE-128 v1.1 operational dimension is fixed at 20")

    q = capability.quality
    primary = np.array([
        math.tanh(math.log1p(max(q.execution_time_ms or 0.0, 0.0)) / math.log1p(1000.0)),
        math.tanh((q.resource_cost or 0.0) / 10.0),
        math.tanh(math.log1p(max(q.monetary_cost or 0.0, 0.0)) / math.log1p(0.10)),
        float(max(0.0, min(1.0, q.risk or 0.0))),
        math.tanh((q.energy_cost or 0.0) / 10.0),
        2.0 * float(max(0.0, min(1.0, capability.reliability))) - 1.0,
        2.0 * float(bool(capability.availability)) - 1.0,
    ], dtype=np.float32)

    squares = primary ** 2
    interactions = np.array([
        primary[0] * primary[5],
        primary[1] * primary[5],
        primary[2] * primary[5],
        primary[3] * primary[6],
        primary[4] * primary[5],
        primary[5] * primary[6],
    ], dtype=np.float32)

    raw = np.concatenate([primary, squares, interactions]).astype(np.float32)
    assert raw.shape == (20,), raw.shape
    return l2_normalize(raw)

def encode_capability(capability: Capability, seed: int = 1729) -> np.ndarray:
    """Return the 128-D SCE vector in the fixed block order."""
    h_f = fixed_projection(token_vector(f"capability_function:{capability.name}", 24, seed), 4, "function")
    h_t = fixed_projection(token_vector(f"capability_type:{capability.type}", 24, seed), 8, "type")
    h_i = encode_io_set(capability.inputs, "input", 16, seed)
    h_o = encode_io_set(capability.outputs, "output", 16, seed)
    h_p = encode_condition_set(capability.preconditions, "precondition", 16, seed)
    h_e = encode_condition_set(capability.effects, "effect", 16, seed)
    h_k = encode_constraints(capability.constraints, 12, seed)
    h_r = encode_resources(capability.resources, 12, seed)
    h_m = encode_mechanism(capability.mechanism, capability.type, 8, seed)
    h_q = encode_quality(capability, 20, seed)

    vector = np.concatenate([h_f, h_t, h_i, h_o, h_p, h_e, h_k, h_r, h_m, h_q]).astype(np.float32)
    assert vector.shape == (128,), vector.shape
    return l2_normalize(vector)


# ----------------------------- state / goal ---------------------------------


def state_to_conditions(state: State) -> List[Condition]:
    return [Condition(attribute=k, operator="==", value=v) for k, v in sorted(state.items())]


def encode_state(state: State, seed: int = 1729) -> np.ndarray:
    return encode_condition_set_common(state_to_conditions(state), out_dim=64, seed=seed)


def encode_goal(goal: Goal, seed: int = 1729) -> np.ndarray:
    return encode_condition_set_common(goal, out_dim=64, seed=seed)


def encode_effects_common(capability: Capability, seed: int = 1729) -> np.ndarray:
    return encode_condition_set_common(capability.effects, out_dim=64, seed=seed)


# ----------------------------- vector block helpers ------------------------


def capability_blocks(vector: np.ndarray) -> Dict[str, np.ndarray]:
    boundaries = {
        "function": (0, 4),
        "type": (4, 12),
        "input": (12, 28),
        "output": (28, 44),
        "precondition": (44, 60),
        "effect": (60, 76),
        "constraint": (76, 88),
        "resource": (88, 100),
        "mechanism": (100, 108),
        "operational": (108, 128),
    }
    return {k: vector[a:b] for k, (a, b) in boundaries.items()}
