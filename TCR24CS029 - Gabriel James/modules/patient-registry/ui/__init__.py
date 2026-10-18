"""Server rendered user interface of the patient registry module.

Pages are plain templates over local static assets; the actionable forms submit through the
same JSON capability endpoints the gateway uses, so the screens and the machine interface cannot
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

    def capability_index():
        return {item["id"]: item for item in spec["capabilities"]}

    @blueprint.get("/")
    @blueprint.get("/ui/")
    def home():
        return render_template(
            "home.html",
            spec=spec,
            counts=service.summary_counts(),
        )

    @blueprint.get("/ui/patients")
    def patients():
        query = request.args.get("q", "").strip()
        return render_template(
            "patients.html",
            patients=service.list_patients(query or None),
            query=query,
        )

    @blueprint.get("/ui/patients/new")
    def patient_new():
        return render_template("patient_new.html", capabilities=capability_index())

    @blueprint.post("/ui/patients/new")
    def patient_new_submit():
        payload = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
        try:
            outputs, effects = service.register_patient(payload)
        except ApiError as error:
            return (
                jsonify({"status": "error", "capability": "PR-Form", "error": str(error)}),
                error.status,
            )
        return jsonify(
            {
                "status": "ok",
                "capability": "PR-Form",
                "outputs": outputs,
                "effects": effects,
                "state": service.state_snapshot(),
                "trace": ["PR-Form submitted through /ui/patients/new"],
            }
        )

    @blueprint.get("/ui/patients/<patient_id>")
    def patient_detail(patient_id):
        try:
            detail = service.patient_detail(patient_id)
        except NotFound:
            return render_template("not_found.html", subject="patient", identifier=patient_id), 404
        return render_template(
            "patient_detail.html",
            patient=detail["patient"],
            admissions=detail["admissions"],
            allergies=detail["allergies"],
        )

    @blueprint.get("/ui/capabilities")
    def capabilities():
        return render_template("capabilities.html", spec=spec)

    return blueprint
