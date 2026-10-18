from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class State:
    id: str
    values: Dict[str, Any]


@dataclass
class Goal:
    id: str
    conditions: Dict[str, Any]


@dataclass
class Capability:
    id: str
    name: str
    description: str
    type: str
    mechanism: str

    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)

    preconditions: Dict[str, Any] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)

    constraints: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)

    time_cost: float = 0.0
    money_cost: float = 0.0
    resource_cost: float = 0.0
    risk: float = 0.0

    reliability: float = 1.0
    available: bool = True

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Capability":
        qos = data.get("qos", {})

        return Capability(
            id=data["id"],
            name=data.get("name", data["id"]),
            description=data.get("description", ""),
            type=data.get("type", "FUNCTION"),
            mechanism=data.get("mechanism", ""),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            preconditions=data.get("preconditions", {}),
            effects=data.get("effects", {}),
            constraints=data.get("constraints", []),
            resources=data.get("resources", []),
            time_cost=qos.get("timeCostMs", 0.0),
            money_cost=qos.get("moneyCost", 0.0),
            resource_cost=qos.get("resourceCost", 0.0),
            risk=qos.get("risk", 0.0),
            reliability=data.get("reliability", 1.0),
            available=data.get("available", True),
        )


@dataclass
class CompositeCapability:
    id: str
    name: str
    components: List[str]

    preconditions: Dict[str, Any]
    effects: Dict[str, Any]

    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]

    resources: List[str]

    time_cost: float
    money_cost: float
    resource_cost: float
    risk: float

    reliability: float
    available: bool = True