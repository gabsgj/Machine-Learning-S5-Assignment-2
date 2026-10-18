"""SCE-128 v2.1: leakage-free learned composition operator.

The operator is trained only on atomic direct-composition pairs. At inference,
longer chains are composed recursively from vectors alone; no formal composite
is constructed during prediction. A separately encoded formal composite is
used only as the evaluation target.

The model is deliberately small because the assignment dataset is small:
for each embedding block we learn a scalar linear mixture over six per-dimension
features with ridge regularization. This keeps the number of learned parameters
low and makes the composition mechanism inspectable.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import json
import numpy as np

from .compatibility import compatibility
from .dataset import load_dataset
from .encoder import capability_blocks, cosine, l2_normalize
from .final_model import compose_formal_v2, encode_capability_v2
from .schema import Capability


BLOCK_NAMES = (
    "function",
    "type",
    "input",
    "output",
    "precondition",
    "effect",
    "constraint",
    "resource",
    "mechanism",
    "operational",
)


@dataclass
class CompositionPair:
    source_id: str
    target_id: str


@dataclass
class FitReport:
    train_pairs: int
    train_mean_cosine: float
    ridge_lambda: float


def is_logical_capability(cid: str) -> bool:
    return not any(cid.endswith(suffix) for suffix in ("_API", "_DB", "_GUI"))


def relation_features(source_vec: np.ndarray, target_vec: np.ndarray) -> np.ndarray:
    """Vector-only directional relation features used by both fit and predict."""
    s = capability_blocks(source_vec)
    t = capability_blocks(target_vec)
    return np.asarray(
        [
            cosine(s["effect"], t["precondition"]),
            cosine(s["output"], t["input"]),
            cosine(s["precondition"], t["effect"]),
            cosine(s["input"], t["output"]),
            cosine(source_vec, target_vec),
            cosine(s["operational"], t["operational"]),
        ],
        dtype=np.float64,
    )


class LearnedBlockComposer:
    """Low-parameter relation-conditioned block composer trained by ridge regression."""

    def __init__(self, ridge_lambda: float = 1e-2):
        self.ridge_lambda = float(ridge_lambda)
        self.coef_: Dict[str, np.ndarray] = {}
        self.fitted = False

    @staticmethod
    def _features(source: np.ndarray, target: np.ndarray, rel: np.ndarray) -> np.ndarray:
        # Relation-conditioned terms remain vector-only at inference.
        r_pe, r_io = float(rel[0]), float(rel[1])
        return np.column_stack(
            [
                source,
                target,
                source * target,
                np.abs(source - target),
                r_pe * source,
                r_io * target,
            ]
        )

    def fit(self, pairs: Sequence[Tuple[np.ndarray, np.ndarray, np.ndarray]],
            targets: Sequence[np.ndarray]) -> FitReport:
        if not pairs:
            raise ValueError("At least one training composition pair is required")
        if len(pairs) != len(targets):
            raise ValueError("Pairs and targets must have the same length")

        blocks_targets = [capability_blocks(t) for t in targets]
        total_cos = []
        for name in BLOCK_NAMES:
            X_parts = []
            y_parts = []
            for (source, target, rel), target_vec in zip(pairs, targets):
                s_block = capability_blocks(source)[name]
                t_block = capability_blocks(target)[name]
                rel_repeat = np.tile(rel, (len(s_block), 1))
                X = self._features(s_block, t_block, rel)
                # X has 6 columns and one row per block dimension.
                X_parts.append(X)
                y_parts.append(blocks_targets[len(X_parts)-1][name])
            X_all = np.vstack(X_parts)
            y_all = np.concatenate(y_parts)
            gram = X_all.T @ X_all
            reg = self.ridge_lambda * np.eye(gram.shape[0], dtype=np.float64)
            coef = np.linalg.solve(gram + reg, X_all.T @ y_all)
            self.coef_[name] = coef

        self.fitted = True
        train_preds = [self.predict(s, t) for s, t, _ in pairs]
        target_vecs = [t for t in targets]
        total_cos = [cosine(p, g) for p, g in zip(train_preds, target_vecs)]
        return FitReport(
            train_pairs=len(pairs),
            train_mean_cosine=float(np.mean(total_cos)),
            ridge_lambda=self.ridge_lambda,
        )

    def predict(self, source_vec: np.ndarray, target_vec: np.ndarray) -> np.ndarray:
        if not self.fitted:
            raise RuntimeError("Composer must be fitted before prediction")
        rel = relation_features(source_vec, target_vec)
        s_blocks = capability_blocks(source_vec)
        t_blocks = capability_blocks(target_vec)
        out_blocks = {}
        for name in BLOCK_NAMES:
            X = self._features(s_blocks[name], t_blocks[name], rel)
            raw = X @ self.coef_[name]
            out_blocks[name] = raw.astype(np.float32)
        out = np.concatenate([out_blocks[name] for name in BLOCK_NAMES]).astype(np.float32)
        return l2_normalize(out)


def build_training_pairs(caps: Mapping[str, Capability], train_pair_ids: Sequence[Tuple[str, str]]) -> Tuple[List[Tuple[np.ndarray, np.ndarray, np.ndarray]], List[np.ndarray]]:
    pairs = []
    targets = []
    vectors = {cid: encode_capability_v2(cap) for cid, cap in caps.items()}
    for source_id, target_id in train_pair_ids:
        source = caps[source_id]
        target = caps[target_id]
        rel = compatibility(source, target)
        if not rel.compatible:
            raise ValueError(f"Training pair {source_id}->{target_id} is not compatible")
        formal = compose_formal_v2(source, target)
        pairs.append((vectors[source_id], vectors[target_id], relation_features(vectors[source_id], vectors[target_id])))
        targets.append(encode_capability_v2(formal))
    return pairs, targets


def predict_chain_vectors(composer: LearnedBlockComposer, caps: Mapping[str, Capability], chain: Sequence[str]) -> List[np.ndarray]:
    """Recursively compose only vectors; formal composites are never used for prediction."""
    if not chain:
        raise ValueError("Empty composition chain")
    vectors = {cid: encode_capability_v2(cap) for cid, cap in caps.items()}
    current = vectors[chain[0]]
    outputs = [current]
    for cid in chain[1:]:
        current = composer.predict(current, vectors[cid])
        outputs.append(current)
    return outputs


def gold_chain_vectors(caps: Mapping[str, Capability], chain: Sequence[str]) -> List[np.ndarray]:
    """Independently encode each formal prefix composite for evaluation only."""
    current = caps[chain[0]]
    outputs = [encode_capability_v2(current)]
    for cid in chain[1:]:
        current = compose_formal_v2(current, caps[cid])
        outputs.append(encode_capability_v2(current))
    return outputs
