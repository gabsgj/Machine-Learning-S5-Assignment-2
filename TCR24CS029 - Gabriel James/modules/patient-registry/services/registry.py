"""Capability implementations of the patient registry module.

Each method implements one capability from spec.json and returns (outputs, effects):

- outputs  the typed output values named by the capability specification
- effects  the state effects actually applied, in the specification effect format

Validation and domain failures raise the ApiError subclasses, which the HTTP layer renders as
{"status": "error", "error": "..."} with the corresponding status code. Nothing is defaulted
silently: an unknown patient is a 404, a duplicate medical record number is a 409 and a missing
input names the input.
"""

import uuid
from datetime import datetime, timezone

from services import validation
from services.errors import Conflict, NotFound

SEVERITIES = ["MILD", "MODERATE", "SEVERE"]
WARD_CAPACITY = 8


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix):
    return "%s-%s" % (prefix, uuid.uuid4().hex[:8].upper())


class RegistryService:
    """Implements the PR capability set against the module database."""

    def __init__(self, connection_factory):
        self._connect = connection_factory

    # ---- state ----

    def state_snapshot(self):
        """Reads the state variables declared in spec.json from the database."""
        connection = self._connect()
        try:
            registered = connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0] > 0
            admitted = (
                connection.execute("SELECT COUNT(*) FROM patients WHERE admitted = 1").fetchone()[0]
                > 0
            )
            allergy = connection.execute("SELECT COUNT(*) FROM allergies").fetchone()[0] > 0
            active = connection.execute(
                "SELECT COUNT(*) FROM admissions WHERE active = 1"
            ).fetchone()[0]
            return {
                "Patient.registered": registered,
                "Patient.admitted": admitted,
                "Patient.allergy_flagged": allergy,
                "Ward.bed_available": active < WARD_CAPACITY,
            }
        finally:
            connection.close()

    # ---- capabilities ----

    def register_patient(self, payload):
        mrn = validation.require_string(payload, "mrn")
        full_name = validation.require_string(payload, "full_name")
        date_of_birth = validation.optional_string(payload, "date_of_birth")
        connection = self._connect()
        try:
            duplicate = connection.execute(
                "SELECT patient_id FROM patients WHERE mrn = ?", (mrn,)
            ).fetchone()
            if duplicate is not None:
                raise Conflict('a patient with MRN "%s" already exists' % mrn)
            patient_id = new_id("PAT")
            created_at = now_iso()
            connection.execute(
                "INSERT INTO patients (patient_id, mrn, full_name, date_of_birth, admitted,"
                " allergy_count, created_at) VALUES (?, ?, ?, ?, 0, 0, ?)",
                (patient_id, mrn, full_name, date_of_birth, created_at),
            )
            connection.commit()
            outputs = {"patient_id": patient_id, "mrn": mrn, "created_at": created_at}
            effects = [{"variable": "Patient.registered", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def admit_patient(self, payload):
        patient_id = validation.require_string(payload, "patient_id")
        ward = validation.require_string(payload, "ward")
        expected_stay_days = validation.optional_int(payload, "expected_stay_days")
        connection = self._connect()
        try:
            patient = connection.execute(
                "SELECT patient_id, admitted FROM patients WHERE patient_id = ?", (patient_id,)
            ).fetchone()
            if patient is None:
                raise NotFound('unknown patient "%s"' % patient_id)
            if patient["admitted"]:
                raise Conflict('patient "%s" is already admitted' % patient_id)
            active = connection.execute(
                "SELECT COUNT(*) FROM admissions WHERE active = 1"
            ).fetchone()[0]
            if active >= WARD_CAPACITY:
                raise Conflict(
                    "no bed available: %d of %d places are occupied" % (active, WARD_CAPACITY)
                )
            admission_id = new_id("ADM")
            admitted_at = now_iso()
            connection.execute(
                "INSERT INTO admissions (admission_id, patient_id, ward, expected_stay_days,"
                " active, admitted_at, discharged_at) VALUES (?, ?, ?, ?, 1, ?, NULL)",
                (admission_id, patient_id, ward, expected_stay_days, admitted_at),
            )
            connection.execute(
                "UPDATE patients SET admitted = 1 WHERE patient_id = ?", (patient_id,)
            )
            connection.commit()
            outputs = {"admission_id": admission_id, "admitted_at": admitted_at}
            effects = [{"variable": "Patient.admitted", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def discharge_patient(self, payload):
        admission_id = validation.require_string(payload, "admission_id")
        connection = self._connect()
        try:
            admission = connection.execute(
                "SELECT admission_id, patient_id, active FROM admissions WHERE admission_id = ?",
                (admission_id,),
            ).fetchone()
            if admission is None:
                raise NotFound('unknown admission "%s"' % admission_id)
            if not admission["active"]:
                raise Conflict('admission "%s" is already closed' % admission_id)
            discharged_at = now_iso()
            connection.execute(
                "UPDATE admissions SET active = 0, discharged_at = ? WHERE admission_id = ?",
                (discharged_at, admission_id),
            )
            remaining = connection.execute(
                "SELECT COUNT(*) FROM admissions WHERE patient_id = ? AND active = 1",
                (admission["patient_id"],),
            ).fetchone()[0]
            if remaining == 0:
                connection.execute(
                    "UPDATE patients SET admitted = 0 WHERE patient_id = ?",
                    (admission["patient_id"],),
                )
            connection.commit()
            outputs = {"discharged": True, "discharged_at": discharged_at}
            effects = [{"variable": "Patient.admitted", "op": "SET", "value": remaining > 0}]
            return outputs, effects
        finally:
            connection.close()

    def flag_allergy(self, payload):
        patient_id = validation.require_string(payload, "patient_id")
        allergen = validation.require_string(payload, "allergen")
        severity = validation.require_enum(payload, "severity", SEVERITIES)
        connection = self._connect()
        try:
            patient = connection.execute(
                "SELECT patient_id FROM patients WHERE patient_id = ?", (patient_id,)
            ).fetchone()
            if patient is None:
                raise NotFound('unknown patient "%s"' % patient_id)
            allergy_id = new_id("ALG")
            flagged_at = now_iso()
            connection.execute(
                "INSERT INTO allergies (allergy_id, patient_id, allergen, severity, flagged_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (allergy_id, patient_id, allergen, severity, flagged_at),
            )
            connection.execute(
                "UPDATE patients SET allergy_count = allergy_count + 1 WHERE patient_id = ?",
                (patient_id,),
            )
            connection.commit()
            outputs = {"flagged": True, "allergy_id": allergy_id}
            effects = [{"variable": "Patient.allergy_flagged", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def lookup_patient(self, payload):
        patient_id = validation.optional_string(payload, "patient_id")
        mrn = validation.optional_string(payload, "mrn")
        if not patient_id and not mrn:
            from services.errors import BadInput

            raise BadInput('one of "patient_id" or "mrn" is required')
        connection = self._connect()
        try:
            if patient_id:
                row = connection.execute(
                    "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
                ).fetchone()
            else:
                row = connection.execute("SELECT * FROM patients WHERE mrn = ?", (mrn,)).fetchone()
            if row is None:
                raise NotFound("no patient matches the given identifier")
            outputs = {
                "patient_id": row["patient_id"],
                "mrn": row["mrn"],
                "full_name": row["full_name"],
                "admitted": bool(row["admitted"]),
                "allergy_count": row["allergy_count"],
            }
            return outputs, []
        finally:
            connection.close()

    # ---- listings used by the UI ----

    def list_patients(self, query=None):
        connection = self._connect()
        try:
            if query:
                like = "%%%s%%" % query
                rows = connection.execute(
                    "SELECT * FROM patients WHERE mrn LIKE ? OR full_name LIKE ?"
                    " ORDER BY created_at DESC",
                    (like, like),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM patients ORDER BY created_at DESC"
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def patient_detail(self, patient_id):
        connection = self._connect()
        try:
            patient = connection.execute(
                "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
            ).fetchone()
            if patient is None:
                raise NotFound('unknown patient "%s"' % patient_id)
            admissions = connection.execute(
                "SELECT * FROM admissions WHERE patient_id = ? ORDER BY admitted_at DESC",
                (patient_id,),
            ).fetchall()
            allergies = connection.execute(
                "SELECT * FROM allergies WHERE patient_id = ? ORDER BY flagged_at DESC",
                (patient_id,),
            ).fetchall()
            return {
                "patient": dict(patient),
                "admissions": [dict(row) for row in admissions],
                "allergies": [dict(row) for row in allergies],
            }
        finally:
            connection.close()

    def summary_counts(self):
        connection = self._connect()
        try:
            return {
                "patients": connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
                "active_admissions": connection.execute(
                    "SELECT COUNT(*) FROM admissions WHERE active = 1"
                ).fetchone()[0],
                "allergies": connection.execute("SELECT COUNT(*) FROM allergies").fetchone()[0],
            }
        finally:
            connection.close()
