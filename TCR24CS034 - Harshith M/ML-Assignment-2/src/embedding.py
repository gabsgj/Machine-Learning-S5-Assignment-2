import hashlib
import numpy as np
from typing import Any

from .models import State, Goal, Capability


# Capability types specified in the assignment
CAPABILITY_TYPES = [
    "API",
    "DATABASE",
    "GUI",
    "EVENT",
    "FUNCTION",
    "FILE",
    "COMPUTATION",
    "MESSAGE",
    "SERVICE"
]


# Reference ranges for normalising operational attributes
#
# [time, resource, money, risk, reliability, availability]
OP_RANGES = np.array(
    [500.0, 5.0, 0.05, 1.0, 1.0, 1.0],
    dtype=float
)


def _hash_index(token: str, size: int) -> int:
    """
    Deterministically maps a token to an index.
    SHA-256 is used so results remain reproducible.
    """
    digest = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    return int(digest[:16], 16) % size


def _hashed_tokens(tokens, size=16):
    """
    Converts symbolic tokens into a deterministic vector.
    """
    vector = np.zeros(size, dtype=float)

    for token in tokens:
        index = _hash_index(
            str(token).lower(),
            size
        )

        vector[index] += 1.0

    norm = np.linalg.norm(vector)

    if norm == 0:
        return vector

    return vector / norm


def _flatten_dict(prefix: str, value: Any):
    """
    Converts nested dictionaries into deterministic key=value tokens.
    """
    if isinstance(value, dict):

        result = []

        for key in sorted(value):

            result.extend(
                _flatten_dict(
                    f"{prefix}.{key}",
                    value[key]
                )
            )

        return result

    return [
        f"{prefix}={value}"
    ]


class CapabilityEmbedding:

    """
    Problem-specific embedding for the assignment.

    Capability vector consists of:

    1. Capability type                 -> 9 dimensions
    2. Structural information          -> 6 dimensions
    3. Functional semantic information -> 16 dimensions
    4. Operational information         -> 6 dimensions

    Total = 37 dimensions.
    """

    DIM = 37

    # ---------------------------------------------------------
    # STATE ENCODING
    # ---------------------------------------------------------

    def encode_state(self, state: State):

        tokens = _flatten_dict(
            "state",
            state.values
        )

        return _hashed_tokens(
            tokens,
            24
        )

    # ---------------------------------------------------------
    # GOAL ENCODING
    # ---------------------------------------------------------

    def encode_goal(self, goal: Goal):

        tokens = _flatten_dict(
            "goal",
            goal.conditions
        )

        return _hashed_tokens(
            tokens,
            24
        )

    # ---------------------------------------------------------
    # CAPABILITY ENCODING
    # ---------------------------------------------------------

    def encode_capability(self, capability: Capability):

        # =====================================================
        # 1. CAPABILITY TYPE
        # =====================================================

        type_vector = np.zeros(
            len(CAPABILITY_TYPES),
            dtype=float
        )

        if capability.capability_type in CAPABILITY_TYPES:

            index = CAPABILITY_TYPES.index(
                capability.capability_type
            )

            type_vector[index] = 1.0

        # Composite capabilities use their component types
        if (
            capability.components
            and capability.component_types
        ):

            type_vector = np.zeros(
                len(CAPABILITY_TYPES),
                dtype=float
            )

            for capability_type in capability.component_types:

                if capability_type in CAPABILITY_TYPES:

                    index = CAPABILITY_TYPES.index(
                        capability_type
                    )

                    type_vector[index] += 1.0

            norm = np.linalg.norm(type_vector)

            if norm != 0:
                type_vector /= norm

        # =====================================================
        # 2. STRUCTURAL INFORMATION
        # =====================================================

        structural = np.array(
            [
                len(capability.inputs),
                len(capability.outputs),
                len(capability.preconditions),
                len(capability.effects),
                len(capability.constraints),
                len(capability.resources)
            ],
            dtype=float
        )

        # Prevent large counts from dominating
        structural = structural / (
            1.0 + structural
        )

        # =====================================================
        # 3. FUNCTIONAL SEMANTIC INFORMATION
        # =====================================================

        tokens = []

        # Inputs
        for key, value in capability.inputs.items():

            tokens.append(
                f"input:{key}"
            )

            tokens.extend(
                _flatten_dict(
                    f"input:{key}",
                    value
                )
            )

        # Outputs
        for key, value in capability.outputs.items():

            tokens.append(
                f"output:{key}"
            )

            tokens.extend(
                _flatten_dict(
                    f"output:{key}",
                    value
                )
            )

        # Preconditions
        for key, value in capability.preconditions.items():

            tokens.extend(
                _flatten_dict(
                    f"precondition:{key}",
                    value
                )
            )

        # Effects
        for key, value in capability.effects.items():

            tokens.extend(
                _flatten_dict(
                    f"effect:{key}",
                    value
                )
            )

        # Constraints
        for constraint in capability.constraints:

            tokens.append(
                f"constraint:{constraint}"
            )

        # Resources
        for resource in capability.resources:

            tokens.append(
                f"resource:{resource}"
            )

        semantic_vector = _hashed_tokens(
            tokens,
            16
        )

        # =====================================================
        # 4. OPERATIONAL INFORMATION
        # =====================================================

        raw_operational = np.array(
            [
                capability.cost_time,
                capability.cost_resource,
                capability.cost_money,
                capability.risk,
                capability.reliability,
                capability.availability
            ],
            dtype=float
        )

        operational = np.clip(
            raw_operational / OP_RANGES,
            0.0,
            1.0
        )

        # =====================================================
        # FINAL VECTOR
        # =====================================================

        vector = np.concatenate(
            [
                type_vector,
                structural,
                semantic_vector,
                operational
            ]
        )

        norm = np.linalg.norm(vector)

        if norm == 0:
            return vector

        return vector / norm

    # ---------------------------------------------------------
    # GENERIC ENCODER
    # ---------------------------------------------------------

    def encode(self, entity):

        if isinstance(entity, State):
            return self.encode_state(entity)

        if isinstance(entity, Goal):
            return self.encode_goal(entity)

        if isinstance(entity, Capability):
            return self.encode_capability(entity)

        raise TypeError(
            f"Unsupported entity type: "
            f"{type(entity).__name__}"
        )


# =============================================================
# COSINE SIMILARITY
# =============================================================

def cosine_similarity(vector_a, vector_b):

    vector_a = np.asarray(
        vector_a,
        dtype=float
    )

    vector_b = np.asarray(
        vector_b,
        dtype=float
    )

    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(
        np.dot(vector_a, vector_b)
        / (norm_a * norm_b)
    )


# =============================================================
# OPERATIONAL SIMILARITY
# =============================================================

def operational_similarity(
    capability_a: Capability,
    capability_b: Capability
):

    values_a = np.array(
        [
            capability_a.cost_time / OP_RANGES[0],
            capability_a.cost_resource / OP_RANGES[1],
            capability_a.cost_money / OP_RANGES[2],
            capability_a.risk / OP_RANGES[3],
            capability_a.reliability,
            capability_a.availability
        ],
        dtype=float
    )

    values_b = np.array(
        [
            capability_b.cost_time / OP_RANGES[0],
            capability_b.cost_resource / OP_RANGES[1],
            capability_b.cost_money / OP_RANGES[2],
            capability_b.risk / OP_RANGES[3],
            capability_b.reliability,
            capability_b.availability
        ],
        dtype=float
    )

    difference = np.abs(
        values_a - values_b
    )

    return float(
        1.0 - np.mean(difference)
    )


# =============================================================
# FINAL SIMILARITY
# =============================================================

def similarity(
    entity_a,
    entity_b,
    embedding=None
):

    if embedding is None:
        embedding = CapabilityEmbedding()

    # Capability similarity
    if (
        isinstance(entity_a, Capability)
        and isinstance(entity_b, Capability)
    ):

        functional_similarity = cosine_similarity(
            embedding.encode_capability(entity_a),
            embedding.encode_capability(entity_b)
        )

        operational = operational_similarity(
            entity_a,
            entity_b
        )

        # Functional properties are more important,
        # but operational attributes are still represented.
        return float(
            0.70 * functional_similarity
            + 0.30 * operational
        )

    # State/goal/etc.
    return cosine_similarity(
        embedding.encode(entity_a),
        embedding.encode(entity_b)
    )