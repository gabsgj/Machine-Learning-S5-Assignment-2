"""Capability implementations of the outpatient EHR module.

Each method implements one capability from spec.json and returns (outputs, effects). Clinical
values are range checked against the domains declared in the specification sheet; an out of
range value is a 400, a missing encounter is a 404 and a state that contradicts a precondition
is a 409. Nothing is defaulted silently: the only documented default is the visit type
CONSULTATION for a new encounter.
"""

import uuid
from datetime import datetime, timezone

from services import validation
from services.errors import BadInput, Conflict, NotFound

VISIT_TYPES = ["CONSULTATION", "FOLLOW_UP", "EMERGENCY"]
TEMPERATURE_RANGE = (25.0, 45.0)
HEART_RATE_RANGE = (20, 300)
SYSTOLIC_RANGE = (60, 260)
DOSE_RANGE = (0.1, 5000.0)


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix):
    return "%s-%s" % (prefix, uuid.uuid4().hex[:8].upper())


def require_real_in_range(payload, name, low, high):
    value = payload.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BadInput('input "%s" must be a number' % name)
    value = float(value)
    if value < low or value > high:
        raise BadInput('input "%s" must be between %s and %s' % (name, low, high))
    return value


def optional_int_in_range(payload, name, low, high, default=None):
    value = payload.get(name)
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise BadInput('input "%s" must be an integer' % name)
    if value < low or value > high:
        raise BadInput('input "%s" must be between %s and %s' % (name, low, high))
    return value


def require_int_in_range(payload, name, low, high):
    value = optional_int_in_range(payload, name, low, high)
    if value is None:
        raise BadInput('input "%s" must be an integer' % name)
    return value


class EhrService:
    """Implements the EHR capability set against the module database."""

    def __init__(self, connection_factory):
        self._connect = connection_factory

    # ---- state ----

    def state_snapshot(self):
        """Reads the state variables declared in spec.json from the tables."""
        connection = self._connect()
        try:
            active = (
                connection.execute(
                    "SELECT COUNT(*) FROM encounters WHERE status = 'active'"
                ).fetchone()[0]
                > 0
            )
            closed = (
                connection.execute(
                    "SELECT COUNT(*) FROM encounters WHERE status = 'closed'"
                ).fetchone()[0]
                > 0
            )
            vitals = connection.execute("SELECT COUNT(*) FROM vitals").fetchone()[0] > 0
            issued = connection.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0] > 0
            count = connection.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0]
            return {
                "Encounter.active": active,
                "Encounter.closed": closed,
                "Vitals.recorded": vitals,
                "Prescription.issued": issued,
                "Prescription.count": count,
            }
        finally:
            connection.close()

    # ---- capabilities ----

    def start_encounter(self, payload):
        patient_mrn = validation.require_string(payload, "patient_mrn")
        clinician = validation.require_string(payload, "clinician")
        visit_type = validation.optional_enum(payload, "visit_type", VISIT_TYPES, "CONSULTATION")
        connection = self._connect()
        try:
            active = connection.execute(
                "SELECT encounter_id FROM encounters WHERE status = 'active' LIMIT 1"
            ).fetchone()
            if active is not None:
                raise Conflict(
                    'encounter "%s" is still active; close it before starting another'
                    % active["encounter_id"]
                )
            encounter_id = new_id("ENC")
            started_at = now_iso()
            connection.execute(
                "INSERT INTO encounters (encounter_id, patient_mrn, clinician, visit_type,"
                " status, summary, started_at, closed_at)"
                " VALUES (?, ?, ?, ?, 'active', NULL, ?, NULL)",
                (encounter_id, patient_mrn, clinician, visit_type, started_at),
            )
            connection.commit()
            outputs = {
                "encounter_id": encounter_id,
                "visit_type": visit_type,
                "started_at": started_at,
            }
            effects = [{"variable": "Encounter.active", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def _active_encounter(self, connection, encounter_id):
        encounter = connection.execute(
            "SELECT encounter_id, status FROM encounters WHERE encounter_id = ?", (encounter_id,)
        ).fetchone()
        if encounter is None:
            raise NotFound('unknown encounter "%s"' % encounter_id)
        if encounter["status"] != "active":
            raise Conflict('encounter "%s" is closed' % encounter_id)
        return encounter

    def record_vitals(self, payload):
        encounter_id = validation.require_string(payload, "encounter_id")
        temperature = require_real_in_range(payload, "temperature_c", *TEMPERATURE_RANGE)
        heart_rate = require_int_in_range(payload, "heart_rate", *HEART_RATE_RANGE)
        systolic = optional_int_in_range(payload, "systolic", *SYSTOLIC_RANGE)
        connection = self._connect()
        try:
            self._active_encounter(connection, encounter_id)
            vitals_id = new_id("VIT")
            recorded_at = now_iso()
            connection.execute(
                "INSERT INTO vitals (vitals_id, encounter_id, temperature_c, heart_rate,"
                " systolic, recorded_at) VALUES (?, ?, ?, ?, ?, ?)",
                (vitals_id, encounter_id, temperature, heart_rate, systolic, recorded_at),
            )
            connection.commit()
            outputs = {"recorded": True, "vitals_id": vitals_id, "recorded_at": recorded_at}
            effects = [{"variable": "Vitals.recorded", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def issue_prescription(self, payload):
        encounter_id = validation.require_string(payload, "encounter_id")
        drug = validation.require_string(payload, "drug")
        dose = require_real_in_range(payload, "dose_mg", *DOSE_RANGE)
        instructions = validation.optional_string(payload, "instructions")
        connection = self._connect()
        try:
            self._active_encounter(connection, encounter_id)
            prescription_id = new_id("RX")
            issued_at = now_iso()
            connection.execute(
                "INSERT INTO prescriptions (prescription_id, encounter_id, drug, dose_mg,"
                " instructions, issued_at) VALUES (?, ?, ?, ?, ?, ?)",
                (prescription_id, encounter_id, drug, dose, instructions, issued_at),
            )
            connection.commit()
            outputs = {"prescription_id": prescription_id, "issued_at": issued_at}
            effects = [
                {"variable": "Prescription.issued", "op": "SET", "value": True},
                {"variable": "Prescription.count", "op": "INCREMENT", "value": 1},
            ]
            return outputs, effects
        finally:
            connection.close()

    def close_encounter(self, payload):
        encounter_id = validation.require_string(payload, "encounter_id")
        summary = validation.optional_string(payload, "summary")
        connection = self._connect()
        try:
            self._active_encounter(connection, encounter_id)
            closed_at = now_iso()
            connection.execute(
                "UPDATE encounters SET status = 'closed', summary = ?, closed_at = ?"
                " WHERE encounter_id = ?",
                (summary, closed_at, encounter_id),
            )
            connection.commit()
            outputs = {"closed": True, "closed_at": closed_at}
            effects = [
                {"variable": "Encounter.active", "op": "SET", "value": False},
                {"variable": "Encounter.closed", "op": "SET", "value": True},
            ]
            return outputs, effects
        finally:
            connection.close()

    # ---- listings used by the UI ----

    def list_encounters(self, query=None):
        connection = self._connect()
        try:
            if query:
                like = "%%%s%%" % query
                rows = connection.execute(
                    "SELECT * FROM encounters WHERE patient_mrn LIKE ? OR clinician LIKE ?"
                    " ORDER BY started_at DESC",
                    (like, like),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM encounters ORDER BY started_at DESC"
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def encounter_detail(self, encounter_id):
        connection = self._connect()
        try:
            encounter = connection.execute(
                "SELECT * FROM encounters WHERE encounter_id = ?", (encounter_id,)
            ).fetchone()
            if encounter is None:
                raise NotFound('unknown encounter "%s"' % encounter_id)
            vitals = connection.execute(
                "SELECT * FROM vitals WHERE encounter_id = ? ORDER BY recorded_at DESC",
                (encounter_id,),
            ).fetchall()
            prescriptions = connection.execute(
                "SELECT * FROM prescriptions WHERE encounter_id = ? ORDER BY issued_at DESC",
                (encounter_id,),
            ).fetchall()
            return {
                "encounter": dict(encounter),
                "vitals": [dict(row) for row in vitals],
                "prescriptions": [dict(row) for row in prescriptions],
            }
        finally:
            connection.close()

    def summary_counts(self):
        connection = self._connect()
        try:
            return {
                "encounters": connection.execute("SELECT COUNT(*) FROM encounters").fetchone()[0],
                "active": connection.execute(
                    "SELECT COUNT(*) FROM encounters WHERE status = 'active'"
                ).fetchone()[0],
                "prescriptions": connection.execute(
                    "SELECT COUNT(*) FROM prescriptions"
                ).fetchone()[0],
            }
        finally:
            connection.close()
