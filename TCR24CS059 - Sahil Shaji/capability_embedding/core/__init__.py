"""
Core domain models and symbolic representations for capabilities, states, goals, and compositions.
"""

from .types import CapabilityType, VariableType, ExecutionMechanism, InputSpec, OutputSpec
from .operational import OperationalQuality, ResourceRequirement, CapabilityConstraint
from .state import State, Goal
from .capability import Capability
from .composition import validate_composition, compose_two, compose_sequence, CompositionValidationError

__all__ = [
    "CapabilityType",
    "VariableType",
    "ExecutionMechanism",
    "InputSpec",
    "OutputSpec",
    "OperationalQuality",
    "ResourceRequirement",
    "CapabilityConstraint",
    "State",
    "Goal",
    "Capability",
    "validate_composition",
    "compose_two",
    "compose_sequence",
    "CompositionValidationError",
]
