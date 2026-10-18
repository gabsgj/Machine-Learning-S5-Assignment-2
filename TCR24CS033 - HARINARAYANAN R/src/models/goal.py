from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from src.models.state import ApplicationState


class ComparisonOp(str, Enum):
    EQ = "=="
    NEQ = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    IN = "in"


@dataclass
class GoalCondition:
    variable: str
    target_value: Any
    op: ComparisonOp = ComparisonOp.EQ
    weight: float = 1.0

    def is_satisfied(self, state: ApplicationState) -> bool:
        val = state.get(self.variable)
        if val is None:
            return False
        if self.op == ComparisonOp.EQ:
            return val == self.target_value
        elif self.op == ComparisonOp.NEQ:
            return val != self.target_value
        elif self.op == ComparisonOp.GT:
            return float(val) > float(self.target_value)
        elif self.op == ComparisonOp.GTE:
            return float(val) >= float(self.target_value)
        elif self.op == ComparisonOp.LT:
            return float(val) < float(self.target_value)
        elif self.op == ComparisonOp.LTE:
            return float(val) <= float(self.target_value)
        elif self.op == ComparisonOp.IN:
            return val in self.target_value
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable": self.variable,
            "target_value": self.target_value,
            "op": self.op.value,
            "weight": self.weight
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GoalCondition:
        return cls(
            variable=data["variable"],
            target_value=data["target_value"],
            op=ComparisonOp(data.get("op", "==")),
            weight=float(data.get("weight", 1.0))
        )

    def __repr__(self) -> str:
        return f"{self.variable} {self.op.value} {self.target_value}"


@dataclass
class GoalSpecification:
    """
    Goal specification: G = {g_1, g_2, ..., g_m}
    A state S satisfies G when S |= G.
    """
    conditions: List[GoalCondition] = field(default_factory=list)
    name: str = "Goal"

    def is_satisfied_by(self, state: ApplicationState) -> bool:
        return all(c.is_satisfied(state) for c in self.conditions)

    def satisfaction_ratio(self, state: ApplicationState) -> float:
        if not self.conditions:
            return 1.0
        sat = sum(1 for c in self.conditions if c.is_satisfied(state))
        return sat / len(self.conditions)

    def unsatisfied_conditions(self, state: ApplicationState) -> List[GoalCondition]:
        return [c for c in self.conditions if not c.is_satisfied(state)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "conditions": [c.to_dict() for c in self.conditions]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GoalSpecification:
        return cls(
            name=data.get("name", "Goal"),
            conditions=[GoalCondition.from_dict(c) for c in data.get("conditions", [])]
        )

    def __repr__(self) -> str:
        cond_str = ", ".join(repr(c) for c in self.conditions)
        return f"GoalSpecification({self.name}: [{cond_str}])"
