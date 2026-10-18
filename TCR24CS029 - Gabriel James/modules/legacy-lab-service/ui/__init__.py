"""Server rendered user interface of the legacy laboratory service module.

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

    @blueprint.get("/ui/orders")
    def orders():
        query = request.args.get("q", "").strip()
        return render_template(
            "orders.html", orders=service.list_orders(query or None), query=query
        )

    @blueprint.get("/ui/orders/new")
    def order_new():
        return render_template(
            "order_new.html",
            test_codes=service.list_test_codes(),
            urgency_levels=["ROUTINE", "URGENT", "STAT"],
        )

    @blueprint.post("/ui/orders/new")
    def order_new_submit():
        payload = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
        try:
            outputs, effects = service.order_test(payload)
        except ApiError as error:
            return (
                jsonify({"status": "error", "capability": "LAB-Form", "error": str(error)}),
                error.status,
            )
        return jsonify(
            {
                "status": "ok",
                "capability": "LAB-Form",
                "outputs": outputs,
                "effects": effects,
                "state": service.state_snapshot(),
                "trace": ["LAB-Form submitted through /ui/orders/new"],
            }
        )

    @blueprint.get("/ui/orders/<lab_order_id>")
    def order_detail(lab_order_id):
        try:
            detail = service.order_detail(lab_order_id)
        except NotFound:
            return (
                render_template("not_found.html", subject="lab order", identifier=lab_order_id),
                404,
            )
        return render_template(
            "order_detail.html",
            order=detail["order"],
            test=detail["test"],
        )

    @blueprint.get("/ui/capabilities")
    def capabilities():
        return render_template("capabilities.html", spec=spec)

    return blueprint
