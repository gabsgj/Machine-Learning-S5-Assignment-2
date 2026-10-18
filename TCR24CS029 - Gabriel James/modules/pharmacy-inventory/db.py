"""SQLite access for the pharmacy inventory module.

The module owns exactly one SQLite database file, opened in WAL mode so the gateway, the
dashboard and a direct database client can read while a capability call writes. Foreign keys and
a busy timeout are enabled on every connection.
"""

import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS drugs (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    on_hand INTEGER NOT NULL DEFAULT 0,
    unit_price REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dispense_log (
    dispense_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL REFERENCES drugs(sku),
    quantity INTEGER NOT NULL,
    patient_mrn TEXT,
    dispensed_at TEXT NOT NULL
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
