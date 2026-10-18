# UI walkthrough

This document describes every user interface in CareWeave Mini: the seven module UIs and the
gateway dashboard, the routes each one serves, and how they were verified. Everything is served
from local files: the pages load their own stylesheet and script, and no page reaches any host
beyond this machine.

## 1. Module user interfaces

Each of the seven modules serves the same shaped interface on its own port:

- A home page with the module's identity, health and row counts.
- A list page for the module's main entity.
- A detail page for one row of that entity.
- A create form that posts to the module's own API and flashes the outcome.
- An actions section for the module specific operations, rendered on the list or detail page.
- A capabilities page that lists every capability the module declares, with its id, name, type
  and endpoint, so the UI and the specification sheet can be compared side by side.
- A not found page for unknown routes.

The shared layout is `ui/templates/base.html` with `ui/static/style.css` and `ui/static/app.js`
in each module. All seven `run.py` entry points register the UI blueprint and seed their
databases at startup, so a freshly started system shows populated pages.

| Module | Port | List route | Detail route | Create route |
| --- | --- | --- | --- | --- |
| patient-registry | 5001 | `/ui/patients` | `/ui/patients/<patient_id>` | `/ui/patients/new` |
| appointment-queue | 5002 | `/ui/tickets` | `/ui/tickets/<ticket_id>` | `/ui/tickets/new` |
| opd-ehr | 5003 | `/ui/encounters` | `/ui/encounters/<encounter_id>` | `/ui/encounters/new` |
| pharmacy-inventory | 5004 | `/ui/drugs` | rows on the list page | `/ui/dispense` |
| pos-billing | 5005 | `/ui/invoices` | `/ui/invoices/<invoice_id>` | `/ui/invoices/new` |
| legacy-lab-service | 5006 | `/ui/orders` | `/ui/orders/<lab_order_id>` | `/ui/orders/new` |
| patient-registry-alt | 5007 | `/ui/patients` | `/ui/patients/<pat_reg>` | `/ui/pat_reg/new` |

Every module also serves `/ui/` (home) and `/ui/capabilities`. The payment action lives at
`/ui/payments/new` on pos-billing, and the alternate registry's create form uses its own
`pat_reg` vocabulary, which is exactly the vocabulary difference the gateway adapts between.

## 2. Gateway dashboard

The dashboard is a static site in `dashboard/` (`index.html`, `styles.css`, `app.js`) mounted by
the gateway at `/`. It is plain HTML, CSS and JavaScript; it uses no framework, no build step
and no external asset. Every panel calls the gateway management API with relative paths and
renders the JSON it returns.

| Panel | What it shows | Gateway endpoint |
| --- | --- | --- |
| Modules | Every discovered module with availability, health, capability count and spec source, and a rediscover button. | `GET /api/modules`, `POST /api/discover` |
| Registry | The full capability registry with a live filter over module, id, name and type. | `GET /api/registry` |
| Embedding | The partitioned vector of every capability in a sheet (block sizes and norms) and the view by view cosine between two capabilities. | `POST /api/embed`, `POST /api/embed/compare` |
| Mapping | The ranked candidates for a requirement sheet, with the ambiguity flag and a button that opens the adapter for a row. | `POST /api/resolve` |
| Requirement | Input fields derived from the requirement's own sheet, a preferred module choice, and the full call outcome with its attempt trace. | `GET /api/sheet`, `POST /api/call` |
| Adapter | The synthesized adapter for one requirement and one registry capability: input and output bindings, transforms, transport and confidence. | `POST /api/adapter` |
| Plan | The planner's step sequence for an application sheet, with the search statistics and the note that the planner is background machinery outside the Assignment 2 scope. | `POST /api/plan` |
| Bundle | Assembles the self contained bundle under a chosen directory and prints the result. Module and workflow checkboxes trim the bundle; the workflow closure additions are reported. | `POST /api/bundle` |
| Workflow | Runs one of the shipped workflows and shows every step with its compatibility verdict and call result. | `GET /api/sheets`, `POST /api/workflow` |
| Experiments | The frozen evaluation criteria and the five experiment result documents. | `GET /api/experiments` |
| Audit | The gateway's audit trail with kind, operation, module, status, latency and message. | `GET /api/audit` |

The endpoints behind the dashboard are thin shells over the same library methods the CLI uses
(`Gateway::adapterJson` wraps the same synthesizer the live call path runs, and `POST /api/bundle`
wraps the same `bundle::createBundle` the CLI's bundle command calls), so the two front ends
cannot drift apart.

## 3. Verification

Three layers of checks cover the interfaces:

1. Module unit tests: every module's `tests/test_module.py` drives the Flask test client over its
   UI routes (home, list, detail, create, capability page, 404), with 79 passing tests across the
   seven suites.
2. Acceptance script: `scripts/verify_all.sh` checks that the dashboard assets exist, that none
   of the HTML, CSS or JS files contains an external address, and then, while the system runs,
   drives the dashboard index and every dashboard endpoint over HTTP and requires a 200 with the
   expected content.
3. Headless browser pass: the list, detail, create, capability and dashboard pages were loaded in
   headless Chrome, which executes the page scripts, and the rendered DOM was checked. The
   dashboard's status line and module table appear only after its script has fetched and rendered
   live data, so the pass also proves the dashboard's data path.

The headless pass used one command per page, of this shape (on this machine `chrome` is the
Chrome executable):

```
chrome --headless --disable-gpu --no-first-run --user-data-dir="$TMPDIR/chrome_profile" \
  --virtual-time-budget=3000 --dump-dom "http://127.0.0.1:5100/" > logs/headless_page_dashboard.html
```

Observed results (dump files under `logs/`):

| Page | Rendered title | Rendered content check |
| --- | --- | --- |
| patient-registry `/ui/patients` | Patients | 11 table rows, patient records listed |
| appointment-queue `/ui/tickets` | Queue | 7 table rows |
| opd-ehr `/ui/encounters` | Encounters | 7 table rows |
| pharmacy-inventory `/ui/drugs` | Stock | 4 table rows |
| pos-billing `/ui/invoices` | Invoices | 12 table rows |
| legacy-lab-service `/ui/orders` | Lab orders | 4 table rows |
| patient-registry-alt `/ui/patients` | Patients | 8 table rows in the alternate vocabulary |
| patient-registry `/ui/patients/new` | Register patient | 1 form |
| patient-registry `/ui/capabilities` | Capabilities | capability table |
| appointment-queue `/ui/tickets/new` | New ticket | 1 form |
| pos-billing `/ui/payments/new` | Take payment | 1 form |
| patient-registry-alt `/ui/pat_reg/new` | New registration | 1 form |
| gateway `/` | CareWeave Mini dashboard | status line reads "7 of 7 modules healthy" after its scripts run, module table populated |

## 4. Starting the interfaces

```
sh scripts/start_all.sh
```

Then open `http://127.0.0.1:5100/` for the dashboard and `http://127.0.0.1:5001/` through
`http://127.0.0.1:5007/` for the module interfaces. `sh scripts/stop_all.sh` stops everything.
