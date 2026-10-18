"""Capability implementations of the legacy laboratory service.

Each method implements one capability from spec.json and returns (outputs, effects):

- outputs  the typed output values named by the capability specification
- effects  the state effects actually applied, in the specification effect format

The workflow of an order is ordered -> sample received -> resulted; a step attempted out of
order is a 409, an unknown order or test code is a 404 and a missing or invalid input is a 400.
The module keeps the legacy laboratory naming: patient_mrn, test_code, urgency_level.
"""

import uuid
from datetime import datetime, timezone

from services import validation
from services.errors import BadInput, Conflict, NotFound

URGENCY_LEVELS = ["ROUTINE", "URGENT", "STAT"]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix):
    return "%s-%s" % (prefix, uuid.uuid4().hex[:8].upper())


def require_result_value(payload):
    value = payload.get("result_value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BadInput('input "result_value" must be a number')
    value = float(value)
    if value < 0 or value > 100000:
        raise BadInput('input "result_value" must be between 0 and 100000')
    return value


class LabService:
    """Implements the LAB capability set against the module database."""

    def __init__(self, connection_factory):
        self._connect = connection_factory

    # ---- state ----

    def state_snapshot(self):
        """Reads the state variables declared in spec.json from the order table."""
        connection = self._connect()
        try:
            ordered = connection.execute("SELECT COUNT(*) FROM lab_orders").fetchone()[0] > 0
            received = (
                connection.execute(
                    "SELECT COUNT(*) FROM lab_orders WHERE status IN ('received', 'resulted')"
                ).fetchone()[0]
                > 0
            )
            resulted = (
                connection.execute(
                    "SELECT COUNT(*) FROM lab_orders WHERE status = 'resulted'"
                ).fetchone()[0]
                > 0
            )
            return {
                "Lab.ordered": ordered,
                "Sample.received": received,
                "Lab.resulted": resulted,
            }
        finally:
            connection.close()

    # ---- capabilities ----

    def order_test(self, payload):
        patient_mrn = validation.require_string(payload, "patient_mrn")
        test_code = validation.require_string(payload, "test_code")
        urgency_level = validation.optional_enum(
            payload, "urgency_level", URGENCY_LEVELS, "ROUTINE"
        )
        connection = self._connect()
        try:
            test = connection.execute(
                "SELECT * FROM test_catalogue WHERE test_code = ?", (test_code,)
            ).fetchone()
            if test is None:
                raise NotFound('unknown test code "%s"' % test_code)
            lab_order_id = new_id("LAB")
            ordered_at = now_iso()
            connection.execute(
                "INSERT INTO lab_orders (lab_order_id, patient_mrn, test_code, urgency_level,"
                " status, sample_label, result_value, result_unit, ordered_at, received_at,"
                " resulted_at) VALUES (?, ?, ?, ?, 'ordered', NULL, NULL, NULL, ?, NULL, NULL)",
                (lab_order_id, patient_mrn, test_code, urgency_level, ordered_at),
            )
            connection.commit()
            outputs = {
                "lab_order_id": lab_order_id,
                "test_code": test_code,
                "test_name": test["name"],
                "urgency_level": urgency_level,
                "ordered_at": ordered_at,
            }
            effects = [{"variable": "Lab.ordered", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def receive_sample(self, payload):
        order_id = validation.require_string(payload, "lab_order_id")
        sample_label = validation.optional_string(payload, "sample_label")
        connection = self._connect()
        try:
            order = connection.execute(
                "SELECT * FROM lab_orders WHERE lab_order_id = ?", (order_id,)
            ).fetchone()
            if order is None:
                raise NotFound('unknown lab order "%s"' % order_id)
            if order["status"] != "ordered":
                raise Conflict(
                    'lab order "%s" is already %s' % (order_id, order["status"])
                )
            received_at = now_iso()
            connection.execute(
                "UPDATE lab_orders SET status = 'received', sample_label = ?,"
                " received_at = ? WHERE lab_order_id = ?",
                (sample_label, received_at, order_id),
            )
            connection.commit()
            outputs = {"received": True, "lab_order_id": order_id, "received_at": received_at}
            effects = [{"variable": "Sample.received", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def enter_result(self, payload):
        order_id = validation.require_string(payload, "lab_order_id")
        result_value = require_result_value(payload)
        result_unit = validation.optional_string(payload, "unit")
        connection = self._connect()
        try:
            order = connection.execute(
                "SELECT * FROM lab_orders WHERE lab_order_id = ?", (order_id,)
            ).fetchone()
            if order is None:
                raise NotFound('unknown lab order "%s"' % order_id)
            if order["status"] == "resulted":
                raise Conflict('lab order "%s" already has a result' % order_id)
            if order["status"] != "received":
                raise Conflict(
                    'lab order "%s" has no received sample yet' % order_id
                )
            resulted_at = now_iso()
            connection.execute(
                "UPDATE lab_orders SET status = 'resulted', result_value = ?,"
                " result_unit = ?, resulted_at = ? WHERE lab_order_id = ?",
                (result_value, result_unit, resulted_at, order_id),
            )
            connection.commit()
            outputs = {"resulted": True, "lab_order_id": order_id, "resulted_at": resulted_at}
            effects = [{"variable": "Lab.resulted", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def get_report(self, payload):
        order_id = validation.require_string(payload, "lab_order_id")
        connection = self._connect()
        try:
            order = connection.execute(
                "SELECT * FROM lab_orders WHERE lab_order_id = ?", (order_id,)
            ).fetchone()
            if order is None:
                raise NotFound('unknown lab order "%s"' % order_id)
            test = connection.execute(
                "SELECT * FROM test_catalogue WHERE test_code = ?", (order["test_code"],)
            ).fetchone()
            resulted = order["status"] == "resulted"
            if resulted:
                report_text = (
                    "%s (%s): %.2f %s, reference %.2f to %.2f"
                    % (
                        test["name"],
                        test["test_code"],
                        order["result_value"],
                        order["result_unit"] or test["unit"],
                        test["ref_low"],
                        test["ref_high"],
                    )
                )
            else:
                report_text = "%s (%s): no result yet, status %s" % (
                    test["name"],
                    test["test_code"],
                    order["status"],
                )
            outputs = {
                "report_text": report_text,
                "status": order["status"],
                "resulted": resulted,
                "patient_mrn": order["patient_mrn"],
                "test_code": order["test_code"],
                "urgency_level": order["urgency_level"],
            }
            return outputs, []
        finally:
            connection.close()

    # ---- listings used by the UI ----

    def list_orders(self, query=None):
        connection = self._connect()
        try:
            if query:
                like = "%%%s%%" % query
                rows = connection.execute(
                    "SELECT * FROM lab_orders WHERE patient_mrn LIKE ? OR test_code LIKE ?"
                    " ORDER BY ordered_at DESC",
                    (like, like),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM lab_orders ORDER BY ordered_at DESC"
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def order_detail(self, lab_order_id):
        connection = self._connect()
        try:
            order = connection.execute(
                "SELECT * FROM lab_orders WHERE lab_order_id = ?", (lab_order_id,)
            ).fetchone()
            if order is None:
                raise NotFound('unknown lab order "%s"' % lab_order_id)
            test = connection.execute(
                "SELECT * FROM test_catalogue WHERE test_code = ?", (order["test_code"],)
            ).fetchone()
            return {"order": dict(order), "test": dict(test)}
        finally:
            connection.close()

    def list_test_codes(self):
        connection = self._connect()
        try:
            rows = connection.execute("SELECT * FROM test_catalogue ORDER BY test_code").fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def summary_counts(self):
        connection = self._connect()
        try:
            return {
                "orders": connection.execute("SELECT COUNT(*) FROM lab_orders").fetchone()[0],
                "received": connection.execute(
                    "SELECT COUNT(*) FROM lab_orders WHERE status IN ('received', 'resulted')"
                ).fetchone()[0],
                "resulted": connection.execute(
                    "SELECT COUNT(*) FROM lab_orders WHERE status = 'resulted'"
                ).fetchone()[0],
                "test_codes": connection.execute(
                    "SELECT COUNT(*) FROM test_catalogue"
                ).fetchone()[0],
            }
        finally:
            connection.close()
