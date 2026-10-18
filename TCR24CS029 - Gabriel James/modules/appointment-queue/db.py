"""SQLite access for the appointment queue module.

The module owns exactly one SQLite database file, opened in WAL mode so the gateway, the
dashboard and a direct database client can read while a capability call writes. Foreign keys and
a busy timeout are enabled on every connection.

Queue state is derived from the tickets table: the queue holds the tickets with open = 1.
"""

import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    ticket_no INTEGER NOT NULL UNIQUE,
    patient_mrn TEXT NOT NULL,
    reason TEXT,
    priority TEXT NOT NULL,
    triaged INTEGER NOT NULL DEFAULT 0,
    open INTEGER NOT NULL DEFAULT 1,
    desk TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    called_at TEXT,
    closed_at TEXT
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
