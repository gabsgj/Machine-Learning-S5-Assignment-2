"""SQLite access for the outpatient department electronic health record module.

The module owns exactly one SQLite database file, opened in WAL mode so the gateway, the
dashboard and a direct database client can read while a capability call writes. Foreign keys and
a busy timeout are enabled on every connection.

An encounter is active while its status is 'active'; the module allows one active encounter at a
time, matching the declared precondition of EHR-StartEncounter.
"""

import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS encounters (
    encounter_id TEXT PRIMARY KEY,
    patient_mrn TEXT NOT NULL,
    clinician TEXT NOT NULL,
    visit_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    summary TEXT,
    started_at TEXT NOT NULL,
    closed_at TEXT
);

CREATE TABLE IF NOT EXISTS vitals (
    vitals_id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL REFERENCES encounters(encounter_id),
    temperature_c REAL NOT NULL,
    heart_rate INTEGER NOT NULL,
    systolic INTEGER,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL REFERENCES encounters(encounter_id),
    drug TEXT NOT NULL,
    dose_mg REAL NOT NULL,
    instructions TEXT,
    issued_at TEXT NOT NULL
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
