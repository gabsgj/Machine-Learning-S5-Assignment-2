"""Seeds the outpatient EHR with a small demonstration dataset.

Idempotent: when the encounters table already has rows the seed leaves the database untouched.
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
    if counts["encounters"] > 0:
        print("database already seeded: %d encounters" % counts["encounters"])
        return
    outputs, _effects = service.start_encounter(
        {"patient_mrn": "MRN-1001", "clinician": "Dr Rivera", "visit_type": "CONSULTATION"}
    )
    encounter_id = outputs["encounter_id"]
    print("started encounter %s" % encounter_id)
    service.record_vitals(
        {
            "encounter_id": encounter_id,
            "temperature_c": 37.2,
            "heart_rate": 72,
            "systolic": 118,
        }
    )
    print("recorded vitals for %s" % encounter_id)
    service.issue_prescription(
        {
            "encounter_id": encounter_id,
            "drug": "Amoxicillin",
            "dose_mg": 500,
            "instructions": "Three times daily for seven days",
        }
    )
    print("issued a prescription for %s" % encounter_id)
    service.close_encounter(
        {"encounter_id": encounter_id, "summary": "Upper respiratory infection, resolved"}
    )
    print("closed encounter %s" % encounter_id)
    print("seed complete: %s" % service.summary_counts())


if __name__ == "__main__":
    main()
