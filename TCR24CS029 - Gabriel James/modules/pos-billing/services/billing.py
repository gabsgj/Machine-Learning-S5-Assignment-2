"""Capability implementations of the point of sale billing module.

Each method implements one capability from spec.json and returns (outputs, effects):

- outputs  the typed output values named by the capability specification
- effects  the state effects actually applied, in the specification effect format

Invoice.amount in the state snapshot is the outstanding amount: the sum of the amounts of the
invoices that are not yet paid. Cash payments must cover the invoice amount; the change due is
reported in the outputs. An unknown invoice is a 404, an already paid invoice is a 409 and a
missing or invalid input is a 400.
"""

import uuid
from datetime import datetime, timezone

from services import validation
from services.errors import BadInput, Conflict, NotFound

PAYMENT_METHODS = ["CARD", "CASH", "TRANSFER"]
NOTICE_CHANNELS = ["EMAIL", "SMS"]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix):
    return "%s-%s" % (prefix, uuid.uuid4().hex[:8].upper())


def require_amount(payload, name):
    value = payload.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BadInput('input "%s" must be a number' % name)
    value = float(value)
    if value <= 0 or value > 100000:
        raise BadInput('input "%s" must be between 0 and 100000' % name)
    return value


class BillingService:
    """Implements the BILL capability set against the module database."""

    def __init__(self, connection_factory):
        self._connect = connection_factory

    # ---- state ----

    def state_snapshot(self):
        """Reads the state variables declared in spec.json from the tables."""
        connection = self._connect()
        try:
            generated = connection.execute("SELECT COUNT(*) FROM invoices").fetchone()[0] > 0
            paid = (
                connection.execute(
                    "SELECT COUNT(*) FROM invoices WHERE status = 'paid'"
                ).fetchone()[0]
                > 0
            )
            outstanding = connection.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE status = 'generated'"
            ).fetchone()[0]
            notified = (
                connection.execute("SELECT COUNT(*) FROM receipt_notices").fetchone()[0] > 0
            )
            return {
                "Invoice.generated": generated,
                "Invoice.paid": paid,
                "Invoice.amount": float(outstanding),
                "Notification.sent": notified,
            }
        finally:
            connection.close()

    # ---- capabilities ----

    def generate_invoice(self, payload):
        patient_mrn = validation.require_string(payload, "patient_mrn")
        amount = require_amount(payload, "amount")
        description = validation.optional_string(payload, "description")
        connection = self._connect()
        try:
            invoice_id = new_id("INV")
            generated_at = now_iso()
            connection.execute(
                "INSERT INTO invoices (invoice_id, patient_mrn, amount, description, status,"
                " generated_at, paid_at, payment_method)"
                " VALUES (?, ?, ?, ?, 'generated', ?, NULL, NULL)",
                (invoice_id, patient_mrn, amount, description, generated_at),
            )
            connection.commit()
            outputs = {"invoice_id": invoice_id, "amount": amount, "generated_at": generated_at}
            effects = [{"variable": "Invoice.generated", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def process_payment(self, payload):
        invoice_id = validation.require_string(payload, "invoice_id")
        method = validation.require_enum(payload, "method", PAYMENT_METHODS)
        connection = self._connect()
        try:
            invoice = connection.execute(
                "SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,)
            ).fetchone()
            if invoice is None:
                raise NotFound('unknown invoice "%s"' % invoice_id)
            if invoice["status"] == "paid":
                raise Conflict('invoice "%s" is already paid' % invoice_id)
            tendered = payload.get("amount_tendered")
            if tendered is not None:
                if isinstance(tendered, bool) or not isinstance(tendered, (int, float)):
                    raise BadInput('input "amount_tendered" must be a number')
                tendered = float(tendered)
                if tendered < invoice["amount"]:
                    raise BadInput(
                        'input "amount_tendered" of %s is below the invoice amount %s'
                        % (tendered, invoice["amount"])
                    )
            else:
                tendered = invoice["amount"]
            change_due = round(tendered - invoice["amount"], 2)
            paid_at = now_iso()
            connection.execute(
                "UPDATE invoices SET status = 'paid', paid_at = ?, payment_method = ?"
                " WHERE invoice_id = ?",
                (paid_at, method, invoice_id),
            )
            connection.commit()
            outputs = {"paid": True, "paid_at": paid_at, "change_due": change_due}
            effects = [{"variable": "Invoice.paid", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def get_receipt(self, payload):
        invoice_id = validation.require_string(payload, "invoice_id")
        connection = self._connect()
        try:
            invoice = connection.execute(
                "SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,)
            ).fetchone()
            if invoice is None:
                raise NotFound('unknown invoice "%s"' % invoice_id)
            paid = invoice["status"] == "paid"
            receipt_text = (
                "Invoice %s for patient %s, amount %.2f, %s"
                % (
                    invoice["invoice_id"],
                    invoice["patient_mrn"],
                    invoice["amount"],
                    "paid on %s by %s" % (invoice["paid_at"], invoice["payment_method"])
                    if paid
                    else "awaiting payment",
                )
            )
            outputs = {
                "receipt_text": receipt_text,
                "amount": invoice["amount"],
                "paid": paid,
            }
            return outputs, []
        finally:
            connection.close()

    def send_receipt_notice(self, payload):
        invoice_id = validation.require_string(payload, "invoice_id")
        channel = validation.require_enum(payload, "channel", NOTICE_CHANNELS)
        destination = validation.optional_string(payload, "destination")
        connection = self._connect()
        try:
            invoice = connection.execute(
                "SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,)
            ).fetchone()
            if invoice is None:
                raise NotFound('unknown invoice "%s"' % invoice_id)
            if invoice["status"] != "paid":
                raise Conflict('invoice "%s" is not paid yet' % invoice_id)
            sent_at = now_iso()
            connection.execute(
                "INSERT INTO receipt_notices (notice_id, invoice_id, channel, destination,"
                " sent_at) VALUES (?, ?, ?, ?, ?)",
                (new_id("NOT"), invoice_id, channel, destination, sent_at),
            )
            connection.commit()
            outputs = {"sent": True, "sent_at": sent_at}
            effects = [{"variable": "Notification.sent", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    # ---- listings used by the UI ----

    def list_invoices(self, query=None):
        connection = self._connect()
        try:
            if query:
                like = "%%%s%%" % query
                rows = connection.execute(
                    "SELECT * FROM invoices WHERE patient_mrn LIKE ? OR invoice_id LIKE ?"
                    " ORDER BY generated_at DESC",
                    (like, like),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM invoices ORDER BY generated_at DESC"
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def invoice_detail(self, invoice_id):
        connection = self._connect()
        try:
            invoice = connection.execute(
                "SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,)
            ).fetchone()
            if invoice is None:
                raise NotFound('unknown invoice "%s"' % invoice_id)
            notices = connection.execute(
                "SELECT * FROM receipt_notices WHERE invoice_id = ? ORDER BY sent_at DESC",
                (invoice_id,),
            ).fetchall()
            return {"invoice": dict(invoice), "notices": [dict(row) for row in notices]}
        finally:
            connection.close()

    def list_notices(self, limit=20):
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT * FROM receipt_notices ORDER BY sent_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def summary_counts(self):
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT status, COUNT(*) AS count, COALESCE(SUM(amount), 0) AS amount"
                " FROM invoices GROUP BY status"
            ).fetchall()
            counts = {"invoices": 0, "paid": 0, "outstanding_amount": 0.0}
            for row in rows:
                counts["invoices"] += row["count"]
                if row["status"] == "paid":
                    counts["paid"] = row["count"]
                else:
                    counts["outstanding_amount"] = float(row["amount"])
            counts["notices"] = connection.execute(
                "SELECT COUNT(*) FROM receipt_notices"
            ).fetchone()[0]
            return counts
        finally:
            connection.close()
