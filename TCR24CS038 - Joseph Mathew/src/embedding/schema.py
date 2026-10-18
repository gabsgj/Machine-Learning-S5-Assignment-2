"""Embedding Schema and Feature Registry.

Defines the partitioned vector space layout and vocabulary mapping for:
- State variables
- Data parameter types
- Functional intents / verbs
- Execution mechanisms
- Operational quality attributes
- Resources
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np


@dataclass
class EmbeddingSchema:
    """Manages dimension mapping and partition offsets for the vector space."""
    state_variables: List[str]
    data_types: List[str]
    resource_types: List[str]
    capability_types: List[str]
    latent_dim: int = 16

    # Dimension slices (computed in __post_init__)
    var_index: Dict[str, int] = field(default_factory=dict)
    type_index: Dict[str, int] = field(default_factory=dict)
    resource_index: Dict[str, int] = field(default_factory=dict)
    cap_type_index: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self.var_index = {v: i for i, v in enumerate(self.state_variables)}
        self.type_index = {t: i for i, t in enumerate(self.data_types)}
        self.resource_index = {r: i for i, r in enumerate(self.resource_types)}
        self.cap_type_index = {c: i for i, c in enumerate(self.capability_types)}

    @property
    def dim_preconditions(self) -> int:
        return len(self.state_variables)

    @property
    def dim_effects(self) -> int:
        return len(self.state_variables)

    @property
    def dim_inputs(self) -> int:
        return len(self.data_types)

    @property
    def dim_outputs(self) -> int:
        return len(self.data_types)

    @property
    def dim_functional(self) -> int:
        return self.latent_dim

    @property
    def dim_mechanism(self) -> int:
        return len(self.capability_types) + 8  # type one-hot + 8 mechanism features

    @property
    def dim_operational(self) -> int:
        return 7  # 5 costs + reliability + availability

    @property
    def dim_resources(self) -> int:
        return len(self.resource_types)

    @property
    def total_dim(self) -> int:
        return (
            self.dim_preconditions
            + self.dim_effects
            + self.dim_inputs
            + self.dim_outputs
            + self.dim_functional
            + self.dim_mechanism
            + self.dim_operational
            + self.dim_resources
        )

    # Slice properties for clean indexing
    @property
    def slice_preconditions(self) -> slice:
        start = 0
        return slice(start, start + self.dim_preconditions)

    @property
    def slice_effects(self) -> slice:
        start = self.dim_preconditions
        return slice(start, start + self.dim_effects)

    @property
    def slice_inputs(self) -> slice:
        start = self.slice_effects.stop
        return slice(start, start + self.dim_inputs)

    @property
    def slice_outputs(self) -> slice:
        start = self.slice_inputs.stop
        return slice(start, start + self.dim_outputs)

    @property
    def slice_functional(self) -> slice:
        start = self.slice_outputs.stop
        return slice(start, start + self.dim_functional)

    @property
    def slice_mechanism(self) -> slice:
        start = self.slice_functional.stop
        return slice(start, start + self.dim_mechanism)

    @property
    def slice_operational(self) -> slice:
        start = self.slice_mechanism.stop
        return slice(start, start + self.dim_operational)

    @property
    def slice_resources(self) -> slice:
        start = self.slice_operational.stop
        return slice(start, start + self.dim_resources)
