# Testing and verification

Nothing in this project is asserted without a run behind it. The verification stack has five
layers: the C++ suites, the module suites, the experiments, the end to end scripts and the
interface checks. `sh scripts/verify_all.sh` runs all of them and exits 0 only when every step
passes, capturing everything into a timestamped log under `logs/`.

## 1. The C++ suites

`cd core && ctest --test-dir build` runs 13 suites: 107 cases and 1909 checks, all against the
real shipped sheets.

| Suite | Cases | Checks | What it pins |
| --- | --- | --- | --- |
| test_adapter | 13 | 188 | synthesis, transforms, rejections, transports |
| test_bundle | 5 | 128 | manifest, layout, exclusions, script set, module selection and workflow closure |
| test_compat_conditions | 13 | 69 | typed condition semantics and entailment |
| test_compat_engine | 7 | 63 | verdicts, checks, contexts, windows |
| test_composer | 5 | 50 | composition algebra and composite behaviour |
| test_corpus | 7 | 354 | every shipped sheet parses and validates; dataset labels replay |
| test_determinism | 5 | 522 | every stage run twice produces identical bytes and numbers |
| test_embedding | 8 | 159 | block layout, views, signed effects, property checks |
| test_gateway | 14 | 187 | live HTTP discovery, retries, circuits, fallback, workflows, hard allow lists, audit, dashboard endpoints |
| test_mapper | 7 | 42 | scoring, weights, kind tie break, ambiguity margins |
| test_planner | 8 | 58 | forward and backward search (outside the grading scope) |
| test_types | 8 | 56 | value algebra, conditions, capability tuples |
| test_yaml_lite | 7 | 33 | the YAML subset parser |

The gateway suite runs every fake module as a real HTTP server on an ephemeral port that serves
its own `/spec`, so discovery, retries, circuit breaking with cooldown and half open recovery,
cross module fallback, workflow binding and the compatibility guard are exercised against real
sockets. Project sources compile under `-Wall -Wextra -Wpedantic -Wshadow -Wconversion
-Wsign-conversion`, third-party headers are included as system headers so their diagnostics
never enter the log, and `scripts/build.sh` fails the build when any warning line appears, so
the build log stays empty of warnings.

## 2. The module suites

Each module ships `tests/test_module.py`, run with coverage:

```
sh scripts/run_unit_tests.sh
```

Results from the last full run: seven suites, 79 tests passing, statement coverage between 84
and 89 percent per module. Every suite drives the Flask test client over the module's API routes
and its UI routes (home, list, detail, create, capability page, 404), asserts the domain
refusals (duplicate medical record number, single active encounter, empty stock, unknown
patient), and checks that seeding is idempotent.

## 3. The experiments

`sh scripts/run_experiments.sh` builds and runs the five experiments and the evaluation harness
against the shipped corpus. Every experiment asserts its own claims; a property that stops
holding fails the run. Outputs go to `experiments/out/` as JSON, CSV and Markdown. The frozen
numbers and what they mean are in `documents/08_EXPERIMENTS.md`.

## 4. The end to end scripts

| Script | What it proves |
| --- | --- |
| `run_integrated_workflow.sh` | both clinic workflows run against the live modules; the runner then checks the module databases directly with sqlite3 (patient rows, admitted flags, active admission, closed encounter, vitals, paid invoice, legacy verified flag) and every check passes |
| `start_all.sh` | seven modules and the gateway start and report healthy (with `/api/discover` retries during the health poll) |
| `stop_all.sh` | everything started is stopped by pid; a second run says "nothing to stop" |
| `verify_all.sh` | the full acceptance path: scans, build, C++ suites, module suites, experiments, workflows, management API checks, dashboard asset check |

`verify_all.sh` writes `logs/verify_all_<timestamp>.log`. On success it prints the last lines of
the log; on failure it prints the first failing step and its tail. Every step runs from the
script's own location, so it can be invoked from any working directory, and it is safe to run
twice in a row.

## 5. Interface verification

- The acceptance run drives the dashboard and every dashboard endpoint over HTTP and requires a
  200 with the expected content while the system is live (verified dashboard index, sheets,
  sheet detail, embedding, embedding compare, adapter preview, plan, experiments, audit).
- The dashboard asset check fails when an asset is missing and when any HTML, CSS or JS file
  contains an external address.
- A headless browser pass rendered the live pages (list, detail, create, capability and the
  dashboard) and checked the rendered DOM, including the dashboard's status line and module
  table, which appear only after its scripts fetched live data. The commands and observed
  results are in `documents/05_UI_WALKTHROUGH.md`.

## 6. Guards that keep the repository honest

- Purge scan: retired names, persona strings and version banners must not appear anywhere,
  except the two documented benign locations (the vendored SQLite amalgamation and the build
  log line that describes the gate itself). The scan pattern is assembled from fragments inside
  the script so the script itself stays clean.
- Placeholder scan: no unfinished markers in source, docs, sheets or scripts.
- Scope check (gate G14): no experiment source references the planner, and no experiment binary
  contains a planner symbol.
- Determinism: the pipeline is byte stable across runs; ids are derived from content, outputs
  are timestamp free, and the determinism suite replays every stage twice.
- No absolute home paths in deliverables or transcripts; commands are documented as
  `python3 ...` or repository relative.

## 7. A regression that was caught and pinned

The live alias workflow found a real bug: preferred module promotion inside the ambiguity
margin promoted the alternate registry's GUI form (a capability without an HTTP endpoint) over
its own live API, consumed the module's single try, and answered the legacy requirement from
the canonical module, which the verify step correctly rejected. The fix (promote only callable
candidates; report endpoint-less candidates as skipped without consuming the try) is pinned by
`live_calls_promote_and_skip_sheets_without_endpoints`, which was first verified to fail
against the old behavior (10 failures) and then to pass. The gateway suite grew from 11 to 12
cases with that fix; it stands at 14 cases and 187 checks today.

## 8. Reading a verify run

```
$ sh scripts/verify_all.sh
...
verify_all ok; full log: logs/verify_all_<timestamp>.log
```

A failure looks like this instead:

```
verify_all failed (status 1); last lines of logs/verify_all_<timestamp>.log:
<the failing step and its output>
```

Useful lines inside a green log: `purge scan clean`, `placeholder scan clean`, `scope check
clean`, `build ok`, `100% tests passed out of 13`, the seven pytest summaries, `experiments
ok`, the workflow and database checks, the verified endpoint list, and `dashboard assets
complete and free of external URLs`.
