# Outpatient EHR module

Standalone hospital module of the CareWeave system. Python and Flask only: the module, its user
interface, its tests and its SQLite database are entirely Python, exactly as the assignment
requires for the Flask part of the system.

## Run

```
python3 run.py
```

Install the dependencies first when the interpreter does not already provide them:

```
python3 -m pip install -r requirements.txt
```

The module listens on `http://127.0.0.1:5003` and stores its data in `data/opd_ehr.db`
(SQLite, WAL mode). `CAREWEAVE_DB` and `CAREWEAVE_PORT` override the database file and the port.

The module installs its demonstration data at startup; `python3 seed.py` reruns the same
idempotent installation. No dependency of this module reaches the
internet at run time: the pages use only local CSS and JavaScript and the module makes no
outbound calls.

## Capability endpoints

| Capability | Method and path | Purpose |
| --- | --- | --- |
| EHR-StartEncounter | POST /api/start_encounter | Start an encounter (one active encounter at a time) |
| EHR-RecordVitals | POST /api/record_vitals | Record temperature, heart rate, optional systolic |
| EHR-IssuePrescription | POST /api/issue_prescription | Issue a prescription for the active encounter |
| EHR-CloseEncounter | POST /api/close_encounter | Close the active encounter with a summary |
| EHR-Form | POST /ui/encounters/new | GUI start form (same code path as EHR-StartEncounter) |

Every API call accepts a JSON object of the inputs named in `spec.json` and answers with

```json
{"status": "ok", "capability": "EHR-StartEncounter", "outputs": {...}, "effects": [...],
 "state": {...}, "trace": ["EHR-StartEncounter executed"]}
```

or, on rejection, `{"status": "error", "capability": "...", "error": "..."}` with status 400
(bad input or out of range clinical value), 404 (unknown encounter) or 409 (the encounter is
closed, or another encounter is still active). Read-only endpoints: `GET /health`, `GET /spec`,
`GET /state`.

## Screens

| Page | Path | Fields and stable element ids |
| --- | --- | --- |
| Home | /ui/ | Summary counts, capability table, `id="module_title"` |
| Encounters | /ui/encounters | Search `id="search_input"`, table `id="encounter_table"` |
| Start encounter | /ui/encounters/new | `id="encounter_form"` with `id="patient_mrn_input"`, `id="clinician_input"`, `id="visit_type_select"`, submit `id="submit_button"`, result `id="result_output"` |
| Encounter detail | /ui/encounters/<encounter_id> | Vitals form `id="vitals_form"`, prescription form `id="prescription_form"`, close form `id="close_form"`, vitals and prescription tables, result `id="result_output"` |
| Capabilities | /ui/capabilities | Formal tuple of every capability from `spec.json` |

Sample values: MRN `MRN-1001`, clinician `Dr Rivera`, visit type `CONSULTATION`, temperature
`37.2`, heart rate `72`, systolic `118`, drug `Amoxicillin`, dose `500` mg. Temperature must lie
between 25 and 45 degrees Celsius, heart rate between 20 and 300, systolic between 60 and 260,
and the dose between 0.1 and 5000 mg; values outside those ranges are rejected with status 400.

## Tests

```
python3 -m pytest tests -q --cov=. --cov-report=term
```

The suite creates a temporary database per test and exercises every capability, the clinical
range checks, every rejection path, the UI pages with their stable ids and the offline asset
check.
