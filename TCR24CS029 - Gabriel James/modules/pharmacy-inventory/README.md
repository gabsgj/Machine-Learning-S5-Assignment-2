# Pharmacy Inventory module

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

The module listens on `http://127.0.0.1:5004` and stores its data in
`data/pharmacy_inventory.db` (SQLite, WAL mode). `CAREWEAVE_DB` and `CAREWEAVE_PORT` override the
database file and the port.

The module installs its demonstration data at startup; `python3 seed.py` reruns the same
idempotent installation. No dependency of this module reaches the
internet at run time: the pages use only local CSS and JavaScript and the module makes no
outbound calls.

## Capability endpoints

| Capability | Method and path | Purpose |
| --- | --- | --- |
| PH-RegisterDrug | POST /api/register_drug | Add a catalogue entry with price and optional initial quantity |
| PH-CheckStock | POST /api/check_stock | Read level, price and availability of one drug |
| PH-DispenseDrug | POST /api/dispense_drug | Dispense units, rejecting shortages with status 409 |
| PH-Replenish | POST /api/replenish_stock | Add units to one drug |
| PH-Form | POST /ui/dispense | GUI dispensing form (same code path as PH-DispenseDrug) |

Every API call accepts a JSON object of the inputs named in `spec.json` and answers with

```json
{"status": "ok", "capability": "PH-DispenseDrug", "outputs": {...}, "effects": [...],
 "state": {...}, "trace": ["PH-DispenseDrug executed"]}
```

or, on rejection, `{"status": "error", "capability": "...", "error": "..."}` with status 400
(bad input or non positive quantity), 404 (unknown SKU) or 409 (duplicate SKU, insufficient
stock). Read-only endpoints: `GET /health`, `GET /spec`, `GET /state`.

## Screens

| Page | Path | Fields and stable element ids |
| --- | --- | --- |
| Home | /ui/ | Summary counts, capability table, `id="module_title"` |
| Stock | /ui/drugs | Search `id="search_input"`, register form `id="register_drug_form"` (`id="sku_input"`, `id="name_input"`, `id="unit_price_input"`, `id="initial_quantity_input"`), table `id="drug_table"`, dispense history `id="dispense_table"` |
| Dispense | /ui/dispense | `id="dispense_form"` with `id="sku_select"`, `id="quantity_input"`, `id="patient_mrn_input"`, submit `id="submit_button"`, result `id="result_output"` |
| Capabilities | /ui/capabilities | Formal tuple of every capability from `spec.json` |

Sample values: SKU `AMOX-500`, name `Amoxicillin 500 mg`, price `0.35`, quantity `10`, patient
MRN `MRN-1001`. Dispensing more units than are on hand is rejected with status 409 and the
message "insufficient stock".

## Tests

```
python3 -m pytest tests -q --cov=. --cov-report=term
```

The suite creates a temporary database per test and exercises every capability, the shortage and
duplicate paths, the UI forms with their stable ids and the offline asset check.
