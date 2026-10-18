"""Capability implementations of the alternate patient registry module.

Each method implements one capability from spec.json and returns (outputs, effects):

- outputs  the typed output values named by the capability specification
- effects  the state effects actually applied, in the specification effect format

The vocabulary is the legacy registration vocabulary: pat_reg (the registration key assigned by
this module), pat_no (the external patient number) and pat_name. A duplicate pat_no is a 409,
an unknown pat_reg is a 404 and a missing input is a 400. The registered and verified
transitions are one way; repeating them is a 409.
"""

import uuid
from datetime import datetime, timezone

from services import validation
from services.errors import Conflict, NotFound


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_reg():
    return "PAT-%s" % uuid.uuid4().hex[:8].upper()


class AltRegistryService:
    """Implements the PA capability set against the module database."""

    def __init__(self, connection_factory):
        self._connect = connection_factory

    # ---- state ----

    def state_snapshot(self):
        """Reads the state variables declared in spec.json from the patients table."""
        connection = self._connect()
        try:
            registered = (
                connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0] > 0
            )
            verified = (
                connection.execute(
                    "SELECT COUNT(*) FROM patients WHERE verified = 1"
                ).fetchone()[0]
                > 0
            )
            return {"Patient.registered": registered, "Patient.verified": verified}
        finally:
            connection.close()

    # ---- capabilities ----

    def register_pat(self, payload):
        pat_no = validation.require_string(payload, "pat_no")
        pat_name = validation.require_string(payload, "pat_name")
        connection = self._connect()
        try:
            duplicate = connection.execute(
                "SELECT pat_reg FROM patients WHERE pat_no = ?", (pat_no,)
            ).fetchone()
            if duplicate is not None:
                raise Conflict(
                    'patient number "%s" is already registered as %s'
                    % (pat_no, duplicate["pat_reg"])
                )
            pat_reg = new_reg()
            registered_at = now_iso()
            connection.execute(
                "INSERT INTO patients (pat_reg, pat_no, pat_name, verified, registered_at,"
                " verified_at) VALUES (?, ?, ?, 0, ?, NULL)",
                (pat_reg, pat_no, pat_name, registered_at),
            )
            connection.commit()
            outputs = {
                "pat_reg": pat_reg,
                "pat_no": pat_no,
                "registered_at": registered_at,
            }
            effects = [{"variable": "Patient.registered", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def lookup_pat(self, payload):
        pat_reg = validation.require_string(payload, "pat_reg")
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM patients WHERE pat_reg = ?", (pat_reg,)
            ).fetchone()
            if row is None:
                raise NotFound('unknown patient registration "%s"' % pat_reg)
            outputs = {
                "pat_reg": row["pat_reg"],
                "pat_no": row["pat_no"],
                "pat_name": row["pat_name"],
                "verified": bool(row["verified"]),
            }
            return outputs, []
        finally:
            connection.close()

    def verify_pat(self, payload):
        pat_reg = validation.require_string(payload, "pat_reg")
        connection = self._connect()
        try:
            any_patient = connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
            if any_patient == 0:
                raise Conflict("no patient registration exists yet")
            row = connection.execute(
                "SELECT * FROM patients WHERE pat_reg = ?", (pat_reg,)
            ).fetchone()
            if row is None:
                raise NotFound('unknown patient registration "%s"' % pat_reg)
            if row["verified"]:
                raise Conflict('patient registration "%s" is already verified' % pat_reg)
            verified_at = now_iso()
            connection.execute(
                "UPDATE patients SET verified = 1, verified_at = ? WHERE pat_reg = ?",
                (verified_at, pat_reg),
            )
            connection.commit()
            outputs = {"verified": True, "pat_reg": pat_reg, "verified_at": verified_at}
            effects = [{"variable": "Patient.verified", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    # ---- listings used by the UI ----

    def list_patients(self, query=None):
        connection = self._connect()
        try:
            if query:
                like = "%%%s%%" % query
                rows = connection.execute(
                    "SELECT * FROM patients WHERE pat_no LIKE ? OR pat_name LIKE ?"
                    " ORDER BY registered_at DESC",
                    (like, like),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM patients ORDER BY registered_at DESC"
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def patient_detail(self, pat_reg):
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM patients WHERE pat_reg = ?", (pat_reg,)
            ).fetchone()
            if row is None:
                raise NotFound('unknown patient registration "%s"' % pat_reg)
            return dict(row)
        finally:
            connection.close()

    def summary_counts(self):
        connection = self._connect()
        try:
            return {
                "patients": connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
                "verified": connection.execute(
                    "SELECT COUNT(*) FROM patients WHERE verified = 1"
                ).fetchone()[0],
                "rows": connection.execute("SELECT COUNT(*) FROM pat_rows").fetchone()[0],
            }
        finally:
            connection.close()
