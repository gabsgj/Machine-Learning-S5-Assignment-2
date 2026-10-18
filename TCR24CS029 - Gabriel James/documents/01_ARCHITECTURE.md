# Architecture

CareWeave Mini is one system in two halves. The C++ half owns the formal model: specification
parsing, embedding, mapping, compatibility, adapter synthesis, composition, planning, bundling
and the gateway that executes calls. The Python half owns the hospital: seven independently
runnable Flask modules, each with its own port, database, tests and user interface. The gateway
is the only component that talks to both halves at once, over local HTTP.

## 1. Repository map

```
core/            the C++ library, the CLI and the gateway binary
  include/careweave/   public headers, one directory per layer
  src/                 the same layers as implementation
  cli/                 command line front end and the gateway entry point
  tests/               13 C++ test suites
  third_party/         vendored httplib, nlohmann json, sqlite3
modules/         seven Flask modules (own port, SQLite database, tests, UI)
dashboard/       the static gateway dashboard (offline HTML, CSS, JavaScript)
specs/           specification sheets, schema, workflows, shared state variables
dataset/         the three embedded application problems with their expected mappings
experiments/     experiment sources, specs, evaluation and the frozen results in out/
scripts/         orchestration only: build, setup, start, stop, tests, experiments, verify
documents/       the work plan, the build log and the numbered documents
dist/            generated bundles (runtime artifact, not source)
```

## 2. The core layers

Each layer is a small library with a header that states its contract, and each one only depends
on the layers to its left:

```
core       typed values, conditions, capability tuple, algebraic state
 spec      YAML and JSON sheet parsers, schema validation, canonical JSON
embedding  hash projections, block layout, the three embeddings, vector math
 mapper    requirement scoring, ranking, ambiguity margins, kind tie breaks
 compat    symbolic entailment plus the vector compatibility score, explainable verdicts
adapter    synthesis of a callable binding, a runner, HTTP/SQLite/file transports
composer  algebraic composition of capabilities into composites
planner   forward and backward search with operational attribute strategies
 bundle    self contained distribution assembly with a manifest
gateway   discovery, registry, resolution, execution, workflows, audit, HTTP server
```

`core/tests` mirrors the layers: one suite per concern plus cross cutting suites for
determinism, the corpus and the bundle.

### Data flow of one requirement

1. The client (CLI, dashboard, workflow step) holds a requirement sheet with exactly one
   capability: its inputs, outputs, preconditions and effects.
2. `embedding` encodes the requirement and every registry capability into the partitioned
   vector; `mapper` scores candidates with the name, field and condition views, applies the
   kind tie break, and marks scores inside the ambiguity margin.
3. `adapter` synthesizes the binding for the chosen candidate: input renames and transforms,
   output renames, transport and endpoint, with the match confidence.
4. The gateway executes the call against the module. A failed call can fall back to the next
   ranked candidate in a different module while that module's circuit allows it; one module is
   tried at most once per call and an attempt log records every decision.
5. Every attempt lands in the SQLite audit trail. Workflow runs guard each adjacent pair with
   `compat` and refuse to continue after an INCOMPATIBLE verdict.

## 3. The modules

| Module | Port | Database | Domain |
| --- | --- | --- | --- |
| patient-registry | 5001 | data/patient_registry.db | registration, admission, discharge, allergy, lookup |
| appointment-queue | 5002 | data/appointment_queue.db | queue tickets, calling next, triage, cancel |
| opd-ehr | 5003 | data/opd_ehr.db | encounters, vitals, prescriptions, closing |
| pharmacy-inventory | 5004 | data/pharmacy_inventory.db | drug catalogue, stock, dispensing, replenishment |
| pos-billing | 5005 | data/pos_billing.db | invoices, payments, receipts, receipt notices |
| legacy-lab-service | 5006 | data/legacy_lab.db | lab orders, sample receipt, results, reports |
| patient-registry-alt | 5007 | data/patient_registry_alt.db | the legacy registration vocabulary and its row interface |

Every module follows the same shape: `app.py` builds the Flask app, `services/` holds the
domain logic, `db.py` owns the SQLite connection in WAL mode, `seed.py` installs demonstration
data idempotently, `ui/` serves the interface and `run.py` seeds and then serves. `GET /spec`
answers the module's specification sheet, which is the same document as its `spec.json`, so the
gateway can discover a running module from the wire; when a module is down the gateway falls
back to reading `spec.json` from disk.

## 4. The gateway

The gateway is one process that owns no domain data:

- Discovery: `GET /spec` from every module on its port, falling back to the specification file.
- Registry: every declared capability of every module, embedded and addressable by name.
- Resolution and execution: as in the data flow above, including per module circuit breaking,
  a single attempt per module, and fallback across modules.
- The canonical hospital API: `POST /api/hospital/<capability name>` binds the name to the
  registry capability that declares it and executes it, giving every clinical area one prefix.
- Workflows: multi step definitions (`module` plus `capability`, or a `requirement` sheet) with
  compatibility verdicts between adjacent steps; only an INCOMPATIBLE verdict stops a run.
- The audit trail: one SQLite row per call, workflow step, resolution or skip, with latency,
  attempt count, fallback flag and message.
- The management API and the dashboard: the endpoints listed in
  `documents/07_API_REFERENCE.md`, all thin shells over the same library methods the CLI uses.

## 5. The dashboard and the bundle

The dashboard is a static site with no build step: `index.html`, `styles.css` and `app.js`.
It is mounted by the gateway at `/` and only calls the gateway's own endpoints with relative
paths, so it works offline and its assets contain no external address.

`bundle::createBundle` assembles a self contained copy of the whole system: the modules, the
specification sheets, the gateway binary, the dashboard and three scripts (`setup.sh`,
`start.sh`, `stop.sh`), plus a `MANIFEST.json` that records what was written. The CLI's bundle
command and the dashboard's bundle panel call the same function. `dist/` is generated output.

## 6. Orchestration and verification

`scripts/` contains orchestration only: no business logic lives there.

| Script | Role |
| --- | --- |
| `build.sh` | configure and build the C++ core, failing on any compiler warning |
| `setup_modules.sh` | create the shared Python environment and install module requirements |
| `start_all.sh` | seed and start the seven modules and the gateway, then poll health |
| `stop_all.sh` | stop the gateway and the modules by their recorded pids |
| `run_unit_tests.sh` | the C++ suites and the seven module test suites with coverage |
| `run_experiments.sh` | the five experiments and the evaluation harness |
| `run_integrated_workflow.sh` | the canonical and alias clinic workflows with database checks |
| `verify_all.sh` | the whole acceptance path into a timestamped log |

All scripts resolve their own location, run from any working directory and are idempotent.

## 7. Runtime picture

```
requirement sheet ---> [embedding] ---> [mapper] ---> [adapter synthesis]
                                                             |
                                                     [gateway execution]
                                                       |     |     |
                                          patient-registry ... patient-registry-alt
                                                       |     |     |
                                                     SQLite databases
                                                             |
                                                     [audit trail]
```

The same pipeline is reachable three ways: the CLI for scripts and experiments, the dashboard
for interactive use, and workflows for multi step runs. All three land in the same audit trail.
