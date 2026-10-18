"""Server rendered user interface of the appointment queue module.

Pages are plain templates over local static assets; the actionable forms submit through the same
JSON capability endpoints the gateway uses, so the screens and the machine interface cannot
drift apart.
"""

import os

from flask import Blueprint, jsonify, render_template, request

from services.errors import ApiError, NotFound

MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_ui_blueprint(service, spec):
    blueprint = Blueprint(
        "ui",
        __name__,
        template_folder=os.path.join(MODULE_DIR, "ui", "templates"),
        static_folder=os.path.join(MODULE_DIR, "ui", "static"),
        static_url_path="/ui/static",
    )

    @blueprint.get("/")
    @blueprint.get("/ui/")
    def home():
        return render_template("home.html", spec=spec, counts=service.summary_counts())

    @blueprint.get("/ui/tickets")
    def tickets():
        query = request.args.get("q", "").strip()
        return render_template(
            "tickets.html",
            tickets=service.list_tickets(query or None),
            query=query,
        )

    @blueprint.get("/ui/tickets/new")
    def ticket_new():
        return render_template("ticket_new.html", priorities=["LOW", "NORMAL", "HIGH", "EMERGENCY"])

    @blueprint.post("/ui/tickets/new")
    def ticket_new_submit():
        payload = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
        if payload.get("priority") == "":
            payload.pop("priority")
        try:
            outputs, effects = service.create_ticket(payload)
        except ApiError as error:
            return (
                jsonify({"status": "error", "capability": "AQ-Form", "error": str(error)}),
                error.status,
            )
        return jsonify(
            {
                "status": "ok",
                "capability": "AQ-Form",
                "outputs": outputs,
                "effects": effects,
                "state": service.state_snapshot(),
                "trace": ["AQ-Form submitted through /ui/tickets/new"],
            }
        )

    @blueprint.get("/ui/tickets/<ticket_id>")
    def ticket_detail(ticket_id):
        try:
            ticket = service.ticket_detail(ticket_id)
        except NotFound:
            return render_template("not_found.html", subject="ticket", identifier=ticket_id), 404
        return render_template(
            "ticket_detail.html",
            ticket=ticket,
            priorities=["LOW", "NORMAL", "HIGH", "EMERGENCY"],
        )

    @blueprint.get("/ui/capabilities")
    def capabilities():
        return render_template("capabilities.html", spec=spec)

    return blueprint
