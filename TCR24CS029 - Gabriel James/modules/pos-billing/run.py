"""Launcher for the point of sale billing module.

Run from anywhere:

    /path/to/python run.py

Environment:
    CAREWEAVE_DB       overrides the SQLite database file
    CAREWEAVE_PORT     overrides the listening port (default 5005)
"""

import os
import seed

from app import create_app


def main():
    seed.main()  # idempotent demonstration data: a fresh checkout is usable immediately
    port = int(os.environ.get("CAREWEAVE_PORT", "5005"))
    app = create_app()
    app.run(host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
