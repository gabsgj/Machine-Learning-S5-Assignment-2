"""
compatibility.py
================
Formal Compatibility Engine for Capability Composition.
Evaluates:
1. Effect -> Precondition compatibility (Ei => Pj)
2. Output -> Input compatibility (Oi -> Ij)
3. State compatibility (S' |= Pj where S' = Apply(S, Ei))

Distinguishes cosine similarity from logical and operational composability.
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from models import Capability, State, Precondition, Effect, InputSpec, OutputSpec
from embedding import CapabilityEmbedder, StateEmbedder, cosine_similarity


class CompatibilityResult:
    """Detailed result of compatibility evaluation between Ci and Cj."""

    def __init__(
        self,
        c1_name: str,
        c2_name: str,
        is_compatible: bool,
        overall_score: float,
        effect_precondition_score: float,
        input_output_score: float,
        state_compatibility_score: float,
        satisfied_preconditions: List[str],
        unmet_preconditions: List[str],
        satisfied_inputs: List[str],
        missing_inputs: List[str],
        conflicts: List[str],
        explanation: str
    ):
        self.c1_name = c1_name
        self.c2_name = c2_name
        self.is_compatible = is_compatible
        self.overall_score = overall_score
        self.effect_precondition_score = effect_precondition_score
        self.input_output_score = input_output_score
        self.state_compatibility_score = state_compatibility_score
        self.satisfied_preconditions = satisfied_preconditions
        self.unmet_preconditions = unmet_preconditions
        self.satisfied_inputs = satisfied_inputs
        self.missing_inputs = missing_inputs
        self.conflicts = conflicts
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "c1_name": self.c1_name,
            "c2_name": self.c2_name,
            "is_compatible": self.is_compatible,
            "overall_score": round(self.overall_score, 4),
            "effect_precondition_score": round(self.effect_precondition_score, 4),
            "input_output_score": round(self.input_output_score, 4),
            "state_compatibility_score": round(self.state_compatibility_score, 4),
            "satisfied_preconditions": self.satisfied_preconditions,
            "unmet_preconditions": self.unmet_preconditions,
            "satisfied_inputs": self.satisfied_inputs,
            "missing_inputs": self.missing_inputs,
            "conflicts": self.conflicts,
            "explanation": self.explanation
        }

    def __repr__(self) -> str:
        status = "COMPATIBLE" if self.is_compatible else "INCOMPATIBLE"
        return f"<CompatibilityResult {self.c1_name} -> {self.c2_name}: {status} (score={self.overall_score:.3f})>"


class CompatibilityEngine:
    """
    Evaluates formal composability between capabilities:
    Compatibility(Ci, Cj) = w1 * S_EP + w2 * S_OI + w3 * S_State
    where w1 + w2 + w3 = 1.0.
    """

    def __init__(
        self,
        embedder: Optional[CapabilityEmbedder] = None,
        w_ep: float = 0.50,
        w_io: float = 0.30,
        w_state: float = 0.20
    ):
        self.embedder = embedder or CapabilityEmbedder()
        self.w_ep = w_ep
        self.w_io = w_io
        self.w_state = w_state
        assert abs((w_ep + w_io + w_state) - 1.0) < 1e-6, "Weights must sum to 1.0"

    def evaluate(
        self,
        c1: Capability,
        c2: Capability,
        context_state: Optional[State] = None
    ) -> CompatibilityResult:
        """
        Determines if capability sequence C1 -> C2 is valid and calculates quantitative compatibility score.
        """
        conflicts: List[str] = []
        satisfied_preconditions: List[str] = []
        unmet_preconditions: List[str] = []
        satisfied_inputs: List[str] = []
        missing_inputs: List[str] = []

        # 1. Effect -> Precondition Analysis (Ei => Pj)
        # Check for direct logical contradiction
        for eff in c1.effects:
            for pre in c2.preconditions:
                if eff.variable == pre.variable:
                    if eff.operation == "SET":
                        # Test if setting eff value satisfies or violates pre
                        if pre.operator == "==" and eff.value != pre.value:
                            conflicts.append(
                                f"Contradiction: {c1.name} sets {eff.variable} := {eff.value}, "
                                f"but {c2.name} requires {pre.variable} == {pre.value}"
                            )
                        elif pre.operator == "!=" and eff.value == pre.value:
                            conflicts.append(
                                f"Contradiction: {c1.name} sets {eff.variable} := {eff.value}, "
                                f"which violates {c2.name} requirement {pre.variable} != {pre.value}"
                            )

        # Vector Effect -> Precondition Score
        vec_c1 = self.embedder.encode_capability(c1)
        vec_c2 = self.embedder.encode_capability(c2)
        v_eff = self.embedder.get_subspaces(vec_c1)["effect"]
        v_pre = self.embedder.get_subspaces(vec_c2)["precondition"]

        # Dot product of effect and precondition vectors
        pre_norm = float(np.sum(np.abs(v_pre)))
        if pre_norm > 0:
            # Positive overlap represents direct satisfaction
            pos_overlap = float(np.sum(np.maximum(0.0, v_eff * v_pre)))
            neg_overlap = float(np.sum(np.maximum(0.0, - (v_eff * v_pre))))
            if neg_overlap > 0:
                s_ep = 0.0  # Penalize direct contradiction severely
            else:
                s_ep = min(1.0, pos_overlap / pre_norm)
        else:
            # C2 has no preconditions
            s_ep = 1.0

        # Symbolic Precondition matching
        for pre in c2.preconditions:
            satisfied = False
            for eff in c1.effects:
                if eff.variable == pre.variable:
                    if pre.operator == "==" and eff.value == pre.value:
                        satisfied = True
                        break
            if satisfied:
                satisfied_preconditions.append(f"{pre.variable} {pre.operator} {pre.value} (from {c1.name} effect)")
            else:
                unmet_preconditions.append(f"{pre.variable} {pre.operator} {pre.value}")

        # 2. Output -> Input Analysis (Oi -> Ij)
        c1_output_names = {o.name for o in c1.outputs}
        required_c2_inputs = [inp for inp in c2.inputs if inp.required]

        for inp in c2.inputs:
            if inp.name in c1_output_names:
                satisfied_inputs.append(f"{inp.name} (supplied by {c1.name})")
            elif inp.required:
                missing_inputs.append(inp.name)

        v_out = self.embedder.get_subspaces(vec_c1)["output"]
        v_in = self.embedder.get_subspaces(vec_c2)["input"]
        in_norm = float(np.sum(v_in))
        if in_norm > 0:
            s_io = float(np.sum(np.minimum(v_out, v_in)) / in_norm)
        else:
            s_io = 1.0

        # 3. State Compatibility Analysis
        # If context state provided, simulate S' = Apply(S, E1) and test if S' |= P2
        if context_state is not None:
            intermediate_state = c1.execute(context_state.clone()) if c1.can_execute_on(context_state) else context_state.apply_effects(c1.effects)
            s2_satisfied = intermediate_state.satisfies_preconditions(c2.preconditions)
            if s2_satisfied:
                s_state = 1.0
            else:
                sat_count = sum(1 for p in c2.preconditions if p.evaluate(intermediate_state.variables))
                s_state = sat_count / max(1, len(c2.preconditions))
        else:
            # When no context state given, state score reflects un-conflicted status
            s_state = 1.0 if len(conflicts) == 0 else 0.0

        # 4. Overall Compatibility Score
        if len(conflicts) > 0:
            overall_score = 0.0
            is_compatible = False
            explanation = f"Incompatible due to {len(conflicts)} direct state/precondition conflict(s): " + "; ".join(conflicts)
        else:
            overall_score = (
                self.w_ep * s_ep +
                self.w_io * s_io +
                self.w_state * s_state
            )
            # Boolean composability decision
            is_compatible = (s_ep > 0.0 or len(c2.preconditions) == 0) and (len(conflicts) == 0)
            if context_state is not None:
                # Must actually be executable on context state
                is_compatible = is_compatible and c1.can_execute_on(context_state) and intermediate_state.satisfies_preconditions(c2.preconditions)

            if is_compatible:
                explanation = f"Compatible: {c1.name} effects & outputs directly support {c2.name} execution."
            else:
                explanation = f"Incompatible: {c1.name} does not provide required preconditions/inputs for {c2.name}."

        return CompatibilityResult(
            c1_name=c1.name,
            c2_name=c2.name,
            is_compatible=is_compatible,
            overall_score=float(overall_score),
            effect_precondition_score=float(s_ep),
            input_output_score=float(s_io),
            state_compatibility_score=float(s_state),
            satisfied_preconditions=satisfied_preconditions,
            unmet_preconditions=unmet_preconditions,
            satisfied_inputs=satisfied_inputs,
            missing_inputs=missing_inputs,
            conflicts=conflicts,
            explanation=explanation
        )

    def compute_compatibility_matrix(
        self,
        capabilities: List[Capability],
        context_state: Optional[State] = None
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Computes pairwise compatibility matrix and boolean matrix for a list of capabilities.
        Returns:
            scores_matrix (N x N)
            boolean_matrix (N x N)
            labels (list of names)
        """
        n = len(capabilities)
        scores = np.zeros((n, n), dtype=np.float64)
        booleans = np.zeros((n, n), dtype=bool)
        labels = [c.name for c in capabilities]

        for i, c1 in enumerate(capabilities):
            for j, c2 in enumerate(capabilities):
                res = self.evaluate(c1, c2, context_state=context_state)
                scores[i, j] = res.overall_score
                booleans[i, j] = res.is_compatible

        return scores, booleans, labels
