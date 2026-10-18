# Assignment 2 Project State

## Phase history

- **Phase 1 — Backend:** formal Pydantic models, named sparse encoding, predicate evaluation, directional capability compatibility, ordered composition, scenario-driven experiments, API routes, and backend tests were implemented.
- **Phase 2 — Frontend:** React/TypeScript pages were added for Overview, Scenario editor, Capabilities, Relationships, Composition, and Experiments. The editor now uses structured fields, scenario-derived datalist suggestions, an example library, import/download, and an optional advanced JSON editor.
- **Phase 3 — Documentation:** completed 2026-10-03 (Asia/Calcutta). Deliverables, current implementation, dataset, results, and user experience are documented below and in `docs/`.

The primary assignment specification is `C:\Users\Admin\Downloads\markitdown\output2.md`. It requires an embedding for formal application entities, capability composition, five experiments, evaluation, an experimental dataset, and a technical report. Assignment 1 path search and replanning are explicitly outside scope.

## Final architecture summary

The FastAPI backend in `backend/app/main.py` is the computation source of truth. Pydantic models in `backend/app/models/formal.py` define scenario entities. `backend/app/embedding/encoder.py` creates deterministic named sparse vectors and calculates sparse and section-weighted cosine. `backend/app/services/formal_logic.py` evaluates predicates, applicability, and goals. `backend/app/composition/compatibility.py` checks producer-to-consumer requirements and returns evidence; `backend/app/composition/composer.py` composes validated ordered chains. `backend/app/experiments/runner.py` discovers formal experiment candidates and returns measured results or reasoned skips. The React/TypeScript frontend in `frontend/src/` calls the backend through `frontend/src/services/api.ts`.

Current routes are `GET /api/health`, `GET/POST /api/scenario`, `POST /api/encode/state`, `/api/encode/goal`, `/api/encode/capability`, `/api/similarity`, `/api/similarity/capabilities`, `/api/compatibility`, `/api/applicability`, `/api/state-goal`, `/api/goal-relevance`, `/api/compose`, `GET /api/experiments`, and `POST /api/experiments/run`.

## Deliverables audit

1. **Formal embedding design:** `docs/EMBEDDING_DESIGN.md` existed but did not document all current implementation details in the required filename. `docs/DESIGN.md` is the current complete specification; the prior filename points to it.
2. **Implementation:** exists and ran. `EmbeddingEncoder.encode_state`, `.encode_goal`, and `.encode_capability` are in `backend/app/embedding/encoder.py`; `compose` is in `backend/app/composition/composer.py`; `sparse_cosine` and `capability_similarity` are in `backend/app/embedding/encoder.py`. Their exact behavior is summarized in `docs/TECHNICAL_REPORT.md` Section 7.
3. **Experimental dataset:** `data/scenarios/commerce.json` and Level 1–5 examples existed. No source dataset file explicitly represented a composite, so `data/scenarios/composition-example.json` was added and validated through the live API. The coverage table is in `docs/TECHNICAL_REPORT.md` and the final response.
4. **Technical report:** absent before Phase 3; created as `docs/TECHNICAL_REPORT.md` with all twelve required sections and observed results.

## Phase 3 verification and results

- Backend tests: from `backend/`, `python -m pytest tests/ -v` reported **20 passed, 1 warning**. The warning is Starlette's deprecation notice for using `httpx` with its test client. The literal requested executable `python3` was unavailable on Windows (`python3.exe` could not run); the same suite passed with the Windows `python` command.
- Frontend build: from `frontend/`, `npm.cmd run build` succeeded. Vite reports a 620.78 kB minified JavaScript chunk (174.78 kB gzip), above its 500 kB advisory threshold.
- Local usage: backend ran at `http://127.0.0.1:8012`; `GET /api/health` returned `{"status":"ok","assignment_scope":"vector embedding and capability composition"}`. Frontend dev server started at `http://127.0.0.1:5173/` and returned HTTP 200. The production preview also started at `http://127.0.0.1:4173/`.
- Captured commerce `GET /api/experiments`: 7 capabilities, 2 states, 1 goal, and 60 observed capability dimensions; `create-order-api -> make-payment` compatible; `create-order-api -> send-receipt` incompatible; the three-stage composite reliability was `0.9554985`, availability `0.9398592`, and time `960.0 ms`; API/database similarity was `0.62915791` and API/GUI `0.60934613`.
- Captured Level 2 response: 2 capabilities, 2 states, 1 goal, 22 feature dimensions; `create-order -> make-payment` compatible. Longer-chain, alternatives, and operational aggregate groups were skipped with reasons.
- Captured Level 3 response: 3 capabilities, 4 states, 1 goal, 31 feature dimensions; the compatible three-stage composition group was skipped because declared preconditions/effects did not create a valid chain.
- Captured Level 5 response: 6 capabilities, 4 states, 1 goal, 45 feature dimensions; the alternative API/database/API-GUI/database-GUI similarity scores were `0.76934296`, `0.74050302`, and `0.67087813`; `get-weather` was irrelevant to the goal; its three-stage group was skipped.
- Captured `POST /api/compose` for `composition-example`: one compatible handoff; composite reliability `0.9702`, availability `0.9506`, and time cost `40.0 ms`. `POST /api/experiments/run` accepted the dataset with 3 capabilities.

## Current known limitations

- Feature dimensions use literal formal names and do not generalize synonyms or semantically equivalent names.
- Compatibility handles declared same-name typed inputs and producer equality effects under the implemented scalar predicate operators; it is not a general theorem prover and does not check domains or resource capacity.
- Composition is an ordered linear chain; it does not implement branching, loops, rollback, concurrency, conditional effects, or resource contention.
- Reliability and availability aggregation assumes independent component outcomes.
- Scenario updates are in-memory and reset when the backend process restarts.
- Feature weights are hand-designed and have not been learned or calibrated on a large benchmark corpus.
- Operational cost values are scaled but unbounded; large cost magnitudes can dominate reliability/availability coordinates within the operational similarity section.
- The current frontend build triggers Vite's large-chunk advisory.
- A scenario's informal intent cannot substitute for missing formal handoff declarations; Level 3 and Level 5 demonstrate skipped chains under the current checks.

## Documentation files created or updated in Phase 3

- Created `README.md` — project orientation, installation/run commands, tests, experiments, results, and limitations.
- Created `docs/DESIGN.md` — current formal vector specification.
- Created `docs/ARCHITECTURE.md` — data flow and actual API route list.
- Created `docs/EXPERIMENTS.md` — method, captured outputs, interpretation, and skips.
- Created `docs/TECHNICAL_REPORT.md` — required twelve-section report.
- Created `docs/USER_MANUAL.md` — setup, scenario editing, API, verification, and troubleshooting.
- Created `docs/USER_GUIDE.md` — first-visit page walkthrough, quick start, editor explanation, and glossary.
- Updated `docs/EMBEDDING_DESIGN.md` and `docs/PHASE_2_USER_GUIDE.md` to point to the current docs.
- Updated `PROJECT_STATE.md` with this final phase record.

No backend or frontend logic, schema, or endpoint was changed in Phase 3. One dataset file was added to close the explicit-composite coverage gap.

## Commands to run the full project

These commands document the local development and verification setup. To use the deployed application without running the project locally, open https://capability-composition-ml-1.onrender.com.

From repository root in PowerShell, install dependencies:

```powershell
python -m pip install -r backend\requirements.txt
cd frontend
npm.cmd install
```

Start the backend in a terminal from the repository root:

```powershell
python -m uvicorn app.main:app --reload --app-dir backend
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Run verification:

```powershell
python -m pytest backend\tests -v
cd frontend
npm.cmd run build
```

Run the default experiment summary from `backend/`:

```powershell
python -c "from app.experiments.runner import run_all_experiments; r=run_all_experiments(); print(r['scenario_id'], r['metrics']); [print(x['id'], 'skipped: '+x['skipped'] if 'skipped' in x else 'completed') for x in r['experiments']]"
```
