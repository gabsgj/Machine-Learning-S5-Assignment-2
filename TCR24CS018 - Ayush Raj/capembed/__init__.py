"""
Capability Embedding System (capembed)
Assignment 2: Design of a Vector Embedding for Capability Composition
"""

from .core import (
    CapabilityType,
    InputSpec,
    OutputSpec,
    OperationalProfile,
    ExecutionMechanism,
    Capability,
    State,
    Goal,
    DomainSchema,
)
from .encoder import CapabilityEncoder, EncodedCapability, EncodedState, EncodedGoal
from .composition import CapabilityComposer
from .metrics import (
    compatibility_score,
    functional_similarity,
    implementation_similarity,
    overall_similarity,
    goal_relevance,
    operational_utility,
)
from .pipeline import CapabilityEmbeddingSystem

__all__ = [
    "CapabilityType",
    "InputSpec",
    "OutputSpec",
    "OperationalProfile",
    "ExecutionMechanism",
    "Capability",
    "State",
    "Goal",
    "DomainSchema",
    "CapabilityEncoder",
    "EncodedCapability",
    "EncodedState",
    "EncodedGoal",
    "CapabilityComposer",
    "compatibility_score",
    "functional_similarity",
    "implementation_similarity",
    "overall_similarity",
    "goal_relevance",
    "operational_utility",
    "CapabilityEmbeddingSystem",
]
