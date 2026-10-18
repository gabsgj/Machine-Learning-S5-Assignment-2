# Developer guide

Everything a maintainer needs: the toolchain, the loop, the extension points and the
conventions that keep the repository consistent.

## 1. Toolchain

- CMake 3.16 or newer and a C++17 compiler (Apple clang or GCC). C99 for the vendored SQLite.
- Python 3.10 or newer for the modules; `python3 -m venv` and `pip` for the environment.
- `sqlite3` on the path, used by the integrated workflow script for its database checks.
- Optional: a browser to open the UIs, and a LaTeX installation to rebuild the report PDF.

## 2. The loop

```
sh scripts/setup_modules.sh     # once: create .venv and install module requirements
sh scripts/build.sh             # configure, build, fail on warnings
sh scripts/run_unit_tests.sh    # C++ suites plus the seven module suites with coverage
sh scripts/start_all.sh         # modules plus gateway, health polled
sh scripts/stop_all.sh          # stop everything by pid
sh scripts/verify_all.sh        # the whole acceptance path into logs/verify_all_<ts>.log
```

`build.sh` defaults to `core/build` and `-j8`; `CAREWEAVE_BUILD_DIR` and `CAREWEAVE_JOBS`
override both. A plain CMake configure defaults to Release because the evaluation numbers
describe an optimized build; `-DCMAKE_BUILD_TYPE=Debug` wins if passed explicitly.
`CAREWEAVE_BUILD_TESTS=OFF` and `CAREWEAVE_BUILD_SQLITE=OFF` exist for special builds.

## 3. Where to change what

| You want to change | Touch |
| --- | --- |
| A module's behaviour | `modules/<module>/services/`, then its `tests/test_module.py` |
| A module's declared capability | `modules/<module>/spec.json` (and its `seed.py` if the capability needs data) |
| A module's page | `modules/<module>/ui/templates/`, `ui/static/` |
| The encoder or block layout | `core/src/embedding/`, `core/include/careweave/embedding/` |
| A new synonym for the lexicon | one line in `kConcepts` in `core/src/embedding/text.cpp` |
| Scoring weights or the margin | `core/src/mapper/`, and update `documents/04_MAPPING_AND_ADAPTERS.md` |
| Compatibility rules | `core/src/compat/`, and the checks table in the same document |
| Adapter transforms or transports | `core/src/adapter/` |
| Gateway behaviour or endpoints | `core/src/gateway/gateway.cpp` (library) and `server.cpp` (routing only) |
| Bundle contents | `core/src/bundle/bundler.cpp` |
| Dashboard panels | `dashboard/app.js`, `dashboard/index.html` |
| The experiment corpus | `experiments/specs/`, checked by `test_corpus` |
| An orchestration step | the matching script under `scripts/` |

The rule that keeps changes safe: logic lives in the core library or in a module service; the
CLI, the gateway server, the dashboard and the scripts are thin shells over it. If a change
needs business logic in two places, the library is missing a method.

## 4. Adding a capability to a module

1. Edit `modules/<module>/spec.json`: id, name, type, inputs, outputs, preconditions, effects,
   mechanism, quality, reliability, availability, resources, roles. The schema is
   `specs/capability.schema.json`; `core/build/careweave_cli validate modules/<module>/spec.json`
   checks it immediately.
2. Implement the route in `modules/<module>/app.py` and the logic in `services/`.
3. Seed any data it needs in `seed.py` (idempotently).
4. Add a test to `tests/test_module.py`; run `sh scripts/run_unit_tests.sh`.
5. Restart the system: the gateway discovers the new capability on `POST /api/discover` or at
   the next start.

A capability with no endpoint (a GUI screen) is legal: resolution can rank it, and the gateway
reports it as skipped rather than trying it.

## 5. Adding a module

1. Create `modules/<name>/` with `spec.json`, `app.py`, `db.py`, `seed.py`, `run.py`,
   `services/`, `ui/`, `tests/`, `requirements.txt` and a README. Copy the closest existing
   module; the shape is identical across all seven.
2. Add its port to the fixed range and its target to `defaultTargets()` in
   `core/src/gateway/gateway.cpp` (the single place that lists the shipped modules).
3. Start it from `scripts/start_all.sh` and stop it from `scripts/stop_all.sh`.
4. Add a line to the module table in `documents/01_ARCHITECTURE.md` and the API table in
   `documents/07_API_REFERENCE.md`.
5. `sh scripts/verify_all.sh`.

## 6. Adding an experiment

1. Add the source under `experiments/src/` and register it in `experiments/CMakeLists.txt`.
2. Write JSON, CSV and Markdown into `experiments/out/` with a stable name; keep timestamps out
   of the output so runs stay comparable.
3. Assert every claim inside the experiment; a violated claim must fail the run.
4. Do not reference the planner: gate G14 fails the acceptance run if an experiment source
   mentions it or an experiment binary carries a planner symbol.
5. Quote the frozen numbers in `documents/08_EXPERIMENTS.md`.

## 7. Conventions

- Zero warnings: the build fails on any warning line. Third-party code is included as system
  headers and never edited.
- No unfinished markers anywhere: source, sheets, scripts and documents are complete or they do
  not ship. The acceptance run scans for them.
- Deterministic outputs: stable ids derived from content, sorted iteration, no timestamps in
  generated result files, byte identical repeat runs (the determinism suite enforces this).
- Repository relative paths only. Scripts resolve their own location; commands in documents run
  from the repository root.
- The gateway audit trail is the record of truth for executed calls; do not add logging that
  duplicates it.
- Tests are never weakened to make a change pass. A behaviour change updates the test with the
  new expected value and a note in the build log.

## 8. Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `start_all.sh` reports a module not running | the port is held by a previous run: `sh scripts/stop_all.sh`, then start again |
| A module answers "unknown test code" or empty lists | its database predates seeding: restart it (`run.py` seeds idempotently), or run its `seed.py` |
| The workflow refuses to start a visit | one active encounter already exists (the EHR allows one): `run_integrated_workflow.sh` closes stale ones; otherwise close it through `/api/close_encounter` |
| A call falls back to another module | read the outcome trace and the audit rows: a skip (no endpoint or open circuit) or a failure followed by fallback is recorded per attempt |
| The gateway answers 502 on a call | the module itself failed after resolution; the outcome carries its reason |
| The dashboard shows stale module states | press rediscover (`POST /api/discover`) |
| Coverage drops below the reported range | run `sh scripts/run_unit_tests.sh` and read the per module table; the report quotes 84 to 89 percent |
