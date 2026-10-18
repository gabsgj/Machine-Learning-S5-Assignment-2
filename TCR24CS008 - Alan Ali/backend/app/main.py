from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.composition import check_compatibility, compose
from app.composition.composer import CompositionError
from app.embedding import EmbeddingEncoder, capability_similarity, sparse_cosine
from app.experiments.runner import load_default_scenario, run_all_experiments
from app.models.formal import ApplicationScenario, Capability, Goal, State
from app.schemas.api import CompositionRequest, GoalRelevanceRequest, SimilarityRequest
from app.services.formal_logic import satisfies, state_satisfies_goal

app = FastAPI(title="Capability Composition Embedding API", version="1.0.0",
              description="Explainable structured embeddings, compatibility, and composition; no path planning.")
app.add_middleware(CORSMiddleware, allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://capability-composition-ml-1.onrender.com",
],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
encoder = EmbeddingEncoder()
scenario = load_default_scenario()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "assignment_scope": "vector embedding and capability composition"}


@app.get("/api/scenario", response_model=ApplicationScenario)
def get_scenario() -> ApplicationScenario:
    return scenario


@app.post("/api/scenario", response_model=ApplicationScenario)
def set_scenario(body: ApplicationScenario) -> ApplicationScenario:
    global scenario
    scenario = body
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
    return {"similarity": sparse_cosine(body.left, body.right), "metric": "weighted sparse cosine", "interpretation": "representation similarity; does not imply composability"}


@app.post("/api/similarity/capabilities")
def capability_similarity(body: CompositionRequest) -> dict:
    if len(body.capabilities) != 2:
        raise HTTPException(422, "Exactly two capabilities are required")
    left, right = body.capabilities
    return {"left_id": left.id, "right_id": right.id, **capability_similarity(encoder, left, right)}


@app.post("/api/compatibility")
def compatibility(producer: Capability, consumer: Capability) -> dict:
    return check_compatibility(producer, consumer)


@app.post("/api/compose")
def composition(body: CompositionRequest) -> dict:
    try:
        result, checks = compose(body.capabilities)
    except CompositionError as error:
        raise HTTPException(status_code=422, detail={"message": str(error), "diagnostics": error.diagnostics}) from error
    vector = encoder.encode_capability(result)
    return {"composite": result.model_dump(), "embedding": vector, "dimension_count": len(vector), "compatibility_checks": checks}


@app.post("/api/goal-relevance")
def goal_relevance(body: GoalRelevanceRequest) -> dict:
    goal_effects = {condition.name: condition for condition in body.goal.conditions}
    matched = [effect.name for effect in body.capability.effects if effect.name in goal_effects and effect.operator == goal_effects[effect.name].operator and effect.value == goal_effects[effect.name].value]
    capability_features = encoder.encode_capability(body.capability)
    goal_features = {f"effect:{encoder._predicate(item)}": encoder.weights["effect"] for item in body.goal.conditions}
    capability_effect_features = {key: value for key, value in capability_features.items() if key.startswith("effect:")}
    return {"capability_id": body.capability.id, "goal_id": body.goal.id, "matched_goal_variables": matched,
            "effect_overlap": len(matched), "goal_effect_coverage": round(len(matched) / len(body.goal.conditions), 8),
            "relevant": bool(matched), "goal_effect_similarity": sparse_cosine(capability_effect_features, goal_features)}


@app.post("/api/state-goal")
def state_goal(body: dict) -> dict:
    try:
        state = State.model_validate(body["state"])
        goal = Goal.model_validate(body["goal"])
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    fulfilled, evidence = state_satisfies_goal(state, goal.conditions)
    return {"state_id": state.id, "goal_id": goal.id, "satisfied": fulfilled, "evidence": evidence}


@app.post("/api/applicability")
def applicability(body: dict) -> dict:
    try:
        state = State.model_validate(body["state"])
        capability = Capability.model_validate(body["capability"])
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    predicates = capability.preconditions + capability.constraints
    evidence = [{"predicate": item.model_dump(), "satisfied": item.name in state.values and
                 satisfies(state.values[item.name], item.operator, item.value)} for item in predicates]
    return {"state_id": state.id, "capability_id": capability.id, "applicable": all(row["satisfied"] for row in evidence), "evidence": evidence}


@app.get("/api/experiments")
def experiments() -> dict:
    return run_all_experiments(scenario)


@app.post("/api/experiments/run")
def run_experiments(body: ApplicationScenario | None = None) -> dict:
    return run_all_experiments(body or scenario)
