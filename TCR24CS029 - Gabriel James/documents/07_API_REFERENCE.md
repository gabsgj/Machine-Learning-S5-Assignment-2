# API reference

Three surfaces: the command line tool, the gateway HTTP API (which the dashboard and the CLI's
`run` command speak) and the seven module HTTP APIs. Everything below is implemented and
exercised by the test suites and the acceptance script.

## 1. Command line

Build first (`sh scripts/build.sh`); the binary is `core/build/careweave_cli`.

```
careweave_cli validate <spec file>...
careweave_cli spec-yaml <spec.json>... [--out <path>]
careweave_cli embed <spec file> [--capability <id>] [--similarity] [--json]
careweave_cli compare <application sheet> <earlier id> <later id> [--json]
careweave_cli mapping <requirement sheet> --pool <spec file>... [--min-score X] [--margin Y] [--top N]
careweave_cli adapters <requirement sheet> --pool <spec file>... [--module <id>] [--base-url <url>] [--out <dir>] [--json]
careweave_cli plan <spec file> [--goal "var=value"] [--strategy fewest|time|money|reliability] [--max-depth N] [--backward] [--json]
careweave_cli run <requirement sheet> [--inputs k=v,...] [--preferred <module,...>] [--allow-modules <module,...>] [--resolve-only] [--gateway <url>] [--json]
careweave_cli run --workflow <workflow file> [--gateway <url>] [--json]
careweave_cli bundle [--root <dir>] [--out <dir>] [--modules <id,...>] [--workflows <name,...>] [--no-workflows] [--no-dashboard] [--json]
careweave_cli export <spec file>... [--what specs|compat|embedding] [--out <dir>]
```

| Command | What it does | Exit codes |
| --- | --- | --- |
| `validate` | parses and schema validates every sheet given | 0 valid, 1 any invalid |
| `spec-yaml` | converts canonical spec JSON to YAML | 0/1 |
| `embed` | prints the partitioned vector per capability; `--similarity` prints the pairwise matrix in the sheet | 0/1 |
| `compare` | compatibility report for one adjacent pair with every check | 0 always (the verdict is output, not an exit code) |
| `mapping` | scores a requirement against a pool, prints the ranking with margin flags | 0/1 |
| `adapters` | synthesizes adapters for the top candidates, writes them with `--out` | 0/1 |
| `plan` | forward or backward plan for a goal (background machinery, outside the Assignment 2 scope) | 0 found, 1 none |
| `run` | resolves and calls through a running gateway; `--preferred` is a tie break and `--allow-modules` a hard filter; `--resolve-only` stops after ranking; `run --workflow` runs a workflow | 0 success, 1 failure, 2 usage |
| `bundle` | assembles a bundle (see the bundling guide); `--modules` is completed with the workflow closure | 0/1 |
| `export` | writes spec, compatibility or embedding tables | 0/1 |

Examples:

```
$ core/build/careweave_cli validate specs/app/hospital_clinic_visit.yaml
ok   specs/app/hospital_clinic_visit.yaml (14 capabilities, 19 state variables)

$ core/build/careweave_cli compare experiments/specs/order_pattern.yaml PAT-CreateOrder PAT-MakePayment
compare PAT-CreateOrder then PAT-MakePayment in experiments/specs/order_pattern.yaml
verdict compatible
entailment overall entailed (entailed 1, possible 0, conflicts 0, unknown 0)
  - Order.exists = true : Order.exists in true -> entailed
scores coverage 1.0000 signed cosine 1.0000 vector 1.0000 functional 0.8399 implementation 0.9835

$ core/build/careweave_cli embed specs/app/requirements/register_pat.yaml --json | head -c 60
{"capabilities":[{"blocks":{"availability":{"norm":1.0,...
```

## 2. Gateway

```
careweave_gateway [--root <dir>] [--host <addr>] [--port <n>] [--audit <path>] [--dashboard <dir>] [--no-audit]
```

Defaults: root `.`, host `127.0.0.1`, port 5100, audit `<root>/logs/gateway_audit.db`,
dashboard `<root>/dashboard` (mounted at `/` when it exists). `--modules <dir>` overrides the
module directory. Discovery targets are the seven modules on ports 5001 to 5007 with their
`spec.json` files as fallbacks.

| Method and path | Body | Answers |
| --- | --- | --- |
| `GET /` | | the dashboard (when mounted) |
| `GET /health` | | status, module count, healthy count, uptime, audit event count |
| `GET /api/modules` | | one row per module: available, healthy, circuit, capabilities, base, spec source, message |
| `POST /api/discover` | | re-runs discovery and answers the module table |
| `GET /api/registry` | | every registered capability with module, id, name, type, endpoint |
| `GET /api/audit?limit=N` | | the newest N audit rows (default 50, cap 500) |
| `POST /api/resolve` | `{"requirement": "<sheet path>", "preferred_modules": [...], "allow_modules": [...]}` (the lists optional) | the ranked candidates with scores and ambiguity flags |
| `POST /api/call` | `{"requirement": "...", "inputs": {...}, "preferred_modules": [...], "allow_modules": [...]}` | the call outcome: module, capability, adapter, outputs, attempts, trace |
| `POST /api/workflow` | `{"workflow": "<path>"}` or `{"definition": {...}}`; a step may carry `preferred_modules` and `allow_modules` | every step with its compatibility verdict and call result |
| `GET /api/hospital/operations` | | the clinical area map plus every capability per module |
| `POST /api/hospital/<capability name>` | the capability's inputs | the call outcome of the registry capability with that name |
| `GET /api/sheets` | | every application, requirement and workflow sheet with metadata |
| `GET /api/sheet?path=<relative>` | | one sheet as canonical JSON (or a workflow definition) |
| `POST /api/embed` | `{"sheet": "...", "capability": "<id optional>"}` | block sizes and norms per capability |
| `POST /api/embed/compare` | `{"sheet": "...", "left": "<id>", "right": "<id>"}` | total, functional, implementation and per block cosines |
| `POST /api/adapter` | `{"requirement": "...", "module": "...", "capability": "..."}` | the synthesized adapter with bindings and confidence |
| `POST /api/plan` | `{"sheet": "...", "goals": {...}, "strategy": "...", "max_depth": N, "backward": bool}` | the plan with search statistics and the scope note |
| `POST /api/bundle` | `{"out": "<dir>", "no_dashboard": bool, "modules": [...], "workflows": [...], "no_workflows": bool}` (all optional) | the bundle manifest |
| `GET /api/experiments` | | the frozen evaluation and the five experiment documents |

Status codes: 200 success; 400 bad body, bad path or bad value (an empty or malformed
`allow_modules`, `modules` or `workflows` list is a 400); 404 unknown capability, unknown sheet
or no experiment results; 422 the requirement did not parse, no candidate matched, the plan was
not found or the adapter could not be synthesized; 502 the module call itself failed after
resolution; 500 a bundle could not be assembled, including an unknown module id or workflow
name. Every error body is `{"status": "error", "error": "<reason>"}`.

Examples:

```
$ curl -sS -X POST -H 'Content-Type: application/json' \
    --data '{"requirement": "specs/app/requirements/register_pat.yaml"}' \
    http://127.0.0.1:5100/api/resolve | head -c 120
[ { "ambiguous": true, "capability_id": "Pat_reg", "module_id": "patient-registry-alt", ...

$ curl -sS -X POST -H 'Content-Type: application/json' \
    --data '{"requirement": "specs/app/requirements/register_pat.yaml", "allow_modules": ["patient-registry"]}' \
    http://127.0.0.1:5100/api/resolve \
    | python3 -c 'import json, sys; rows = json.load(sys.stdin); print(len(rows), rows[0]["module_id"], rows[0]["capability_id"], round(rows[0]["total"], 4))'
6 patient-registry PR-Register 0.7928

$ curl -sS -X POST -H 'Content-Type: application/json' \
    --data '{"mrn": "BND-0001", "full_name": "Bundle Check"}' \
    http://127.0.0.1:5100/api/hospital/register_patient
{ "adapter_id": "adapter-live-patient-registry-PR-Register", "attempts": 1, ... "ok": true, ... }

$ curl -sS -X POST -H 'Content-Type: application/json' \
    --data '{}' http://127.0.0.1:5100/api/hospital/teleport_patient -w ' [%{http_code}]'
{ "error": "no registry capability is named teleport_patient", "status": "error" } [404]
```

## 3. Module HTTP APIs

Every module serves `GET /health`, `GET /spec` and its user interface under `/ui/`. The API
routes, by module and capability id:

| Module | Capability | Route |
| --- | --- | --- |
| patient-registry | PR-Register / PR-Admit / PR-Discharge / PR-FlagAllergy / PR-Lookup | `/api/register_patient`, `/api/admit_patient`, `/api/discharge_patient`, `/api/flag_allergy`, `/api/lookup_patient` |
| appointment-queue | AQ-CreateTicket / AQ-CallNext / AQ-UpdateTriage / AQ-Cancel | `/api/create_ticket`, `/api/call_next_ticket`, `/api/update_triage`, `/api/cancel_ticket` |
| opd-ehr | EHR-StartEncounter / EHR-RecordVitals / EHR-IssuePrescription / EHR-CloseEncounter | `/api/start_encounter`, `/api/record_vitals`, `/api/issue_prescription`, `/api/close_encounter` |
| pharmacy-inventory | PH-RegisterDrug / PH-CheckStock / PH-DispenseDrug / PH-Replenish | `/api/register_drug`, `/api/check_stock`, `/api/dispense_drug`, `/api/replenish_stock` |
| pos-billing | BILL-GenerateInvoice / BILL-ProcessPayment / BILL-GetReceipt / BILL-SendReceiptNotice | `/api/generate_invoice`, `/api/process_payment`, `/api/get_receipt`, `/api/send_receipt_notice` |
| legacy-lab-service | LAB-OrderTest / LAB-ReceiveSample / LAB-EnterResult / LAB-GetReport | `/api/order_test`, `/api/receive_sample`, `/api/enter_result`, `/api/get_report` |
| patient-registry-alt | PA-Register / PA-Lookup / PA-Verify | `/api/pat_reg`, `/api/pat_lookup`, `/api/pat_verify` |

All module APIs accept and answer JSON. A domain refusal (unknown mrn, empty stock, single
active encounter) answers 422 with a reason; an unknown route answers 404.

## 4. Scripts and environment

The orchestration scripts (`scripts/build.sh`, `setup_modules.sh`, `start_all.sh`,
`stop_all.sh`, `run_unit_tests.sh`, `run_experiments.sh`, `run_integrated_workflow.sh`,
`verify_all.sh`) are described in `documents/09_TESTING_AND_VERIFICATION.md` and
`documents/01_ARCHITECTURE.md`. Recognized environment variables:

| Variable | Used by | Meaning |
| --- | --- | --- |
| `CAREWEAVE_PYTHON` | scripts and bundles | interpreter for the modules (default: the repository `.venv`, then `python3`) |
| `CAREWEAVE_GATEWAY_PORT` | scripts and bundles | gateway port (default 5100) |
| `CAREWEAVE_BUILD_DIR` | build scripts | build directory (default `core/build`) |
| `CAREWEAVE_JOBS` | build scripts | parallel build jobs (default 8) |
| `CAREWEAVE_PORT` | module `run.py` | one module's port (defaults from its spec) |
