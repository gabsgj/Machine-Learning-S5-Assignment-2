from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from src.models.state import StateVariable, ApplicationState
from src.models.goal import GoalSpecification
from src.models.capability import Capability, CapabilityConstraint


@dataclass
class ApplicationProblem:
    """
    Formal Application Model:
    A = (S, C, S_I, G, R, K)
    """
    name: str
    state_variables: List[StateVariable] = field(default_factory=list)
    capabilities: List[Capability] = field(default_factory=list)
    initial_state: ApplicationState = field(default_factory=ApplicationState)
    goal: GoalSpecification = field(default_factory=GoalSpecification)
    available_resources: List[str] = field(default_factory=list)
    global_constraints: List[CapabilityConstraint] = field(default_factory=list)
    description: str = ""

    def get_capability(self, cap_id: str) -> Optional[Capability]:
        for c in self.capabilities:
            if c.id == cap_id:
                return c
        return None

    def get_variable(self, var_name: str) -> Optional[StateVariable]:
        for v in self.state_variables:
            if v.name == var_name:
                return v
        return None

    def is_goal_satisfied(self, state: ApplicationState) -> bool:
        return self.goal.is_satisfied_by(state)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "state_variables": [
                {
                    "name": v.name,
                    "var_type": v.var_type.value,
                    "domain": v.domain,
                    "default_value": v.default_value,
                    "description": v.description
                }
                for v in self.state_variables
            ],
            "initial_state": self.initial_state.to_dict(),
            "goal": self.goal.to_dict(),
            "available_resources": list(self.available_resources),
            "global_constraints": [k.to_dict() for k in self.global_constraints],
            "capabilities": [c.to_dict() for c in self.capabilities]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ApplicationProblem:
        from src.models.state import StateVariableType
        vars_list = [
            StateVariable(
                name=v["name"],
                var_type=StateVariableType(v["var_type"]),
                domain=v.get("domain"),
                default_value=v.get("default_value"),
                description=v.get("description", "")
            )
            for v in data.get("state_variables", [])
        ]
        return cls(
            name=data.get("name", "ApplicationProblem"),
            description=data.get("description", ""),
            state_variables=vars_list,
            initial_state=ApplicationState.from_dict(data.get("initial_state", {})),
            goal=GoalSpecification.from_dict(data.get("goal", {})),
            available_resources=list(data.get("available_resources", [])),
            global_constraints=[CapabilityConstraint.from_dict(k) for k in data.get("global_constraints", [])],
            capabilities=[Capability.from_dict(c) for c in data.get("capabilities", [])]
        )
