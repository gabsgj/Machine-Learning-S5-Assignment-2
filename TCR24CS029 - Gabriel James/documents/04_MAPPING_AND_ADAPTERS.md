# Mapping and adapters

Two questions stand between a requirement and a running call. Mapping: which registry
capability implements the requirement? Adaptation: how does a call to that capability carry the
requirement's vocabulary? This document answers both, describes the live call path in the
gateway, and records the evidence.

## 1. Scoring

A requirement sheet declares exactly one capability. Every registry capability is scored
against it in three views, combined with the weights documented in the experiment sweep:

| View | What it compares | Weight |
| --- | --- | --- |
| Name | capability names, ids and descriptions | 0.35 |
| Fields | inputs and outputs, name and type | 0.35 |
| Conditions | preconditions and effects | 0.30 |

The total is a weighted mean in [0,1]. Two refinements:

- Kind tie break: when the top candidates are inside the ambiguity margin, the delivery kind
  (API, DATABASE, GUI, COMPOSITE, FILE, ...) singles out a unique candidate when exactly one of
  them matches the requirement's own kind. A GUI form that shares a name with its API
  capability does not silently win.
- Ambiguity margin (default 0.05): every candidate within the margin below the best score is
  marked ambiguous in the ranking instead of being hidden. Resolution still happens, but the
  near tie is visible in the CLI output, the dashboard and the audit trail, and the workflow
  compatibility engine can weigh it.

Live example, the alias requirement `register_pat` resolved against the 36 registry
capabilities of the two registries:

```
patient-registry-alt  PA-Register  Pat_reg              0.8346   (preferred, promoted)
patient-registry-alt  PA-Form      Pat_reg_form         0.7971   inside the 0.05 margin
patient-registry      PR-Register  register_patient     0.7928   inside the 0.05 margin
```

Three candidates sit inside the margin, so the ranking is genuinely ambiguous, and the two
capabilities are the same function in two vocabularies. The default resolution picks the best
ranked callable candidate; a preferred module list rotates candidates inside the margin when
the preferred module has a callable candidate there (`preferred_modules` in a workflow step, or
`--preferred` on the CLI).

## 2. Adapter synthesis

An adapter is data, and it round trips through JSON. `AdapterSynthesizer::synthesize` builds:

- identity: adapter id, requirement id and name, target module, target capability id and name;
- transport: kind, method, base address, endpoint (or table, page, file operation, depending on
  the target kind), and the timeout;
- input map: one row per requirement input, with the provider field it binds to, the transform,
  and whether the requirement marks it optional;
- output map: one row per provider output the requirement consumes, with the rename back;
- confidence: the match total, and a short explanation list for the report.

Field binding matches by name first, then by type-compatible renaming using the text features,
and reports unmatched required inputs as errors instead of guessing. Transforms are a closed
registry with hard type rules:

| Provider field type | Transform chosen |
| --- | --- |
| same normalized type | `identity` |
| boolean target | `to_bool` |
| integer target | `to_int` |
| real target | `to_real` |
| string or enum target | `to_string` |
| list on either side | rejected (no silent payload reshaping) |

The runtime also carries `lowercase`, `uppercase` and `trim` for text cleanup declared directly
in a sheet. Unknown transform names are rejected at synthesis and at parse time, so a malformed
adapter fails loudly.

Transports: HTTP and form (live modules), SQLite (a module's own database for DATABASE
capabilities, such as the alternate registry's direct row interface), file (read and write
operations with an explicit file operation), computation (pure computation capabilities) and
local (in-process capabilities used by tests and the composer).

## 3. The live call path

For one requirement call the gateway runs:

1. Resolution as described above, producing a ranked list of callable candidates.
2. The first candidate is tried. A module is tried at most once per requirement call: a second
   candidate from the same module is skipped, so fallback explores other modules, not retries
   of the same one. A candidate without an operational endpoint (a GUI screen, for example) is
   reported as skipped and does not consume its module's single try.
3. Each candidate call is attempted up to `maxAttempts` (2) with a 50 ms delay; the request
   timeout is 2500 ms.
4. When a module fails `circuitThreshold` (3) consecutive calls its circuit opens for
   `circuitCooldownMs` (10000 ms) and its candidates are skipped with an explanation.
5. If everything fails, the outcome reports the best ranked candidate's failure (its reason is
   the most informative) and the attempt trace of the remaining candidates.

Every attempt, skip, resolution and workflow step lands in the SQLite audit trail with kind,
operation, module, capability, success, status, attempts, fallback flag, latency and message,
which is what the dashboard's audit panel renders.

## 4. The alias resolution story

The hospital alias dataset is the hard case by construction: registration exists twice, once
as the canonical API (`register_patient`, fields `mrn`, `full_name`) and once in the legacy
vocabulary (`Pat_reg`, fields `pat_no`, `pat_name`), plus a GUI form and a direct row write in
the same module. The requirement `specs/app/requirements/register_pat.yaml` uses the legacy
vocabulary, so the honest answer is the alternate module, with an adapter that renames
`pat_no` to `mrn` and `pat_name` to `full_name`.

Verified live: the workflow `specs/workflows/visit_legacy.json` registers through the alternate
module (`patient-registry-alt` answered the legacy registration), verifies the patient through
the alternate module's own verify capability (which only succeeds if the registration really
landed in its database), then ticks the appointment queue, invoices and pays through the other
modules. All database checks pass.

A real bug was found by this path and fixed: preferred module promotion originally promoted any
preferred candidate inside the ambiguity margin, and the legacy module's promotion promoted its
GUI form, which has no endpoint. The call then consumed the module's single try on the form,
fell through to the canonical module and answered the legacy requirement from the wrong
vocabulary, which the verify step correctly rejected. The fix restricts promotion to callable
candidates and reports endpoint-less candidates as skipped, and the regression test
`live_calls_promote_and_skip_sheets_without_endpoints` was verified to fail against the old
behavior (10 failures) and to pass with the fix.

## 5. Workflows

A workflow definition is a list of steps. A step names either a `requirement` sheet (mapped,
like a single call) or a `module` plus a `capability` (direct), with `inputs`, `bind` (mapping
earlier step outputs into later inputs), optional `preferred_modules` and optional
`allow_modules` (a hard filter: a mapped step resolves only inside the list, and a direct step
that binds a module outside it fails before any call). Between adjacent
steps the compatibility engine renders a verdict: `first step`, `compatible`, `uncertain` or
`incompatible`. Only INCOMPATIBLE stops the run; uncertain is reported and continues. Two
workflows ship:

| Workflow | Steps | Shape |
| --- | --- | --- |
| `specs/workflows/visit.json` | 7 | register, admit, encounter, vitals, close, invoice, pay |
| `specs/workflows/visit_legacy.json` | 5 | register (legacy vocabulary), verify, queue ticket, invoice, pay |

`scripts/run_integrated_workflow.sh` runs both against the live system and checks the module
databases directly with sqlite3 (patient rows, admitted flags, active admission, closed
encounter, recorded vitals, paid invoice, legacy verified flag), and closes stale active
encounters before a fresh visit because the EHR module allows one active encounter at a time.

## 6. Client requirements and chosen pools

A client joins the system with three choices: the requirement it states, the pool of sheets its
requirement may be satisfied from, and the way the call is executed. This section is the
recipe; every command below was run and every number is observed output.

Stating the requirement. A client requirement is a sheet in the same formal language, declaring
exactly one capability in the client's own vocabulary. The commented template is
`specs/app/requirements/register_pat.yaml`; the worked example
`specs/clients/example-clinic/requirements/create_followup_ticket.yaml` states the same kind of
need in example clinic words (`patient_ref`, `visit_reason`, `urgency`, `ticket_ref`) and
validates as `ok (1 capabilities, 3 state variables)`. Client sheets live wherever the client
keeps them; `specs/clients/<client>/requirements/` is a convention, not a rule, because every
command takes the file path. `careweave_cli validate <file>` checks a sheet against the schema
before anything else happens.

Choosing the pool, offline. The pool is the list of sheets the command is given, nothing else:

```
careweave_cli mapping <requirement> --pool <sheet> [--pool <sheet>...]
careweave_cli adapters <requirement> --pool <sheet>... [--module <capability id>]
```

A pool entry can be a module `spec.json`, an application sheet, a proposal sheet, or any
mixture. Three runs of the example requirement show the pool working:

| Pool | Result |
| --- | --- |
| `specs/app/hospital_clinic_visit.yaml` (14 capabilities) | SELECTED `CV-CreateTicket` 0.7508, margin 0.3384 |
| `modules/appointment-queue/spec.json` (5 capabilities) | SELECTED `AQ-CreateTicket` 0.8073, margin 0.1467 |
| `modules/patient-registry-alt/spec.json` plus `modules/pos-billing/spec.json` (queue excluded) | REJECTED: best 0.3414 below the threshold 0.55, exit status 1 |

So the chosen subset is a hard boundary for decisions: a requirement the pool cannot serve is
refused with the score it would take, before any call is made. `--min-score`, `--margin` and
`--top` tune the offline view, and the same ranking is what the gateway and the dashboard use.

Executing through a gateway. `careweave_cli run <requirement> --inputs k=v --preferred
<module,...> --gateway <url>` is the thin client; `--resolve-only` prints candidates without
calling. The same two operations over HTTP take repository relative sheet paths:

```
POST /api/resolve  {"requirement": "...", "preferred_modules": ["..."]}
POST /api/call     {"requirement": "...", "inputs": {...}, "preferred_modules": ["..."]}
```

`preferred_modules` is a tie break, not a filter. A preferred module is promoted to the front
only when its candidate is callable and its score is inside the ambiguity margin of the best;
the ambiguity flags stay reported. Observed: `register_pat` resolves `patient-registry-alt`
first (0.8346) with the top three marked ambiguous; adding `"preferred_modules":
["patient-registry"]` puts the canonical `PR-Register` (0.7928) first while the three
candidates stay marked ambiguous. A live call of the example requirement executed through the
synthesized adapter, with the trace showing the renames (`patient_ref -> patient_mrn`,
`visit_reason -> reason`, `urgency -> priority`) and the outputs mapped back (`ticket_id ->
ticket_ref`, `ticket_no -> ticket_number`).

A hard filter per call. `allow_modules` in a resolve or call body (and `--allow-modules` on
`careweave_cli run`) is the second, stricter boundary: only the listed modules are ranked,
preferred modules outside the list are never promoted, and fallbacks cannot leave the list.
Because it travels with the request, one gateway can serve restricted and unrestricted clients
at once. Observed: `register_pat` ranks 36 candidates with `patient-registry-alt` first
(0.8346, top three ambiguous); adding `"allow_modules": ["patient-registry"]` leaves 6
candidates, puts `PR-Register` first (0.7928, margin 0.1721, no ambiguity rows) and the
alternate registry is absent. A live call with `--allow-modules patient-registry` registered a
fresh MRN through the canonical registry (`outputs {"pat_reg":"ALLOW-3"}`); the same call
restricted to `legacy-lab-service` was executed against the lab API and answered 502 with the
module's own reason (`unknown test code "ALLOW-1"`), because the filter never lets the call
escape to an excluded module.

Hard pinning. `POST /api/hospital/<capability name>` (body is the inputs object) executes one
registry capability directly, and `?module=<module id>` pins the module; outside the registry
the answer is 404 with the reason.

A closed pool for one client. For a client that must not reach every module, run only the
modules it may use and give the client its own gateway whose modules directory contains only
those module folders:

```
careweave_gateway --root . --port 5200 --modules <client-modules-dir>
```

The dev tree fills such a directory with symlinks to the shared module folders. Observed with a
two module directory: discovery reports `discovered 2 of 7 modules` (the other five
unavailable and never ranked); the pinned call to the excluded canonical registry answers 404;
a requirement whose capability lives in an excluded module fails 502 with the full attempt
story of the pool's best candidates and their errors, instead of silently escaping to a module
outside the pool; and `register_pat` succeeds on the alternate registry inside the pool. The
client gateway keeps its own audit trail and its own port, so several clients can run side by
side against the same module processes, or against their own copies.

Workflows as client processes. When the client's need is a small fixed process rather than a
single call, a workflow file names the steps: a step pins `module` plus `capability` directly,
or resolves a `requirement` with optional `preferred_modules` and `allow_modules`, and `bind`
wires earlier outputs into later inputs (`"patient_id": "register.patient_id"`).
`specs/workflows/visit.json` is the seven step example and `specs/workflows/visit_legacy.json`
the five step alias variant. A workflow a client may not fully reach also travels in a selected
bundle: the bundler follows the module ids its steps bind and adds those modules (see the
bundling guide).

## 7. Evidence

| Claim | Evidence |
| --- | --- |
| Scoring separates equivalent, distinct and mechanism-different name pairs | experiment 1: equivalent mean 0.7698 (min 0.6369), distinct mean 0.1890 (max 0.6699), mechanism-only pairs max 0.0000; name pair AUC 0.9846 |
| Composability is separated from similarity | experiment 1: compatibility discrimination AUC 1.0 for the vector score against 0.7778 for raw cosine and 0.7778 for functional similarity |
| Same function, different delivery kind moves apart | experiment 3: within-function functional mean 0.9582 and implementation mean 0.8330; cross-function functional 0.6526 and implementation 0.8485 |
| Unrelated capabilities are refused | experiment 4: pool of 77, 24 decoys; mean reciprocal rank 1.0; strongest decoy 0.4962 against the weakest intended 0.8346 |
| The margin is meaningful and small | experiment 5: 21 weight settings swept; the smallest positive margin observed is 0.0035; default weights produce margin 0.0492 with `AR-PatReg` selected and the kind tie break active |
| The mapper, synthesizer and gateway agree with the frozen corpus | `core/tests/test_mapper.cpp`, `core/tests/test_adapter.cpp`, `core/tests/test_gateway.cpp` (14 cases, 187 checks) |
| The live alias path is real | `scripts/run_integrated_workflow.sh` database checks, dashboard mapping studio, `logs/verify_all_*.log` |
