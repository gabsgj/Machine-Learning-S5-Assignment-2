# Legacy Laboratory Service module

Standalone hospital module of the CareWeave system. Python and Flask only: the module, its user
interface, its tests and its SQLite database are entirely Python, exactly as the assignment
requires for the Flask part of the system.

The input naming of this module keeps the legacy laboratory vocabulary: `patient_mrn`,
`test_code`, `urgency_level`. That makes this module the vocabulary counterpart of
`patient-registry-alt`, whose naming is `pat_reg`, `pat_no`, `pat_name`; the gateway mapper has
to reconcile the two.

## Run

```
python3 run.py
```

Install the dependencies first when the interpreter does not already provide them:

```
python3 -m pip install -r requirements.txt
```

The module listens on `http://127.0.0.1:5006` and stores its data in `data/legacy_lab.db`
(SQLite, WAL mode). `CAREWEAVE_DB` and `CAREWEAVE_PORT` override the database file and the port.

The module installs the test catalogue and two demonstration orders at startup;
`python3 seed.py` reruns the same idempotent installation. No
dependency of this module reaches the internet at run time: the pages use only local CSS and
JavaScript and the module makes no outbound calls.

## Capability endpoints

| Capability | Method and path | Purpose |
| --- | --- | --- |
| LAB-OrderTest | POST /api/order_test | Order a test (patient_mrn, test_code, urgency_level) |
| LAB-ReceiveSample | POST /api/receive_sample | Accept the physical sample of an order |
| LAB-EnterResult | POST /api/enter_result | Enter the measured result |
| LAB-GetReport | POST /api/get_report | Read the report line and order status |
| LAB-Form | POST /ui/orders/new | GUI order form (same code path as LAB-OrderTest) |

Every API call accepts a JSON object of the inputs named in `spec.json` and answers with

```json
{"status": "ok", "capability": "LAB-OrderTest", "outputs": {...}, "effects": [...],
 "state": {...}, "trace": ["LAB-OrderTest executed"]}
```

or, on rejection, `{"status": "error", "capability": "...", "error": "..."}` with status 400
(bad input or invalid urgency level), 404 (unknown order or test code) or 409 (a workflow step
out of order). Read-only endpoints: `GET /health`, `GET /spec`, `GET /state`.

The workflow of an order is `ordered` -> `received` -> `resulted`. The test catalogue is
reference data: entries carry the test code, the name, the unit and the reference range.

## Screens

| Page | Path | Fields and stable element ids |
| --- | --- | --- |
| Home | /ui/ | Summary counts, capability table, `id="module_title"` |
| Lab orders | /ui/orders | Search `id="search_input"`, table `id="order_table"` |
| New order | /ui/orders/new | `id="order_form"` with `id="patient_mrn_input"`, `id="test_code_select"`, `id="urgency_select"`, submit `id="submit_button"`, result `id="result_output"` |
| Order detail | /ui/orders/<lab_order_id> | Receive form `id="receive_form"` while ordered, result form `id="result_form"` while received, report `id="report_output"` once resulted |
| Capabilities | /ui/capabilities | Formal tuple of every capability from `spec.json` |

Sample values: MRN `MRN-1001`, test code `GLU` (fasting glucose, mmol/L), urgency `URGENT`,
result `5.4`. Entering a result before the sample is received is rejected with status 409 and
the message "no received sample yet".

## Tests

```
python3 -m pytest tests -q --cov=. --cov-report=term
```

The suite creates a temporary database per test, installs the catalogue, and exercises every
capability, the workflow order rules, the UI pages with their stable ids and the offline asset
check.
