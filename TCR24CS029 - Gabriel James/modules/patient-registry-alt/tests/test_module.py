"""Module tests for the alternate patient registry.

Every test runs against a fresh temporary SQLite database created through create_app, so the
suite never touches the demonstration data and the tests can run in any order. The tests also
pin the legacy registration vocabulary and the database capability backing table, because the
mapping experiments rely on both.
"""

import json
import os
import sys

import pytest

MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, MODULE_DIR)

from app import create_app  # noqa: E402
from db import connect  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "alt_registry.db"))
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def call(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def register(client, pat_no="P-1", pat_name="Ada Lovelace"):
    response = call(client, "/api/pat_reg", {"pat_no": pat_no, "pat_name": pat_name})
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["outputs"]["pat_reg"]


def test_health_reports_module_identity(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok"
    assert body["module"] == "patient-registry-alt"
    assert body["port"] == 5007


def test_spec_declares_the_alt_vocabulary_and_database_capability(client):
    spec = client.get("/spec").get_json()
    assert spec["module"]["module_id"] == "patient-registry-alt"
    assert len(spec["capabilities"]) == 5
    by_id = {capability["id"]: capability for capability in spec["capabilities"]}
    assert by_id["PA-Register"]["name"] == "Pat_reg"

    api_endpoints = {
        capability["mechanism"]["endpoint"]
        for capability in spec["capabilities"]
        if capability["mechanism"]["kind"] == "API"
    }
    registered = {rule.rule for rule in client.application.url_map.iter_rules()}
    assert api_endpoints.issubset(registered), api_endpoints - registered

    database = by_id["PA-RowWrite"]
    assert database["type"] == "DATABASE"
    assert database["mechanism"]["operation"] == "insert"
    assert database["mechanism"]["table"] == "pat_rows"
    assert {i["name"] for i in database["inputs"]} == {"pat_no", "pat_name"}

    declared = {variable["name"] for variable in spec["state_schema"]}
    for capability in spec["capabilities"]:
        assert capability["mechanism"]["kind"] == capability["type"]
        for effect in capability["effects"]:
            assert effect["variable"] in declared
        for precondition in capability["preconditions"]:
            assert precondition["variable"] in declared


def test_empty_state_snapshot(client):
    state = client.get("/state").get_json()["state"]
    assert state == {"Patient.registered": False, "Patient.verified": False}


def test_register_pat_assigns_a_registration_key(client):
    pat_reg = register(client)
    assert pat_reg.startswith("PAT-")
    state = client.get("/state").get_json()["state"]
    assert state["Patient.registered"] is True

    duplicate = call(client, "/api/pat_reg", {"pat_no": "P-1", "pat_name": "Someone Else"})
    assert duplicate.status_code == 409
    assert "already registered" in duplicate.get_json()["error"]

    missing = call(client, "/api/pat_reg", {"pat_no": "P-2"})
    assert missing.status_code == 400
    assert "pat_name" in missing.get_json()["error"]


def test_lookup_pat_reads_the_record(client):
    pat_reg = register(client, "P-77", "Grace Hopper")
    body = call(client, "/api/pat_lookup", {"pat_reg": pat_reg}).get_json()
    assert body["outputs"]["pat_no"] == "P-77"
    assert body["outputs"]["pat_name"] == "Grace Hopper"
    assert body["outputs"]["verified"] is False

    unknown = call(client, "/api/pat_lookup", {"pat_reg": "PAT-NOPE"})
    assert unknown.status_code == 404
    assert "unknown patient registration" in unknown.get_json()["error"]


def test_verify_pat_is_one_way(client):
    empty = call(client, "/api/pat_verify", {"pat_reg": "PAT-NOPE"})
    assert empty.status_code == 409
    assert "no patient registration exists yet" in empty.get_json()["error"]

    pat_reg = register(client)
    verified = call(client, "/api/pat_verify", {"pat_reg": pat_reg})
    assert verified.status_code == 200
    assert verified.get_json()["outputs"]["verified"] is True
    assert client.get("/state").get_json()["state"]["Patient.verified"] is True

    again = call(client, "/api/pat_verify", {"pat_reg": pat_reg})
    assert again.status_code == 409
    assert "already verified" in again.get_json()["error"]

    unknown = call(client, "/api/pat_verify", {"pat_reg": "PAT-NOPE"})
    assert unknown.status_code == 404


def test_database_capability_backing_table_exists(client):
    connection = connect(client.application.extensions["db_path"])
    try:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(pat_rows)").fetchall()
        }
        assert {"row_id", "pat_no", "pat_name"}.issubset(columns)
        cursor = connection.execute(
            "INSERT INTO pat_rows (pat_no, pat_name) VALUES (?, ?)", ("P-ROW", "Row Person")
        )
        connection.commit()
        assert cursor.lastrowid == 1
    finally:
        connection.close()


def test_ui_pages_render_with_stable_element_ids(client):
    home = client.get("/ui/")
    assert home.status_code == 200
    assert 'id="module_title"' in home.get_data(as_text=True)

    new_page = client.get("/ui/pat_reg/new")
    text = new_page.get_data(as_text=True)
    assert 'id="pat_reg_form"' in text
    assert 'id="pat_no_input"' in text
    assert 'id="pat_name_input"' in text
    assert 'id="submit_button"' in text
    assert 'id="result_output"' in text

    patients = client.get("/ui/patients")
    assert 'id="patient_table"' in patients.get_data(as_text=True)

    capabilities = client.get("/ui/capabilities")
    capabilities_text = capabilities.get_data(as_text=True)
    assert "PA-Register" in capabilities_text
    assert "PA-RowWrite" in capabilities_text


def test_ui_form_submission_uses_the_gui_capability(client):
    response = client.post(
        "/ui/pat_reg/new", data={"pat_no": "P-FORM", "pat_name": "Form Person"}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["capability"] == "PA-Form"
    listing = client.get("/ui/patients").get_data(as_text=True)
    assert "P-FORM" in listing
    assert "Form Person" in listing


def test_patient_detail_page_verification_form(client):
    pat_reg = register(client, "P-DETAIL", "Detail Person")
    detail = client.get("/ui/patients/%s" % pat_reg).get_data(as_text=True)
    assert 'id="verify_form"' in detail
    assert 'id="verify_button"' in detail
    assert "P-DETAIL" in detail

    call(client, "/api/pat_verify", {"pat_reg": pat_reg})
    verified_detail = client.get("/ui/patients/%s" % pat_reg).get_data(as_text=True)
    assert 'id="verified_notice"' in verified_detail
    assert 'id="verify_form"' not in verified_detail

    missing = client.get("/ui/patients/PAT-NOPE")
    assert missing.status_code == 404


def test_served_pages_have_no_external_assets(client):
    for path in ["/ui/", "/ui/patients", "/ui/pat_reg/new", "/ui/capabilities"]:
        text = client.get(path).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
    for asset in ["/ui/static/style.css", "/ui/static/app.js"]:
        text = client.get(asset).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
