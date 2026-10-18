"""
Composition Engine and Algebraic Vector Closure Verification.
Assignment 2: Design of a Vector Embedding for Capability Composition.
Student: Melita Mariam Mathew
Registration Number: TCCR24CS046
"""

from typing import List, Dict, Any, Tuple
import numpy as np

from src.models import Capability, CompositeCapability
from src.embedding import CapabilityEmbeddingSpace


class CompositionEngine:
    """
    Engine to compose capabilities both symbolically and vectorially,
    and analyze algebraic homomorphism between symbolic and vector spaces.
    """

    def __init__(self, space: CapabilityEmbeddingSpace):
        self.space = space

    def compose_symbolic(self, capabilities: List[Capability]) -> CompositeCapability:
        """Construct composite capability via formal symbolic rules."""
        return CompositeCapability.compose_sequence(capabilities)

    def compose_vector(self, capabilities: List[Capability]) -> np.ndarray:
        """Construct composite capability via vector-level algebraic operators."""
        if not capabilities:
            raise ValueError("Capabilities list cannot be empty.")
        vectors = [self.space.encode_capability(c) for c in capabilities]
        res = vectors[0]
        for v in vectors[1:]:
            res = self.space.compose_vectors(res, v)
        return res

    def evaluate_composition_fidelity(
        self,
        capabilities: List[Capability],
    ) -> Dict[str, Any]:
        """
        Evaluate the fidelity of vector composition against symbolic composition.
        
        Compares:
            v_symbolic = space.encode_capability(CompositeCapability.compose_sequence(caps))
            v_vector = space.compose_vectors(...)
            
        Metrics:
            - Cosine Similarity across full vector and each subspace
            - L2 / Mean Squared Error
            - Exact match on discrete effect/precondition indices
        """
        c_sym = self.compose_symbolic(capabilities)
        v_sym = self.space.encode_capability(c_sym)
        v_vec = self.compose_vector(capabilities)

        def cos_sim(a: np.ndarray, b: np.ndarray) -> float:
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            if na < 1e-8 and nb < 1e-8:
                return 1.0
            if na < 1e-8 or nb < 1e-8:
                return 0.0
            return float(np.dot(a, b) / (na * nb))

        l2_err = float(np.linalg.norm(v_sym - v_vec))
        mse = float(np.mean((v_sym - v_vec) ** 2))

        # Subspace comparisons
        subspaces = {
            "precondition": (self.space.get_pre(v_sym), self.space.get_pre(v_vec)),
            "effect": (self.space.get_eff(v_sym), self.space.get_eff(v_vec)),
            "input": (self.space.get_in(v_sym), self.space.get_in(v_vec)),
            "output": (self.space.get_out(v_sym), self.space.get_out(v_vec)),
            "delta": (self.space.get_delta(v_sym), self.space.get_delta(v_vec)),
            "mechanism": (self.space.get_mech(v_sym), self.space.get_mech(v_vec)),
            "operational": (self.space.get_ops(v_sym), self.space.get_ops(v_vec)),
        }

        subspace_sims = {}
        for name, (s_vec, v_sub) in subspaces.items():
            subspace_sims[name] = float(np.round(cos_sim(s_vec, v_sub), 4))

        return {
            "pipeline": " -> ".join([c.id for c in capabilities]),
            "full_cosine_similarity": float(np.round(cos_sim(v_sym, v_vec), 4)),
            "l2_error": float(np.round(l2_err, 4)),
            "mean_squared_error": float(np.round(mse, 6)),
            "subspace_similarities": subspace_sims,
            "symbolic_composite": c_sym,
            "symbolic_vector": v_sym,
            "algebraic_vector": v_vec,
        }

    def build_compatibility_matrix(
        self,
        capabilities: List[Capability],
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Build an N x N compatibility adjacency matrix where
        matrix[i, j] = compatibility score of C_i -> C_j.
        """
        n = len(capabilities)
        matrix = np.zeros((n, n), dtype=np.float64)
        names = [c.id for c in capabilities]

        for i, ci in enumerate(capabilities):
            for j, cj in enumerate(capabilities):
                res = self.space.compatibility(ci, cj)
                matrix[i, j] = res["compatibility_score"]

        return matrix, names
