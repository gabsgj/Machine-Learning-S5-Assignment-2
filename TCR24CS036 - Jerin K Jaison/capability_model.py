"""
Formal data model for Assignment 2.

Mirrors the formal application model A = (S, C, SI, G, R, K) and the formal
capability model C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
from the assignment PDF, as plain, serializable Python dataclasses.

Design choice: preconditions, effects and goal conditions are represented as
*ground atoms* -- strings of the form "variable=value" (equality) or
"variable>threshold" / "variable<threshold" / "variable>=threshold" etc. for
numeric comparisons. Using strings as atoms lets preconditions and effects
share a single vocabulary, which is what makes precondition-effect
compatibility a direct set-overlap check later rather than something that
has to be learned.
"""

from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Dict, List, Tuple, Optional, Union
import itertools

Number = Union[int, float]

CAPABILITY_TYPES = [
    "API", "DATABASE", "GUI", "EVENT", "FUNCTION",
    "FILE", "COMPUTATION", "MESSAGE", "SERVICE", "COMPOSITE",
]


def atom_eq(var: str, value) -> str:
    """Build an equality ground atom, e.g. atom_eq('OrderExists', True) -> 'OrderExists=True'."""
    return f"{var}={value}"


def atom_cmp(var: str, op: str, value) -> str:
    """Build a comparison ground atom, e.g. atom_cmp('Cart.item_count','>',0) -> 'Cart.item_count>0'."""
    assert op in (">", "<", ">=", "<=", "!=")
    return f"{var}{op}{value}"


@dataclass(frozen=True)
class IOSpec:
    """A single input or output specification: (name, type, domain, required)."""
    name: str
    type: str
    domain: str = ""
    required: bool = True

    def key(self) -> str:
        # Identity used for input<->output matching: name + type must agree.
        return f"{self.name}:{self.type}"


@dataclass(frozen=True)
class State:
    """A concrete application state S = {(x1,v1), ..., (xn,vn)}."""
    assignments: Dict[str, object] = field(default_factory=dict)

    def atoms(self) -> List[str]:
        return [atom_eq(k, v) for k, v in self.assignments.items()]

    def get(self, var: str):
        return self.assignments.get(var)


@dataclass(frozen=True)
class Goal:
    """A goal specification G = {g1, ..., gm}, expressed as ground atoms."""
    conditions: Tuple[str, ...] = field(default_factory=tuple)

    @staticmethod
    def from_equalities(d: Dict[str, object]) -> "Goal":
        return Goal(tuple(atom_eq(k, v) for k, v in d.items()))


@dataclass(frozen=True)
class Capability:
    """
    Formal capability C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)

    id              unique capability identifier
    type            T_i in CAPABILITY_TYPES
    inputs          I_i: tuple of IOSpec
    outputs         O_i: tuple of IOSpec
    preconditions   P_i: tuple of ground atoms (strings)
    effects         E_i: dict var->value (equality effects only; this is the
                    common case in the assignment's examples and is required
                    for the deterministic "apply effect, override on reuse"
                    semantics used by compose()). Non-equality effects are
                    not needed by any required experiment.
    constraints     K_i: tuple of free-text constraint strings, e.g. "quantity>0"
    resources       R_i: tuple of resource names, e.g. "Database"
    cost            Q_i: dict with keys time, money, resource, risk, energy
    reliability     Rel_i in [0,1]
    availability    A_i in [0,1] (treated as a static flag; time-varying
                    availability A_i(t) is discussed as a limitation)
    mechanism       M_i: dict of implementation-specific key/value pairs
    composed_of     traceability list of constituent capability ids, set by compose()
    """
    id: str
    type: str
    inputs: Tuple[IOSpec, ...] = field(default_factory=tuple)
    outputs: Tuple[IOSpec, ...] = field(default_factory=tuple)
    preconditions: Tuple[str, ...] = field(default_factory=tuple)
    effects: Dict[str, object] = field(default_factory=dict)
    constraints: Tuple[str, ...] = field(default_factory=tuple)
    resources: Tuple[str, ...] = field(default_factory=tuple)
    cost: Dict[str, Number] = field(default_factory=lambda: {
        "time": 0.0, "money": 0.0, "resource": 0.0, "risk": 0.0, "energy": 0.0})
    reliability: float = 1.0
    availability: float = 1.0
    mechanism: Dict[str, str] = field(default_factory=dict)
    composed_of: Tuple[str, ...] = field(default_factory=tuple)

    def effect_atoms(self) -> List[str]:
        return [atom_eq(k, v) for k, v in self.effects.items()]

    def __post_init__(self):
        assert self.type in CAPABILITY_TYPES, f"Unknown capability type {self.type}"
        assert 0.0 <= self.reliability <= 1.0
        assert 0.0 <= self.availability <= 1.0
