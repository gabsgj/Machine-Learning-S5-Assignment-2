from __future__ import annotations
from typing import Any, List, Optional, Tuple, Union
import numpy as np

from src.models.state import ApplicationState
from src.models.goal import GoalSpecification
from src.models.capability import Capability
from src.embedding.schema import EmbeddingSchema, SubspaceSlice
from src.embedding.encoder import (
    StateEmbedding,
    GoalEmbedding,
    CapabilityEmbedding,
    CapabilityEncoder
)
from src.embedding.composition import (
    CapabilityComposer,
    CompositionValidation
)
from src.embedding.metrics import (
    CompatibilityScore,
    SimilarityEngine,
    cosine_sim,
    euclidean_dist
)
from src.embedding.operational import (
    OperationalEvaluator,
    ParetoRankingResult
)


class EmbeddingSystem:
    """
    Unified high-level interface implementing Deliverable 2:
    - encode(state)
    - encode(goal)
    - encode(capability)
    - compose(capabilities)
    - similarity(x, y)
    plus compatibility, goal relevance, and Pareto analysis.
    """
    def __init__(self, schema: Optional[EmbeddingSchema] = None):
        self.schema = schema or EmbeddingSchema()
        self.encoder = CapabilityEncoder(self.schema)
        self.composer = CapabilityComposer(self.encoder)
        self.similarity_engine = SimilarityEngine()
        self.operational_evaluator = OperationalEvaluator()

    def encode(
        self,
        entity: Union[ApplicationState, GoalSpecification, Capability]
    ) -> Union[StateEmbedding, GoalEmbedding, CapabilityEmbedding]:
        """Encodes state, goal, or capability into its respective embedding."""
        return self.encoder.encode(entity)

    def encode_state(self, state: ApplicationState) -> StateEmbedding:
        return self.encoder.encode_state(state)

    def encode_goal(self, goal: GoalSpecification) -> GoalEmbedding:
        return self.encoder.encode_goal(goal)

    def encode_capability(self, capability: Capability) -> CapabilityEmbedding:
        return self.encoder.encode_capability(capability)

    def compose(
        self,
        capabilities: Union[Tuple[Capability, ...], List[Capability]],
        composite_id: Optional[str] = None
    ) -> Tuple[Capability, CapabilityEmbedding]:
        """
        Constructs composite capability and returns both:
        (composite_capability_model, composite_embedding)
        """
        cap_list = list(capabilities)
        if len(cap_list) == 0:
            raise ValueError("No capabilities provided for composition")
        elif len(cap_list) == 1:
            composite_cap = cap_list[0]
        else:
            composite_cap = self.composer.compose_chain(cap_list, composite_id=composite_id)

        composite_emb = self.encoder.encode_capability(composite_cap)
        return composite_cap, composite_emb

    def similarity(
        self,
        x: Union[CapabilityEmbedding, Capability, np.ndarray],
        y: Union[CapabilityEmbedding, Capability, np.ndarray],
        metric: str = "functional"
    ) -> float:
        """
        Compares two encoded entities or capability objects.
        Supported metrics: 'functional', 'effects', 'preconditions', 'mechanism', 'operational', 'full', 'euclidean'
        """
        emb_x = self.encoder.encode_capability(x) if isinstance(x, Capability) else x
        emb_y = self.encoder.encode_capability(y) if isinstance(y, Capability) else y
        return self.similarity_engine.compute_similarity(emb_x, emb_y, metric=metric)

    def compatibility(
        self,
        c1: Union[Capability, CapabilityEmbedding],
        c2: Union[Capability, CapabilityEmbedding]
    ) -> CompatibilityScore:
        """Computes directional compatibility C1 -> C2."""
        cap1 = c1 if isinstance(c1, Capability) else None
        cap2 = c2 if isinstance(c2, Capability) else None
        emb1 = self.encoder.encode_capability(c1) if isinstance(c1, Capability) else c1
        emb2 = self.encoder.encode_capability(c2) if isinstance(c2, Capability) else c2
        return self.similarity_engine.compute_compatibility(emb1, emb2, c1=cap1, c2=cap2)

    def goal_relevance(
        self,
        cap: Union[Capability, CapabilityEmbedding],
        goal: Union[GoalSpecification, GoalEmbedding]
    ) -> float:
        """Computes capability relevance to achieving the goal."""
        cap_emb = self.encoder.encode_capability(cap) if isinstance(cap, Capability) else cap
        goal_emb = self.encoder.encode_goal(goal) if isinstance(goal, GoalSpecification) else goal
        return self.similarity_engine.compute_goal_relevance(cap_emb, goal_emb)

    def state_applicability(
        self,
        state: Union[ApplicationState, StateEmbedding],
        cap: Union[Capability, CapabilityEmbedding]
    ) -> bool:
        """Checks if state satisfies preconditions of capability."""
        state_emb = self.encoder.encode_state(state) if isinstance(state, ApplicationState) else state
        cap_emb = self.encoder.encode_capability(cap) if isinstance(cap, Capability) else cap
        return self.similarity_engine.compute_state_applicability(state_emb, cap_emb)


__all__ = [
    "EmbeddingSchema",
    "SubspaceSlice",
    "StateEmbedding",
    "GoalEmbedding",
    "CapabilityEmbedding",
    "CapabilityEncoder",
    "CapabilityComposer",
    "CompositionValidation",
    "CompatibilityScore",
    "SimilarityEngine",
    "OperationalEvaluator",
    "ParetoRankingResult",
    "EmbeddingSystem",
    "cosine_sim",
    "euclidean_dist",
]
