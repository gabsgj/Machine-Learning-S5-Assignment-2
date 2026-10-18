"""Module tests for the legacy laboratory service.

Every test runs against a fresh temporary SQLite database created through create_app, so the
suite never touches the demonstration data and the tests can run in any order. The test
catalogue is reference data, installed by the fixture for the tests that need it.
"""

import json
import os
import sys

import pytest

MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, MODULE_DIR)

from app import create_app  # noqa: E402
from db import connect  # noqa: E402

CATALOGUE = [
    ("CBC", "Complete blood count", "10^9/L", 4.0, 11.0),
    ("GLU", "Fasting glucose", "mmol/L", 3.9, 5.5),
]


@pytest.fixture()
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "lab.db"))
    app.config["TESTING"] = True
    connection = connect(app.extensions["db_path"])
    try:
        for test_code, name, unit, ref_low, ref_high in CATALOGUE:
            connection.execute(
                "INSERT INTO test_catalogue (test_code, name, unit, ref_low, ref_high)"
                " VALUES (?, ?, ?, ?, ?)",
                (test_code, name, unit, ref_low, ref_high),
            )
        connection.commit()
    finally:
        connection.close()
    with app.test_client() as test_client:
        yield test_client


def call(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def order(client, mrn="MRN-1", test_code="GLU", urgency=None):
    payload = {"patient_mrn": mrn, "test_code": test_code}
    if urgency is not None:
        payload["urgency_level"] = urgency
    response = call(client, "/api/order_test", payload)
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["outputs"]["lab_order_id"]


def test_health_reports_module_identity(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok"
    assert body["module"] == "legacy-lab-service"
    assert body["port"] == 5006


def test_spec_matches_the_implemented_routes(client):
    spec = client.get("/spec").get_json()
    assert spec["module"]["module_id"] == "legacy-lab-service"
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
    assert state == {"Lab.ordered": False, "Sample.received": False, "Lab.resulted": False}


def test_order_test_validates_catalogue_and_inputs(client):
    lab_order_id = order(client, "MRN-1", "GLU", "STAT")
    assert lab_order_id.startswith("LAB-")
    state = client.get("/state").get_json()["state"]
    assert state["Lab.ordered"] is True

    unknown_code = call(
        client, "/api/order_test", {"patient_mrn": "MRN-1", "test_code": "HBA1C"}
    )
    assert unknown_code.status_code == 404
    assert "unknown test code" in unknown_code.get_json()["error"]

    missing = call(client, "/api/order_test", {"test_code": "GLU"})
    assert missing.status_code == 400
    assert "patient_mrn" in missing.get_json()["error"]

    bad_urgency = call(
        client,
        "/api/order_test",
        {"patient_mrn": "MRN-1", "test_code": "GLU", "urgency_level": "SOMEDAY"},
    )
    assert bad_urgency.status_code == 400
    assert "urgency_level" in bad_urgency.get_json()["error"]


def test_workflow_order_receive_result(client):
    lab_order_id = order(client)

    early_result = call(
        client, "/api/enter_result", {"lab_order_id": lab_order_id, "result_value": 5.4}
    )
    assert early_result.status_code == 409
    assert "no received sample" in early_result.get_json()["error"]

    received = call(
        client,
        "/api/receive_sample",
        {"lab_order_id": lab_order_id, "sample_label": "Tube 7"},
    )
    assert received.status_code == 200
    assert received.get_json()["outputs"]["received"] is True
    assert client.get("/state").get_json()["state"]["Sample.received"] is True

    twice = call(client, "/api/receive_sample", {"lab_order_id": lab_order_id})
    assert twice.status_code == 409

    resulted = call(
        client,
        "/api/enter_result",
        {"lab_order_id": lab_order_id, "result_value": 5.4, "unit": "mmol/L"},
    )
    assert resulted.status_code == 200
    assert resulted.get_json()["outputs"]["resulted"] is True
    state = client.get("/state").get_json()["state"]
    assert state["Lab.resulted"] is True

    again = call(
        client, "/api/enter_result", {"lab_order_id": lab_order_id, "result_value": 6.0}
    )
    assert again.status_code == 409
    assert "already has a result" in again.get_json()["error"]

    unknown = call(
        client, "/api/receive_sample", {"lab_order_id": "LAB-NOPE"}
    )
    assert unknown.status_code == 404

    bad_value = call(
        client, "/api/enter_result", {"lab_order_id": lab_order_id, "result_value": "high"}
    )
    assert bad_value.status_code == 400


def test_get_report_before_and_after_result(client):
    lab_order_id = order(client, "MRN-REPORT", "CBC")
    early = call(client, "/api/get_report", {"lab_order_id": lab_order_id}).get_json()
    assert early["outputs"]["resulted"] is False
    assert "no result yet" in early["outputs"]["report_text"]
    assert early["outputs"]["patient_mrn"] == "MRN-REPORT"
    assert early["outputs"]["test_code"] == "CBC"

    call(client, "/api/receive_sample", {"lab_order_id": lab_order_id})
    call(client, "/api/enter_result", {"lab_order_id": lab_order_id, "result_value": 7.7})
    final = call(client, "/api/get_report", {"lab_order_id": lab_order_id}).get_json()
    assert final["outputs"]["resulted"] is True
    assert "7.70" in final["outputs"]["report_text"]
    assert "reference 4.00 to 11.00" in final["outputs"]["report_text"]

    unknown = call(client, "/api/get_report", {"lab_order_id": "LAB-NOPE"})
    assert unknown.status_code == 404


def test_ui_pages_render_with_stable_element_ids(client):
    home = client.get("/ui/")
    assert home.status_code == 200
    assert 'id="module_title"' in home.get_data(as_text=True)

    new_page = client.get("/ui/orders/new")
    text = new_page.get_data(as_text=True)
    assert 'id="order_form"' in text
    assert 'id="patient_mrn_input"' in text
    assert 'id="test_code_select"' in text
    assert 'id="urgency_select"' in text
    assert 'id="submit_button"' in text
    assert 'id="result_output"' in text

    orders = client.get("/ui/orders")
    assert 'id="order_table"' in orders.get_data(as_text=True)

    capabilities = client.get("/ui/capabilities")
    assert "LAB-OrderTest" in capabilities.get_data(as_text=True)


def test_ui_form_submission_uses_the_gui_capability(client):
    response = client.post(
        "/ui/orders/new",
        data={"patient_mrn": "MRN-FORM", "test_code": "GLU", "urgency_level": "STAT"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["capability"] == "LAB-Form"
    listing = client.get("/ui/orders").get_data(as_text=True)
    assert "MRN-FORM" in listing
    assert "STAT" in listing


def test_order_detail_page_workflow(client):
    lab_order_id = order(client, "MRN-DETAIL", "GLU", "URGENT")
    detail = client.get("/ui/orders/%s" % lab_order_id).get_data(as_text=True)
    assert 'id="receive_form"' in detail
    assert "MRN-DETAIL" in detail

    call(client, "/api/receive_sample", {"lab_order_id": lab_order_id})
    received_detail = client.get("/ui/orders/%s" % lab_order_id).get_data(as_text=True)
    assert 'id="result_form"' in received_detail

    call(client, "/api/enter_result", {"lab_order_id": lab_order_id, "result_value": 4.4})
    resulted_detail = client.get("/ui/orders/%s" % lab_order_id).get_data(as_text=True)
    assert 'id="report_output"' in resulted_detail

    missing = client.get("/ui/orders/LAB-NOPE")
    assert missing.status_code == 404


def test_served_pages_have_no_external_assets(client):
    for path in ["/ui/", "/ui/orders", "/ui/orders/new", "/ui/capabilities"]:
        text = client.get(path).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
    for asset in ["/ui/static/style.css", "/ui/static/app.js"]:
        text = client.get(asset).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
