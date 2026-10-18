"""
Capability Embedding Framework
Vector Embedding for Capability Composition and Functional Reasoning.
"""

from .core.types import CapabilityType, VariableType, ExecutionMechanism, InputSpec, OutputSpec
from .core.operational import OperationalQuality, ResourceRequirement, CapabilityConstraint
from .core.state import State, Goal
from .core.capability import Capability
from .core.composition import compose_two, compose_sequence, validate_composition, CompositionValidationError

from .embedding.vocabulary import StateVariableRegistry, ResourceRegistry, SchemaRegistry
from .embedding.vector_space import SubspaceLayout, MultiFacetedEmbedding
from .embedding.encoder import CapabilityEmbeddingSystem
from .embedding.algebra import compose_embeddings, compose_vector_sequence

from .metrics.similarity import similarity, functional_similarity, mechanism_similarity, operational_similarity
from .metrics.compatibility import precondition_effect_compatibility, input_output_compatibility, composability
from .metrics.applicability import state_applicability
from .metrics.goal_relevance import goal_relevance, goal_distance, rank_capabilities_by_goal_relevance

from .evaluation.pareto import compute_operational_pareto_frontier, is_pareto_efficient
from .evaluation.benchmarks import benchmark_system_performance

# Global default system instance for convenient top-level function calls
_default_system = CapabilityEmbeddingSystem()


def encode(entity):
    """
    Deliverable 2 Primary API:
    Polymorphic encoder for States, Goals, Capabilities, and sequences of Capabilities.
    """
    return _default_system.encode(entity)


def compose(capabilities, name=None):
    """
    Deliverable 2 Primary API:
    Constructs a composite representation from atomic or sub-composite capabilities
    either symbolically or via vector composition.
    """
    if isinstance(capabilities, (list, tuple)):
        if all(isinstance(c, Capability) for c in capabilities):
            return compose_sequence(capabilities, name=name)
        elif all(isinstance(c, MultiFacetedEmbedding) for c in capabilities):
            return compose_vector_sequence(capabilities, name=name)
    raise TypeError("compose() accepts a sequence of Capability or MultiFacetedEmbedding objects.")


__version__ = "1.0.0"

__all__ = [
    # Top-level API (Deliverable 2)
    "encode",
    "compose",
    "similarity",
    "composability",
    "goal_relevance",
    "state_applicability",
    # Core domain models
    "State",
    "Goal",
    "Capability",
    "CapabilityType",
    "VariableType",
    "ExecutionMechanism",
    "InputSpec",
    "OutputSpec",
    "OperationalQuality",
    "ResourceRequirement",
    "CapabilityConstraint",
    # Embedding infrastructure
    "CapabilityEmbeddingSystem",
    "SchemaRegistry",
    "MultiFacetedEmbedding",
    "SubspaceLayout",
    "compose_embeddings",
    "compose_vector_sequence",
    "compose_two",
    "compose_sequence",
    "validate_composition",
    # Metrics
    "functional_similarity",
    "mechanism_similarity",
    "operational_similarity",
    "precondition_effect_compatibility",
    "input_output_compatibility",
    "goal_distance",
    "rank_capabilities_by_goal_relevance",
    # Evaluation
    "compute_operational_pareto_frontier",
    "is_pareto_efficient",
    "benchmark_system_performance",
]
