from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Condition:
    attribute: str
    operator: str
    value: Any


@dataclass(frozen=True)
class InputSpec:
    name: str
    type: str
    domain: str
    required: bool = True


@dataclass(frozen=True)
class OutputSpec:
    name: str
    type: str
    domain: str


@dataclass(frozen=True)
class Constraint:
    expression: str


@dataclass(frozen=True)
class QualityAttributes:
    execution_time_ms: Optional[float] = None
    resource_cost: Optional[float] = None
    monetary_cost: Optional[float] = None
    risk: Optional[float] = None
    energy_cost: Optional[float] = None


@dataclass
class Capability:
    id: str
    name: str
    type: str
    inputs: List[InputSpec] = field(default_factory=list)
    outputs: List[OutputSpec] = field(default_factory=list)
    preconditions: List[Condition] = field(default_factory=list)
    effects: List[Condition] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    quality: QualityAttributes = field(default_factory=QualityAttributes)
    reliability: float = 1.0
    availability: int = 1
    mechanism: Dict[str, str] = field(default_factory=dict)


State = Dict[str, Any]
Goal = List[Condition]
