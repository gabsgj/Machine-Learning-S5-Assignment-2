# Capability Composition Embedding

I built this project to explore the assignment's central question: how can application states, goals, and capabilities be represented so that resemblance, compatibility, and composition can be computed from formal descriptions instead of only being described? The backend computes embeddings, compatibility, composition, and experiment results; the React interface displays and edits the active scenario.

## Why I built it this way

I started with the backend: formal Pydantic models, named sparse encoding, predicate evaluation, directional capability compatibility, ordered composition, scenario-driven experiments, API routes, and backend tests. I then built the React/TypeScript pages. The first editor exposed scenario JSON directly; I rebuilt it as a form-based Scenario Editor, then added scenario-derived suggestions, an example-scenario library, import/download, and an optional advanced JSON editor. After that came the visual redesign and, finally, this documentation pass. That order let me build the interface around the backend's formal model and then give readers examples they can load and inspect.

One choice shaped the representation: I used named sparse feature dimensions rather than a learned embedding. The inputs are formal fields and predicates, so I wanted each coordinate to remain inspectable. Similarity measures resemblance, but cannot establish whether a producer satisfies a consumer's typed input and preconditions; a separate symbolic check handles that directional handoff. This suits the small formal dataset, without making a claim that it outperforms learned methods generally.

## Assignment objective

I represent preconditions, effects, typed inputs and outputs, constraints, resources, mechanisms, and operational attributes. The system measures resemblance separately from whether two operations can be connected. Assignment 1's planner and path-search algorithms are outside this project's scope.

## Architecture and stack

The backend uses Python, FastAPI, Pydantic, and pytest. The frontend uses React, TypeScript, Vite, Recharts, and lucide-react. Scenarios are JSON files in `data/scenarios/`. Browser pages call the FastAPI endpoints in `backend/app/main.py`; embedding, compatibility, composition, and experiment logic live in separate backend modules. The browser API base defaults to `http://127.0.0.1:8000`; copy `frontend/.env.example` to `frontend/.env.local` when a different API URL is needed.

See [the architecture guide](docs/ARCHITECTURE.md) and [the formal design](docs/DESIGN.md) for details.

## Project structure

```text
backend/app/models/       Formal Pydantic models
backend/app/embedding/    Named sparse vector encoding and similarity
backend/app/composition/  Directional compatibility and ordered composition
backend/app/experiments/  Scenario-driven experiment runner
backend/tests/            Backend test suite
scripts/                  Repository-level data validation checks
frontend/src/pages/       Overview, capability, relationship, composition,
                          experiment, and scenario editor pages
frontend/src/services/    API client
data/scenarios/           Commerce, composition, and Level 1–5 examples
docs/                     Design, architecture, reports, and user documentation
pyproject.toml            Shared pytest discovery/options
```

## Installation and run

I use PowerShell from the repository root. Install backend dependencies and frontend dependencies:

```powershell
python -m pip install -r backend\requirements.txt
cd frontend
npm.cmd install
```

Start the backend in one terminal from the repository root:

```powershell
python -m uvicorn app.main:app --reload --app-dir backend
```

Start the frontend in another terminal:

```powershell
cd frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173/`. The backend API is at `http://127.0.0.1:8000`; its interactive API reference is at `http://127.0.0.1:8000/docs`.

To run the local quality gates from the repository root:

```powershell
python scripts\validate_scenarios.py
python -m pytest backend\tests -v
cd frontend
npm.cmd run check
```

`validate_scenarios.py` checks every JSON file under `data/scenarios/` against the backend's Pydantic schema. The frontend `check` script runs the strict TypeScript build and Vite production build. Use `npm run ...` instead of `npm.cmd run ...` in a POSIX shell.

To run the default commerce experiment report from `backend/`:

```powershell
python -c "from app.experiments.runner import run_all_experiments; r=run_all_experiments(); print(r['scenario_id'], r['metrics']); [print(x['id'], 'skipped: '+x['skipped'] if 'skipped' in x else 'completed') for x in r['experiments']]"
```

The experiment code prints measurements from the formal JSON scenario; it does not execute the described external application operations. The browser uses the same backend and its active in-memory scenario. Scenario changes made in the editor replace that backend scenario until it restarts; use **Download** to keep a JSON copy.

## Mathematical ideas

I encode states, goals, and capabilities as deterministic sparse maps whose dimensions are named by formal field and role. Named sparse cosine measures vector resemblance. Capability resemblance is the weighted mean of within-section cosines. Compatibility is a distinct symbolic, directional check of required typed inputs and preconditions against producer outputs and effects. Composition validates every ordered handoff and returns a `COMPOSITE` capability. The full formulas and exact section weights are in [DESIGN.md](docs/DESIGN.md).

## Captured results

When I ran the current commerce scenario, I got 7 capabilities, 2 states, 1 goal, and 60 observed capability feature dimensions. `create-order-api -> make-payment` was compatible, and `create-order-api -> make-payment -> send-receipt` composed with reliability `0.9554985`, availability `0.9398592`, and time cost `960 ms`. Alternative implementation similarities were `0.62915791` (API/database) and `0.60934613` (API/GUI). These are measurements on the supplied scenario, not general benchmark claims. [EXPERIMENTS.md](docs/EXPERIMENTS.md) contains the observed outputs and the Level 2, 3, and 5 runs.

## Limitations

I know feature names are literal, so synonyms do not match. Compatibility supports the implemented named fields and scalar predicate operators rather than general theorem proving. Composition is a linear chain; it does not handle branching, loops, rollback, concurrency, or resource contention. Reliability and availability products assume independent component outcomes. Scenario replacement is in-memory and resets on backend restart. The [technical report](docs/TECHNICAL_REPORT.md) discusses these limits in more detail.

## User documentation

- [First-visit website guide](docs/USER_GUIDE.md)
- [Setup and detailed user manual](docs/USER_MANUAL.md)
- [Formal embedding and composition design](docs/DESIGN.md)
- [API and runtime architecture](docs/ARCHITECTURE.md)
- [Experimental setup and results](docs/EXPERIMENTS.md)
- [Technical report](docs/TECHNICAL_REPORT.md)

## Contributor

Alan P Ali
TCR24CS008
CSE/S5
