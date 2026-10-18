"""Seeds the appointment queue with a small demonstration dataset.

Idempotent: when the tickets table already has rows the seed leaves the database untouched.
Every insertion goes through the same capability service functions the HTTP layer calls.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402

SEED_TICKETS = [
    {"patient_mrn": "MRN-1001", "reason": "Fever", "priority": "NORMAL"},
    {"patient_mrn": "MRN-1002", "reason": "Chest pain", "priority": "EMERGENCY"},
    {"patient_mrn": "MRN-1003", "reason": "Follow up", "priority": "LOW"},
]


def main():
    app = create_app()
    service = app.extensions["service"]
    counts = service.summary_counts()
    if counts["tickets"] > 0:
        print("database already seeded: %d tickets" % counts["tickets"])
        return
    created = []
    for ticket in SEED_TICKETS:
        outputs, _effects = service.create_ticket(ticket)
        created.append(outputs["ticket_id"])
        print("created ticket %d for %s" % (outputs["ticket_no"], ticket["patient_mrn"]))
    service.update_triage(
        {"ticket_id": created[1], "priority": "EMERGENCY", "notes": "Triaged on arrival"}
    )
    print("triaged ticket %s as EMERGENCY" % created[1])
    print("seed complete: %s" % service.summary_counts())


if __name__ == "__main__":
    main()
