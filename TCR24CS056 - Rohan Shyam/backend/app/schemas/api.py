from typing import Any

from pydantic import BaseModel, Field

from app.models.formal import ApplicationScenario, Capability, Goal, State


class SimilarityRequest(BaseModel):
    left: dict[str, float]
    right: dict[str, float]


class CompositionRequest(BaseModel):
    capabilities: list[Capability] = Field(min_length=2)


class GoalRelevanceRequest(BaseModel):
    capability: Capability
    goal: Goal


class ScenarioRequest(BaseModel):
    scenario: ApplicationScenario


class EncodeResponse(BaseModel):
    entity_type: str
    entity_id: str
    vector: dict[str, float]
    dimension_count: int


class GenericResponse(BaseModel):
    result: dict[str, Any]
