from typing import List, Dict, Tuple, Any, Optional
import numpy as np
from sklearn.decomposition import PCA

from src.capability import Capability
from src.state import State, Goal
from src.utils import min_max_normalize, canonicalize_predicate

class CapabilityVocabulary:
    """
    Constructs discrete feature vocabularies over all capabilities in a dataset
    to establish a consistent, aligned feature space.
    """
    def __init__(self, capabilities: List[Capability]):
        self.types: List[str] = sorted(list(set(c.type for c in capabilities)))
        
        inputs_set = set()
        outputs_set = set()
        precond_set = set()
        effects_set = set()
        constraints_set = set()
        resources_set = set()
        mechanism_set = set()

        for c in capabilities:
            for i in c.inputs:
                inputs_set.add(f"{i.name}:{i.type}")
            for o in c.outputs:
                outputs_set.add(f"{o.name}:{o.type}")
            for p in c.preconditions:
                precond_set.add(canonicalize_predicate(p))
            for e in c.effects:
                effects_set.add(canonicalize_predicate(e))
            for k in c.constraints:
                constraints_set.add(k)
            for r in c.resources:
                resources_set.add(r)
            for k_m, v_m in c.mechanism.items():
                mechanism_set.add(f"{k_m}={v_m}")

        self.inputs: List[str] = sorted(list(inputs_set))
        self.outputs: List[str] = sorted(list(outputs_set))
        self.preconditions: List[str] = sorted(list(precond_set))
        self.effects: List[str] = sorted(list(effects_set))
        self.constraints: List[str] = sorted(list(constraints_set))
        self.resources: List[str] = sorted(list(resources_set))
        self.mechanism: List[str] = sorted(list(mechanism_set))

        # Range bounds for operational attribute normalization
        times = [c.cost.time for c in capabilities]
        res_costs = [c.cost.resource for c in capabilities]
        mon_costs = [c.cost.money for c in capabilities]
        risks = [c.cost.risk for c in capabilities]
        energies = [c.cost.energy for c in capabilities]

        self.time_range = (min(times, default=0.0), max(times, default=1.0))
        self.res_cost_range = (min(res_costs, default=0.0), max(res_costs, default=1.0))
        self.mon_cost_range = (min(mon_costs, default=0.0), max(mon_costs, default=1.0))
        self.risk_range = (min(risks, default=0.0), max(risks, default=1.0))
        self.energy_range = (min(energies, default=0.0), max(energies, default=1.0))


class CapabilityEncoder:
    """
    Hybrid Structured Capability Encoder.
    Encodes formal capability C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
    into a structured feature vector V(C_i).
    """
    def __init__(self, vocab: CapabilityVocabulary):
        self.vocab = vocab
        
        # Calculate sub-vector block slice offsets
        self.block_slices: Dict[str, Tuple[int, int]] = {}
        curr_idx = 0

        blocks = [
            ("type", len(vocab.types)),
            ("inputs", len(vocab.inputs)),
            ("outputs", len(vocab.outputs)),
            ("preconditions", len(vocab.preconditions)),
            ("effects", len(vocab.effects)),
            ("constraints", len(vocab.constraints)),
            ("resources", len(vocab.resources)),
            ("mechanism", len(vocab.mechanism)),
            ("operational", 7) # time, resource, money, risk, energy, reliability, availability
        ]

        for block_name, size in blocks:
            self.block_slices[block_name] = (curr_idx, curr_idx + size)
            curr_idx += size

        self.dimension = curr_idx

    def encode_capability(self, c: Capability) -> np.ndarray:
        """Encode a capability object into a structured vector V(C_i)."""
        vec = np.zeros(self.dimension, dtype=np.float64)

        # 1. Type sub-vector (one-hot)
        s, e = self.block_slices["type"]
        if c.type in self.vocab.types:
            idx = self.vocab.types.index(c.type)
            vec[s + idx] = 1.0

        # 2. Inputs sub-vector (multi-hot)
        s, e = self.block_slices["inputs"]
        for inp in c.inputs:
            key = f"{inp.name}:{inp.type}"
            if key in self.vocab.inputs:
                idx = self.vocab.inputs.index(key)
                vec[s + idx] = 1.0

        # 3. Outputs sub-vector (multi-hot)
        s, e = self.block_slices["outputs"]
        for out in c.outputs:
            key = f"{out.name}:{out.type}"
            if key in self.vocab.outputs:
                idx = self.vocab.outputs.index(key)
                vec[s + idx] = 1.0

        # 4. Preconditions sub-vector (multi-hot)
        s, e = self.block_slices["preconditions"]
        for p in c.preconditions:
            cp = canonicalize_predicate(p)
            if cp in self.vocab.preconditions:
                idx = self.vocab.preconditions.index(cp)
                vec[s + idx] = 1.0

        # 5. Effects sub-vector (multi-hot)
        s, e = self.block_slices["effects"]
        for eff in c.effects:
            ce = canonicalize_predicate(eff)
            if ce in self.vocab.effects:
                idx = self.vocab.effects.index(ce)
                vec[s + idx] = 1.0

        # 6. Constraints sub-vector (multi-hot)
        s, e = self.block_slices["constraints"]
        for k in c.constraints:
            if k in self.vocab.constraints:
                idx = self.vocab.constraints.index(k)
                vec[s + idx] = 1.0

        # 7. Resources sub-vector (multi-hot)
        s, e = self.block_slices["resources"]
        for r in c.resources:
            if r in self.vocab.resources:
                idx = self.vocab.resources.index(r)
                vec[s + idx] = 1.0

        # 8. Mechanism sub-vector (multi-hot)
        s, e = self.block_slices["mechanism"]
        for k_m, v_m in c.mechanism.items():
            key = f"{k_m}={v_m}"
            if key in self.vocab.mechanism:
                idx = self.vocab.mechanism.index(key)
                vec[s + idx] = 1.0

        # 9. Operational sub-vector (normalized numerical attributes)
        s, e = self.block_slices["operational"]
        norm_time = min_max_normalize(c.cost.time, *self.vocab.time_range)
        norm_res = min_max_normalize(c.cost.resource, *self.vocab.res_cost_range)
        norm_mon = min_max_normalize(c.cost.money, *self.vocab.mon_cost_range)
        norm_risk = min_max_normalize(c.cost.risk, *self.vocab.risk_range)
        norm_energy = min_max_normalize(c.cost.energy, *self.vocab.energy_range)

        vec[s + 0] = norm_time
        vec[s + 1] = norm_res
        vec[s + 2] = norm_mon
        vec[s + 3] = norm_risk
        vec[s + 4] = norm_energy
        vec[s + 5] = float(c.reliability)
        vec[s + 6] = float(c.availability)

        return vec

    def encode_state(self, state: State) -> np.ndarray:
        """Encode an application state S into a vector aligned with the feature space."""
        vec = np.zeros(self.dimension, dtype=np.float64)
        preds = state.to_predicates()

        # Map state predicates to preconditions and effects dimensions
        s_p, e_p = self.block_slices["preconditions"]
        for p in preds:
            cp = canonicalize_predicate(p)
            if cp in self.vocab.preconditions:
                idx = self.vocab.preconditions.index(cp)
                vec[s_p + idx] = 1.0

        s_e, e_e = self.block_slices["effects"]
        for p in preds:
            cp = canonicalize_predicate(p)
            if cp in self.vocab.effects:
                idx = self.vocab.effects.index(cp)
                vec[s_e + idx] = 1.0

        return vec

    def encode_goal(self, goal: Goal) -> np.ndarray:
        """Encode a goal specification G into a vector aligned with effect/precondition feature space."""
        vec = np.zeros(self.dimension, dtype=np.float64)
        g_preds = goal.to_predicates()

        # Goal conditions are primarily target effects
        s_e, e_e = self.block_slices["effects"]
        for gp in g_preds:
            cgp = canonicalize_predicate(gp)
            if cgp in self.vocab.effects:
                idx = self.vocab.effects.index(cgp)
                vec[s_e + idx] = 1.0

        s_p, e_p = self.block_slices["preconditions"]
        for gp in g_preds:
            cgp = canonicalize_predicate(gp)
            if cgp in self.vocab.preconditions:
                idx = self.vocab.preconditions.index(cgp)
                vec[s_p + idx] = 1.0

        return vec

    def get_subvector(self, vec: np.ndarray, block_name: str) -> np.ndarray:
        """Extract a specific sub-vector block from a full structured vector."""
        if block_name not in self.block_slices:
            raise KeyError(f"Unknown block name '{block_name}'")
        s, e = self.block_slices[block_name]
        return vec[s:e]


class CapabilityPCAEncoder:
    """
    Dimensionality reduction component mapping high-dimensional structured capability vectors V(C_i)
    to a compact, dense numerical vector space e(C_i) in R^d using PCA.
    """
    def __init__(self, n_components: int = 16, random_state: int = 42):
        self.n_components = n_components
        self.pca = PCA(n_components=n_components, random_state=random_state)
        self.is_fitted = False

    def fit(self, structured_vectors: np.ndarray) -> "CapabilityPCAEncoder":
        """Fit PCA model on matrix of structured capability vectors [N, D]."""
        self.pca.fit(structured_vectors)
        self.is_fitted = True
        return self

    def transform(self, structured_vectors: np.ndarray) -> np.ndarray:
        """Project structured vectors to dense lower-dimensional space [N, d]."""
        if not self.is_fitted:
            raise RuntimeError("PCA encoder must be fitted before calling transform()")
        return self.pca.transform(structured_vectors)

    def fit_transform(self, structured_vectors: np.ndarray) -> np.ndarray:
        return self.fit(structured_vectors).transform(structured_vectors)
