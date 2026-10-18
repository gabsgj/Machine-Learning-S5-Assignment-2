"""Appointment queue module (port 5002).

Flask application implementing the capability set declared in spec.json. Every capability is a
POST endpoint that accepts a JSON object of named inputs and answers with the module response
convention:

  {"status": "ok", "capability": "...", "outputs": {...}, "effects": [...],
   "state": {...}, "trace": [...]}

  {"status": "error", "capability": "...", "error": "..."}   with 4xx on rejection

The state block reports the module state variables after the call, so the gateway and the
dashboard see the same snapshot through HTTP that the services compute from SQLite.
"""

import json
import os

from flask import Flask, jsonify, request

from db import connect, init_db
from services.errors import ApiError
from services.queue import QueueService
from ui import create_ui_blueprint

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# capability id, capability name, route path and service method.
CAPABILITY_ROUTES = [
    ("AQ-CreateTicket", "create_ticket", "/api/create_ticket", "create_ticket"),
    ("AQ-CallNext", "call_next_ticket", "/api/call_next_ticket", "call_next_ticket"),
    ("AQ-UpdateTriage", "update_triage", "/api/update_triage", "update_triage"),
    ("AQ-Cancel", "cancel_ticket", "/api/cancel_ticket", "cancel_ticket"),
]


def default_db_path():
    return os.path.join(MODULE_DIR, "data", "appointment_queue.db")


def load_spec():
    with open(os.path.join(MODULE_DIR, "spec.json"), "r", encoding="utf-8") as handle:
        return json.load(handle)


def create_app(db_path=None):
    app = Flask(__name__, static_folder=None)
    resolved_db = db_path or os.environ.get("CAREWEAVE_DB") or default_db_path()
    init_db(resolved_db)
    service = QueueService(lambda: connect(resolved_db))
    app.extensions["service"] = service
    app.extensions["db_path"] = resolved_db
    app.extensions["spec"] = load_spec()

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "module": "appointment-queue",
                "port": 5002,
                "database": os.path.relpath(resolved_db, MODULE_DIR),
            }
        )

    @app.get("/spec")
    def spec():
        return jsonify(app.extensions["spec"])

    @app.get("/state")
    def state():
        return jsonify(
            {"status": "ok", "module": "appointment-queue", "state": service.state_snapshot()}
        )

    def make_view(capability_id, method_name):
        def view():
            payload = request.get_json(silent=True)
            if payload is None:
                payload = {}
            if not isinstance(payload, dict):
                return (
                    jsonify(
                        {
                            "status": "error",
                            "capability": capability_id,
                            "error": "the request body must be a JSON object",
                        }
                    ),
                    400,
                )
            try:
                outputs, effects = getattr(service, method_name)(payload)
            except ApiError as error:
                return (
                    jsonify(
                        {"status": "error", "capability": capability_id, "error": str(error)}
                    ),
                    error.status,
                )
            return jsonify(
                {
                    "status": "ok",
                    "capability": capability_id,
                    "outputs": outputs,
                    "effects": effects,
                    "state": service.state_snapshot(),
                    "trace": ["%s executed" % capability_id],
                }
            )

        view.__name__ = "capability_%s" % method_name
        return view

    for capability_id, _name, path, method_name in CAPABILITY_ROUTES:
        app.add_url_rule(
            path,
            endpoint="capability_%s" % method_name,
            view_func=make_view(capability_id, method_name),
            methods=["POST"],
        )

    app.register_blueprint(create_ui_blueprint(service, app.extensions["spec"]))
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
