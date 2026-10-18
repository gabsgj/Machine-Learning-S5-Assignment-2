"""
Formal representations of State and Goal (Sections 3.1 and 3.2).
"""

from typing import Dict, Any, List, Optional, Set
import copy


class State:
    """
    Formal Application State (Section 3.1).
    S = {(x_1, v_1), (x_2, v_2), ..., (x_n, v_n)}
    where x_i is a state variable and v_i is its value (Boolean, integer, real, categorical, etc.)
    """

    def __init__(self, variables: Optional[Dict[str, Any]] = None):
        self._variables: Dict[str, Any] = {}
        if variables:
            for k, v in variables.items():
                self._variables[k] = v

    @property
    def variables(self) -> Dict[str, Any]:
        return dict(self._variables)

    def get(self, key: str, default: Any = None) -> Any:
        return self._variables.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._variables[key] = value

    def contains(self, key: str) -> bool:
        return key in self._variables

    def clone(self) -> "State":
        return State(copy.deepcopy(self._variables))

    def satisfies(self, conditions: Dict[str, Any]) -> bool:
        """
        Check if S |= P (Section 4.3).
        Supports exact match and basic predicate conditions.
        """
        for var, req_val in conditions.items():
            if var not in self._variables:
                return False
            curr_val = self._variables[var]
            if callable(req_val):
                if not req_val(curr_val):
                    return False
            else:
                if curr_val != req_val:
                    return False
        return True

    def apply(self, effects: Dict[str, Any]) -> "State":
        """
        Apply effects: S' = Apply(S, E_i) (Section 4.3).
        Produces a new State instance with updated values.
        """
        new_state = self.clone()
        for var, val in effects.items():
            new_state.set(var, val)
        return new_state

    def diff(self, other: "State") -> Dict[str, Any]:
        """Returns variables that differ between self and other."""
        diffs = {}
        all_keys = set(self._variables.keys()).union(other._variables.keys())
        for k in all_keys:
            v_self = self.get(k)
            v_other = other.get(k)
            if v_self != v_other:
                diffs[k] = (v_self, v_other)
        return diffs

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._variables)

    def __repr__(self) -> str:
        items = ", ".join(f"{k}: {v}" for k, v in sorted(self._variables.items()))
        return f"State({{{items}}})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, State):
            return False
        return self._variables == other._variables


class Goal:
    """
    Formal Goal Specification (Section 3.2).
    G = {g_1, g_2, ..., g_m}
    A state S satisfies the goal when S |= G.
    """

    def __init__(self, target_conditions: Optional[Dict[str, Any]] = None):
        self._conditions: Dict[str, Any] = {}
        if target_conditions:
            for k, v in target_conditions.items():
                self._conditions[k] = v

    @property
    def conditions(self) -> Dict[str, Any]:
        return dict(self._conditions)

    def is_satisfied_by(self, state: State) -> bool:
        """S |= G predicate satisfaction."""
        return state.satisfies(self._conditions)

    def unmet_conditions(self, state: State) -> Dict[str, Any]:
        """Returns conditions in G not currently satisfied by state S."""
        unmet = {}
        for var, req_val in self._conditions.items():
            curr_val = state.get(var)
            if callable(req_val):
                if not req_val(curr_val):
                    unmet[var] = (curr_val, req_val)
            else:
                if curr_val != req_val:
                    unmet[var] = (curr_val, req_val)
        return unmet

    def satisfaction_ratio(self, state: State) -> float:
        """Fraction of goal conditions satisfied by state."""
        if not self._conditions:
            return 1.0
        satisfied = sum(
            1 for var, req in self._conditions.items()
            if (req(state.get(var)) if callable(req) else state.get(var) == req)
        )
        return satisfied / len(self._conditions)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._conditions)

    def __repr__(self) -> str:
        items = ", ".join(f"{k}: {v}" for k, v in sorted(self._conditions.items()))
        return f"Goal({{{items}}})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Goal):
            return False
        return self._conditions == other._conditions
