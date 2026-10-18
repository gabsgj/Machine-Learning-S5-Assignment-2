"""Launches one module for real and captures a transcript of every endpoint call.

Usage (with the project virtual environment):

    .venv/bin/python scripts/module_transcripts.py patient-registry
    .venv/bin/python scripts/module_transcripts.py --all

For each module the script

1. starts `run.py` with CAREWEAVE_DB pointing into documents/evidence/modules/ so each run
   starts from a fresh database and the repository data directory stays untouched,
2. waits for /health to answer,
3. calls /health, /spec, /state, every declared UI page and the module transcript plan below
   (the plan calls each capability endpoint at least once, including one rejection where the
   module declares an error case),
4. writes documents/evidence/modules/<module>.transcript.txt with every request and response,
5. stops the server.

The transcript plans use "$name" placeholders resolved from outputs of earlier calls, so a
registration id created in one step is reused by the next; this keeps the evidence honest.
"""

import argparse
import json
import os
import platform
import signal
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES_DIR = os.path.join(ROOT, "modules")
EVIDENCE_DIR = os.path.join(ROOT, "documents", "evidence", "modules")

# Per module: the UI pages plus a sequence of capability calls. Each step is
# (description, method, path, body or None). Bodies may reference "$name" values produced by
# earlier steps (an output key, taken from the most recent successful response that carried it).
# "prepare" holds reference data statements executed against the fresh evidence database before
# the server starts (the laboratory test catalogue), and "detail_page" one UI page that needs a
# generated identifier.
TRANSCRIPT_PLANS = {
    "patient-registry": {
        "pages": ["/ui/", "/ui/patients", "/ui/patients/new", "/ui/capabilities"],
        "steps": [
            ("register a patient", "POST", "/api/register_patient",
             {"mrn": "MRN-2001", "full_name": "Ada Lovelace", "date_of_birth": "1815-12-10"}),
            ("register with a duplicate MRN is rejected", "POST", "/api/register_patient",
             {"mrn": "MRN-2001", "full_name": "Copy"}),
            ("look the patient up by MRN", "POST", "/api/lookup_patient", {"mrn": "MRN-2001"}),
            ("admit the patient", "POST", "/api/admit_patient",
             {"patient_id": "$patient_id", "ward": "Ward A", "expected_stay_days": 3}),
            ("flag an allergy", "POST", "/api/flag_allergy",
             {"patient_id": "$patient_id", "allergen": "Penicillin", "severity": "SEVERE"}),
            ("look the patient up by identifier", "POST", "/api/lookup_patient",
             {"patient_id": "$patient_id"}),
            ("discharge the admission", "POST", "/api/discharge_patient",
             {"admission_id": "$admission_id"}),
            ("state snapshot after the calls", "GET", "/state", None),
            ("GUI capability form submission", "POST", "/ui/patients/new",
             {"mrn": "MRN-2002", "full_name": "Grace Hopper"}, "form"),
        ],
        "detail_page": "/ui/patients/$patient_id",
    },
    "appointment-queue": {
        "pages": ["/ui/", "/ui/tickets", "/ui/tickets/new", "/ui/capabilities"],
        "steps": [
            ("create an emergency ticket", "POST", "/api/create_ticket",
             {"patient_mrn": "MRN-3002", "reason": "Chest pain", "priority": "EMERGENCY"}),
            ("triage the waiting ticket", "POST", "/api/update_triage",
             {"ticket_id": "$ticket_id", "priority": "EMERGENCY",
              "notes": "Triaged on arrival"}),
            ("create a routine ticket", "POST", "/api/create_ticket",
             {"patient_mrn": "MRN-3001", "reason": "Fever", "priority": "NORMAL"}),
            ("call the highest priority ticket", "POST", "/api/call_next_ticket",
             {"desk": "Desk 1"}),
            ("cancel an already called ticket is rejected", "POST", "/api/cancel_ticket",
             {"ticket_id": "$ticket_id", "reason": "Left without being seen"}),
            ("create a low priority ticket", "POST", "/api/create_ticket",
             {"patient_mrn": "MRN-3003", "reason": "Follow up", "priority": "LOW"}),
            ("cancel the low priority ticket", "POST", "/api/cancel_ticket",
             {"ticket_id": "$ticket_id", "reason": "Left without being seen"}),
            ("call the remaining ticket", "POST", "/api/call_next_ticket", {"desk": "Desk 2"}),
            ("calling next on an empty queue is rejected", "POST", "/api/call_next_ticket", {}),
            ("state snapshot after the calls", "GET", "/state", None),
            ("GUI capability form submission", "POST", "/ui/tickets/new",
             {"patient_mrn": "MRN-3004", "reason": "Dressing change", "priority": "LOW"}, "form"),
        ],
        "detail_page": "/ui/tickets/$ticket_id",
    },
    "opd-ehr": {
        "pages": ["/ui/", "/ui/encounters", "/ui/encounters/new", "/ui/capabilities"],
        "steps": [
            ("start an encounter", "POST", "/api/start_encounter",
             {"patient_mrn": "MRN-4001", "clinician": "Dr Rivera",
              "visit_type": "CONSULTATION"}),
            ("starting a second encounter is rejected", "POST", "/api/start_encounter",
             {"patient_mrn": "MRN-4002", "clinician": "Dr Chen"}),
            ("record vitals", "POST", "/api/record_vitals",
             {"encounter_id": "$encounter_id", "temperature_c": 37.2, "heart_rate": 72,
              "systolic": 118}),
            ("issue a prescription", "POST", "/api/issue_prescription",
             {"encounter_id": "$encounter_id", "drug": "Amoxicillin", "dose_mg": 500,
              "instructions": "Three times daily for seven days"}),
            ("record an out of range temperature is rejected", "POST", "/api/record_vitals",
             {"encounter_id": "$encounter_id", "temperature_c": 52.0, "heart_rate": 72}),
            ("close the encounter", "POST", "/api/close_encounter",
             {"encounter_id": "$encounter_id",
              "summary": "Upper respiratory infection, resolved"}),
            ("recording vitals on a closed encounter is rejected", "POST", "/api/record_vitals",
             {"encounter_id": "$encounter_id", "temperature_c": 37.0, "heart_rate": 72}),
            ("state snapshot after the calls", "GET", "/state", None),
            ("GUI capability form submission", "POST", "/ui/encounters/new",
             {"patient_mrn": "MRN-4003", "clinician": "Dr Chen", "visit_type": "FOLLOW_UP"},
             "form"),
        ],
        "detail_page": "/ui/encounters/$encounter_id",
    },
    "pharmacy-inventory": {
        "pages": ["/ui/", "/ui/drugs", "/ui/dispense", "/ui/capabilities"],
        "steps": [
            ("register a drug", "POST", "/api/register_drug",
             {"sku": "AMOX-500", "name": "Amoxicillin 500 mg", "unit_price": 0.35,
              "initial_quantity": 100}),
            ("registering the same SKU again is rejected", "POST", "/api/register_drug",
             {"sku": "AMOX-500", "name": "Copy", "unit_price": 1.0}),
            ("check the stock level", "POST", "/api/check_stock", {"sku": "$sku"}),
            ("dispense ten units", "POST", "/api/dispense_drug",
             {"sku": "$sku", "quantity": 10, "patient_mrn": "MRN-5001"}),
            ("dispensing more than is on hand is rejected", "POST", "/api/dispense_drug",
             {"sku": "$sku", "quantity": 95}),
            ("replenish fifty units", "POST", "/api/replenish_stock",
             {"sku": "$sku", "quantity": 50}),
            ("state snapshot after the calls", "GET", "/state", None),
            ("GUI capability form submission", "POST", "/ui/dispense",
             {"sku": "AMOX-500", "quantity": 5, "patient_mrn": "MRN-5002"}, "form"),
        ],
    },
    "pos-billing": {
        "pages": ["/ui/", "/ui/invoices", "/ui/invoices/new", "/ui/payments/new",
                  "/ui/capabilities"],
        "steps": [
            ("generate an invoice", "POST", "/api/generate_invoice",
             {"patient_mrn": "MRN-6001", "amount": 42.5, "description": "Consultation fee"}),
            ("a cash tender below the amount is rejected", "POST", "/api/process_payment",
             {"invoice_id": "$invoice_id", "method": "CASH", "amount_tendered": 40.0}),
            ("pay the invoice with cash", "POST", "/api/process_payment",
             {"invoice_id": "$invoice_id", "method": "CASH", "amount_tendered": 50.0}),
            ("paying the invoice twice is rejected", "POST", "/api/process_payment",
             {"invoice_id": "$invoice_id", "method": "CARD"}),
            ("read the receipt", "POST", "/api/get_receipt", {"invoice_id": "$invoice_id"}),
            ("send the receipt notice", "POST", "/api/send_receipt_notice",
             {"invoice_id": "$invoice_id", "channel": "EMAIL",
              "destination": "patient contact"}),
            ("generate a second invoice", "POST", "/api/generate_invoice",
             {"patient_mrn": "MRN-6002", "amount": 13.75, "description": "Pharmacy dispense"}),
            ("state snapshot after the calls", "GET", "/state", None),
            ("GUI capability form submission", "POST", "/ui/payments/new",
             {"invoice_id": "$invoice_id", "method": "CARD"}, "form"),
        ],
        "detail_page": "/ui/invoices/$invoice_id",
    },
    "legacy-lab-service": {
        "pages": ["/ui/", "/ui/orders", "/ui/orders/new", "/ui/capabilities"],
        "prepare": [
            ("INSERT INTO test_catalogue (test_code, name, unit, ref_low, ref_high)"
             " VALUES (?, ?, ?, ?, ?)", ("GLU", "Fasting glucose", "mmol/L", 3.9, 5.5)),
            ("INSERT INTO test_catalogue (test_code, name, unit, ref_low, ref_high)"
             " VALUES (?, ?, ?, ?, ?)", ("CBC", "Complete blood count", "10^9/L", 4.0, 11.0)),
        ],
        "steps": [
            ("order a test", "POST", "/api/order_test",
             {"patient_mrn": "MRN-7001", "test_code": "GLU", "urgency_level": "URGENT"}),
            ("ordering an unknown test code is rejected", "POST", "/api/order_test",
             {"patient_mrn": "MRN-7001", "test_code": "HBA1C"}),
            ("entering a result before the sample is rejected", "POST", "/api/enter_result",
             {"lab_order_id": "$lab_order_id", "result_value": 5.4}),
            ("receive the sample", "POST", "/api/receive_sample",
             {"lab_order_id": "$lab_order_id", "sample_label": "Tube 7"}),
            ("enter the result", "POST", "/api/enter_result",
             {"lab_order_id": "$lab_order_id", "result_value": 5.4}),
            ("read the report", "POST", "/api/get_report", {"lab_order_id": "$lab_order_id"}),
            ("state snapshot after the calls", "GET", "/state", None),
            ("GUI capability form submission", "POST", "/ui/orders/new",
             {"patient_mrn": "MRN-7002", "test_code": "CBC", "urgency_level": "ROUTINE"},
             "form"),
        ],
        "detail_page": "/ui/orders/$lab_order_id",
    },
    "patient-registry-alt": {
        "pages": ["/ui/", "/ui/patients", "/ui/pat_reg/new", "/ui/capabilities"],
        "steps": [
            ("register a patient", "POST", "/api/pat_reg",
             {"pat_no": "P-3001", "pat_name": "Ada Lovelace"}),
            ("registering the same patient number again is rejected", "POST", "/api/pat_reg",
             {"pat_no": "P-3001", "pat_name": "Copy"}),
            ("look the registration up", "POST", "/api/pat_lookup", {"pat_reg": "$pat_reg"}),
            ("verify the registration", "POST", "/api/pat_verify", {"pat_reg": "$pat_reg"}),
            ("verifying the registration again is rejected", "POST", "/api/pat_verify",
             {"pat_reg": "$pat_reg"}),
            ("state snapshot after the calls", "GET", "/state", None),
            ("GUI capability form submission", "POST", "/ui/pat_reg/new",
             {"pat_no": "P-3002", "pat_name": "Grace Hopper"}, "form"),
        ],
        "detail_page": "/ui/patients/$pat_reg",
    },
}


def http_call(method, url, body=None, form=False):
    data = None
    headers = {}
    if body is not None:
        if form:
            data = urllib.parse.urlencode(body).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")


def resolve(body, context):
    if body is None:
        return None
    resolved = {}
    for key, value in body.items():
        if isinstance(value, str) and value.startswith("$"):
            name = value[1:]
            if name not in context:
                raise SystemExit('step needs "$%s" but no earlier response provided it' % name)
            resolved[key] = context[name]
        else:
            resolved[key] = value
    return resolved


def start_module(name, port, db_path):
    environment = dict(os.environ)
    environment["CAREWEAVE_DB"] = db_path
    environment["CAREWEAVE_PORT"] = str(port)
    log_path = os.path.join(EVIDENCE_DIR, "%s.server.log" % name)
    log = open(log_path, "w", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=os.path.join(MODULES_DIR, name),
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    base = "http://127.0.0.1:%d" % port
    for _ in range(60):
        try:
            status, _body = http_call("GET", base + "/health")
            if status == 200:
                return process, base, log_path
        except Exception:
            time.sleep(0.25)
    process.send_signal(signal.SIGTERM)
    process.wait(timeout=10)
    raise SystemExit("module %s did not become healthy; see %s" % (name, log_path))


def stop_module(process):
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def capture(name):
    module_dir = os.path.join(MODULES_DIR, name)
    with open(os.path.join(module_dir, "spec.json"), "r", encoding="utf-8") as handle:
        spec = json.load(handle)
    port = spec["module"]["port"]
    db_path = os.path.join(EVIDENCE_DIR, "%s.db" % name)
    for suffix in ("", "-wal", "-shm"):
        path = db_path + suffix
        if os.path.exists(path):
            os.remove(path)
    plan = TRANSCRIPT_PLANS.get(name, {"pages": ["/ui/", "/ui/capabilities"], "steps": []})
    prepare = plan.get("prepare", [])

    process, base, log_path = start_module(name, port, db_path)
    lines = []
    context = {}

    def record(title, method, path, body=None, form=False):
        lines.append("\n$ %s %s" % (method, path))
        lines.append("  (%s)" % title)
        if body is not None:
            lines.append("  request body: %s" % json.dumps(body, sort_keys=True))
        status, text = http_call(method, base + path, body, form)
        lines.append("  http status: %d" % status)
        try:
            lines.append("  response: %s" % json.dumps(json.loads(text), sort_keys=True))
        except ValueError:
            lines.append("  response (%d bytes of HTML): %s" % (len(text), text.splitlines()[0]))
        if status == 200 and method == "POST":
            try:
                payload = json.loads(text)
                for key, value in payload.get("outputs", {}).items():
                    context[key] = value
            except ValueError:
                pass
        return status, text

    try:
        lines.append("TRANSCRIPT %s live run" % name)
        lines.append("database: %s" % os.path.relpath(db_path, ROOT))
        lines.append("server log: %s" % os.path.relpath(log_path, ROOT))
        lines.append("python: %s" % platform.python_version())
        if prepare:
            connection = sqlite3.connect(db_path)
            try:
                for statement, params in prepare:
                    connection.execute(statement, params)
                connection.commit()
            finally:
                connection.close()
            lines.append("prepared reference data: %d statements" % len(prepare))
        record("module health", "GET", "/health")
        status, text = http_call("GET", base + "/spec")
        lines.append("\n$ GET /spec")
        spec_body = json.loads(text)
        lines.append("  http status: %d" % status)
        lines.append("  capability ids: %s" % json.dumps(
            [c["id"] for c in spec_body["capabilities"]]))
        lines.append("  state variables: %s" % json.dumps(
            [v["name"] for v in spec_body["state_schema"]]))
        record("state before any capability call", "GET", "/state")
        for page in plan["pages"]:
            record("UI page", "GET", page)
        for step in plan["steps"]:
            title, method, path, body = step[0], step[1], step[2], step[3]
            form = len(step) > 4 and step[4] == "form"
            record(title, method, path, resolve(body, context), form)
        detail = plan.get("detail_page")
        if detail:
            for key in sorted(context, key=len, reverse=True):
                detail = detail.replace("$" + key, str(context[key]))
            record("UI detail page", "GET", detail)
        transcript_path = os.path.join(EVIDENCE_DIR, "%s.transcript.txt" % name)
        with open(transcript_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        print("wrote %s" % os.path.relpath(transcript_path, ROOT))
    finally:
        stop_module(process)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", nargs="?", help="module directory name")
    parser.add_argument("--all", action="store_true", help="capture every module listed in the plans")
    arguments = parser.parse_args()
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    if arguments.all:
        names = sorted(TRANSCRIPT_PLANS)
    elif arguments.module:
        names = [arguments.module]
    else:
        parser.error("give a module name or --all")
    for name in names:
        capture(name)


if __name__ == "__main__":
    main()
