from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class State:
    values: Dict[str, Any]


@dataclass
class Goal:
    conditions: Dict[str, Any]


@dataclass
class Capability:
    name: str
    capability_type: str

    inputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    preconditions: Dict[str, Any] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)

    constraints: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)

    cost_time: float = 0.0
    cost_resource: float = 0.0
    cost_money: float = 0.0

    risk: float = 0.0
    reliability: float = 1.0
    availability: float = 1.0

    execution: Dict[str, Any] = field(default_factory=dict)

    # Used for composite capabilities
    components: List[str] = field(default_factory=list)
    component_types: List[str] = field(default_factory=list)