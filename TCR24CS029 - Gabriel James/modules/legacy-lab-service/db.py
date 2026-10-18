"""SQLite access for the legacy laboratory service module.

The module owns exactly one SQLite database file, opened in WAL mode so the gateway, the
dashboard and a direct database client can read while a capability call writes. Foreign keys and
a busy timeout are enabled on every connection.

The laboratory workflow is ordered -> sample received -> resulted. The naming of the inputs
follows the legacy laboratory vocabulary of this module: patient_mrn, test_code, urgency_level.
"""

import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS test_catalogue (
    test_code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    ref_low REAL,
    ref_high REAL
);

CREATE TABLE IF NOT EXISTS lab_orders (
    lab_order_id TEXT PRIMARY KEY,
    patient_mrn TEXT NOT NULL,
    test_code TEXT NOT NULL REFERENCES test_catalogue(test_code),
    urgency_level TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ordered',
    sample_label TEXT,
    result_value REAL,
    result_unit TEXT,
    ordered_at TEXT NOT NULL,
    received_at TEXT,
    resulted_at TEXT
);
"""


def connect(path):
    """Opens one connection with the module's pragmas and row factory."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA foreign_keys=ON;")
    connection.execute("PRAGMA busy_timeout=5000;")
    return connection


def init_db(path):
    """Creates the schema when absent and returns a ready connection."""
    connection = connect(path)
    connection.executescript(SCHEMA)
    connection.commit()
    return connection
