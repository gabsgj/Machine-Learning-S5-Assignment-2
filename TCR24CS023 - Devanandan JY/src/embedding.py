import numpy as np
from numpy.linalg import norm
from .models import Capability

class VectorSpace:
    def __init__(self, state_vocab: list):
        self.vocab = {k: v for v, k in enumerate(state_vocab)}
        self.dim = len(self.vocab)

    def _encode_subspace(self, criteria: dict):
        """Returns [values, active_mask]"""
        val_vec = np.zeros(self.dim)
        mask_vec = np.zeros(self.dim)
        for k, v in criteria.items():
            if k in self.vocab:
                idx = self.vocab[k]
                val_vec[idx] = 1.0 if v else -1.0
                mask_vec[idx] = 1.0 # 1.0 means this variable is active/required
        return val_vec, mask_vec

    def encode_capability(self, cap: Capability) -> np.ndarray:
        """
        Maps capability to R^{4d + 3}.
        Vector = [p_val || p_mask || e_val || e_mask || latency || cost || log_rel]
        """
        p_val, p_mask = self._encode_subspace(cap.preconditions)
        e_val, e_mask = self._encode_subspace(cap.effects)
        
        # Logarithmic transformation for multiplicative reliability
        log_rel = -np.log(cap.reliability)
        ops_vec = np.array([cap.latency, cap.cost, log_rel])
        
        return np.concatenate([p_val, p_mask, e_val, e_mask, ops_vec])

    def algebraic_compose(self, vec_a: np.ndarray, vec_b: np.ndarray) -> np.ndarray:
        """
        Vectorized composition B ◦ A. 
        Calculates the exact algebraic homomorphism of capabilities.
        """
        d = self.dim
        p_val_a, p_mask_a = vec_a[0:d], vec_a[d:2*d]
        e_val_a, e_mask_a = vec_a[2*d:3*d], vec_a[3*d:4*d]
        
        p_val_b, p_mask_b = vec_b[0:d], vec_b[d:2*d]
        e_val_b, e_mask_b = vec_b[2*d:3*d], vec_b[3*d:4*d]

        # B's preconditions not satisfied by A's effects
        unmet_p_mask_b = np.where(e_mask_a == 1, 0, p_mask_b)
        
        # Composite Preconditions
        comp_p_mask = np.clip(p_mask_a + unmet_p_mask_b, 0, 1)
        comp_p_val = np.where(p_mask_a == 1, p_val_a, p_val_b * unmet_p_mask_b)
        
        # Composite Effects (B overrides A)
        comp_e_mask = np.clip(e_mask_b + e_mask_a, 0, 1)
        comp_e_val = np.where(e_mask_b == 1, e_val_b, e_val_a)
        
        # Composite Operations (Strictly Additive)
        comp_ops = vec_a[-3:] + vec_b[-3:]
        
        return np.concatenate([comp_p_val, comp_p_mask, comp_e_val, comp_e_mask, comp_ops])

    def compatibility_score(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Evaluates directed transition A -> B."""
        d = self.dim
        e_val_a, e_mask_a = vec_a[2*d:3*d], vec_a[3*d:4*d]
        p_val_b, p_mask_b = vec_b[0:d], vec_b[d:2*d]
        
        overlap_mask = e_mask_a * p_mask_b
        
        # Check for strict contradictions (e.g., A makes X=False, B needs X=True)
        conflicts = np.sum(overlap_mask * (e_val_a != p_val_b))
        if conflicts > 0:
            return 0.0
            
        fulfilled = np.sum(overlap_mask * (e_val_a == p_val_b))
        total_required = np.sum(overlap_mask)
        return (fulfilled / total_required) if total_required > 0 else 1.0

    def functional_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Isolates the functional sectors (ignoring operational costs) for Cosine Sim."""
        func_a = vec_a[:-3]
        func_b = vec_b[:-3]
        if norm(func_a) == 0 or norm(func_b) == 0: return 0.0
        return np.dot(func_a, func_b) / (norm(func_a) * norm(func_b))