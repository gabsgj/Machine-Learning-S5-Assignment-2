"""
Domain Models for Capability Composition and Formal Application Modeling.
Assignment 2: Design of a Vector Embedding for Capability Composition.
Student: Melita Mariam Mathew
Registration Number: TCCR24CS046
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple
import math


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


@dataclass(frozen=True)
class InputSpec:
    name: str
    data_type: str
    domain: str = "general"
    required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "domain": self.domain,
            "required": self.required,
        }


@dataclass(frozen=True)
class OutputSpec:
    name: str
    data_type: str
    domain: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "domain": self.domain,
        }


@dataclass(frozen=True)
class StateCondition:
    variable: str
    value: Any
    operator: str = "=="  # "==", "!=", ">", "<", ">=", "<=", "in"

    def evaluate(self, state_dict: Dict[str, Any]) -> bool:
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
            "value": self.value,
            "operator": self.operator,
        }


@dataclass
class State:
    variables: Dict[str, Any] = field(default_factory=dict)

    def satisfy(self, conditions: List[StateCondition]) -> bool:
        return all(cond.evaluate(self.variables) for cond in conditions)

    def apply_effects(self, effects: List[StateCondition]) -> "State":
        new_vars = dict(self.variables)
        for eff in effects:
            if eff.operator == "==":
                new_vars[eff.variable] = eff.value
            elif eff.operator == "+=":
                new_vars[eff.variable] = new_vars.get(eff.variable, 0) + eff.value
            elif eff.operator == "-=":
                new_vars[eff.variable] = new_vars.get(eff.variable, 0) - eff.value
            else:
                new_vars[eff.variable] = eff.value
        return State(variables=new_vars)

    def clone(self) -> "State":
        return State(variables=dict(self.variables))

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.variables)


@dataclass
class Goal:
    conditions: List[StateCondition] = field(default_factory=list)

    def is_satisfied_by(self, state: State) -> bool:
        return state.satisfy(self.conditions)

    def to_dict(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self.conditions]


@dataclass
class ExecutionMechanism:
    mechanism_type: CapabilityType
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.mechanism_type.value,
            "details": self.details,
        }


@dataclass
class OperationalAttributes:
    time_ms: float = 100.0        # C_time (latency in milliseconds)
    cost_money: float = 0.01      # C_money (cost in USD)
    resource_cost: float = 1.0    # C_resource (CPU/Memory unit score)
    risk: float = 0.05            # C_risk in [0, 1]
    energy: float = 1.0           # C_energy in Joules/relative unit
    reliability: float = 0.99     # Rel in [0, 1] (success probability)
    availability: float = 1.0     # A in [0, 1] (or binary 1/0)

    def combine_with(self, other: "OperationalAttributes") -> "OperationalAttributes":
        """
        Combine operational attributes under sequential composition C1 -> C2.
        - Additive: time, cost_money, resource_cost, energy
        - Risk: 1 - (1 - risk1) * (1 - risk2) (probability of at least one failure mode)
        - Reliability: rel1 * rel2 (joint success probability)
        - Availability: min(avail1, avail2) (series availability bottleneck)
        """
        return OperationalAttributes(
            time_ms=self.time_ms + other.time_ms,
            cost_money=self.cost_money + other.cost_money,
            resource_cost=self.resource_cost + other.resource_cost,
            risk=1.0 - ((1.0 - self.risk) * (1.0 - other.risk)),
            energy=self.energy + other.energy,
            reliability=self.reliability * other.reliability,
            availability=min(self.availability, other.availability),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time_ms": self.time_ms,
            "cost_money": self.cost_money,
            "resource_cost": self.resource_cost,
            "risk": self.risk,
            "energy": self.energy,
            "reliability": self.reliability,
            "availability": self.availability,
        }


@dataclass
class Capability:
    id: str
    name: str
    type: CapabilityType
    inputs: List[InputSpec] = field(default_factory=list)
    outputs: List[OutputSpec] = field(default_factory=list)
    preconditions: List[StateCondition] = field(default_factory=list)
    effects: List[StateCondition] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    operational: OperationalAttributes = field(default_factory=OperationalAttributes)
    mechanism: Optional[ExecutionMechanism] = None

    def is_applicable(self, state: State) -> bool:
        return state.satisfy(self.preconditions)

    def execute(self, state: State) -> State:
        if not self.is_applicable(state):
            raise ValueError(f"Capability '{self.name}' preconditions not met on state.")
        return state.apply_effects(self.effects)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "preconditions": [p.to_dict() for p in self.preconditions],
            "effects": [e.to_dict() for e in self.effects],
            "constraints": self.constraints,
            "resources": self.resources,
            "operational": self.operational.to_dict(),
            "mechanism": self.mechanism.to_dict() if self.mechanism else None,
        }


@dataclass
class CompositeCapability(Capability):
    """
    Represents a sequence of capabilities C = C_n o ... o C_2 o C_1.
    Execution order is C_1 then C_2 then ... then C_n.
    """
    sub_capabilities: List[Capability] = field(default_factory=list)

    @classmethod
    def compose(cls, c1: Capability, c2: Capability) -> "CompositeCapability":
        """
        Compose two capabilities: c_comp = c2 o c1 (execute c1, then c2).
        Preconditions:
            P(c2 o c1) = P(c1) union { p in P(c2) | p not established by E(c1) }
        Effects:
            E(c2 o c1) = E(c1) overridden/extended by E(c2)
        Inputs:
            I(c2 o c1) = I(c1) union { i in I(c2) | i not produced by O(c1) }
        Outputs:
            O(c2 o c1) = O(c1) union O(c2) (all outputs produced during execution)
        """
        # Determine sequence of atomic capabilities
        subs_1 = c1.sub_capabilities if isinstance(c1, CompositeCapability) else [c1]
        subs_2 = c2.sub_capabilities if isinstance(c2, CompositeCapability) else [c2]
        all_subs = subs_1 + subs_2

        # 1. Effects: c1 effects updated by c2 effects
        eff_dict: Dict[str, StateCondition] = {e.variable: e for e in c1.effects}
        for e2 in c2.effects:
            eff_dict[e2.variable] = e2
        combined_effects = list(eff_dict.values())

        # 2. Preconditions: c1 preconditions + remaining c2 preconditions not satisfied by c1 effects
        c1_effect_vars = {e.variable: e.value for e in c1.effects if e.operator == "=="}
        combined_preconditions = list(c1.preconditions)
        for p2 in c2.preconditions:
            # Check if c1 effect already fulfills p2
            if p2.operator == "==" and p2.variable in c1_effect_vars:
                if c1_effect_vars[p2.variable] == p2.value:
                    continue  # fulfilled by c1, no external precondition needed
            # Otherwise, keep p2 as required precondition
            if not any(p.variable == p2.variable and p.value == p2.value for p in combined_preconditions):
                combined_preconditions.append(p2)

        # 3. Inputs: c1 inputs + c2 inputs that are not satisfied by c1 outputs
        c1_output_types = {(o.name, o.data_type) for o in c1.outputs}
        combined_inputs = list(c1.inputs)
        for i2 in c2.inputs:
            if (i2.name, i2.data_type) not in c1_output_types:
                if not any(i.name == i2.name for i in combined_inputs):
                    combined_inputs.append(i2)

        # 4. Outputs: union of outputs
        out_dict: Dict[str, OutputSpec] = {o.name: o for o in c1.outputs}
        for o2 in c2.outputs:
            out_dict[o2.name] = o2
        combined_outputs = list(out_dict.values())

        # 5. Resources and constraints: union
        combined_resources = sorted(list(set(c1.resources).union(set(c2.resources))))
        combined_constraints = sorted(list(set(c1.constraints).union(set(c2.constraints))))

        # 6. Operational attributes
        combined_ops = c1.operational.combine_with(c2.operational)

        comp_id = f"{c1.id}_then_{c2.id}"
        comp_name = f"({c1.name} >> {c2.name})"

        return cls(
            id=comp_id,
            name=comp_name,
            type=CapabilityType.SERVICE,
            inputs=combined_inputs,
            outputs=combined_outputs,
            preconditions=combined_preconditions,
            effects=combined_effects,
            constraints=combined_constraints,
            resources=combined_resources,
            operational=combined_ops,
            mechanism=ExecutionMechanism(
                mechanism_type=CapabilityType.SERVICE,
                details={"composition_pipeline": [c.id for c in all_subs]}
            ),
            sub_capabilities=all_subs,
        )

    @classmethod
    def compose_sequence(cls, capabilities: List[Capability]) -> Capability:
        if not capabilities:
            raise ValueError("Cannot compose an empty list of capabilities.")
        result = capabilities[0]
        for cap in capabilities[1:]:
            result = cls.compose(result, cap)
        return result
