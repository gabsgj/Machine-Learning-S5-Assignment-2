from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from src.models.state import StateVariable, StateVariableType
from src.models.capability import CapabilityType


@dataclass
class SubspaceSlice:
    name: str
    start: int
    end: int

    @property
    def dim(self) -> int:
        return self.end - self.start


class EmbeddingSchema:
    """
    Manages structured subspace definitions, feature index offsets,
    and categorical registries for mapping formal entities to Euclidean vectors.
    """
    def __init__(
        self,
        state_variables: Optional[List[StateVariable]] = None,
        resource_vocab: Optional[List[str]] = None,
        io_vocab: Optional[List[str]] = None,
        io_dim: int = 16,
        mech_dim: int = 8
    ):
        self.state_variables = state_variables or []
        self.state_var_map: Dict[str, StateVariable] = {v.name: v for v in self.state_variables}

        # Build state variable layout
        self.var_offsets: Dict[str, int] = {}
        self.var_dims: Dict[str, int] = {}
        self.enum_mappings: Dict[str, Dict[Any, int]] = {}

        current_offset = 0
        for var in self.state_variables:
            self.var_offsets[var.name] = current_offset
            if var.var_type == StateVariableType.BOOLEAN:
                dim = 1
            elif var.var_type == StateVariableType.ENUM:
                domain = var.domain or []
                dim = max(len(domain), 1)
                self.enum_mappings[var.name] = {val: idx for idx, val in enumerate(domain)}
            elif var.var_type in (StateVariableType.INTEGER, StateVariableType.FLOAT):
                dim = 1
            else:
                dim = 1
            self.var_dims[var.name] = dim
            current_offset += dim

        self.state_dim = max(current_offset, 1)

        # Standard Capability Types
        self.capability_types = list(CapabilityType)
        self.type_dim = len(self.capability_types)

        # Standard Resource Registry
        default_resources = [
            "Database", "PaymentGateway", "Network", "FileSystem", "GPU",
            "AuthToken", "ExternalService", "MessageQueue", "EmailService", "InventorySystem"
        ]
        self.resource_vocab = sorted(list(set((resource_vocab or []) + default_resources)))
        self.resource_dim = len(self.resource_vocab)
        self.resource_index = {r.lower(): i for i, r in enumerate(self.resource_vocab)}

        # IO Subspace
        self.io_dim = io_dim

        # Operational Subspace: [time, res_cost, money, risk, energy, log_rel, avail]
        self.ops_dim = 7

        # Mechanism Subspace
        self.mech_dim = mech_dim

        # Calculate Capability Subspaces
        # 1. Precondition: val (state_dim) + mask (state_dim) = 2 * state_dim
        # 2. Effect: val (state_dim) + mask (state_dim) = 2 * state_dim
        # 3. Input: io_dim
        # 4. Output: io_dim
        # 5. Type: type_dim
        # 6. Resources: resource_dim
        # 7. Operational: ops_dim
        # 8. Mechanism: mech_dim
        idx = 0
        self.slice_pre_val = SubspaceSlice("pre_val", idx, idx + self.state_dim); idx += self.state_dim
        self.slice_pre_mask = SubspaceSlice("pre_mask", idx, idx + self.state_dim); idx += self.state_dim
        self.slice_eff_val = SubspaceSlice("eff_val", idx, idx + self.state_dim); idx += self.state_dim
        self.slice_eff_mask = SubspaceSlice("eff_mask", idx, idx + self.state_dim); idx += self.state_dim
        self.slice_in = SubspaceSlice("input", idx, idx + self.io_dim); idx += self.io_dim
        self.slice_out = SubspaceSlice("output", idx, idx + self.io_dim); idx += self.io_dim
        self.slice_type = SubspaceSlice("type", idx, idx + self.type_dim); idx += self.type_dim
        self.slice_res = SubspaceSlice("resources", idx, idx + self.resource_dim); idx += self.resource_dim
        self.slice_ops = SubspaceSlice("operational", idx, idx + self.ops_dim); idx += self.ops_dim
        self.slice_mech = SubspaceSlice("mechanism", idx, idx + self.mech_dim); idx += self.mech_dim

        self.capability_dim = idx

        # Normalization scale factors for operational attributes
        self.time_norm = 1000.0   # 1 second = 1.0
        self.money_norm = 1.0     # $1.00 = 1.0
        self.res_norm = 10.0      # 10 units = 1.0
        self.energy_norm = 1.0    # 1 kWh = 1.0

    def encode_variable_value(self, var_name: str, value: Any) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (value_vector, mask_vector) for a single variable."""
        if var_name not in self.var_offsets:
            return np.zeros(0, dtype=np.float32), np.zeros(0, dtype=np.float32)

        dim = self.var_dims[var_name]
        val_vec = np.zeros(dim, dtype=np.float32)
        mask_vec = np.ones(dim, dtype=np.float32)

        var = self.state_var_map[var_name]
        if var.var_type == StateVariableType.BOOLEAN:
            val_vec[0] = 1.0 if bool(value) else 0.0
        elif var.var_type == StateVariableType.ENUM:
            mapping = self.enum_mappings.get(var_name, {})
            idx = mapping.get(value)
            if idx is not None and idx < dim:
                val_vec[idx] = 1.0
            else:
                # Value not recognized or None
                mask_vec[:] = 0.0
        elif var.var_type in (StateVariableType.INTEGER, StateVariableType.FLOAT):
            if value is not None:
                val_vec[0] = float(value)
            else:
                mask_vec[0] = 0.0
        else:
            val_vec[0] = float(hash(str(value)) % 1000) / 1000.0

        return val_vec, mask_vec
