"""Seeds the legacy laboratory service with a small demonstration dataset.

Idempotent: when the catalogue or the order table already has rows the seed leaves the database
untouched. The test catalogue is reference data installed here directly; the orders are created
through the same capability service functions the HTTP layer calls.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from db import connect  # noqa: E402

CATALOGUE = [
    ("CBC", "Complete blood count", "10^9/L", 4.0, 11.0),
    ("GLU", "Fasting glucose", "mmol/L", 3.9, 5.5),
    ("CRP", "C reactive protein", "mg/L", 0.0, 5.0),
]


def main():
    app = create_app()
    service = app.extensions["service"]
    db_path = app.extensions["db_path"]
    connection = connect(db_path)
    try:
        for test_code, name, unit, ref_low, ref_high in CATALOGUE:
            connection.execute(
                "INSERT OR IGNORE INTO test_catalogue (test_code, name, unit, ref_low, ref_high)"
                " VALUES (?, ?, ?, ?, ?)",
                (test_code, name, unit, ref_low, ref_high),
            )
        connection.commit()
        catalogue_size = connection.execute(
            "SELECT COUNT(*) FROM test_catalogue"
        ).fetchone()[0]
    finally:
        connection.close()
    print("test catalogue holds %d codes" % catalogue_size)

    counts = service.summary_counts()
    if counts["orders"] > 0:
        print("database already seeded: %d lab orders" % counts["orders"])
        return
    first, _effects = service.order_test(
        {"patient_mrn": "MRN-1001", "test_code": "GLU", "urgency_level": "URGENT"}
    )
    print("ordered %s for MRN-1001" % first["lab_order_id"])
    service.receive_sample({"lab_order_id": first["lab_order_id"], "sample_label": "Tube 1"})
    service.enter_result({"lab_order_id": first["lab_order_id"], "result_value": 5.1})
    print("received and resulted %s" % first["lab_order_id"])
    second, _effects = service.order_test({"patient_mrn": "MRN-1002", "test_code": "CBC"})
    print("ordered %s for MRN-1002" % second["lab_order_id"])
    print("seed complete: %s" % service.summary_counts())


if __name__ == "__main__":
    main()
