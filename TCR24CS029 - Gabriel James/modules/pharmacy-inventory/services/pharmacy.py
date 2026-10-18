"""Capability implementations of the pharmacy inventory module.

Each method implements one capability from spec.json and returns (outputs, effects):

- outputs  the typed output values named by the capability specification
- effects  the state effects actually applied, in the specification effect format

Stock levels live in the drugs table; the state snapshot derives the module state variables from
it. Requesting more units than are on hand is a 409 that names the shortage; an unknown SKU is a
404; a non positive or non integer quantity is a 400.
"""

import uuid
from datetime import datetime, timezone

from services import validation
from services.errors import BadInput, Conflict, NotFound


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix):
    return "%s-%s" % (prefix, uuid.uuid4().hex[:8].upper())


def require_positive_int(payload, name, maximum):
    value = validation.optional_int(payload, name)
    if value is None:
        raise BadInput('input "%s" must be an integer' % name)
    if value < 1 or value > maximum:
        raise BadInput('input "%s" must be between 1 and %d' % (name, maximum))
    return value


class PharmacyService:
    """Implements the PH capability set against the module database."""

    def __init__(self, connection_factory):
        self._connect = connection_factory

    # ---- state ----

    def state_snapshot(self):
        """Reads the state variables declared in spec.json from the stock tables."""
        connection = self._connect()
        try:
            total = connection.execute("SELECT COALESCE(SUM(on_hand), 0) FROM drugs").fetchone()[0]
            dispensed = (
                connection.execute("SELECT COUNT(*) FROM dispense_log").fetchone()[0] > 0
            )
            return {
                "Stock.available": total > 0,
                "Stock.quantity": total,
                "Drug.dispensed": dispensed,
            }
        finally:
            connection.close()

    # ---- capabilities ----

    def register_drug(self, payload):
        sku = validation.require_string(payload, "sku")
        name = validation.require_string(payload, "name")
        unit_price = payload.get("unit_price")
        if isinstance(unit_price, bool) or not isinstance(unit_price, (int, float)):
            raise BadInput('input "unit_price" must be a number')
        unit_price = float(unit_price)
        if unit_price <= 0 or unit_price > 100000:
            raise BadInput('input "unit_price" must be between 0 and 100000')
        initial_quantity = validation.optional_int(payload, "initial_quantity", 0) or 0
        if initial_quantity < 0 or initial_quantity > 100000:
            raise BadInput('input "initial_quantity" must be between 0 and 100000')
        connection = self._connect()
        try:
            duplicate = connection.execute("SELECT sku FROM drugs WHERE sku = ?", (sku,)).fetchone()
            if duplicate is not None:
                raise Conflict('drug "%s" is already in the catalogue' % sku)
            connection.execute(
                "INSERT INTO drugs (sku, name, on_hand, unit_price, updated_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (sku, name, initial_quantity, unit_price, now_iso()),
            )
            connection.commit()
            outputs = {"sku": sku, "name": name, "on_hand": initial_quantity}
            return outputs, []
        finally:
            connection.close()

    def check_stock(self, payload):
        sku = validation.require_string(payload, "sku")
        connection = self._connect()
        try:
            row = connection.execute("SELECT * FROM drugs WHERE sku = ?", (sku,)).fetchone()
            if row is None:
                raise NotFound('unknown drug "%s"' % sku)
            outputs = {
                "sku": row["sku"],
                "name": row["name"],
                "on_hand": row["on_hand"],
                "unit_price": row["unit_price"],
                "available": row["on_hand"] > 0,
            }
            return outputs, []
        finally:
            connection.close()

    def dispense_drug(self, payload):
        sku = validation.require_string(payload, "sku")
        quantity = require_positive_int(payload, "quantity", 1000)
        patient_mrn = validation.optional_string(payload, "patient_mrn")
        connection = self._connect()
        try:
            row = connection.execute("SELECT * FROM drugs WHERE sku = ?", (sku,)).fetchone()
            if row is None:
                raise NotFound('unknown drug "%s"' % sku)
            if row["on_hand"] < quantity:
                raise Conflict(
                    'insufficient stock for "%s": %d on hand, %d requested'
                    % (sku, row["on_hand"], quantity)
                )
            remaining = row["on_hand"] - quantity
            dispensed_at = now_iso()
            connection.execute(
                "UPDATE drugs SET on_hand = ?, updated_at = ? WHERE sku = ?",
                (remaining, dispensed_at, sku),
            )
            connection.execute(
                "INSERT INTO dispense_log (dispense_id, sku, quantity, patient_mrn,"
                " dispensed_at) VALUES (?, ?, ?, ?, ?)",
                (new_id("DSP"), sku, quantity, patient_mrn, dispensed_at),
            )
            connection.commit()
            outputs = {"dispensed": True, "remaining": remaining, "dispensed_at": dispensed_at}
            effects = [{"variable": "Drug.dispensed", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def replenish_stock(self, payload):
        sku = validation.require_string(payload, "sku")
        quantity = require_positive_int(payload, "quantity", 10000)
        connection = self._connect()
        try:
            row = connection.execute("SELECT * FROM drugs WHERE sku = ?", (sku,)).fetchone()
            if row is None:
                raise NotFound('unknown drug "%s"' % sku)
            on_hand = row["on_hand"] + quantity
            connection.execute(
                "UPDATE drugs SET on_hand = ?, updated_at = ? WHERE sku = ?",
                (on_hand, now_iso(), sku),
            )
            connection.commit()
            outputs = {"sku": sku, "on_hand": on_hand}
            effects = [{"variable": "Stock.available", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    # ---- listings used by the UI ----

    def list_drugs(self, query=None):
        connection = self._connect()
        try:
            if query:
                like = "%%%s%%" % query
                rows = connection.execute(
                    "SELECT * FROM drugs WHERE sku LIKE ? OR name LIKE ? ORDER BY sku",
                    (like, like),
                ).fetchall()
            else:
                rows = connection.execute("SELECT * FROM drugs ORDER BY sku").fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def list_dispenses(self, limit=20):
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT * FROM dispense_log ORDER BY dispensed_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def summary_counts(self):
        connection = self._connect()
        try:
            return {
                "drugs": connection.execute("SELECT COUNT(*) FROM drugs").fetchone()[0],
                "units_on_hand": connection.execute(
                    "SELECT COALESCE(SUM(on_hand), 0) FROM drugs"
                ).fetchone()[0],
                "dispenses": connection.execute("SELECT COUNT(*) FROM dispense_log").fetchone()[0],
            }
        finally:
            connection.close()
