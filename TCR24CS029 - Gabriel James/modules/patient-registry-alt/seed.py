"""Seeds the alternate patient registry with a small demonstration dataset.

Idempotent: when the patients table already has rows the seed leaves the database untouched.
Registrations go through the same capability service functions the HTTP layer calls; the
pat_rows row mirrors what the adapter SQLite transport writes for the PA-RowWrite capability.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from db import connect  # noqa: E402


def main():
    app = create_app()
    service = app.extensions["service"]
    counts = service.summary_counts()
    if counts["patients"] > 0:
        print("database already seeded: %d patients" % counts["patients"])
        return
    first, _effects = service.register_pat({"pat_no": "P-1001", "pat_name": "Ada Lovelace"})
    print("registered %s as %s" % (first["pat_no"], first["pat_reg"]))
    second, _effects = service.register_pat({"pat_no": "P-1002", "pat_name": "Grace Hopper"})
    print("registered %s as %s" % (second["pat_no"], second["pat_reg"]))
    service.verify_pat({"pat_reg": first["pat_reg"]})
    print("verified %s" % first["pat_reg"])
    connection = connect(app.extensions["db_path"])
    try:
        cursor = connection.execute(
            "INSERT INTO pat_rows (pat_no, pat_name) VALUES (?, ?)",
            ("P-1003", "Katherine Johnson"),
        )
        connection.commit()
        print("wrote pat_rows row %d" % cursor.lastrowid)
    finally:
        connection.close()
    print("seed complete: %s" % service.summary_counts())


if __name__ == "__main__":
    main()
