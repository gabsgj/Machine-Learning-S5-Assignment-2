from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from src.models.state import ApplicationState
from src.models.goal import ComparisonOp


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


@dataclass
class InputSpec:
    name: str
    data_type: str
    domain: Optional[str] = None
    required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "domain": self.domain,
            "required": self.required
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InputSpec:
        return cls(
            name=data["name"],
            data_type=data.get("data_type", "string"),
            domain=data.get("domain"),
            required=data.get("required", True)
        )


@dataclass
class OutputSpec:
    name: str
    data_type: str
    domain: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "domain": self.domain
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OutputSpec:
        return cls(
            name=data["name"],
            data_type=data.get("data_type", "string"),
            domain=data.get("domain")
        )


@dataclass
class Precondition:
    variable: str
    expected_value: Any
    op: ComparisonOp = ComparisonOp.EQ

    def is_satisfied(self, state: ApplicationState) -> bool:
        val = state.get(self.variable)
        if val is None:
            return False
        if self.op == ComparisonOp.EQ:
            return val == self.expected_value
        elif self.op == ComparisonOp.NEQ:
            return val != self.expected_value
        elif self.op == ComparisonOp.GT:
            return float(val) > float(self.expected_value)
        elif self.op == ComparisonOp.GTE:
            return float(val) >= float(self.expected_value)
        elif self.op == ComparisonOp.LT:
            return float(val) < float(self.expected_value)
        elif self.op == ComparisonOp.LTE:
            return float(val) <= float(self.expected_value)
        elif self.op == ComparisonOp.IN:
            return val in self.expected_value
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable": self.variable,
            "expected_value": self.expected_value,
            "op": self.op.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Precondition:
        return cls(
            variable=data["variable"],
            expected_value=data["expected_value"],
            op=ComparisonOp(data.get("op", "=="))
        )

    def __repr__(self) -> str:
        return f"{self.variable} {self.op.value} {self.expected_value}"


@dataclass
class Effect:
    variable: str
    new_value: Any
    action: str = "SET"  # SET, INCREMENT, DECREMENT, APPEND

    def apply(self, state: ApplicationState) -> None:
        if self.action == "SET":
            state.set(self.variable, self.new_value)
        elif self.action == "INCREMENT":
            current = state.get(self.variable, 0)
            state.set(self.variable, current + self.new_value)
        elif self.action == "DECREMENT":
            current = state.get(self.variable, 0)
            state.set(self.variable, current - self.new_value)
        elif self.action == "APPEND":
            current = list(state.get(self.variable, []))
            current.append(self.new_value)
            state.set(self.variable, current)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable": self.variable,
            "new_value": self.new_value,
            "action": self.action
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Effect:
        return cls(
            variable=data["variable"],
            new_value=data["new_value"],
            action=data.get("action", "SET")
        )

    def __repr__(self) -> str:
        if self.action == "SET":
            return f"{self.variable} := {self.new_value}"
        return f"{self.variable} {self.action} {self.new_value}"


@dataclass
class CapabilityConstraint:
    name: str
    expression: str
    constraint_type: str = "STATE"  # INPUT, STATE, RESOURCE, SECURITY, TEMPORAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "expression": self.expression,
            "constraint_type": self.constraint_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CapabilityConstraint:
        return cls(
            name=data.get("name", "constraint"),
            expression=data.get("expression", ""),
            constraint_type=data.get("constraint_type", "STATE")
        )


@dataclass
class QualityAttributes:
    """Q_i = (C_time, C_resource, C_money, C_risk, C_energy)"""
    time_ms: float = 100.0
    resource_cost: float = 1.0
    monetary_cost: float = 0.01
    risk: float = 0.05
    energy_cost: float = 0.01

    def to_vector(self) -> List[float]:
        return [self.time_ms, self.resource_cost, self.monetary_cost, self.risk, self.energy_cost]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time_ms": self.time_ms,
            "resource_cost": self.resource_cost,
            "monetary_cost": self.monetary_cost,
            "risk": self.risk,
            "energy_cost": self.energy_cost
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QualityAttributes:
        return cls(
            time_ms=float(data.get("time_ms", 100.0)),
            resource_cost=float(data.get("resource_cost", 1.0)),
            monetary_cost=float(data.get("monetary_cost", 0.01)),
            risk=float(data.get("risk", 0.05)),
            energy_cost=float(data.get("energy_cost", 0.01))
        )


@dataclass
class ExecutionMechanism:
    """M_i records implementation-specific details."""
    mechanism_type: str = "HTTP_API"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mechanism_type": self.mechanism_type,
            "details": dict(self.details)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionMechanism:
        return cls(
            mechanism_type=data.get("mechanism_type", "HTTP_API"),
            details=dict(data.get("details", {}))
        )


@dataclass
class Capability:
    """
    Formal Capability Representation:
    C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
    """
    id: str
    name: str
    type: CapabilityType = CapabilityType.API
    inputs: List[InputSpec] = field(default_factory=list)
    outputs: List[OutputSpec] = field(default_factory=list)
    preconditions: List[Precondition] = field(default_factory=list)
    effects: List[Effect] = field(default_factory=list)
    constraints: List[CapabilityConstraint] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    quality: QualityAttributes = field(default_factory=QualityAttributes)
    reliability: float = 0.99
    availability: float = 1.0
    mechanism: ExecutionMechanism = field(default_factory=ExecutionMechanism)
    description: str = ""
    sub_capabilities: List[str] = field(default_factory=list)

    @property
    def is_composite(self) -> bool:
        return len(self.sub_capabilities) > 0

    def is_applicable(self, state: ApplicationState) -> bool:
        """C_i is applicable to S <=> S |= P_i"""
        return all(p.is_satisfied(state) for p in self.preconditions)

    def apply(self, state: ApplicationState) -> ApplicationState:
        """C_i : S -> S', S' = Apply(S, E_i)"""
        new_state = state.clone(new_name=f"{state.name}_after_{self.id}")
        for effect in self.effects:
            effect.apply(new_state)
        return new_state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "preconditions": [p.to_dict() for p in self.preconditions],
            "effects": [e.to_dict() for e in self.effects],
            "constraints": [k.to_dict() for k in self.constraints],
            "resources": list(self.resources),
            "quality": self.quality.to_dict(),
            "reliability": self.reliability,
            "availability": self.availability,
            "mechanism": self.mechanism.to_dict(),
            "description": self.description,
            "sub_capabilities": list(self.sub_capabilities)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Capability:
        return cls(
            id=data["id"],
            name=data["name"],
            type=CapabilityType(data.get("type", "API")),
            inputs=[InputSpec.from_dict(i) for i in data.get("inputs", [])],
            outputs=[OutputSpec.from_dict(o) for o in data.get("outputs", [])],
            preconditions=[Precondition.from_dict(p) for p in data.get("preconditions", [])],
            effects=[Effect.from_dict(e) for e in data.get("effects", [])],
            constraints=[CapabilityConstraint.from_dict(k) for k in data.get("constraints", [])],
            resources=list(data.get("resources", [])),
            quality=QualityAttributes.from_dict(data.get("quality", {})),
            reliability=float(data.get("reliability", 0.99)),
            availability=float(data.get("availability", 1.0)),
            mechanism=ExecutionMechanism.from_dict(data.get("mechanism", {})),
            description=data.get("description", ""),
            sub_capabilities=list(data.get("sub_capabilities", []))
        )

    def __repr__(self) -> str:
        tag = "[COMPOSITE] " if self.is_composite else ""
        return f"Capability({tag}{self.id}: {self.name}, Type={self.type.value}, Rel={self.reliability:.2f}, Avail={self.availability:.2f})"
