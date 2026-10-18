from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


@dataclass
class State:
    """Represents the current state of the application."""

    values: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Goal:
    """Represents the desired conditions of an application."""

    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Capability:
    """Represents an executable capability."""

    name: str

    preconditions: Dict[str, Any] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)

    inputs: Set[str] = field(default_factory=set)
    outputs: Set[str] = field(default_factory=set)

    constraints: Set[str] = field(default_factory=set)
    resources: Set[str] = field(default_factory=set)

    cost: float = 0.0
    reliability: float = 1.0
    availability: float = 1.0

    def is_available(self) -> bool:
        """Return True when the capability is available."""
        return self.availability > 0.0
