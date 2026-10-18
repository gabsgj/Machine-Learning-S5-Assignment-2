"""Seeds the point of sale billing with a small demonstration dataset.

Idempotent: when the invoices table already has rows the seed leaves the database untouched.
Every insertion goes through the same capability service functions the HTTP layer calls.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402


def main():
    app = create_app()
    service = app.extensions["service"]
    counts = service.summary_counts()
    if counts["invoices"] > 0:
        print("database already seeded: %d invoices" % counts["invoices"])
        return
    first, _effects = service.generate_invoice(
        {"patient_mrn": "MRN-1001", "amount": 42.5, "description": "Consultation fee"}
    )
    print("generated invoice %s for 42.50" % first["invoice_id"])
    second, _effects = service.generate_invoice(
        {"patient_mrn": "MRN-1002", "amount": 13.75, "description": "Pharmacy dispense"}
    )
    print("generated invoice %s for 13.75" % second["invoice_id"])
    payment, _effects = service.process_payment(
        {"invoice_id": first["invoice_id"], "method": "CASH", "amount_tendered": 50.0}
    )
    print("paid %s with change due %.2f" % (first["invoice_id"], payment["change_due"]))
    notice, _effects = service.send_receipt_notice(
        {"invoice_id": first["invoice_id"], "channel": "EMAIL", "destination": "patient contact"}
    )
    print("sent receipt notice at %s" % notice["sent_at"])
    print("seed complete: %s" % service.summary_counts())


if __name__ == "__main__":
    main()
