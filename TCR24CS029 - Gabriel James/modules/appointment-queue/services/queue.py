"""Capability implementations of the appointment queue module.

Each method implements one capability from spec.json and returns (outputs, effects):

- outputs  the typed output values named by the capability specification
- effects  the state effects actually applied, in the specification effect format

The queue holds the tickets with open = 1. Call next selects the ticket with the highest
priority, oldest first within a priority, and reports the queue length through the state
snapshot. Failures raise the ApiError subclasses rendered by the HTTP layer.
"""

import uuid
from datetime import datetime, timezone

from services import validation
from services.errors import Conflict, NotFound

PRIORITIES = ["LOW", "NORMAL", "HIGH", "EMERGENCY"]
PRIORITY_RANK = "CASE priority WHEN 'EMERGENCY' THEN 3 WHEN 'HIGH' THEN 2 WHEN 'NORMAL' THEN 1 ELSE 0 END"


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix):
    return "%s-%s" % (prefix, uuid.uuid4().hex[:8].upper())


class QueueService:
    """Implements the AQ capability set against the module database."""

    def __init__(self, connection_factory):
        self._connect = connection_factory

    # ---- state ----

    def state_snapshot(self):
        """Reads the state variables declared in spec.json from the queue table."""
        connection = self._connect()
        try:
            queue_length = connection.execute(
                "SELECT COUNT(*) FROM tickets WHERE open = 1"
            ).fetchone()[0]
            open_ticket = queue_length > 0
            triaged = (
                connection.execute(
                    "SELECT COUNT(*) FROM tickets WHERE triaged = 1 AND open = 1"
                ).fetchone()[0]
                > 0
            )
            return {
                "Ticket.open": open_ticket,
                "Ticket.triaged": triaged,
                "Queue.length": queue_length,
            }
        finally:
            connection.close()

    # ---- capabilities ----

    def create_ticket(self, payload):
        patient_mrn = validation.require_string(payload, "patient_mrn")
        reason = validation.optional_string(payload, "reason")
        priority = validation.optional_enum(payload, "priority", PRIORITIES, "NORMAL")
        connection = self._connect()
        try:
            ticket_no = (
                connection.execute("SELECT COALESCE(MAX(ticket_no), 0) FROM tickets").fetchone()[0]
                + 1
            )
            ticket_id = new_id("TKT")
            created_at = now_iso()
            connection.execute(
                "INSERT INTO tickets (ticket_id, ticket_no, patient_mrn, reason, priority,"
                " triaged, open, desk, notes, created_at, called_at, closed_at)"
                " VALUES (?, ?, ?, ?, ?, 0, 1, NULL, NULL, ?, NULL, NULL)",
                (ticket_id, ticket_no, patient_mrn, reason, priority, created_at),
            )
            connection.commit()
            outputs = {"ticket_id": ticket_id, "ticket_no": ticket_no}
            effects = [
                {"variable": "Ticket.open", "op": "SET", "value": True},
                {"variable": "Queue.length", "op": "INCREMENT", "value": 1},
            ]
            return outputs, effects
        finally:
            connection.close()

    def call_next_ticket(self, payload):
        desk = validation.optional_string(payload, "desk")
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT ticket_id, patient_mrn, priority FROM tickets WHERE open = 1"
                " ORDER BY %s DESC, created_at ASC, ticket_no ASC LIMIT 1" % PRIORITY_RANK
            ).fetchone()
            if row is None:
                raise Conflict("the queue is empty: no open ticket to call")
            called_at = now_iso()
            connection.execute(
                "UPDATE tickets SET open = 0, desk = ?, called_at = ? WHERE ticket_id = ?",
                (desk, called_at, row["ticket_id"]),
            )
            connection.commit()
            outputs = {
                "ticket_id": row["ticket_id"],
                "patient_mrn": row["patient_mrn"],
                "priority": row["priority"],
                "called_at": called_at,
            }
            effects = [
                {"variable": "Ticket.open", "op": "SET", "value": False},
                {"variable": "Queue.length", "op": "DECREMENT", "value": 1},
            ]
            return outputs, effects
        finally:
            connection.close()

    def update_triage(self, payload):
        ticket_id = validation.require_string(payload, "ticket_id")
        priority = validation.require_enum(payload, "priority", PRIORITIES)
        notes = validation.optional_string(payload, "notes")
        connection = self._connect()
        try:
            ticket = connection.execute(
                "SELECT ticket_id, open FROM tickets WHERE ticket_id = ?", (ticket_id,)
            ).fetchone()
            if ticket is None:
                raise NotFound('unknown ticket "%s"' % ticket_id)
            if not ticket["open"]:
                raise Conflict('ticket "%s" is no longer in the queue' % ticket_id)
            connection.execute(
                "UPDATE tickets SET priority = ?, triaged = 1, notes = ? WHERE ticket_id = ?",
                (priority, notes, ticket_id),
            )
            connection.commit()
            outputs = {"updated": True, "ticket_id": ticket_id, "priority": priority}
            effects = [{"variable": "Ticket.triaged", "op": "SET", "value": True}]
            return outputs, effects
        finally:
            connection.close()

    def cancel_ticket(self, payload):
        ticket_id = validation.require_string(payload, "ticket_id")
        reason = validation.optional_string(payload, "reason")
        connection = self._connect()
        try:
            ticket = connection.execute(
                "SELECT ticket_id, open FROM tickets WHERE ticket_id = ?", (ticket_id,)
            ).fetchone()
            if ticket is None:
                raise NotFound('unknown ticket "%s"' % ticket_id)
            if not ticket["open"]:
                raise Conflict('ticket "%s" is already closed' % ticket_id)
            closed_at = now_iso()
            connection.execute(
                "UPDATE tickets SET open = 0, closed_at = ?, notes = COALESCE(?, notes)"
                " WHERE ticket_id = ?",
                (closed_at, reason, ticket_id),
            )
            connection.commit()
            outputs = {"cancelled": True, "closed_at": closed_at}
            effects = [
                {"variable": "Ticket.open", "op": "SET", "value": False},
                {"variable": "Queue.length", "op": "DECREMENT", "value": 1},
            ]
            return outputs, effects
        finally:
            connection.close()

    # ---- listings used by the UI ----

    def list_tickets(self, query=None):
        connection = self._connect()
        try:
            if query:
                like = "%%%s%%" % query
                rows = connection.execute(
                    "SELECT * FROM tickets WHERE patient_mrn LIKE ? OR reason LIKE ?"
                    " ORDER BY open DESC, %s DESC, ticket_no ASC" % PRIORITY_RANK,
                    (like, like),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM tickets ORDER BY open DESC, %s DESC, ticket_no ASC"
                    % PRIORITY_RANK
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def ticket_detail(self, ticket_id):
        connection = self._connect()
        try:
            ticket = connection.execute(
                "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)
            ).fetchone()
            if ticket is None:
                raise NotFound('unknown ticket "%s"' % ticket_id)
            return dict(ticket)
        finally:
            connection.close()

    def summary_counts(self):
        connection = self._connect()
        try:
            return {
                "tickets": connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
                "open_tickets": connection.execute(
                    "SELECT COUNT(*) FROM tickets WHERE open = 1"
                ).fetchone()[0],
                "triaged": connection.execute(
                    "SELECT COUNT(*) FROM tickets WHERE triaged = 1"
                ).fetchone()[0],
            }
        finally:
            connection.close()
