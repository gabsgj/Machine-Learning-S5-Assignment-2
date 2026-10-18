from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class IOField:
    name: str
    type: str
    domain: str = ""
    required: bool = True


@dataclass
class Condition:
    name: str
    value: Any = True

    def key(self) -> str:
        return f"{self.name}={str(self.value).lower()}"


@dataclass
class Capability:
    name: str
    type: str
    inputs: List[IOField] = field(default_factory=list)
    outputs: List[IOField] = field(default_factory=list)
    preconditions: List[Condition] = field(default_factory=list)
    effects: List[Condition] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    cost: float = 0.0
    reliability: float = 1.0
    availability: float = 1.0
    risk: float = 0.0
    execution_mechanism: Dict[str, Any] = field(default_factory=dict)


@dataclass
class State:
    values: Dict[str, Any]


@dataclass
class Goal:
    conditions: List[Condition]


def condition_from_dict(item: Dict[str, Any]) -> Condition:
    return Condition(name=item["name"], value=item.get("value", True))


def io_from_dict(item: Dict[str, Any]) -> IOField:
    return IOField(
        name=item["name"],
        type=item["type"],
        domain=item.get("domain", ""),
        required=item.get("required", True),
    )


def capability_from_dict(item: Dict[str, Any]) -> Capability:
    return Capability(
        name=item["name"],
        type=item["type"],
        inputs=[io_from_dict(x) for x in item.get("inputs", [])],
        outputs=[io_from_dict(x) for x in item.get("outputs", [])],
        preconditions=[condition_from_dict(x) for x in item.get("preconditions", [])],
        effects=[condition_from_dict(x) for x in item.get("effects", [])],
        constraints=item.get("constraints", []),
        resources=item.get("resources", []),
        cost=float(item.get("cost", 0.0)),
        reliability=float(item.get("reliability", 1.0)),
        availability=float(item.get("availability", 1.0)),
        risk=float(item.get("risk", 0.0)),
        execution_mechanism=item.get("execution_mechanism", {}),
    )
