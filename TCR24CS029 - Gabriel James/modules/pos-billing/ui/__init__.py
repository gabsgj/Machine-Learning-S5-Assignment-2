"""Server rendered user interface of the point of sale billing module.

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

    @blueprint.get("/ui/invoices")
    def invoices():
        query = request.args.get("q", "").strip()
        return render_template(
            "invoices.html",
            invoices=service.list_invoices(query or None),
            query=query,
        )

    @blueprint.get("/ui/invoices/new")
    def invoice_new():
        return render_template("invoice_new.html")

    @blueprint.get("/ui/invoices/<invoice_id>")
    def invoice_detail(invoice_id):
        try:
            detail = service.invoice_detail(invoice_id)
        except NotFound:
            return (
                render_template("not_found.html", subject="invoice", identifier=invoice_id),
                404,
            )
        return render_template(
            "invoice_detail.html",
            invoice=detail["invoice"],
            notices=detail["notices"],
            payment_methods=["CARD", "CASH", "TRANSFER"],
            channels=["EMAIL", "SMS"],
        )

    @blueprint.get("/ui/payments/new")
    def payment_new():
        return render_template(
            "payment_new.html",
            invoices=service.list_invoices(),
            payment_methods=["CARD", "CASH", "TRANSFER"],
        )

    @blueprint.post("/ui/payments/new")
    def payment_new_submit():
        payload = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
        if not isinstance(payload, dict):
            payload = {}
        # A browser form sends every value as text; the JSON client sends numbers already.
        if isinstance(payload.get("amount_tendered"), str):
            text = payload["amount_tendered"].strip()
            if text == "":
                payload.pop("amount_tendered")
            else:
                try:
                    payload["amount_tendered"] = float(text)
                except ValueError:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "capability": "BILL-Form",
                                "error": 'input "amount_tendered" must be a number',
                            }
                        ),
                        400,
                    )
        try:
            outputs, effects = service.process_payment(payload)
        except ApiError as error:
            return (
                jsonify({"status": "error", "capability": "BILL-Form", "error": str(error)}),
                error.status,
            )
        return jsonify(
            {
                "status": "ok",
                "capability": "BILL-Form",
                "outputs": outputs,
                "effects": effects,
                "state": service.state_snapshot(),
                "trace": ["BILL-Form submitted through /ui/payments/new"],
            }
        )

    @blueprint.get("/ui/capabilities")
    def capabilities():
        return render_template("capabilities.html", spec=spec)

    return blueprint
