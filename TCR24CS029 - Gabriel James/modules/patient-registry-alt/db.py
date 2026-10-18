"""SQLite access for the alternate patient registry module.

The module owns exactly one SQLite database file, opened in WAL mode so the gateway, the
dashboard, an adapter process and a direct database client can read while a capability call
writes. Foreign keys and a busy timeout are enabled on every connection.

The vocabulary of this module is the legacy registration vocabulary pat_reg, pat_no, pat_name.
The patients table backs the HTTP capabilities; the pat_rows table backs the DATABASE capability
PA-RowWrite, a single row insert executed by the adapter SQLite transport rather than by HTTP.
"""

import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
    pat_reg TEXT PRIMARY KEY,
    pat_no TEXT NOT NULL UNIQUE,
    pat_name TEXT NOT NULL,
    verified INTEGER NOT NULL DEFAULT 0,
    registered_at TEXT NOT NULL,
    verified_at TEXT
);

CREATE TABLE IF NOT EXISTS pat_rows (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pat_no TEXT NOT NULL,
    pat_name TEXT NOT NULL
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
