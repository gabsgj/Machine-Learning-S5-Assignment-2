"""Module tests for the point of sale billing module.

Every test runs against a fresh temporary SQLite database created through create_app, so the
suite never touches the demonstration data and the tests can run in any order.
"""

import json
import os
import sys

import pytest

MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, MODULE_DIR)

from app import create_app  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "billing.db"))
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def call(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def generate(client, amount=42.5, mrn="MRN-1"):
    response = call(
        client, "/api/generate_invoice", {"patient_mrn": mrn, "amount": amount, "description": "Fee"}
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["outputs"]["invoice_id"]


def test_health_reports_module_identity(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok"
    assert body["module"] == "pos-billing"
    assert body["port"] == 5005


def test_spec_matches_the_implemented_routes(client):
    spec = client.get("/spec").get_json()
    assert spec["module"]["module_id"] == "pos-billing"
    assert len(spec["capabilities"]) == 5
    api_endpoints = {
        capability["mechanism"]["endpoint"]
        for capability in spec["capabilities"]
        if capability["mechanism"]["kind"] == "API"
    }
    registered = {rule.rule for rule in client.application.url_map.iter_rules()}
    assert api_endpoints.issubset(registered), api_endpoints - registered
    declared = {variable["name"] for variable in spec["state_schema"]}
    for capability in spec["capabilities"]:
        assert capability["mechanism"]["kind"] == capability["type"]
        for effect in capability["effects"]:
            assert effect["variable"] in declared
        for precondition in capability["preconditions"]:
            assert precondition["variable"] in declared


def test_empty_state_snapshot(client):
    state = client.get("/state").get_json()["state"]
    assert state == {
        "Invoice.generated": False,
        "Invoice.paid": False,
        "Invoice.amount": 0.0,
        "Notification.sent": False,
    }


def test_generate_invoice_validates_inputs(client):
    invoice_id = generate(client, 42.5)
    assert invoice_id.startswith("INV-")
    state = client.get("/state").get_json()["state"]
    assert state["Invoice.generated"] is True
    assert state["Invoice.amount"] == 42.5

    missing = call(client, "/api/generate_invoice", {"patient_mrn": "MRN-1"})
    assert missing.status_code == 400
    assert "amount" in missing.get_json()["error"]

    negative = call(
        client, "/api/generate_invoice", {"patient_mrn": "MRN-1", "amount": -5}
    )
    assert negative.status_code == 400
    assert "amount" in negative.get_json()["error"]


def test_process_payment_cash_tender_rule(client):
    invoice_id = generate(client, 42.5)

    short = call(
        client,
        "/api/process_payment",
        {"invoice_id": invoice_id, "method": "CASH", "amount_tendered": 40.0},
    )
    assert short.status_code == 400
    assert "below the invoice amount" in short.get_json()["error"]

    paid = call(
        client,
        "/api/process_payment",
        {"invoice_id": invoice_id, "method": "CASH", "amount_tendered": 50.0},
    )
    assert paid.status_code == 200
    body = paid.get_json()
    assert body["outputs"]["paid"] is True
    assert body["outputs"]["change_due"] == 7.5
    state = client.get("/state").get_json()["state"]
    assert state["Invoice.paid"] is True
    assert state["Invoice.amount"] == 0.0

    again = call(client, "/api/process_payment", {"invoice_id": invoice_id, "method": "CARD"})
    assert again.status_code == 409
    assert "already paid" in again.get_json()["error"]

    unknown = call(client, "/api/process_payment", {"invoice_id": "INV-NOPE", "method": "CARD"})
    assert unknown.status_code == 404

    bad_method = call(
        client, "/api/process_payment", {"invoice_id": invoice_id, "method": "COUPON"}
    )
    assert bad_method.status_code == 400


def test_get_receipt_reflects_status(client):
    invoice_id = generate(client, 10.0)
    unpaid = call(client, "/api/get_receipt", {"invoice_id": invoice_id}).get_json()
    assert unpaid["outputs"]["paid"] is False
    assert "awaiting payment" in unpaid["outputs"]["receipt_text"]

    call(client, "/api/process_payment", {"invoice_id": invoice_id, "method": "TRANSFER"})
    paid = call(client, "/api/get_receipt", {"invoice_id": invoice_id}).get_json()
    assert paid["outputs"]["paid"] is True
    assert "paid" in paid["outputs"]["receipt_text"]

    unknown = call(client, "/api/get_receipt", {"invoice_id": "INV-NOPE"})
    assert unknown.status_code == 404


def test_send_receipt_notice_requires_payment(client):
    invoice_id = generate(client, 10.0)
    early = call(
        client, "/api/send_receipt_notice", {"invoice_id": invoice_id, "channel": "EMAIL"}
    )
    assert early.status_code == 409
    assert "not paid" in early.get_json()["error"]

    call(client, "/api/process_payment", {"invoice_id": invoice_id, "method": "CARD"})
    sent = call(
        client,
        "/api/send_receipt_notice",
        {"invoice_id": invoice_id, "channel": "SMS", "destination": "555-0100"},
    )
    assert sent.status_code == 200
    assert sent.get_json()["outputs"]["sent"] is True
    assert client.get("/state").get_json()["state"]["Notification.sent"] is True

    bad_channel = call(
        client, "/api/send_receipt_notice", {"invoice_id": invoice_id, "channel": "FAX"}
    )
    assert bad_channel.status_code == 400


def test_ui_pages_render_with_stable_element_ids(client):
    home = client.get("/ui/")
    assert home.status_code == 200
    assert 'id="module_title"' in home.get_data(as_text=True)

    new_page = client.get("/ui/invoices/new")
    text = new_page.get_data(as_text=True)
    assert 'id="invoice_form"' in text
    assert 'id="submit_button"' in text
    assert 'id="result_output"' in text

    invoices = client.get("/ui/invoices")
    assert 'id="invoice_table"' in invoices.get_data(as_text=True)

    payment = client.get("/ui/payments/new")
    payment_text = payment.get_data(as_text=True)
    assert 'id="payment_form"' in payment_text
    assert 'id="invoice_select"' in payment_text
    assert 'id="submit_button"' in payment_text

    capabilities = client.get("/ui/capabilities")
    assert "BILL-ProcessPayment" in capabilities.get_data(as_text=True)


def test_ui_payment_form_submission_uses_the_gui_capability(client):
    invoice_id = generate(client, 25.0, "MRN-FORM")
    response = client.post(
        "/ui/payments/new",
        data={"invoice_id": invoice_id, "method": "CASH", "amount_tendered": "30"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["capability"] == "BILL-Form"
    assert body["outputs"]["change_due"] == 5.0

    bad_tender = client.post(
        "/ui/payments/new",
        data={"invoice_id": invoice_id, "method": "CASH", "amount_tendered": "lots"},
    )
    assert bad_tender.status_code == 400


def test_invoice_detail_page_forms_and_missing_invoice(client):
    invoice_id = generate(client, 15.0, "MRN-DETAIL")
    detail = client.get("/ui/invoices/%s" % invoice_id)
    assert detail.status_code == 200
    text = detail.get_data(as_text=True)
    assert 'id="payment_form"' in text
    assert "MRN-DETAIL" in text

    call(client, "/api/process_payment", {"invoice_id": invoice_id, "method": "CARD"})
    paid_detail = client.get("/ui/invoices/%s" % invoice_id).get_data(as_text=True)
    assert 'id="notice_form"' in paid_detail

    missing = client.get("/ui/invoices/INV-NOPE")
    assert missing.status_code == 404


def test_served_pages_have_no_external_assets(client):
    for path in ["/ui/", "/ui/invoices", "/ui/invoices/new", "/ui/payments/new", "/ui/capabilities"]:
        text = client.get(path).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
    for asset in ["/ui/static/style.css", "/ui/static/app.js"]:
        text = client.get(asset).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
