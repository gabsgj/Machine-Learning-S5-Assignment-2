from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class Condition:
    variable: str
    operator: str
    value: Any

    def token(self) -> str:
        return f"{self.variable}|{self.operator}|{self.value}"


@dataclass(frozen=True)
class IOField:
    name: str
    type: str
    domain: str = "any"
    required: bool = True

    def token(self) -> str:
        return f"{self.name}|{self.type}|{self.domain}|{self.required}"


@dataclass
class Quality:
    time_ms: float = 0.0
    resource_cost: float = 0.0
    money_cost: float = 0.0
    risk: float = 0.0
    energy: float = 0.0


@dataclass
class Capability:
    name: str
    capability_type: str
    inputs: List[IOField] = field(default_factory=list)
    outputs: List[IOField] = field(default_factory=list)
    preconditions: List[Condition] = field(default_factory=list)
    effects: List[Condition] = field(default_factory=list)
    constraints: List[Condition] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    quality: Quality = field(default_factory=Quality)
    reliability: float = 1.0
    availability: float = 1.0
    mechanism: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)

    @property
    def is_composite(self) -> bool:
        return len(self.components) > 0


@dataclass
class State:
    values: Dict[str, Any]


@dataclass
class Goal:
    conditions: List[Condition]


@dataclass
class CompositeCapability(Capability):
    pass
