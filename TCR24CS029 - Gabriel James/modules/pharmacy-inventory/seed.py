"""Seeds the pharmacy inventory with a small demonstration catalogue.

Idempotent: when the drugs table already has rows the seed leaves the database untouched.
Every insertion goes through the same capability service functions the HTTP layer calls.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402

SEED_DRUGS = [
    {"sku": "AMOX-500", "name": "Amoxicillin 500 mg", "unit_price": 0.35, "initial_quantity": 120},
    {"sku": "PARA-500", "name": "Paracetamol 500 mg", "unit_price": 0.08, "initial_quantity": 400},
    {"sku": "SALB-100", "name": "Salbutamol inhaler 100 mcg", "unit_price": 4.2, "initial_quantity": 25},
]


def main():
    app = create_app()
    service = app.extensions["service"]
    counts = service.summary_counts()
    if counts["drugs"] > 0:
        print("database already seeded: %d catalogue entries" % counts["drugs"])
        return
    for drug in SEED_DRUGS:
        outputs, _effects = service.register_drug(drug)
        print("registered %s with %d units" % (outputs["sku"], outputs["on_hand"]))
    outputs, _effects = service.dispense_drug({"sku": "PARA-500", "quantity": 20, "patient_mrn": "MRN-1002"})
    print("dispensed 20 units of PARA-500, %d remaining" % outputs["remaining"])
    print("seed complete: %s" % service.summary_counts())


if __name__ == "__main__":
    main()
