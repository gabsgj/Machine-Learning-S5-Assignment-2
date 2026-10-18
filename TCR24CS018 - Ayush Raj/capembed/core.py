"""
Core domain models and formal representation structures for capabilities,
states, goals, resources, constraints, and operational attributes.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Any, Optional, Tuple, Union


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
    """Specification of a capability input parameter."""
    name: str
    data_type: str = "ANY"
    domain: str = "ALL"
    required: bool = True

    def matches(self, other_output: OutputSpec) -> bool:
        """Check if an output matches this input requirement."""
        if self.data_type != "ANY" and other_output.data_type != "ANY":
            if self.data_type != other_output.data_type:
                return False
        if self.domain != "ALL" and other_output.domain != "ALL":
            if self.domain != other_output.domain:
                return False
        return self.name.lower() == other_output.name.lower()


@dataclass(frozen=True)
class OutputSpec:
    """Specification of a capability output artifact or value."""
    name: str
    data_type: str = "ANY"
    domain: str = "ALL"


@dataclass
class OperationalProfile:
    """
    Operational attributes and Quality of Service (QoS) metrics:
    Q_i = (C_time, C_resource, C_money, C_risk, C_energy)
    Rel_i in [0, 1]
    A_i in {0, 1}
    """
    execution_time_ms: float = 10.0   # C_time
    monetary_cost: float = 0.0        # C_money
    resource_cost: float = 1.0        # C_resource
    risk: float = 0.05                # C_risk (0 to 1)
    energy_cost: float = 0.0          # C_energy
    reliability: float = 0.99         # Rel_i (probability of success in [0, 1])
    availability: float = 1.0         # A_i in {0, 1}

    def copy(self) -> OperationalProfile:
        return OperationalProfile(
            execution_time_ms=self.execution_time_ms,
            monetary_cost=self.monetary_cost,
            resource_cost=self.resource_cost,
            risk=self.risk,
            energy_cost=self.energy_cost,
            reliability=self.reliability,
            availability=self.availability,
        )


@dataclass
class ExecutionMechanism:
    """
    Records implementation-specific details (M_i)
    e.g. API endpoint, SQL table/query, GUI component ID, Event channel.
    """
    mechanism_type: CapabilityType
    properties: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        props = ", ".join(f"{k}={v}" for k, v in self.properties.items())
        return f"ExecutionMechanism({self.mechanism_type.value}: {props})"


@dataclass
class State:
    """
    Formal application state S = {(x_1, v_1), ..., (x_n, v_n)}.
    Variables may be Boolean, numerical, categorical/enumerated.
    """
    variables: Dict[str, Any] = field(default_factory=dict)

    def get(self, var_name: str, default: Any = None) -> Any:
        return self.variables.get(var_name, default)

    def set(self, var_name: str, value: Any) -> None:
        self.variables[var_name] = value

    def satisfies(self, conditions: Dict[str, Any]) -> bool:
        """Checks if S |= conditions."""
        for var, req_val in conditions.items():
            if var not in self.variables:
                return False
            actual_val = self.variables[var]
            if isinstance(req_val, tuple) and len(req_val) == 2:
                # Comparison operator predicate: (">", 0), ("<=", 10)
                op, target = req_val
                if op == ">" and not (actual_val > target):
                    return False
                elif op == ">=" and not (actual_val >= target):
                    return False
                elif op == "<" and not (actual_val < target):
                    return False
                elif op == "<=" and not (actual_val <= target):
                    return False
                elif op == "!=" and not (actual_val != target):
                    return False
                elif op == "in" and not (actual_val in target):
                    return False
            else:
                if actual_val != req_val:
                    return False
        return True

    def apply(self, effects: Dict[str, Any]) -> State:
        """Returns new state S' = Apply(S, E)."""
        new_vars = dict(self.variables)
        for var, eff_val in effects.items():
            if isinstance(eff_val, tuple) and len(eff_val) == 2 and eff_val[0] in ("+", "-"):
                op, delta = eff_val
                curr = new_vars.get(var, 0)
                new_vars[var] = (curr + delta) if op == "+" else (curr - delta)
            else:
                new_vars[var] = eff_val
        return State(variables=new_vars)

    def copy(self) -> State:
        return State(variables=dict(self.variables))


@dataclass
class Goal:
    """
    Formal goal specification G = {g_1, ..., g_m}.
    A state S satisfies G when S |= G.
    """
    conditions: Dict[str, Any] = field(default_factory=dict)
    name: str = "Goal"

    def is_satisfied_by(self, state: State) -> bool:
        return state.satisfies(self.conditions)


@dataclass
class Capability:
    """
    Formal capability C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
    """
    name: str
    cap_type: CapabilityType
    inputs: List[InputSpec] = field(default_factory=list)
    outputs: List[OutputSpec] = field(default_factory=list)
    preconditions: Dict[str, Any] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    resources: Set[str] = field(default_factory=set)
    operational_profile: OperationalProfile = field(default_factory=OperationalProfile)
    mechanism: Optional[ExecutionMechanism] = field(default=None)

    # Composition metadata
    is_composite: bool = False
    sub_capabilities: List[Capability] = field(default_factory=list)

    def is_applicable_to(self, state: State) -> bool:
        """C_i is applicable to S <=> S |= P_i."""
        return state.satisfies(self.preconditions)

    def execute(self, state: State) -> State:
        """Executes capability on state if applicable."""
        if not self.is_applicable_to(state):
            raise ValueError(f"Capability '{self.name}' preconditions not satisfied by state.")
        return state.apply(self.effects)

    def __repr__(self) -> str:
        return f"Capability({self.name}, type={self.cap_type.value}, composite={self.is_composite})"


class DomainSchema:
    """
    Canonical schema for a problem domain to establish deterministic
    variable and feature indices for vector embeddings.
    """
    def __init__(
        self,
        name: str,
        state_variables: List[str],
        data_types: Optional[List[str]] = None,
        data_names: Optional[List[str]] = None,
        resource_names: Optional[List[str]] = None,
    ):
        self.name = name
        # Sorted canonical lists
        self.state_variables = sorted(list(set(state_variables)))
        self.var_to_idx = {v: i for i, v in enumerate(self.state_variables)}
        
        self.data_types = sorted(list(set(data_types or ["UUID", "STRING", "INTEGER", "BOOLEAN", "DICT", "OBJECT"])))
        self.type_to_idx = {t: i for i, t in enumerate(self.data_types)}

        self.data_names = sorted(list(set(data_names or [])))
        self.data_name_to_idx = {d: i for i, d in enumerate(self.data_names)}

        self.resource_names = sorted(list(set(resource_names or [
            "Database", "PaymentGateway", "Network", "GPU", "FileSystem",
            "AuthenticationToken", "ExternalService", "MessageQueue", "KubernetesCluster"
        ])))
        self.resource_to_idx = {r: i for i, r in enumerate(self.resource_names)}

        self.capability_types = [t.value for t in CapabilityType]
        self.cap_type_to_idx = {t: i for i, t in enumerate(self.capability_types)}

    @property
    def d_state(self) -> int:
        return len(self.state_variables)

    @property
    def d_io(self) -> int:
        # Vector size for inputs or outputs: data_names + data_types
        return len(self.data_names) + len(self.data_types)

    @property
    def d_type(self) -> int:
        return len(self.capability_types)

    @property
    def d_res(self) -> int:
        return len(self.resource_names)

    @property
    def d_ops(self) -> int:
        # time, money, resource, risk, energy, log_rel, availability
        return 7

    @property
    def d_mech(self) -> int:
        # Mechanism feature dimension (hash/signature space)
        return 8

    @classmethod
    def from_capabilities_and_states(
        cls,
        name: str,
        capabilities: List[Capability],
        states: Optional[List[State]] = None,
        goals: Optional[List[Goal]] = None,
    ) -> DomainSchema:
        """Automatically builds domain schema from domain entities."""
        state_vars = set()
        data_names = set()
        data_types = set()
        resources = set()

        if states:
            for s in states:
                state_vars.update(s.variables.keys())

        if goals:
            for g in goals:
                state_vars.update(g.conditions.keys())

        for c in capabilities:
            state_vars.update(c.preconditions.keys())
            state_vars.update(c.effects.keys())
            resources.update(c.resources)
            for inp in c.inputs:
                data_names.add(inp.name)
                data_types.add(inp.data_type)
            for out in c.outputs:
                data_names.add(out.name)
                data_types.add(out.data_type)

        return cls(
            name=name,
            state_variables=list(state_vars),
            data_types=list(data_types),
            data_names=list(data_names),
            resource_names=list(resources) if resources else None,
        )
