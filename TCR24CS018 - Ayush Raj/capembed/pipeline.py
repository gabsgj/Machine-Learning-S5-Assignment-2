"""
High-Level API for Deliverable 2:
Implements encode(state), encode(goal), encode(capability), compose(capabilities), similarity(x, y).
"""

from __future__ import annotations
from typing import Union, List, Optional
import numpy as np

from .core import State, Goal, Capability, DomainSchema
from .encoder import CapabilityEncoder, EncodedState, EncodedGoal, EncodedCapability
from .composition import CapabilityComposer
from .metrics import (
    compatibility_score,
    precondition_effect_compatibility,
    input_output_compatibility,
    functional_similarity,
    implementation_similarity,
    overall_similarity,
    goal_relevance,
    state_applicability_score,
    cosine_similarity,
)


class CapabilityEmbeddingSystem:
    """
    Unified embedding system implementing the five required core functions:
    - encode(entity)
    - compose(capabilities)
    - similarity(x, y)
    - compatibility(c1, c2)
    - goal_relevance(cap, goal)
    """
    def __init__(self, schema: DomainSchema):
        self.schema = schema
        self.encoder = CapabilityEncoder(schema)
        self.composer = CapabilityComposer(self.encoder)

    def encode(
        self,
        entity: Union[State, Goal, Capability],
    ) -> Union[EncodedState, EncodedGoal, EncodedCapability]:
        """
        Encodes an application state, goal specification, or atomic/composite capability.
        """
        if isinstance(entity, State):
            return self.encoder.encode_state(entity)
        elif isinstance(entity, Goal):
            return self.encoder.encode_goal(entity)
        elif isinstance(entity, Capability):
            return self.encoder.encode_capability(entity)
        else:
            raise TypeError(f"Unsupported entity type for encoding: {type(entity)}")

    def compose(
        self,
        capabilities: Union[List[Capability], List[EncodedCapability]],
        name: Optional[str] = None,
    ) -> EncodedCapability:
        """
        Constructs a composite representation from a sequence of capabilities.
        Evaluates chain C_n o ... o C_2 o C_1 directly in vector space.
        """
        if not capabilities:
            raise ValueError("Capabilities list cannot be empty.")

        # Ensure elements are EncodedCapability
        encoded_list: List[EncodedCapability] = []
        for c in capabilities:
            if isinstance(c, Capability):
                encoded_list.append(self.encoder.encode_capability(c))
            elif isinstance(c, EncodedCapability):
                encoded_list.append(c)
            else:
                raise TypeError(f"Invalid capability element: {type(c)}")

        return self.composer.compose_chain_vector(encoded_list, name=name)

    def similarity(
        self,
        x: Union[EncodedCapability, EncodedState, EncodedGoal, Capability, State, Goal],
        y: Union[EncodedCapability, EncodedState, EncodedGoal, Capability, State, Goal],
        mode: str = "functional",
    ) -> float:
        """
        Compares two encoded entities.
        Modes: 'functional', 'implementation', 'overall', 'raw_cosine'.
        """
        # Auto-encode if raw objects are passed
        if isinstance(x, (State, Goal, Capability)):
            x = self.encode(x)
        if isinstance(y, (State, Goal, Capability)):
            y = self.encode(y)

        if isinstance(x, EncodedCapability) and isinstance(y, EncodedCapability):
            if mode == "functional":
                return functional_similarity(x, y)
            elif mode == "implementation":
                return implementation_similarity(x, y)
            elif mode == "overall":
                return overall_similarity(x, y)
            elif mode == "raw_cosine":
                return cosine_similarity(x.vector, y.vector)
            else:
                raise ValueError(f"Unknown similarity mode: {mode}")
        else:
            # Generic vector cosine similarity
            return cosine_similarity(x.vector, y.vector)

    def compatibility(
        self,
        c1: Union[Capability, EncodedCapability],
        c2: Union[Capability, EncodedCapability],
        detailed: bool = False,
    ) -> Union[float, dict]:
        """
        Evaluates directional composability: does C1 compose with C2 (C1 -> C2)?
        """
        ec1 = self.encode(c1) if isinstance(c1, Capability) else c1
        ec2 = self.encode(c2) if isinstance(c2, Capability) else c2

        if not isinstance(ec1, EncodedCapability) or not isinstance(ec2, EncodedCapability):
            raise TypeError("Both entities must be capabilities to compute compatibility.")

        if detailed:
            return {
                "precondition_effect": precondition_effect_compatibility(ec1, ec2),
                "input_output": input_output_compatibility(ec1, ec2),
                "total_composability": compatibility_score(ec1, ec2),
            }
        return compatibility_score(ec1, ec2)

    def goal_relevance(
        self,
        cap: Union[Capability, EncodedCapability],
        goal: Union[Goal, EncodedGoal],
    ) -> float:
        """Evaluates goal relevance of a capability."""
        ec = self.encode(cap) if isinstance(cap, Capability) else cap
        eg = self.encode(goal) if isinstance(goal, Goal) else goal
        return goal_relevance(ec, eg)

    def state_applicability(
        self,
        state: Union[State, EncodedState],
        cap: Union[Capability, EncodedCapability],
    ) -> float:
        """Evaluates state applicability: can capability execute on state?"""
        es = self.encode(state) if isinstance(state, State) else state
        ec = self.encode(cap) if isinstance(cap, Capability) else cap
        return state_applicability_score(es, ec)
