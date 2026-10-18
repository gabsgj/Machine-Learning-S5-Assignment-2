"""
Deterministic structured vector embedding.

The design is intentionally problem-specific rather than a direct application
of Word2Vec. Symbolic formal fields are hashed into fixed vector blocks, while
operational values are explicitly normalized.
"""

from __future__ import annotations

import hashlib
import math
from typing import Iterable, List

import numpy as np

from .models import Capability, Goal, State


class StructuredEmbedder:
    """
    Structured feature-hashing embedder.

    Vector layout:
        [0:8]    type/mechanism
        [8:20]   inputs
        [20:32]  outputs
        [32:44]  preconditions
        [44:56]  effects
        [56:64]  constraints/resources
        [64:72]  operational attributes
        [72:80]  composition metadata
    """

    DIM = 80
    BLOCKS = {
        "type": (0, 8),
        "input": (8, 20),
        "output": (20, 32),
        "precondition": (32, 44),
        "effect": (44, 56),
        "constraint": (56, 64),
        "operational": (64, 72),
        "composition": (72, 80),
    }

    def __init__(self, seed: int = 503):
        self.seed = seed

    def _hash(self, token: str) -> int:
        raw = f"{self.seed}:{token}".encode("utf-8")
        digest = hashlib.sha256(raw).digest()
        return int.from_bytes(digest[:8], "big")

    def _add_tokens(
        self,
        vector: np.ndarray,
        tokens: Iterable[str],
        start: int,
        end: int,
        weight: float = 1.0,
    ) -> None:
        width = end - start
        for token in tokens:
            h = self._hash(token)
            idx = start + (h % width)
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            vector[idx] += sign * weight

    def _safe_log(self, x: float) -> float:
        return math.log1p(max(0.0, x))

    def _normalise_operational(self, cap: Capability) -> np.ndarray:
        q = cap.quality

        # Smooth, bounded transformations.
        time = 1.0 / (1.0 + self._safe_log(q.time_ms + 1.0) / 8.0)
        resource = 1.0 / (1.0 + max(0.0, q.resource_cost))
        money = 1.0 / (1.0 + max(0.0, q.money_cost))
        risk = max(0.0, min(1.0, q.risk))
        energy = 1.0 / (1.0 + max(0.0, q.energy))
        reliability = max(0.0, min(1.0, cap.reliability))
        availability = max(0.0, min(1.0, cap.availability))

        return np.array([
            time, resource, money, 1.0 - risk, energy,
            reliability, availability, reliability * availability
        ], dtype=float)

    def encode_capability(self, cap: Capability) -> np.ndarray:
        v = np.zeros(self.DIM, dtype=float)

        self._add_tokens(
            v,
            [f"type:{cap.capability_type}"]
            + [f"mechanism:{k}={val}" for k, val in cap.mechanism.items()]
            + [f"tag:{x}" for x in cap.tags],
            *self.BLOCKS["type"],
            weight=1.0,
        )

        self._add_tokens(
            v,
            [f"input:{x.token()}" for x in cap.inputs],
            *self.BLOCKS["input"],
            weight=1.0,
        )
        self._add_tokens(
            v,
            [f"output:{x.token()}" for x in cap.outputs],
            *self.BLOCKS["output"],
            weight=1.0,
        )
        self._add_tokens(
            v,
            [f"pre:{x.token()}" for x in cap.preconditions],
            *self.BLOCKS["precondition"],
            weight=1.15,
        )
        self._add_tokens(
            v,
            [f"effect:{x.token()}" for x in cap.effects],
            *self.BLOCKS["effect"],
            weight=1.15,
        )
        self._add_tokens(
            v,
            [f"constraint:{x.token()}" for x in cap.constraints]
            + [f"resource:{x}" for x in cap.resources],
            *self.BLOCKS["constraint"],
            weight=0.9,
        )

        op_start, op_end = self.BLOCKS["operational"]
        v[op_start:op_end] = self._normalise_operational(cap)

        self._add_tokens(
            v,
            [f"component:{x}" for x in cap.components],
            *self.BLOCKS["composition"],
            weight=0.8,
        )

        return self._unit(v)

    def encode_state(self, state: State) -> np.ndarray:
        v = np.zeros(self.DIM, dtype=float)
        tokens = [f"state:{k}={val}" for k, val in sorted(state.values.items())]
        self._add_tokens(v, tokens, 32, 64, weight=1.0)
        return self._unit(v)

    def encode_goal(self, goal: Goal) -> np.ndarray:
        v = np.zeros(self.DIM, dtype=float)
        tokens = [f"effect:{c.token()}" for c in goal.conditions]
        self._add_tokens(v, tokens, *self.BLOCKS["effect"], weight=1.2)
        return self._unit(v)

    def compose_vectors(self, vectors: List[np.ndarray]) -> np.ndarray:
        if not vectors:
            raise ValueError("At least one vector is required for composition.")

        # Earlier and later operations contribute equally; the vector is
        # additionally scaled by chain length to retain a weak composition cue.
        result = np.mean(np.vstack(vectors), axis=0)
        return self._unit(result)

    @staticmethod
    def _unit(v: np.ndarray) -> np.ndarray:
        n = np.linalg.norm(v)
        return v if n == 0 else v / n

    @staticmethod
    def similarity(a: np.ndarray, b: np.ndarray) -> float:
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))
