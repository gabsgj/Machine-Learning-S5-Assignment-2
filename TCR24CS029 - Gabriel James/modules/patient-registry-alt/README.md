# Patient Registry (Alt) module

Standalone hospital module of the CareWeave system. Python and Flask only: the module, its user
interface, its tests and its SQLite database are entirely Python, exactly as the assignment
requires for the Flask part of the system.

This module speaks the legacy registration vocabulary `pat_reg`, `pat_no`, `pat_name`, and its
registration capability is named `Pat_reg` while the abstract requirement it answers is
`register_pat`. That vocabulary split is the subject of the mapping experiments: the embedding
mapper resolves `register_pat` to this module's `Pat_reg` capability, and the contract engine
then binds the request fields to the fields this module accepts.

The module also carries one DATABASE capability, `PA-RowWrite`, with no HTTP endpoint: the
adapter SQLite transport executes it directly against the module database file, writing single
rows into the `pat_rows` table.

## Run

```
python3 run.py
```

Install the dependencies first when the interpreter does not already provide them:

```
python3 -m pip install -r requirements.txt
```

The module listens on `http://127.0.0.1:5007` and stores its data in
`data/patient_registry_alt.db` (SQLite, WAL mode). `CAREWEAVE_DB` and `CAREWEAVE_PORT` override
the database file and the port.

The module installs its demonstration data at startup; `python3 seed.py` reruns the same
idempotent installation. No dependency of this module reaches the
internet at run time: the pages use only local CSS and JavaScript and the module makes no
outbound calls.

## Capability endpoints

| Capability | Id | Method and path | Purpose |
| --- | --- | --- | --- |
| Pat_reg | PA-Register | POST /api/pat_reg | Register a patient (pat_no, pat_name), assign a pat_reg |
| Pat_lookup | PA-Lookup | POST /api/pat_lookup | Read a registration by pat_reg |
| Pat_verify | PA-Verify | POST /api/pat_verify | Verify a registration once |
| Pat_row_write | PA-RowWrite | DATABASE insert into pat_rows | Executed by the adapter, not over HTTP |
| Pat_reg_form | PA-Form | POST /ui/pat_reg/new | GUI registration form |

Every API call accepts a JSON object of the inputs named in `spec.json` and answers with

```json
{"status": "ok", "capability": "PA-Register", "outputs": {...}, "effects": [...],
 "state": {...}, "trace": ["PA-Register executed"]}
```

or, on rejection, `{"status": "error", "capability": "...", "error": "..."}` with status 400
(missing input), 404 (unknown registration) or 409 (duplicate patient number, verification
repeated, verification before any registration). Read-only endpoints: `GET /health`,
`GET /spec`, `GET /state`.

## Screens

| Page | Path | Fields and stable element ids |
| --- | --- | --- |
| Home | /ui/ | Summary counts, capability table, `id="module_title"` |
| Patients | /ui/patients | Search `id="search_input"`, table `id="patient_table"` |
| New registration | /ui/pat_reg/new | `id="pat_reg_form"` with `id="pat_no_input"`, `id="pat_name_input"`, submit `id="submit_button"`, result `id="result_output"` |
| Registration detail | /ui/patients/<pat_reg> | Verify form `id="verify_form"` until verified, notice `id="verified_notice"` afterwards |
| Capabilities | /ui/capabilities | Formal tuple of every capability from `spec.json` |

Sample values: patient number `P-1001`, patient name `Ada Lovelace`, registration key format
`PAT-XXXXXXXX`. A repeated patient number is rejected with status 409.

## Tests

```
python3 -m pytest tests -q --cov=. --cov-report=term
```

The suite creates a temporary database per test and exercises every capability, the vocabulary
pins (`Pat_reg`, `pat_no`, `pat_name`), the database capability backing table, the UI forms
with their stable ids and the offline asset check.
