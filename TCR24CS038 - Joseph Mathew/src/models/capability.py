"""Formal Capability Model.

C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)

T_i in {API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE}
I_i = {i_1, ..., i_p}, i_j = (name, type, domain, required)
O_i = {o_1, ..., o_q}, o_j = (name, type, domain)
P_i = {p_1, ..., p_r} (preconditions)
E_i = {e_1, ..., e_s} (effects)
K_i = {k_1, ..., k_t} (constraints)
R_i = {r_1, ..., r_u} (resources)
Q_i = cost profile
Rel_i in [0, 1]
A_i in {0, 1}
M_i = execution mechanism details
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from src.models.state import State, Condition, Effect
from src.models.operational import (
    CostProfile, ResourceRequirement, Constraint, OperationalProfile
)


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


class ExecutionMechanism(BaseModel):
    """M_i records implementation-specific details."""
    type: CapabilityType
    details: Dict[str, Any] = Field(default_factory=dict)
    # Examples:
    # API: {"method": "POST", "endpoint": "/orders"}
    # Database: {"operation": "INSERT", "table": "orders"}
    # GUI: {"action": "CLICK", "component": "submit_button"}


class DataParameter(BaseModel):
    """Input i_j or Output o_j specification: (name, type, domain, required)."""
    name: str
    data_type: str  # e.g., 'UUID', 'String', 'Integer', 'Float', 'JSON', 'Token'
    domain: str = "general"
    required: bool = True


class Capability(BaseModel):
    """Formal capability representation C_i."""
    name: str
    capability_type: CapabilityType
    inputs: List[DataParameter] = Field(default_factory=list)
    outputs: List[DataParameter] = Field(default_factory=list)
    preconditions: List[Condition] = Field(default_factory=list)
    effects: List[Effect] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)
    resources: List[ResourceRequirement] = Field(default_factory=list)
    cost: CostProfile = Field(default_factory=CostProfile)
    reliability: float = Field(default=1.0, ge=0.0, le=1.0)
    availability: float = Field(default=1.0, ge=0.0, le=1.0)
    execution_mechanism: Optional[ExecutionMechanism] = None
    sub_capabilities: List[str] = Field(default_factory=list)  # If composite

    @property
    def operational_profile(self) -> OperationalProfile:
        return OperationalProfile(
            cost=self.cost,
            reliability=self.reliability,
            availability=self.availability,
            resources=self.resources,
            constraints=self.constraints
        )

    def is_applicable(self, state: State) -> bool:
        """C_i is applicable to S <=> S |= P_i."""
        return state.satisfies(self.preconditions)

    def apply(self, state: State) -> State:
        """C_i: S -> S', S' = Apply(S, E_i)."""
        if not self.is_applicable(state):
            raise ValueError(f"Capability '{self.name}' not applicable to given state.")
        return state.apply_effects(self.effects)

    def can_compose_with(self, next_cap: Capability) -> Tuple[bool, Dict[str, Any]]:
        """Checks if C1 (self) can compose with C2 (next_cap), i.e., C2 o C1 is valid.
        
        Section 5: If the outputs and effects of C1 satisfy the inputs and
        preconditions of C2, then C2 o C1 is a valid composition.
        """
        reasons = []
        is_compatible = True

        # 1. State effect -> Precondition satisfaction check
        # Map of variables modified by C1
        c1_effects_map = {eff.variable: eff for eff in self.effects}
        satisfied_preconds = 0
        total_preconds = len(next_cap.preconditions)

        for p in next_cap.preconditions:
            if p.variable in c1_effects_map:
                eff = c1_effects_map[p.variable]
                if eff.action == "set" and p.operator == "==":
                    if eff.value == p.value:
                        satisfied_preconds += 1
                    else:
                        is_compatible = False
                        reasons.append(f"Precondition conflict on {p.variable}: C1 sets {eff.value} != C2 needs {p.value}")
            # If not modified by C1, it must come from initial state (or external context)

        # 2. Output -> Input satisfaction check
        c1_output_names = {o.name: o for o in self.outputs}
        c1_output_types = {o.data_type for o in self.outputs}
        satisfied_inputs = 0
        required_inputs = [inp for inp in next_cap.inputs if inp.required]
        
        for inp in required_inputs:
            # Check by exact name match or data_type compatibility
            if inp.name in c1_output_names:
                satisfied_inputs += 1
            elif inp.data_type in c1_output_types:
                satisfied_inputs += 1

        info = {
            "is_valid": is_compatible,
            "satisfied_preconditions": satisfied_preconds,
            "total_preconditions": total_preconds,
            "satisfied_inputs": satisfied_inputs,
            "total_required_inputs": len(required_inputs),
            "reasons": reasons
        }
        return is_compatible, info
