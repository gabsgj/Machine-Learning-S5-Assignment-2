"""
Embedding sub-package: vector space definitions, encoders, and compositional algebra.
"""

from .vocabulary import StateVariableRegistry, ResourceRegistry, SchemaRegistry
from .vector_space import SubspaceLayout, MultiFacetedEmbedding
from .encoder import CapabilityEmbeddingSystem, _hash_to_vector
from .algebra import compose_embeddings, compose_vector_sequence

__all__ = [
    "StateVariableRegistry",
    "ResourceRegistry",
    "SchemaRegistry",
    "SubspaceLayout",
    "MultiFacetedEmbedding",
    "CapabilityEmbeddingSystem",
    "compose_embeddings",
    "compose_vector_sequence",
]
