# Backend

The backend implements the formal models, named sparse embedding, symbolic compatibility checks, ordered composition, experiment runner, and FastAPI endpoints. It contains no path search or replanning code.

## Setup and commands

These instructions are for backend development and API inspection. To use the deployed application, open https://capability-composition-ml-1.onrender.com; no local setup is needed.

From the repository root, create a virtual environment and install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Run tests from the repository root:

```powershell
python -m pytest backend\tests -v
```

Start the API from the repository root:

```powershell
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --reload --app-dir backend
```

API docs are served at `http://127.0.0.1:8000/docs`. The default dataset is `data/scenarios/commerce.json`.

## API outline

| Method and path | Purpose |
|---|---|
| `GET /api/health` | Health/status |
| `GET /api/scenario`, `POST /api/scenario` | Read/replace the in-memory scenario |
| `POST /api/encode/state` | Encode one formal state |
| `POST /api/encode/goal` | Encode one formal goal |
| `POST /api/encode/capability` | Encode one capability |
| `POST /api/similarity` | Cosine between named feature maps |
| `POST /api/similarity/capabilities` | Encode and compare exactly two capabilities |
| `POST /api/compatibility` | Producer/consumer symbolic compatibility |
| `POST /api/applicability` | Check preconditions and constraints against a state |
| `POST /api/state-goal` | Check whether a state satisfies a goal |
| `POST /api/compose` | Validate and compose an ordered chain |
| `POST /api/goal-relevance` | Explain goal effect overlap and cosine |
| `GET /api/experiments`, `POST /api/experiments/run` | Run measured experiment scenarios |

Compatibility request bodies use `{"producer": ..., "consumer": ...}`. Composition uses `{"capabilities": [...]}`. The complete request schema for each endpoint is visible through OpenAPI `/docs`.

## Example

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/compatibility `
  -ContentType 'application/json' -InFile backend\examples\compatibility.json
```

The response includes a `compatible` boolean, requirement-by-requirement `evidence`, and failure `reasons`. Exact output is in `backend/examples/compatibility_response.json`.

## Experiment run (default commerce scenario)

The `GET /api/experiments` endpoint computes the following from the JSON scenario at request time:

- CreateOrder API -> MakePayment: compatible; the `Order.exists=true` precondition and UUID `order_id` input are both evidenced.
- CreateOrder API -> CancelCart: incompatible; `Order.exists=false` conflicts with the produced `Order.exists=true`.
- Three-item ordered composition succeeds with aggregate reliability `0.9554985`, availability `0.9398592`, and execution time `960 ms`.
- Alternative implementation similarity: API/Database `0.62915791`, API/GUI `0.60934613`; API/MakePayment `0.07704056`. These are weighted means of per-section cosine scores, not compatibility probabilities.
- Goal effect coverage finds CreateOrder API, MakePayment, and SendReceipt each contribute one of three goal conditions; CancelCart and RefreshProductCatalog contribute none.
- Operational comparison returns measured times of `120`, `80`, and `1400 ms` for API, Database, and GUI implementations, respectively, with their declared reliability and availability values.

These are measured outputs of the provided formal dataset and current encoding/aggregation functions. They are illustrative scenario results, not general benchmark claims.

