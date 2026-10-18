"""Server rendered user interface of the outpatient EHR module.

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

    @blueprint.get("/ui/encounters")
    def encounters():
        query = request.args.get("q", "").strip()
        return render_template(
            "encounters.html",
            encounters=service.list_encounters(query or None),
            query=query,
        )

    @blueprint.get("/ui/encounters/new")
    def encounter_new():
        return render_template(
            "encounter_new.html", visit_types=["CONSULTATION", "FOLLOW_UP", "EMERGENCY"]
        )

    @blueprint.post("/ui/encounters/new")
    def encounter_new_submit():
        payload = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
        try:
            outputs, effects = service.start_encounter(payload)
        except ApiError as error:
            return (
                jsonify({"status": "error", "capability": "EHR-Form", "error": str(error)}),
                error.status,
            )
        return jsonify(
            {
                "status": "ok",
                "capability": "EHR-Form",
                "outputs": outputs,
                "effects": effects,
                "state": service.state_snapshot(),
                "trace": ["EHR-Form submitted through /ui/encounters/new"],
            }
        )

    @blueprint.get("/ui/encounters/<encounter_id>")
    def encounter_detail(encounter_id):
        try:
            detail = service.encounter_detail(encounter_id)
        except NotFound:
            return (
                render_template("not_found.html", subject="encounter", identifier=encounter_id),
                404,
            )
        return render_template(
            "encounter_detail.html",
            encounter=detail["encounter"],
            vitals=detail["vitals"],
            prescriptions=detail["prescriptions"],
        )

    @blueprint.get("/ui/capabilities")
    def capabilities():
        return render_template("capabilities.html", spec=spec)

    return blueprint
