# Appointment Queue module

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

The module listens on `http://127.0.0.1:5002` and stores its data in
`data/appointment_queue.db` (SQLite, WAL mode). `CAREWEAVE_DB` and `CAREWEAVE_PORT` override the
database file and the port.

The module installs its demonstration data at startup; `python3 seed.py` reruns the same
idempotent installation. No dependency of this module reaches the internet
at run time: the pages use only local CSS and JavaScript and the module makes no outbound calls.

## Capability endpoints

| Capability | Method and path | Purpose |
| --- | --- | --- |
| AQ-CreateTicket | POST /api/create_ticket | Create a queue ticket (priority default NORMAL) |
| AQ-CallNext | POST /api/call_next_ticket | Call the highest priority waiting ticket |
| AQ-UpdateTriage | POST /api/update_triage | Change the priority of a waiting ticket |
| AQ-Cancel | POST /api/cancel_ticket | Cancel a waiting ticket |
| AQ-Form | POST /ui/tickets/new | GUI creation form (same code path as AQ-CreateTicket) |

Every API call accepts a JSON object of the inputs named in `spec.json` and answers with

```json
{"status": "ok", "capability": "AQ-CreateTicket", "outputs": {...}, "effects": [...],
 "state": {...}, "trace": ["AQ-CreateTicket executed"]}
```

or, on rejection, `{"status": "error", "capability": "...", "error": "..."}` with status 400
(bad input), 404 (unknown ticket) or 409 (the ticket is no longer waiting, or the queue is
empty). Read-only endpoints: `GET /health`, `GET /spec`, `GET /state`.

## Screens

| Page | Path | Fields and stable element ids |
| --- | --- | --- |
| Home | /ui/ | Summary counts, capability table, `id="module_title"` |
| Queue | /ui/tickets | Search `id="search_input"`, call next form `id="call_next_form"` with `id="desk_input"` and `id="call_next_button"`, ticket table `id="ticket_table"` |
| Create ticket | /ui/tickets/new | `id="ticket_form"` with `id="patient_mrn_input"`, `id="reason_input"`, `id="priority_select"`, submit `id="submit_button"`, result `id="result_output"` |
| Ticket detail | /ui/tickets/<ticket_id> | Triage form `id="triage_form"` (priority `id="triage_priority_select"`, notes `id="notes_input"`), cancel form `id="cancel_form"`, result `id="result_output"` |
| Capabilities | /ui/capabilities | Formal tuple of every capability from `spec.json` |

Sample values: MRN `MRN-1001`, reason `Chest pain`, priority `EMERGENCY`. Calling next with an
empty queue is rejected with status 409 and the message "the queue is empty".

## Tests

```
python3 -m pytest tests -q --cov=. --cov-report=term
```

The suite creates a temporary database per test and exercises every capability, every rejection
path, the UI pages with their stable ids and the offline asset check.
