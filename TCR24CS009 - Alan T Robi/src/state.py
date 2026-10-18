from dataclasses import dataclass, field
from typing import Dict, List, Any, Union, Set

@dataclass
class State:
    """
    Formal application state representation: S = {(x1, v1), (x2, v2), ..., (xn, vn)}
    Variable-value mapping describing system condition at a given point in time.
    """
    variables: Dict[str, Any] = field(default_factory=dict)

    def set_var(self, var_name: str, val: Any) -> None:
        self.variables[var_name] = val

    def get_var(self, var_name: str, default: Any = None) -> Any:
        return self.variables.get(var_name, default)

    def to_predicates(self) -> List[str]:
        """Convert current state variables into predicate string representations."""
        predicates = []
        for var, val in sorted(self.variables.items()):
            if isinstance(val, bool):
                str_val = "true" if val else "false"
            else:
                str_val = str(val)
            predicates.append(f"{var}={str_val}")
        return predicates

    def apply_effect(self, effect_str: str) -> None:
        """Apply a single effect string (e.g. 'Order.exists=true') to state."""
        if "=" in effect_str:
            parts = effect_str.split("=", 1)
            var_name = parts[0].strip()
            val_str = parts[1].strip()
            if val_str.lower() == "true":
                val = True
            elif val_str.lower() == "false":
                val = False
            else:
                try:
                    val = int(val_str)
                except ValueError:
                    try:
                        val = float(val_str)
                    except ValueError:
                        val = val_str
            self.variables[var_name] = val

    def satisfies_predicate(self, pred_str: str) -> bool:
        """Check if state satisfies a predicate string (e.g. 'CartExists=true', 'CartItemCount>0')."""
        if ">=" in pred_str:
            var, val_str = pred_str.split(">=", 1)
            var = var.strip()
            val = float(val_str.strip())
            return self.get_var(var, 0) >= val
        elif "<=" in pred_str:
            var, val_str = pred_str.split("<=", 1)
            var = var.strip()
            val = float(val_str.strip())
            return self.get_var(var, 0) <= val
        elif ">" in pred_str:
            var, val_str = pred_str.split(">", 1)
            var = var.strip()
            val = float(val_str.strip())
            return self.get_var(var, 0) > val
        elif "<" in pred_str:
            var, val_str = pred_str.split("<", 1)
            var = var.strip()
            val = float(val_str.strip())
            return self.get_var(var, 0) < val
        elif "=" in pred_str:
            var, val_str = pred_str.split("=", 1)
            var = var.strip()
            val_str = val_str.strip()
            curr_val = self.get_var(var, None)
            if curr_val is None:
                return False
            if isinstance(curr_val, bool):
                return (val_str.lower() == "true") == curr_val
            return str(curr_val).lower() == val_str.lower()
        return False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "State":
        return cls(variables=dict(data))


@dataclass
class Goal:
    """
    Formal goal specification: G = {g1, g2, ..., gm}
    Set of desired condition predicates that a final state must satisfy (S |= G).
    """
    conditions: List[str] = field(default_factory=list)

    def is_satisfied_by(self, state: State) -> bool:
        """Check S |= G."""
        return all(state.satisfies_predicate(c) for c in self.conditions)

    def to_predicates(self) -> List[str]:
        return list(self.conditions)
