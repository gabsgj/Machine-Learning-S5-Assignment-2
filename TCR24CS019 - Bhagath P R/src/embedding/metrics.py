from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import numpy as np

from src.models.capability import Capability
from src.models.state import ApplicationState
from src.models.goal import GoalSpecification
from src.embedding.encoder import CapabilityEmbedding, StateEmbedding, GoalEmbedding


@dataclass
class CompatibilityScore:
    """Detailed breakdown of directional compatibility C1 -> C2."""
    c1_id: str
    c2_id: str
    is_compatible: bool
    total_score: float
    pe_score: float
    io_score: float
    conflict_count: int
    conflicts: List[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "c1_id": self.c1_id,
            "c2_id": self.c2_id,
            "is_compatible": self.is_compatible,
            "total_score": round(self.total_score, 4),
            "pe_score": round(self.pe_score, 4),
            "io_score": round(self.io_score, 4),
            "conflict_count": self.conflict_count,
            "conflicts": self.conflicts,
            "explanation": self.explanation
        }


def cosine_sim(a: np.ndarray, b: np.ndarray, eps: float = 1e-8) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < eps or norm_b < eps:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def euclidean_dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


class SimilarityEngine:
    """
    Computes similarities across various subspaces and assesses
    capability compatibility, goal relevance, and state applicability.
    """

    @staticmethod
    def compute_similarity(
        x: Union[CapabilityEmbedding, np.ndarray],
        y: Union[CapabilityEmbedding, np.ndarray],
        metric: str = "functional"
    ) -> float:
        """
        Compare two encoded entities.
        Supported metrics:
        - 'functional': Cosine similarity of functional sector [pre || eff || in || out]
        - 'effects': Cosine similarity of effects sector [eff_val || eff_mask]
        - 'preconditions': Cosine similarity of preconditions [pre_val || pre_mask]
        - 'mechanism': Cosine similarity of type and mechanism [type || mech]
        - 'operational': Euclidean proximity 1 / (1 + dist) on quality vector
        - 'full': Cosine similarity across full embedding vector
        - 'euclidean': Proximity 1 / (1 + ||x - y||)
        """
        if isinstance(x, CapabilityEmbedding) and isinstance(y, CapabilityEmbedding):
            if metric == "functional":
                return cosine_sim(x.functional_vec, y.functional_vec)
            elif metric == "effects":
                eff_x = np.concatenate([x.eff_val, x.eff_mask])
                eff_y = np.concatenate([y.eff_val, y.eff_mask])
                return cosine_sim(eff_x, eff_y)
            elif metric == "preconditions":
                pre_x = np.concatenate([x.pre_val, x.pre_mask])
                pre_y = np.concatenate([y.pre_val, y.pre_mask])
                return cosine_sim(pre_x, pre_y)
            elif metric == "mechanism":
                return cosine_sim(x.implementation_vec, y.implementation_vec)
            elif metric == "operational":
                d = euclidean_dist(x.operational_vec, y.operational_vec)
                return float(1.0 / (1.0 + d))
            elif metric == "euclidean":
                d = euclidean_dist(x.vector, y.vector)
                return float(1.0 / (1.0 + d))
            else:  # full
                return cosine_sim(x.vector, y.vector)

        # Raw numpy array fallback
        vec_x = x.vector if hasattr(x, "vector") else x
        vec_y = y.vector if hasattr(y, "vector") else y
        if metric == "euclidean":
            return float(1.0 / (1.0 + euclidean_dist(vec_x, vec_y)))
        return cosine_sim(vec_x, vec_y)

    @staticmethod
    def compute_compatibility(
        c1_emb: CapabilityEmbedding,
        c2_emb: CapabilityEmbedding,
        c1: Optional[Capability] = None,
        c2: Optional[Capability] = None,
        w_pe: float = 0.7,
        w_io: float = 0.3
    ) -> CompatibilityScore:
        """
        Directional compatibility C1 -> C2.
        Evaluates whether C1's effects satisfy C2's preconditions (E1 => P2)
        and whether C1's outputs satisfy C2's inputs (O1 => I2).
        """
        conflicts = []
        conflict_count = 0

        # Vectorized Precondition-Effect Analysis
        e1_val = c1_emb.eff_val
        e1_mask = c1_emb.eff_mask
        p2_val = c2_emb.pre_val
        p2_mask = c2_emb.pre_mask

        # Overlap mask: dimensions where C1 has an effect AND C2 has a precondition
        overlap_mask = e1_mask * p2_mask
        overlap_sum = float(np.sum(overlap_mask))

        if overlap_sum > 0:
            # Check for value mismatch on overlapping dimensions
            # abs(val_diff) * overlap_mask
            val_diff = np.abs(e1_val - p2_val) * overlap_mask
            mismatch_sum = float(np.sum(val_diff > 1e-4))
            matches = overlap_sum - mismatch_sum

            if mismatch_sum > 0:
                conflict_count += int(mismatch_sum)
                conflicts.append(f"{int(mismatch_sum)} conflicting state variable(s) between E1 and P2")

            pe_score = float(max(0.0, matches / overlap_sum)) if conflict_count == 0 else 0.0
        else:
            # No direct overlap: C1 does not directly satisfy or contradict C2
            # Neutral baseline (requires initial state)
            pe_score = 0.5

        # IO compatibility: dot product of normalized output and input vectors
        io_score = float(np.clip(np.dot(c1_emb.output_vec, c2_emb.input_vec), 0.0, 1.0))
        if np.linalg.norm(c2_emb.input_vec) == 0:
            # C2 requires no inputs
            io_score = 1.0

        # Also check symbolic models if provided
        if c1 is not None and c2 is not None:
            eff_map = {e.variable: e for e in c1.effects}
            for prec in c2.preconditions:
                if prec.variable in eff_map:
                    eff = eff_map[prec.variable]
                    if eff.new_value != prec.expected_value:
                        sym_conf = f"Contradiction: {eff.variable}:={eff.new_value} != required {prec.expected_value}"
                        if sym_conf not in conflicts:
                            conflicts.append(sym_conf)
                            conflict_count += 1

        is_compatible = (conflict_count == 0)
        total_score = (w_pe * pe_score + w_io * io_score) if is_compatible else 0.0

        explanation = (
            f"Compatible (PE match: {pe_score:.2f}, IO match: {io_score:.2f})"
            if is_compatible else
            f"Incompatible due to {conflict_count} conflict(s): {'; '.join(conflicts)}"
        )

        return CompatibilityScore(
            c1_id=c1.id if c1 else c1_emb.capability_id,
            c2_id=c2.id if c2 else c2_emb.capability_id,
            is_compatible=is_compatible,
            total_score=total_score,
            pe_score=pe_score,
            io_score=io_score,
            conflict_count=conflict_count,
            conflicts=conflicts,
            explanation=explanation
        )

    @staticmethod
    def compute_goal_relevance(
        cap_emb: CapabilityEmbedding,
        goal_emb: GoalEmbedding
    ) -> float:
        """
        Measures alignment between capability effects and goal targets:
        Relevance = < e_val * e_mask, g_val * g_mask > / (||g_val * g_mask|| + eps)
        """
        g_target = goal_emb.val_vector * goal_emb.mask_vector
        norm_g = np.linalg.norm(g_target)
        if norm_g == 0:
            return 0.0

        eff_active = cap_emb.eff_val * cap_emb.eff_mask * goal_emb.mask_vector
        # Positive dot product indicates positive movement towards goal
        dot = float(np.dot(eff_active, g_target))
        # Check if effect opposes goal on any dimension
        overlap = cap_emb.eff_mask * goal_emb.mask_vector
        if np.any(overlap > 0):
            # Check accuracy of match
            mismatch = np.abs(cap_emb.eff_val - goal_emb.val_vector) * overlap
            if np.any(mismatch > 1e-4):
                # Detrimental effect
                return -1.0
            # Matched target variables
            match_count = float(np.sum(overlap))
            total_goal_vars = float(np.sum(goal_emb.mask_vector))
            return float(match_count / max(total_goal_vars, 1.0))
        return 0.0

    @staticmethod
    def compute_state_applicability(
        state_emb: StateEmbedding,
        cap_emb: CapabilityEmbedding
    ) -> bool:
        """
        Checks if S |= P_C in vector space:
        Applicable <=> || (state_vec - pre_val) * pre_mask || == 0
        """
        diff = (state_emb.vector - cap_emb.pre_val) * cap_emb.pre_mask
        return bool(np.linalg.norm(diff) < 1e-4)
