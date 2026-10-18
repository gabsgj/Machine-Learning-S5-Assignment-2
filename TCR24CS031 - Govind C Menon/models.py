"""
models.py
==========
Formal Data Models for Capability Vector Embedding System
Compliant with Assignment 2: Design of a Vector Embedding for Capability Composition.

Formal Application Model: A = (S, C, SI, G, R, K)
Formal Capability Model:  Ci = (Ti, Ii, Oi, Pi, Ei, Ki, Ri, Qi, Reli, Ai, Mi)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple


class CapabilityType(str, Enum):
    """Formal capability types Ti in {API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE}."""
    API = "API"
    DATABASE = "DATABASE"
    GUI = "GUI"
    EVENT = "EVENT"
    FUNCTION = "FUNCTION"
    FILE = "FILE"
    COMPUTATION = "COMPUTATION"
    MESSAGE = "MESSAGE"
    SERVICE = "SERVICE"


@dataclass(frozen=True)
class InputSpec:
    """
    Formal input specification: ij = (name, type, domain, required)
    """
    name: str
    data_type: str = "string"
    domain: str = "general"
    required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "domain": self.domain,
            "required": self.required
        }


@dataclass(frozen=True)
class OutputSpec:
    """
    Formal output specification: oj = (name, type, domain)
    """
    name: str
    data_type: str = "string"
    domain: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "domain": self.domain
        }


@dataclass(frozen=True)
class Precondition:
    """
    Formal precondition predicate: pi: variable operator value
    E.g. CartExists == True, CartItemCount > 0, OrderStatus == CREATED
    """
    variable: str
    operator: str = "=="  # "==", "!=", ">", "<", ">=", "<=", "in"
    value: Any = True

    def evaluate(self, state_dict: Dict[str, Any]) -> bool:
        """Evaluates whether this precondition holds in the given state."""
        if self.variable not in state_dict:
            return False
        curr_val = state_dict[self.variable]
        if self.operator == "==":
            return curr_val == self.value
        elif self.operator == "!=":
            return curr_val != self.value
        elif self.operator == ">":
            return curr_val > self.value
        elif self.operator == "<":
            return curr_val < self.value
        elif self.operator == ">=":
            return curr_val >= self.value
        elif self.operator == "<=":
            return curr_val <= self.value
        elif self.operator == "in":
            return curr_val in self.value
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable": self.variable,
            "operator": self.operator,
            "value": self.value
        }


@dataclass(frozen=True)
class Effect:
    """
    Formal effect predicate: ei: variable := value (state transformation Delta S)
    E.g. OrderExists := True, OrderStatus := CREATED
    """
    variable: str
    value: Any = True
    operation: str = "SET"  # "SET", "INCREMENT", "DECREMENT", "DELETE"

    def apply(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Applies effect to produce a new state dictionary."""
        new_state = dict(state_dict)
        if self.operation == "SET":
            new_state[self.variable] = self.value
        elif self.operation == "INCREMENT":
            new_state[self.variable] = new_state.get(self.variable, 0) + (self.value if isinstance(self.value, (int, float)) else 1)
        elif self.operation == "DECREMENT":
            new_state[self.variable] = new_state.get(self.variable, 0) - (self.value if isinstance(self.value, (int, float)) else 1)
        elif self.operation == "DELETE":
            new_state.pop(self.variable, None)
        return new_state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable": self.variable,
            "value": self.value,
            "operation": self.operation
        }


@dataclass(frozen=True)
class Constraint:
    """
    Formal capability-specific constraint: ki in Ki
    E.g. quantity > 0, payment_amount <= transaction_limit, user_role in {CUSTOMER, ADMIN}
    """
    name: str
    expression: str
    constraint_type: str = "domain"  # "input", "state", "resource", "security", "domain"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "expression": self.expression,
            "constraint_type": self.constraint_type
        }


@dataclass(frozen=True)
class Resource:
    """
    Formal resource requirement: ri in Ri
    E.g. Database, PaymentGateway, Network, FileSystem, GPU, ExternalService
    """
    name: str
    resource_type: str = "system"  # "system", "network", "hardware", "service", "security"
    quantity: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "resource_type": self.resource_type,
            "quantity": self.quantity
        }


@dataclass
class QualityAttributes:
    """
    Operational costs & quality attributes: Qi = (Ctime, Cresource, Cmoney, Crisk, Cenergy)
    """
    monetary_cost: float = 0.01     # Cmoney (USD or credits)
    execution_time_ms: float = 50.0 # Ctime (milliseconds)
    resource_cost: float = 1.0      # Cresource (abstract units 1-10)
    risk: float = 0.05              # Crisk in [0, 1]
    energy_cost: float = 0.01       # Cenergy (abstract units)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "monetary_cost": self.monetary_cost,
            "execution_time_ms": self.execution_time_ms,
            "resource_cost": self.resource_cost,
            "risk": self.risk,
            "energy_cost": self.energy_cost
        }


@dataclass
class ExecutionMechanism:
    """
    Formal execution mechanism Mi recording implementation-specific details.
    E.g. API: POST /orders, Database: INSERT orders, GUI: CLICK submit_btn
    """
    mechanism_type: str = "FUNCTION_CALL"
    endpoint_or_target: str = "default_handler"
    protocol_or_action: str = "CALL"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mechanism_type": self.mechanism_type,
            "endpoint_or_target": self.endpoint_or_target,
            "protocol_or_action": self.protocol_or_action,
            "details": self.details
        }


@dataclass
class State:
    """
    Formal state representation: S = {(x1, v1), (x2, v2), ..., (xn, vn)}
    """
    variables: Dict[str, Any] = field(default_factory=dict)
    name: str = "State"

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def satisfies_preconditions(self, preconditions: List[Precondition]) -> bool:
        """Checks if S |= Pi"""
        return all(p.evaluate(self.variables) for p in preconditions)

    def apply_effects(self, effects: List[Effect]) -> State:
        """Computes S' = Apply(S, Ei)"""
        curr = dict(self.variables)
        for eff in effects:
            curr = eff.apply(curr)
        return State(variables=curr, name=f"{self.name}'")

    def satisfies_goal(self, goal: Goal) -> bool:
        """Checks if S |= G"""
        return all(g.evaluate(self.variables) for g in goal.conditions)

    def clone(self) -> State:
        return State(variables=dict(self.variables), name=self.name)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "variables": dict(self.variables)}


@dataclass
class Goal:
    """
    Formal goal specification: G = {g1, g2, ..., gm}
    """
    conditions: List[Precondition] = field(default_factory=list)
    name: str = "GoalSpecification"

    def evaluate_state(self, state: State) -> bool:
        return state.satisfies_goal(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "conditions": [c.to_dict() for c in self.conditions]
        }


@dataclass
class Capability:
    """
    Formal Capability Model:
    Ci = (Ti, Ii, Oi, Pi, Ei, Ki, Ri, Qi, Reli, Ai, Mi)
    """
    name: str
    capability_type: CapabilityType
    inputs: List[InputSpec] = field(default_factory=list)
    outputs: List[OutputSpec] = field(default_factory=list)
    preconditions: List[Precondition] = field(default_factory=list)
    effects: List[Effect] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)
    quality: QualityAttributes = field(default_factory=QualityAttributes)
    reliability: float = 0.99       # Reli in [0, 1]
    availability: float = 1.0       # Ai in [0, 1]
    mechanism: ExecutionMechanism = field(default_factory=ExecutionMechanism)
    description: str = ""

    def is_composite(self) -> bool:
        return False

    def can_execute_on(self, state: State) -> bool:
        return state.satisfies_preconditions(self.preconditions)

    def execute(self, state: State) -> State:
        if not self.can_execute_on(state):
            raise ValueError(f"Capability {self.name} cannot execute: preconditions not satisfied in {state.name}")
        return state.apply_effects(self.effects)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "capability_type": self.capability_type.value,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "preconditions": [p.to_dict() for p in self.preconditions],
            "effects": [e.to_dict() for e in self.effects],
            "constraints": [k.to_dict() for k in self.constraints],
            "resources": [r.to_dict() for r in self.resources],
            "quality": self.quality.to_dict(),
            "reliability": self.reliability,
            "availability": self.availability,
            "mechanism": self.mechanism.to_dict(),
            "description": self.description,
            "is_composite": self.is_composite()
        }


@dataclass
class CompositeCapability(Capability):
    """
    Formal Composite Capability Model:
    C_comp = Cn o ... o C2 o C1
    Contains aggregated operational properties and composite sequential semantics.
    """
    sequence: List[Capability] = field(default_factory=list)
    composition_method: str = "SEQUENTIAL"

    def is_composite(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict["sequence"] = [c.name for c in self.sequence]
        base_dict["composition_method"] = self.composition_method
        return base_dict


@dataclass
class Application:
    """
    Formal Application Model:
    A = (S, C, SI, G, R, K)
    """
    name: str
    state_space_schema: Dict[str, Any]
    capabilities: Dict[str, Capability]
    initial_state: State
    goal: Goal
    available_resources: List[Resource]
    global_constraints: List[Constraint]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state_space_schema": self.state_space_schema,
            "capabilities": {k: v.to_dict() for k, v in self.capabilities.items()},
            "initial_state": self.initial_state.to_dict(),
            "goal": self.goal.to_dict(),
            "available_resources": [r.to_dict() for r in self.available_resources],
            "global_constraints": [k.to_dict() for k in self.global_constraints]
        }
