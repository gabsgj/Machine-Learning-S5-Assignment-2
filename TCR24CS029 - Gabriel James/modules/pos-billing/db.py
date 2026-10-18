"""SQLite access for the point of sale billing module.

The module owns exactly one SQLite database file, opened in WAL mode so the gateway, the
dashboard and a direct database client can read while a capability call writes. Foreign keys and
a busy timeout are enabled on every connection.
"""

import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id TEXT PRIMARY KEY,
    patient_mrn TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'generated',
    generated_at TEXT NOT NULL,
    paid_at TEXT,
    payment_method TEXT
);

CREATE TABLE IF NOT EXISTS receipt_notices (
    notice_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL REFERENCES invoices(invoice_id),
    channel TEXT NOT NULL,
    destination TEXT,
    sent_at TEXT NOT NULL
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
