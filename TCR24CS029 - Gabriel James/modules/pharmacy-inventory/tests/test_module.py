"""Module tests for the pharmacy inventory.

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
    app = create_app(db_path=str(tmp_path / "pharmacy.db"))
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def call(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def register(client, sku="AMOX-500", quantity=100, price=0.35):
    response = call(
        client,
        "/api/register_drug",
        {"sku": sku, "name": "Amoxicillin 500 mg", "unit_price": price, "initial_quantity": quantity},
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["outputs"]


def test_health_reports_module_identity(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok"
    assert body["module"] == "pharmacy-inventory"
    assert body["port"] == 5004


def test_spec_matches_the_implemented_routes(client):
    spec = client.get("/spec").get_json()
    assert spec["module"]["module_id"] == "pharmacy-inventory"
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


def test_empty_state_snapshot(client):
    state = client.get("/state").get_json()["state"]
    assert state == {"Stock.available": False, "Stock.quantity": 0, "Drug.dispensed": False}


def test_register_drug_validates_and_rejects_duplicates(client):
    outputs = register(client, "AMOX-500", 100)
    assert outputs == {"sku": "AMOX-500", "name": "Amoxicillin 500 mg", "on_hand": 100}
    assert client.get("/state").get_json()["state"]["Stock.available"] is True
    assert client.get("/state").get_json()["state"]["Stock.quantity"] == 100

    duplicate = call(
        client,
        "/api/register_drug",
        {"sku": "AMOX-500", "name": "Other", "unit_price": 1.0},
    )
    assert duplicate.status_code == 409
    assert "already in the catalogue" in duplicate.get_json()["error"]

    bad_price = call(
        client, "/api/register_drug", {"sku": "X-1", "name": "X", "unit_price": -1}
    )
    assert bad_price.status_code == 400
    assert "unit_price" in bad_price.get_json()["error"]

    missing = call(client, "/api/register_drug", {"sku": "X-1", "unit_price": 1.0})
    assert missing.status_code == 400


def test_check_stock_reports_levels(client):
    register(client, "PARA-500", 250, 0.08)
    body = call(client, "/api/check_stock", {"sku": "PARA-500"}).get_json()
    assert body["status"] == "ok"
    assert body["outputs"]["on_hand"] == 250
    assert body["outputs"]["available"] is True
    assert body["outputs"]["unit_price"] == 0.08

    unknown = call(client, "/api/check_stock", {"sku": "NOPE"})
    assert unknown.status_code == 404
    assert "unknown drug" in unknown.get_json()["error"]


def test_dispense_decrements_stock_and_rejects_shortages(client):
    register(client, "AMOX-500", 30)
    dispensed = call(
        client, "/api/dispense_drug", {"sku": "AMOX-500", "quantity": 10, "patient_mrn": "MRN-1"}
    )
    assert dispensed.status_code == 200
    assert dispensed.get_json()["outputs"]["dispensed"] is True
    assert dispensed.get_json()["outputs"]["remaining"] == 20
    state = client.get("/state").get_json()["state"]
    assert state["Drug.dispensed"] is True
    assert state["Stock.quantity"] == 20

    shortage = call(client, "/api/dispense_drug", {"sku": "AMOX-500", "quantity": 21})
    assert shortage.status_code == 409
    assert "insufficient stock" in shortage.get_json()["error"]

    zero = call(client, "/api/dispense_drug", {"sku": "AMOX-500", "quantity": 0})
    assert zero.status_code == 400
    assert "quantity" in zero.get_json()["error"]

    unknown = call(client, "/api/dispense_drug", {"sku": "NOPE", "quantity": 1})
    assert unknown.status_code == 404


def test_replenish_adds_units(client):
    register(client, "SALB-100", 5, 4.2)
    body = call(client, "/api/replenish_stock", {"sku": "SALB-100", "quantity": 15}).get_json()
    assert body["status"] == "ok"
    assert body["outputs"]["on_hand"] == 20
    assert body["effects"] == [{"variable": "Stock.available", "op": "SET", "value": True}]
    unknown = call(client, "/api/replenish_stock", {"sku": "NOPE", "quantity": 5})
    assert unknown.status_code == 404
    bad = call(client, "/api/replenish_stock", {"sku": "SALB-100", "quantity": "many"})
    assert bad.status_code == 400


def test_ui_pages_render_with_stable_element_ids(client):
    home = client.get("/ui/")
    assert home.status_code == 200
    assert 'id="module_title"' in home.get_data(as_text=True)

    stock = client.get("/ui/drugs")
    text = stock.get_data(as_text=True)
    assert 'id="register_drug_form"' in text
    assert 'id="drug_table"' in text

    dispense = client.get("/ui/dispense")
    dispense_text = dispense.get_data(as_text=True)
    assert 'id="dispense_form"' in dispense_text
    assert 'id="submit_button"' in dispense_text
    assert 'id="result_output"' in dispense_text

    capabilities = client.get("/ui/capabilities")
    assert "PH-DispenseDrug" in capabilities.get_data(as_text=True)


def test_ui_register_and_dispense_forms_work(client):
    registered = client.post(
        "/api/register_drug",
        data=json.dumps(
            {
                "sku": "FORM-1",
                "name": "Form drug",
                "unit_price": 1.5,
                "initial_quantity": 12,
            }
        ),
        content_type="application/json",
    )
    assert registered.status_code == 200

    response = client.post(
        "/ui/dispense",
        data={"sku": "FORM-1", "quantity": "2", "patient_mrn": "MRN-FORM"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["capability"] == "PH-Form"
    assert body["outputs"]["remaining"] == 10

    bad_quantity = client.post("/ui/dispense", data={"sku": "FORM-1", "quantity": "lots"})
    assert bad_quantity.status_code == 400


def test_served_pages_have_no_external_assets(client):
    for path in ["/ui/", "/ui/drugs", "/ui/dispense", "/ui/capabilities"]:
        text = client.get(path).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
    for asset in ["/ui/static/style.css", "/ui/static/app.js"]:
        text = client.get(asset).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
