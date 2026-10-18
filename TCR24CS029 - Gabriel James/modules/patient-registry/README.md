# Patient Registry module

Standalone hospital module of the CareWeave system. Python and Flask only: the module, its user
interface, its tests and its SQLite database are entirely Python, exactly as the assignment
requires for the Flask part of the system.

This module is the canonical registry of the hospital: patients are registered under a unique
medical record number, admitted to a ward, discharged again, their allergies flagged, and the
records looked up by identifier or MRN. The registry also answers the abstract requirement
`register_patient` with its `register_patient` capability, so it appears in every mapping and
compatibility experiment next to the legacy vocabulary module.

## Run

```
python3 run.py
```

Install the dependencies first when the interpreter does not already provide them:

```
python3 -m pip install -r requirements.txt
```

The module listens on `http://127.0.0.1:5001` and stores its data in `data/patient_registry.db`
(SQLite, WAL mode). `CAREWEAVE_DB` and `CAREWEAVE_PORT` override the database file and the port.

The module installs its demonstration data at startup; `python3 seed.py` reruns the same
idempotent installation. No dependency of this module reaches the internet at run time: the
pages use only local CSS and JavaScript and the module makes no outbound calls.

## Capability endpoints

| Capability | Id | Method and path | Purpose |
| --- | --- | --- | --- |
| register_patient | PR-Register | POST /api/register_patient | Register a patient under a unique MRN |
| admit_patient | PR-Admit | POST /api/admit_patient | Admit a registered patient to a ward |
| discharge_patient | PR-Discharge | POST /api/discharge_patient | Discharge an active admission and free the bed |
| flag_allergy | PR-FlagAllergy | POST /api/flag_allergy | Record one allergy with a severity grade |
| lookup_patient | PR-Lookup | POST /api/lookup_patient | Read a patient by patient id or MRN |
| register_patient_form | PR-Form | POST /ui/patients/new | GUI registration form |

Every API call accepts a JSON object of the inputs named in `spec.json` and answers with

```json
{"status": "ok", "capability": "PR-Register", "outputs": {...}, "effects": [...],
 "state": {...}, "trace": ["PR-Register executed"]}
```

or, on rejection, `{"status": "error", "capability": "...", "error": "..."}` with status 400
(missing input), 404 (unknown patient) or 409 (duplicate MRN, admitting an already admitted
patient, discharge without an active admission). Read-only endpoints: `GET /health`,
`GET /spec`, `GET /state`.

## Screens

| Page | Path | Fields and stable element ids |
| --- | --- | --- |
| Home | /ui/ | Title `id="module_title"`, counts `id="count_patients"`, `id="count_admissions"`, `id="count_allergies"`, links `id="register_link"`, `id="patients_link"`, table `id="capability_table"` |
| Patients | /ui/patients | Search `id="search_input"` with `id="search_button"`, table `id="patient_table"`, rows `id="patient_row_<patient_id>"`, empty notice `id="empty_row"` |
| New patient | /ui/patients/new | Form `id="patient_form"` with `id="mrn_input"`, `id="full_name_input"`, `id="date_of_birth_input"`, submit `id="submit_button"`, result `id="result_output"` |
| Patient detail | /ui/patients/<patient_id> | Admit form `id="admit_form"` (`id="ward_input"`, `id="stay_input"`, `id="admit_button"`), allergy form `id="allergy_form"` (`id="allergen_input"`, `id="severity_select"`, `id="flag_allergy_button"`), discharge form `id="discharge_form"` (`id="admission_select"`, `id="discharge_button"`), tables `id="admission_table"`, `id="allergy_table"`, result `id="result_output"` |
| Capabilities | /ui/capabilities | Formal tuple of every capability from `spec.json`, one article `id="capability_<capability id>"` each |

Sample values: MRN `MRN-1001`, patient name `Ada Lovelace`, registration key format
`PAT-XXXXXXXX`. The demonstration data registers Ada Lovelace, Grace Hopper and Alan Turing,
admits Ada Lovelace to `Ward A` and flags a `SEVERE` Penicillin allergy for Grace Hopper. A
repeated MRN is rejected with status 409.

## Tests

```
python3 -m pytest tests -q --cov=. --cov-report=term
```

The suite creates a temporary database per test and exercises every capability, the admission
and discharge rules, the allergy records, the lookup paths, the UI forms with their stable ids
and the offline asset check.
