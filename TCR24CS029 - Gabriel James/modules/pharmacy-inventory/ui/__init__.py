"""Server rendered user interface of the pharmacy inventory module.

Pages are plain templates over local static assets; the actionable forms submit through the same
JSON capability endpoints the gateway uses, so the screens and the machine interface cannot
drift apart.
"""

import os

from flask import Blueprint, jsonify, render_template, request

from services.errors import ApiError

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

    @blueprint.get("/ui/drugs")
    def drugs():
        query = request.args.get("q", "").strip()
        return render_template(
            "drugs.html",
            drugs=service.list_drugs(query or None),
            dispenses=service.list_dispenses(),
            query=query,
        )

    @blueprint.get("/ui/dispense")
    def dispense():
        return render_template("dispense.html", drugs=service.list_drugs())

    @blueprint.post("/ui/dispense")
    def dispense_submit():
        payload = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
        if not isinstance(payload, dict):
            payload = {}
        # A browser form sends every value as text; the JSON client sends a number already.
        if isinstance(payload.get("quantity"), str):
            try:
                payload["quantity"] = int(payload["quantity"])
            except ValueError:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "capability": "PH-Form",
                            "error": 'input "quantity" must be an integer',
                        }
                    ),
                    400,
                )
        try:
            outputs, effects = service.dispense_drug(payload)
        except ApiError as error:
            return (
                jsonify({"status": "error", "capability": "PH-Form", "error": str(error)}),
                error.status,
            )
        return jsonify(
            {
                "status": "ok",
                "capability": "PH-Form",
                "outputs": outputs,
                "effects": effects,
                "state": service.state_snapshot(),
                "trace": ["PH-Form submitted through /ui/dispense"],
            }
        )

    @blueprint.get("/ui/capabilities")
    def capabilities():
        return render_template("capabilities.html", spec=spec)

    return blueprint
