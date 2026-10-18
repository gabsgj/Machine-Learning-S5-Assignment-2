"""Server rendered user interface of the alternate patient registry module.

Pages are plain templates over local static assets; the actionable forms submit through the same
JSON capability endpoints the gateway uses, so the screens and the machine interface cannot
drift apart. The screens keep the legacy vocabulary pat_reg, pat_no, pat_name.
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

    @blueprint.get("/ui/patients")
    def patients():
        query = request.args.get("q", "").strip()
        return render_template(
            "patients.html",
            patients=service.list_patients(query or None),
            query=query,
        )

    @blueprint.get("/ui/pat_reg/new")
    def pat_reg_new():
        return render_template("pat_reg_new.html")

    @blueprint.post("/ui/pat_reg/new")
    def pat_reg_new_submit():
        payload = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
        try:
            outputs, effects = service.register_pat(payload)
        except ApiError as error:
            return (
                jsonify({"status": "error", "capability": "PA-Form", "error": str(error)}),
                error.status,
            )
        return jsonify(
            {
                "status": "ok",
                "capability": "PA-Form",
                "outputs": outputs,
                "effects": effects,
                "state": service.state_snapshot(),
                "trace": ["PA-Form submitted through /ui/pat_reg/new"],
            }
        )

    @blueprint.get("/ui/patients/<pat_reg>")
    def patient_detail(pat_reg):
        try:
            patient = service.patient_detail(pat_reg)
        except NotFound:
            return (
                render_template(
                    "not_found.html", subject="patient registration", identifier=pat_reg
                ),
                404,
            )
        return render_template("patient_detail.html", patient=patient)

    @blueprint.get("/ui/capabilities")
    def capabilities():
        return render_template("capabilities.html", spec=spec)

    return blueprint
