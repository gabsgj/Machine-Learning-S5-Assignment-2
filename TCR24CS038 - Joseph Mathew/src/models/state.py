"""Formal Application State and Goal Specifications.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class Condition(BaseModel):
    """A formal condition or predicate evaluated on application state."""
    variable: str
    operator: str = "=="  # '==', '!=', '>', '>=', '<', '<=', 'in'
    value: Any

    def evaluate(self, state: State) -> bool:
        if self.variable not in state.variables:
            return False
        curr_val = state.variables[self.variable]
        
        # Handle type coercion for numeric/bool comparisons
        if self.operator == "==":
            return curr_val == self.value
        elif self.operator == "!=":
            return curr_val != self.value
        elif self.operator == ">":
            return float(curr_val) > float(self.value)
        elif self.operator == ">=":
            return float(curr_val) >= float(self.value)
        elif self.operator == "<":
            return float(curr_val) < float(self.value)
        elif self.operator == "<=":
            return float(curr_val) <= float(self.value)
        elif self.operator == "in":
            return curr_val in self.value
        return False


class Effect(BaseModel):
    """A formal state transition effect: S' = Apply(S, E)."""
    variable: str
    action: str = "set"  # 'set', 'increment', 'decrement', 'toggle'
    value: Any

    def apply(self, state_dict: Dict[str, Any]) -> None:
        if self.action == "set":
            state_dict[self.variable] = self.value
        elif self.action == "increment":
            curr = state_dict.get(self.variable, 0)
            state_dict[self.variable] = curr + self.value
        elif self.action == "decrement":
            curr = state_dict.get(self.variable, 0)
            state_dict[self.variable] = curr - self.value
        elif self.action == "toggle":
            curr = state_dict.get(self.variable, False)
            state_dict[self.variable] = not curr


class State(BaseModel):
    """Application state S = {(x_1, v_1), ..., (x_n, v_n)}."""
    name: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict)

    def satisfies(self, conditions: List[Condition]) -> bool:
        """Checks if S |= conditions."""
        return all(cond.evaluate(self) for cond in conditions)

    def clone(self) -> State:
        return State(name=self.name, variables=dict(self.variables))

    def apply_effects(self, effects: List[Effect]) -> State:
        """Computes S' = Apply(S, E)."""
        new_vars = dict(self.variables)
        for eff in effects:
            eff.apply(new_vars)
        return State(name=f"{self.name}_next" if self.name else None, variables=new_vars)

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)


class Goal(BaseModel):
    """Formal Goal specification G = {g_1, ..., g_m}."""
    name: str = "Goal"
    conditions: List[Condition] = Field(default_factory=list)

    def is_satisfied_by(self, state: State) -> bool:
        """A state S satisfies the goal when S |= G."""
        return state.satisfies(self.conditions)
