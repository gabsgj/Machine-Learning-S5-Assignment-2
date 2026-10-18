"""
Vocabulary and Schema Registries for canonical feature indexing in vector spaces.
"""

from typing import Dict, List, Any, Optional, Set
from ..core.types import CapabilityType, VariableType


class StateVariableRegistry:
    """
    Maintains a canonical dictionary of state variables, their types, and index offsets.
    Enables consistent encoding of States, Goals, Preconditions, and Effects into R^{D_s}.
    """

    def __init__(self):
        self.var_to_idx: Dict[str, int] = {}
        self.idx_to_var: Dict[int, str] = {}
        self.var_types: Dict[str, VariableType] = {}
        self.categorical_domains: Dict[str, List[str]] = {}
        self._dim: int = 0

    def register_variable(
        self,
        name: str,
        var_type: VariableType = VariableType.BOOLEAN,
        domain: Optional[List[str]] = None
    ) -> int:
        """Register a variable. If already registered, returns its existing index."""
        if name in self.var_to_idx:
            return self.var_to_idx[name]

        idx = self._dim
        self.var_to_idx[name] = idx
        self.idx_to_var[idx] = name
        self.var_types[name] = var_type

        if var_type == VariableType.CATEGORICAL and domain:
            self.categorical_domains[name] = list(domain)

        self._dim += 1
        return idx

    @property
    def dimension(self) -> int:
        return self._dim

    def get_index(self, name: str) -> Optional[int]:
        return self.var_to_idx.get(name)

    def get_variable_name(self, idx: int) -> Optional[str]:
        return self.idx_to_var.get(idx)


class ResourceRegistry:
    """Canonical registry of system resources."""

    def __init__(self):
        self.res_to_idx: Dict[str, int] = {}
        self.idx_to_res: Dict[int, str] = {}
        self._dim: int = 0

    def register_resource(self, name: str) -> int:
        if name in self.res_to_idx:
            return self.res_to_idx[name]
        idx = self._dim
        self.res_to_idx[name] = idx
        self.idx_to_res[idx] = name
        self._dim += 1
        return idx

    @property
    def dimension(self) -> int:
        return self._dim

    def get_index(self, name: str) -> Optional[int]:
        return self.res_to_idx.get(name)


class SchemaRegistry:
    """
    Combined registry containing state variable definitions, resource types,
    and capability mechanism vocabularies for an application domain.
    """

    def __init__(self):
        self.state_vars = StateVariableRegistry()
        self.resources = ResourceRegistry()
        self.type_to_idx = {cap_type: i for i, cap_type in enumerate(CapabilityType)}

    def auto_register_from_domain(
        self,
        states: Optional[List[Any]] = None,
        capabilities: Optional[List[Any]] = None,
        goals: Optional[List[Any]] = None
    ) -> None:
        """Automatically registers all variables and resources observed in a domain."""
        if states:
            for s in states:
                for k, v in s.variables.items():
                    v_type = VariableType.BOOLEAN if isinstance(v, bool) else (
                        VariableType.INTEGER if isinstance(v, int) else (
                            VariableType.FLOAT if isinstance(v, float) else VariableType.CATEGORICAL
                        )
                    )
                    self.state_vars.register_variable(k, v_type)

        if goals:
            for g in goals:
                for k in g.conditions.keys():
                    if self.state_vars.get_index(k) is None:
                        self.state_vars.register_variable(k, VariableType.BOOLEAN)

        if capabilities:
            for c in capabilities:
                for k in c.preconditions.keys():
                    if self.state_vars.get_index(k) is None:
                        self.state_vars.register_variable(k, VariableType.BOOLEAN)
                for k in c.effects.keys():
                    if self.state_vars.get_index(k) is None:
                        self.state_vars.register_variable(k, VariableType.BOOLEAN)
                for r in c.resources:
                    self.resources.register_resource(r.name)
