from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

VALID_PREDICATE_OPERATORS = {"=", "!=", ">", ">=", "<", "<=", "in"}


class CapabilityType(str, Enum):
    API = "API"
    DATABASE = "DATABASE"
    GUI = "GUI"
    EVENT = "EVENT"
    FUNCTION = "FUNCTION"
    FILE = "FILE"
    COMPUTATION = "COMPUTATION"
    MESSAGE = "MESSAGE"
    SERVICE = "SERVICE"
    COMPOSITE = "COMPOSITE"


@dataclass
class Predicate:
    name: str
    operator: str
    value: Any

    def __post_init__(self):
        if self.operator not in VALID_PREDICATE_OPERATORS:
            raise ValueError(f"Invalid predicate operator '{self.operator}'. Must be one of {VALID_PREDICATE_OPERATORS}")


@dataclass
class IOField:
    name: str
    type: str
    domain: Optional[str] = None
    required: bool = True


@dataclass
class Constraint:
    expression: str
    variable: str = ""
    operator: str = ""
    limit: Any = None


@dataclass
class Resource:
    name: str
    resource_type: str = "SHARED"


@dataclass
class OperationalCost:
    execution_time_ms: float = 0.0
    monetary_cost: float = 0.0
    resource_cost: float = 0.0
    risk: float = 0.0
    energy_cost: float = 0.0

    def __post_init__(self):
        if self.execution_time_ms < 0:
            raise ValueError("execution_time_ms must be non-negative")
        if self.monetary_cost < 0:
            raise ValueError("monetary_cost must be non-negative")
        if self.resource_cost < 0:
            raise ValueError("resource_cost must be non-negative")
        if self.energy_cost < 0:
            raise ValueError("energy_cost must be non-negative")
        if not (0.0 <= self.risk <= 1.0):
            raise ValueError("risk must be between 0.0 and 1.0")


@dataclass
class Capability:
    id: str
    name: str
    T: CapabilityType
    I: list[IOField] = field(default_factory=list)
    O: list[IOField] = field(default_factory=list)
    P: list[Predicate] = field(default_factory=list)
    E: list[Predicate] = field(default_factory=list)
    K: list[Constraint] = field(default_factory=list)
    R: list[Resource] = field(default_factory=list)
    Q: OperationalCost = field(default_factory=OperationalCost)
    Rel: float = 1.0
    A: float = 1.0
    M: dict[str, str] = field(default_factory=dict)
    components: list[str] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.T, str):
            self.T = CapabilityType(self.T)
        if not (0.0 <= self.Rel <= 1.0):
            raise ValueError(f"Reliability must be in [0, 1], got {self.Rel}")
        if not (0.0 <= self.A <= 1.0):
            raise ValueError(f"Availability must be in [0, 1], got {self.A}")


@dataclass
class State:
    id: str
    values: dict[str, Any] = field(default_factory=dict)


@dataclass
class Goal:
    id: str
    conditions: list[Predicate] = field(default_factory=list)
