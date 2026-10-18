"""
Multi-Faceted Vector Space Container and Subspace Projections.
Section 6: Formal embedding representation phi_C : C -> R^d.
"""

from typing import Dict, Any, Optional, Tuple
import numpy as np


class SubspaceLayout:
    """
    Defines coordinate index slices for each sub-manifold in the embedding space:
      - req: Precondition values [0 : Ds] and Precondition mask [Ds : 2*Ds]
      - eff: Effect values [2*Ds : 3*Ds] and Effect mask [3*Ds : 4*Ds]
      - io: Input hash [4*Ds : 4*Ds + D_io] and Output hash [4*Ds + D_io : 4*Ds + 2*D_io]
      - ops: Operational attributes [4*Ds + 2*D_io : 4*Ds + 2*D_io + D_ops]
      - impl: Type one-hot + mechanism [4*Ds + 2*D_io + D_ops : Total_D]
    """

    def __init__(self, num_state_vars: int, io_dim: int = 16, num_resources: int = 8, impl_dim: int = 16):
        self.num_state_vars = max(num_state_vars, 1)
        self.io_dim = io_dim
        self.num_resources = max(num_resources, 1)
        self.num_ops_scalars = 7  # time, money, resource_cost, energy, -log(rel), -log(avail), risk
        self.ops_dim = self.num_ops_scalars + self.num_resources
        self.impl_dim = impl_dim

        # Offsets
        ds = self.num_state_vars
        self.req_val_slice = slice(0, ds)
        self.req_mask_slice = slice(ds, 2 * ds)
        self.eff_val_slice = slice(2 * ds, 3 * ds)
        self.eff_mask_slice = slice(3 * ds, 4 * ds)

        offset = 4 * ds
        self.io_in_slice = slice(offset, offset + io_dim)
        self.io_out_slice = slice(offset + io_dim, offset + 2 * io_dim)

        offset = offset + 2 * io_dim
        self.ops_slice = slice(offset, offset + self.ops_dim)

        offset = offset + self.ops_dim
        self.impl_slice = slice(offset, offset + impl_dim)

        self.total_dim = offset + impl_dim

    def __repr__(self) -> str:
        return f"SubspaceLayout(vars={self.num_state_vars}, total_dim={self.total_dim})"


class MultiFacetedEmbedding:
    """
    Structured numerical embedding of a capability, composed entity, state, or goal.
    Provides mathematically grounded projections onto specific sub-manifolds.
    """

    def __init__(self, vector: np.ndarray, layout: SubspaceLayout, name: str = "", entity_type: str = "capability"):
        self.vector = np.asarray(vector, dtype=np.float64).flatten()
        self.layout = layout
        self.name = name
        self.entity_type = entity_type

        if len(self.vector) != self.layout.total_dim:
            raise ValueError(
                f"Vector dimension mismatch: got {len(self.vector)}, expected {self.layout.total_dim}"
            )

    @property
    def raw(self) -> np.ndarray:
        return self.vector

    # 1. Precondition Subspace (Requirements)
    @property
    def req_values(self) -> np.ndarray:
        return self.vector[self.layout.req_val_slice]

    @property
    def req_mask(self) -> np.ndarray:
        return self.vector[self.layout.req_mask_slice]

    @property
    def req_vector(self) -> np.ndarray:
        """Combined requirement vector (values masked by relevance)."""
        return self.req_values * self.req_mask

    # 2. Effect Subspace (State Transformation)
    @property
    def eff_values(self) -> np.ndarray:
        return self.vector[self.layout.eff_val_slice]

    @property
    def eff_mask(self) -> np.ndarray:
        return self.vector[self.layout.eff_mask_slice]

    @property
    def delta_vector(self) -> np.ndarray:
        """Effective state transformation delta: e * m_E."""
        return self.eff_values * self.eff_mask

    # 3. Input-Output Dataflow Subspace
    @property
    def io_inputs(self) -> np.ndarray:
        return self.vector[self.layout.io_in_slice]

    @property
    def io_outputs(self) -> np.ndarray:
        return self.vector[self.layout.io_out_slice]

    # 4. Operational Quality Subspace
    @property
    def operational_vector(self) -> np.ndarray:
        return self.vector[self.layout.ops_slice]

    @property
    def execution_time(self) -> float:
        return float(self.operational_vector[0])

    @property
    def monetary_cost(self) -> float:
        return float(self.operational_vector[1])

    @property
    def reliability(self) -> float:
        """Decoded reliability in [0, 1] from negative log."""
        neg_log_rel = float(self.operational_vector[4])
        return float(np.exp(-np.clip(neg_log_rel, 0.0, 50.0)))

    @property
    def availability(self) -> float:
        """Decoded availability in [0, 1] from negative log."""
        neg_log_avail = float(self.operational_vector[5])
        return float(np.exp(-np.clip(neg_log_avail, 0.0, 50.0)))

    @property
    def risk(self) -> float:
        return float(self.operational_vector[6])

    # 5. Implementation Mechanism Subspace
    @property
    def implementation_vector(self) -> np.ndarray:
        return self.vector[self.layout.impl_slice]

    def align_to_layout(self, target_layout: "SubspaceLayout") -> "MultiFacetedEmbedding":
        """Re-projects embedding into a larger or updated subspace layout."""
        if self.layout.total_dim == target_layout.total_dim:
            return self
        new_vec = np.zeros(target_layout.total_dim, dtype=np.float64)
        ds_min = min(self.layout.num_state_vars, target_layout.num_state_vars)
        new_vec[0:ds_min] = self.req_values[:ds_min]
        new_vec[target_layout.req_mask_slice.start : target_layout.req_mask_slice.start + ds_min] = self.req_mask[:ds_min]
        new_vec[target_layout.eff_val_slice.start : target_layout.eff_val_slice.start + ds_min] = self.eff_values[:ds_min]
        new_vec[target_layout.eff_mask_slice.start : target_layout.eff_mask_slice.start + ds_min] = self.eff_mask[:ds_min]
        io_min = min(self.layout.io_dim, target_layout.io_dim)
        new_vec[target_layout.io_in_slice.start : target_layout.io_in_slice.start + io_min] = self.io_inputs[:io_min]
        new_vec[target_layout.io_out_slice.start : target_layout.io_out_slice.start + io_min] = self.io_outputs[:io_min]
        ops_min = min(self.layout.ops_dim, target_layout.ops_dim)
        new_vec[target_layout.ops_slice.start : target_layout.ops_slice.start + ops_min] = self.operational_vector[:ops_min]
        impl_min = min(self.layout.impl_dim, target_layout.impl_dim)
        new_vec[target_layout.impl_slice.start : target_layout.impl_slice.start + impl_min] = self.implementation_vector[:impl_min]
        return MultiFacetedEmbedding(new_vec, target_layout, name=self.name, entity_type=self.entity_type)

    # Mathematical norms and projections
    def norm(self) -> float:
        return float(np.linalg.norm(self.vector))

    def cosine_similarity(self, other: "MultiFacetedEmbedding", subspace: Optional[str] = None) -> float:
        """
        Compute cosine similarity over the full vector or a targeted subspace.
        Subspaces: 'full', 'effect', 'requirement', 'io', 'operational', 'implementation'.
        """
        if subspace is None or subspace == "full":
            v1, v2 = self.vector, other.vector
        elif subspace in ("effect", "eff", "functional"):
            v1, v2 = self.delta_vector, other.delta_vector
        elif subspace in ("requirement", "req", "precondition"):
            v1, v2 = self.req_vector, other.req_vector
        elif subspace == "io":
            v1 = np.concatenate([self.io_inputs, self.io_outputs])
            v2 = np.concatenate([other.io_inputs, other.io_outputs])
        elif subspace == "operational":
            v1, v2 = self.operational_vector, other.operational_vector
        elif subspace in ("implementation", "impl", "mechanism"):
            v1, v2 = self.implementation_vector, other.implementation_vector
        else:
            raise ValueError(f"Unknown subspace: {subspace}")

        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 < 1e-12 or norm2 < 1e-12:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def euclidean_distance(self, other: "MultiFacetedEmbedding", subspace: Optional[str] = None) -> float:
        if subspace is None or subspace == "full":
            return float(np.linalg.norm(self.vector - other.vector))
        elif subspace in ("effect", "eff", "functional"):
            return float(np.linalg.norm(self.delta_vector - other.delta_vector))
        elif subspace in ("requirement", "req"):
            return float(np.linalg.norm(self.req_vector - other.req_vector))
        elif subspace == "operational":
            return float(np.linalg.norm(self.operational_vector - other.operational_vector))
        elif subspace in ("implementation", "impl"):
            return float(np.linalg.norm(self.implementation_vector - other.implementation_vector))
        else:
            raise ValueError(f"Unknown subspace: {subspace}")

    def __repr__(self) -> str:
        return f"Embedding(name='{self.name}', type={self.entity_type}, dim={len(self.vector)})"
