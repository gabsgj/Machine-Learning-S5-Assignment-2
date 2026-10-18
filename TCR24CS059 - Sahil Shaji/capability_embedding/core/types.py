"""
Core types, enumerations, and data structures for formal capability representations.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field


class CapabilityType(str, Enum):
    """
    Formal capability types defining the realization mechanism (Section 4.1).
    T_i in {API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE}
    """
    API = "API"
    DATABASE = "DATABASE"
    GUI = "GUI"
    EVENT = "EVENT"
    FUNCTION = "FUNCTION"
    FILE = "FILE"
    COMPUTATION = "COMPUTATION"
    MESSAGE = "MESSAGE"
    SERVICE = "SERVICE"


class VariableType(str, Enum):
    """Data types for state variables and input/output domains."""
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    CATEGORICAL = "CATEGORICAL"
    UUID = "UUID"
    OBJECT = "OBJECT"


@dataclass(frozen=True)
class ExecutionMechanism:
    """
    Implementation-specific execution details (Section 4.1).
    Examples:
      - API: method='POST', endpoint='/orders'
      - Database: operation='INSERT', table='orders'
      - GUI: action='CLICK', component='submit_button'
      - Event: trigger='OrderCreated', handler='SendNotification'
    """
    mechanism_type: CapabilityType
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mechanism_type": self.mechanism_type.value,
            "details": dict(self.details)
        }


@dataclass(frozen=True)
class InputSpec:
    """
    Formal specification of an input requirement (Section 4.2).
    i_j = (name, type, domain, required)
    """
    name: str
    var_type: str = "STRING"
    domain: str = "any"
    required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.var_type,
            "domain": self.domain,
            "required": self.required
        }


@dataclass(frozen=True)
class OutputSpec:
    """
    Formal specification of a produced output (Section 4.2).
    o_j = (name, type, domain)
    """
    name: str
    var_type: str = "STRING"
    domain: str = "any"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.var_type,
            "domain": self.domain
        }
