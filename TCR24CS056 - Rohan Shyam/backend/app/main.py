from __future__ import annotations

from typing import Any, TypeVar

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.composition import check_compatibility, compose
from app.composition.composer import CompositionError
from app.embedding import EmbeddingEncoder, capability_similarity as compare_capabilities, sparse_cosine
from app.experiments.runner import run_all_experiments
from app.models.formal import ApplicationScenario, Capability, Goal, State
from app.schemas.api import CompositionRequest, GoalRelevanceRequest, SimilarityRequest
from app.services.applicability import capability_applicability
from app.services.formal_logic import state_satisfies_goal
from app.services.relevance import goal_effect_analysis
from app.services.scenario import ScenarioStore

app = FastAPI(
    title="Capability Composition Embedding API",
    version="1.0.0",
    description="Explainable structured embeddings, compatibility, and composition; no path planning.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
encoder = EmbeddingEncoder()
scenario_store = ScenarioStore.with_default_scenario()
# Preserve the module-level name used by the original application while the
# store provides an explicit seam for tests and future persistence.
scenario = scenario_store.get()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "assignment_scope": "vector embedding and capability composition"}


@app.get("/api/scenario", response_model=ApplicationScenario)
def get_scenario() -> ApplicationScenario:
    return scenario


@app.post("/api/scenario", response_model=ApplicationScenario)
def set_scenario(body: ApplicationScenario) -> ApplicationScenario:
    global scenario
    scenario = scenario_store.replace(body)
    return scenario


@app.post("/api/encode/state")
def encode_state(body: State) -> dict:
    vector = encoder.encode_state(body)
    return {"entity_type": "state", "entity_id": body.id, "vector": vector, "dimension_count": len(vector)}


@app.post("/api/encode/goal")
def encode_goal(body: Goal) -> dict:
    vector = encoder.encode_goal(body)
    return {"entity_type": "goal", "entity_id": body.id, "vector": vector, "dimension_count": len(vector)}


@app.post("/api/encode/capability")
def encode_capability(body: Capability) -> dict:
    vector = encoder.encode_capability(body)
    return {"entity_type": "capability", "entity_id": body.id, "vector": vector, "dimension_count": len(vector)}


@app.post("/api/similarity")
def similarity(body: SimilarityRequest) -> dict:
    return {
        "similarity": sparse_cosine(body.left, body.right),
        "metric": "weighted sparse cosine",
        "interpretation": "representation similarity; does not imply composability",
    }


@app.post("/api/similarity/capabilities")
def capability_similarity(body: CompositionRequest) -> dict:
    if len(body.capabilities) != 2:
        raise HTTPException(422, "Exactly two capabilities are required")
    left, right = body.capabilities
    return {
        "left_id": left.id,
        "right_id": right.id,
        **compare_capabilities(encoder, left, right),
    }


@app.post("/api/compatibility")
def compatibility(producer: Capability, consumer: Capability) -> dict:
    return check_compatibility(producer, consumer)


@app.post("/api/compose")
def composition(body: CompositionRequest) -> dict:
    try:
        result, checks = compose(body.capabilities)
    except CompositionError as error:
        raise HTTPException(
            status_code=422,
            detail={"message": str(error), "diagnostics": error.diagnostics},
        ) from error
    vector = encoder.encode_capability(result)
    return {
        "composite": result.model_dump(),
        "embedding": vector,
        "dimension_count": len(vector),
        "compatibility_checks": checks,
    }


@app.post("/api/goal-relevance")
def goal_relevance(body: GoalRelevanceRequest) -> dict:
    return {
        "capability_id": body.capability.id,
        "goal_id": body.goal.id,
        **goal_effect_analysis(body.capability, body.goal, encoder),
    }


ModelT = TypeVar("ModelT", bound=BaseModel)


def _parse_body_model(body: dict[str, Any], key: str, model: type[ModelT]) -> ModelT:
    """Convert nested endpoint payloads to formal models with one error path."""
    try:
        return model.model_validate(body[key])
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/state-goal")
def state_goal(body: dict[str, Any]) -> dict:
    state = _parse_body_model(body, "state", State)
    goal = _parse_body_model(body, "goal", Goal)
    fulfilled, evidence = state_satisfies_goal(state, goal.conditions)
    return {"state_id": state.id, "goal_id": goal.id, "satisfied": fulfilled, "evidence": evidence}


@app.post("/api/applicability")
def applicability(body: dict[str, Any]) -> dict:
    state = _parse_body_model(body, "state", State)
    capability = _parse_body_model(body, "capability", Capability)
    applicable, evidence = capability_applicability(state, capability)
    return {
        "state_id": state.id,
        "capability_id": capability.id,
        "applicable": applicable,
        "evidence": evidence,
    }


@app.get("/api/experiments")
def experiments() -> dict:
    return run_all_experiments(scenario)


@app.post("/api/experiments/run")
def run_experiments(body: ApplicationScenario | None = None) -> dict:
    return run_all_experiments(body or scenario)
