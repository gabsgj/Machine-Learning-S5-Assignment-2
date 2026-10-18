# Architecture

## Runtime flow

The React and TypeScript application in `frontend/src/` loads the active scenario from the FastAPI backend and calls backend endpoints for computations. `frontend/src/services/api.ts` is the client boundary. Pages render response data; encoding, compatibility, composition, and experiment calculations are performed by Python modules under `backend/app/`.

```text
Sidebar page → frontend page component → services/api.ts
   → FastAPI route in backend/app/main.py
      → Pydantic models/schemas
      → embedding, formal_logic, compatibility, composer, or runner
   ← JSON response ← page renders evidence, vectors, and charts
```

The backend loads `data/scenarios/commerce.json` at process startup. `GET /api/scenario` returns the active scenario; `POST /api/scenario` replaces it in memory. The example library imports JSON files from `data/scenarios/examples/` into the frontend bundle and posts a selected example as the new active backend scenario. Custom changes are also sent to the same endpoint. No scenario persistence store is implemented.

## Frontend pages

The sidebar runs from Overview through Scenario editor, Capabilities, Relationships, Composition, and Experiments. Overview summarizes the active scenario, while Scenario editor loads examples or edits structured state, goal, and capability fields. Capabilities requests a vector and applicability evidence; Relationships requests capability similarity and directional compatibility, goal relevance, and state/goal evaluation. Composition submits an ordered chain, and Experiments requests and visualizes the report.

## Current API routes

Confirmed against route decorators in `backend/app/main.py` and calls in `frontend/src/services/api.ts`:

| Method | Path | Function |
|---|---|---|
| `GET` | `/api/health` | Service health and assignment scope |
| `GET` | `/api/scenario` | Read active in-memory scenario |
| `POST` | `/api/scenario` | Replace active in-memory scenario |
| `POST` | `/api/encode/state` | Encode a state |
| `POST` | `/api/encode/goal` | Encode a goal |
| `POST` | `/api/encode/capability` | Encode a capability |
| `POST` | `/api/similarity` | Cosine of supplied sparse maps |
| `POST` | `/api/similarity/capabilities` | Section-weighted similarity of exactly two capabilities |
| `POST` | `/api/compatibility` | Producer/consumer compatibility evidence |
| `POST` | `/api/applicability` | Preconditions and constraints against a state |
| `POST` | `/api/state-goal` | Evaluate a state's goal predicates |
| `POST` | `/api/goal-relevance` | Effect overlap and cosine against a goal |
| `POST` | `/api/compose` | Validate and compose an ordered capability chain |
| `GET` | `/api/experiments` | Run experiments on the current active scenario |
| `POST` | `/api/experiments/run` | Run experiments on the supplied scenario or current active scenario |

`POST /api/compatibility` accepts `producer` and `consumer` capability bodies. Composition accepts a `capabilities` array. The API reference is served by FastAPI at `/docs` when the backend is running.

## Computation modules

`backend/app/models/formal.py` defines the strict Pydantic state, goal, predicate, field, cost, capability, and scenario structures. `backend/app/embedding/encoder.py` extracts deterministic features and computes sparse cosine and section-weighted capability comparison. Predicate truth and state/goal checks live in `backend/app/services/formal_logic.py`; directional handoff checks with evidence live in `backend/app/composition/compatibility.py`. `backend/app/composition/composer.py` handles linear composition and operational aggregation, while `backend/app/experiments/runner.py` selects experiment evidence and skip reasons from declared capabilities.

There is no path planner in this architecture. The system describes and evaluates capability representations and compositions; it does not execute the represented services.
