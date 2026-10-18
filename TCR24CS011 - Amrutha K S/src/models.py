from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class InputSpec:
    name: str
    type: str
    domain: str
    required: bool = True

@dataclass
class OutputSpec:
    name: str
    type: str
    domain: str

@dataclass
class Cost:
    time: float
    resource: float
    money: float
    risk: float
    energy: float

@dataclass
class Capability:
    id: str
    name: str
    type: str
    inputs: List[InputSpec]
    outputs: List[OutputSpec]
    preconditions: Dict[str, Any]
    effects: Dict[str, Any]
    constraints: List[str]
    resources: List[str]
    cost: Cost
    reliability: float
    availability: float
    mechanism: Dict[str, Any]

@dataclass
class State:
    values: Dict[str, Any]

@dataclass
class Goal:
    conditions: Dict[str, Any]

@dataclass
class CompositeCapability:
    name: str
    components: List[Capability]
    preconditions: Dict[str, Any]
    effects: Dict[str, Any]
