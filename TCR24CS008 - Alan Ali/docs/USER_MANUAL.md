# User Manual

## 1. What the application does

Capability Composition is a local analysis tool for formal application scenarios. It encodes states, goals, and capabilities; checks state applicability and capability handoffs; builds ordered composite capabilities; and reports scenario-based experiments. It does not invoke the external operations described in a scenario or create an execution plan.

## 2. Start the project

> This manual covers running the project locally for development or inspection. If you just want to use the live application, see the Live Demo link in the main [README](../README.md) — you don't need anything on this page to do that.

Use PowerShell from the repository root. Install the backend and frontend dependencies:

```powershell
python -m pip install -r backend\requirements.txt
cd frontend
npm.cmd install
```

Start each service in a separate terminal. From the repository root, start the API:

```powershell
python -m uvicorn app.main:app --reload --app-dir backend
```

From `frontend/`, start Vite:

```powershell
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Visit `http://127.0.0.1:5173/`. The normal API address is `http://127.0.0.1:8000`; API docs are at `http://127.0.0.1:8000/docs`. The frontend expects this backend address unless `VITE_API_BASE_URL` is configured at frontend build time.

## 3. Understand a scenario

A scenario has an ID and name, a list of states, goals, and capabilities. State values describe snapshots. Goal predicates express desired values or simple comparisons. Each capability declares formal interfaces and behavior plus operational data. For exact fields and feature formulas, read [DESIGN.md](DESIGN.md).

The default active scenario is `data/scenarios/commerce.json`. Example files appear in `data/scenarios/examples/`; `data/scenarios/composition-example.json` explicitly stores a two-stage composite alongside its component capabilities.

## 4. Work through the pages

The [website guide](USER_GUIDE.md) walks through a first visit. Overview summarizes the active scenario. In Scenario editor you can load examples or edit a working scenario; Capabilities inspects a vector and applicability, and Relationships compares resemblance, compatibility, and goal relevance. Composition constructs a validated chain, while Experiments displays calculated measurements and skip reasons.

Use Similarity and Compatibility differently. Similarity is a vector score. Compatibility is a directional symbolic check. A high similarity score cannot make a failed handoff valid.

## 5. Edit and save scenarios

Example cards load bundled example JSON into the active scenario endpoint. This creates a working server copy; the example source is not edited. In Custom Scenario, structured fields edit a draft. **Validate & save scenario** sends the whole scenario to the backend. Import JSON loads into the form first; Download saves the draft as a file. The scenario endpoint stores changes in memory and the backend restart reloads default commerce data.

The editor suggests variable names and values from the current scenario. These are browser datalist suggestions, not a closed vocabulary. The formal backend schema performs final validation, including required fields, capability types, and reliability/availability ranges.

## 6. Run and interpret experiments

Open Experiments and click **Run all experiments**, or use the example library's **Load & Run** action. The backend evaluates seven groups: compatibility, three-capability composition, alternative implementations, goal relevance, operational properties, state/goal encoding, and state awareness. Read [EXPERIMENTS.md](EXPERIMENTS.md) for actual responses and why some groups are skipped on smaller scenarios.

A skipped group means its input conditions were not met (for example, no chain of at least three compatible capabilities); it does not mean the runner crashed. Experiment results come from the current active backend scenario.

## 7. API and command line

The full route list and request boundaries are documented in [ARCHITECTURE.md](ARCHITECTURE.md). `GET /api/experiments` evaluates the active scenario. `POST /api/experiments/run` accepts a supplied scenario for a one-off run. The Python runner can also be called from `backend/`:

```powershell
python -c "from app.experiments.runner import run_all_experiments; r=run_all_experiments(); print(r['scenario_id'], r['metrics']); [print(x['id'], 'skipped: '+x['skipped'] if 'skipped' in x else 'completed') for x in r['experiments']]"
```

## 8. Verification commands

From the repository root, run the backend tests and frontend production build:

```powershell
python -m pytest backend\tests -v
cd frontend
npm.cmd run build
```

## 9. Troubleshooting

The local backend checks below apply when running the project locally. For normal app use, open the [live application](https://capability-composition-ml-1.onrender.com).

| Symptom | Check |
|---|---|
| API disconnected | Confirm the backend is running at port 8000 and open `http://127.0.0.1:8000/api/health`. |
| Scenario rejected | Check JSON types, required IDs/names, predicate operators, capability type, and reliability/availability values in [formal.py](../backend/app/models/formal.py). |
| Composition rejected | Read the returned evidence. Check producer output names/types and whether producer equality effects satisfy consumer preconditions. |
| Experiment group skipped | Read the reason displayed above the experiment cards; the current scenario may not contain a qualifying pair, chain, alternative group, state, or goal. |
| Scenario changes disappear after restart | Scenario replacement is in-memory; download the JSON and reload it into the editor after restart if needed. |

## 10. Current limits

Feature matching uses literal names; compatibility is not a general theorem prover; composition supports linear chains only; reliability and availability aggregation assumes independence; and active scenarios are not persisted across backend restarts. More detail and observed limitations are in [TECHNICAL_REPORT.md](TECHNICAL_REPORT.md).
