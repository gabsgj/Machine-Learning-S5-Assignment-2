from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class StateVariableType(str, Enum):
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    ENUM = "ENUM"
    STRING = "STRING"


@dataclass
class StateVariable:
    name: str
    var_type: StateVariableType
    domain: Optional[List[Any]] = None
    default_value: Any = None
    description: str = ""

    def validate_value(self, val: Any) -> bool:
        if val is None:
            return True
        if self.var_type == StateVariableType.BOOLEAN:
            return isinstance(val, bool)
        elif self.var_type in (StateVariableType.INTEGER, StateVariableType.FLOAT):
            return isinstance(val, (int, float))
        elif self.var_type == StateVariableType.ENUM:
            return self.domain is None or val in self.domain
        return True


@dataclass
class ApplicationState:
    """
    Formal state of an application at a specific point in time:
    S = {(x_1, v_1), (x_2, v_2), ..., (x_n, v_n)}
    """
    values: Dict[str, Any] = field(default_factory=dict)
    name: str = "State"

    def get(self, var_name: str, default: Any = None) -> Any:
        return self.values.get(var_name, default)

    def set(self, var_name: str, value: Any) -> None:
        self.values[var_name] = value

    def clone(self, new_name: Optional[str] = None) -> ApplicationState:
        return ApplicationState(
            values=dict(self.values),
            name=new_name or f"{self.name}_copy"
        )

    def diff(self, other: ApplicationState) -> Dict[str, tuple[Any, Any]]:
        """Returns {var: (self_val, other_val)} for differing variables."""
        differences = {}
        all_keys = set(self.values.keys()) | set(other.values.keys())
        for k in all_keys:
            v1 = self.values.get(k)
            v2 = other.values.get(k)
            if v1 != v2:
                differences[k] = (v1, v2)
        return differences

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "values": dict(self.values)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ApplicationState:
        return cls(
            name=data.get("name", "State"),
            values=dict(data.get("values", {}))
        )

    def __repr__(self) -> str:
        items = ", ".join(f"{k}={v}" for k, v in sorted(self.values.items()))
        return f"ApplicationState({self.name}: {items})"
