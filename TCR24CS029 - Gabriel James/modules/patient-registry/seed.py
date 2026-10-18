"""Seeds the patient registry with a small demonstration dataset.

Idempotent: when the patients table already has rows the seed leaves the database untouched.
Every insertion goes through the same capability service functions the HTTP layer calls, so the
seeded state is reachable by the declared capabilities and nothing bypasses validation.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from services.errors import ApiError  # noqa: E402

SEED_PATIENTS = [
    {"mrn": "MRN-1001", "full_name": "Ada Lovelace", "date_of_birth": "1815-12-10"},
    {"mrn": "MRN-1002", "full_name": "Grace Hopper", "date_of_birth": "1906-12-09"},
    {"mrn": "MRN-1003", "full_name": "Alan Turing", "date_of_birth": "1912-06-23"},
]


def main():
    app = create_app()
    service = app.extensions["service"]
    counts = service.summary_counts()
    if counts["patients"] > 0:
        print("database already seeded: %d patients" % counts["patients"])
        return
    created = []
    for patient in SEED_PATIENTS:
        outputs, _effects = service.register_patient(patient)
        created.append(outputs["patient_id"])
        print("registered %s as %s" % (patient["mrn"], outputs["patient_id"]))
    try:
        service.admit_patient({"patient_id": created[0], "ward": "Ward A", "expected_stay_days": 3})
        print("admitted %s to Ward A" % created[0])
    except ApiError as error:
        print("admission skipped: %s" % error)
    try:
        service.flag_allergy(
            {"patient_id": created[1], "allergen": "Penicillin", "severity": "SEVERE"}
        )
        print("flagged Penicillin allergy for %s" % created[1])
    except ApiError as error:
        print("allergy skipped: %s" % error)
    print("seed complete: %s" % service.summary_counts())


if __name__ == "__main__":
    main()
