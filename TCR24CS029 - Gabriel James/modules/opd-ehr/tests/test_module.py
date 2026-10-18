"""Module tests for the outpatient EHR.

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
    app = create_app(db_path=str(tmp_path / "ehr.db"))
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def call(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def start_encounter(client, mrn="MRN-1"):
    response = call(
        client, "/api/start_encounter", {"patient_mrn": mrn, "clinician": "Dr Rivera"}
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["outputs"]["encounter_id"]


def test_health_reports_module_identity(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok"
    assert body["module"] == "opd-ehr"
    assert body["port"] == 5003


def test_spec_matches_the_implemented_routes(client):
    spec = client.get("/spec").get_json()
    assert spec["module"]["module_id"] == "opd-ehr"
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
        "Encounter.active": False,
        "Encounter.closed": False,
        "Vitals.recorded": False,
        "Prescription.issued": False,
        "Prescription.count": 0,
    }


def test_start_encounter_and_single_active_rule(client):
    encounter_id = start_encounter(client)
    assert encounter_id.startswith("ENC-")
    state = client.get("/state").get_json()["state"]
    assert state["Encounter.active"] is True

    second = call(
        client, "/api/start_encounter", {"patient_mrn": "MRN-2", "clinician": "Dr Chen"}
    )
    assert second.status_code == 409
    assert "still active" in second.get_json()["error"]

    missing = call(client, "/api/start_encounter", {"patient_mrn": "MRN-3"})
    assert missing.status_code == 400
    assert "clinician" in missing.get_json()["error"]

    bad_type = call(
        client,
        "/api/start_encounter",
        {"patient_mrn": "MRN-3", "clinician": "Dr Chen", "visit_type": "SURGERY"},
    )
    assert bad_type.status_code == 400
    assert "visit_type" in bad_type.get_json()["error"]


def test_record_vitals_validates_ranges(client):
    encounter_id = start_encounter(client)
    ok = call(
        client,
        "/api/record_vitals",
        {"encounter_id": encounter_id, "temperature_c": 37.2, "heart_rate": 72, "systolic": 118},
    )
    assert ok.status_code == 200
    assert ok.get_json()["outputs"]["recorded"] is True
    assert client.get("/state").get_json()["state"]["Vitals.recorded"] is True

    fever = call(
        client,
        "/api/record_vitals",
        {"encounter_id": encounter_id, "temperature_c": 52.0, "heart_rate": 72},
    )
    assert fever.status_code == 400
    assert "temperature_c" in fever.get_json()["error"]

    fast = call(
        client,
        "/api/record_vitals",
        {"encounter_id": encounter_id, "temperature_c": 37.0, "heart_rate": 400},
    )
    assert fast.status_code == 400
    assert "heart_rate" in fast.get_json()["error"]

    unknown = call(
        client,
        "/api/record_vitals",
        {"encounter_id": "ENC-NOPE", "temperature_c": 37.0, "heart_rate": 72},
    )
    assert unknown.status_code == 404


def test_clinical_actions_require_an_active_encounter(client):
    encounter_id = start_encounter(client)
    call(client, "/api/close_encounter", {"encounter_id": encounter_id})
    closed_vitals = call(
        client,
        "/api/record_vitals",
        {"encounter_id": encounter_id, "temperature_c": 37.0, "heart_rate": 72},
    )
    assert closed_vitals.status_code == 409
    close_again = call(client, "/api/close_encounter", {"encounter_id": encounter_id})
    assert close_again.status_code == 409
    unknown = call(client, "/api/close_encounter", {"encounter_id": "ENC-NOPE"})
    assert unknown.status_code == 404


def test_issue_prescription_updates_state(client):
    encounter_id = start_encounter(client)
    issued = call(
        client,
        "/api/issue_prescription",
        {
            "encounter_id": encounter_id,
            "drug": "Amoxicillin",
            "dose_mg": 500,
            "instructions": "Three times daily",
        },
    )
    assert issued.status_code == 200
    assert issued.get_json()["outputs"]["prescription_id"].startswith("RX-")
    state = client.get("/state").get_json()["state"]
    assert state["Prescription.issued"] is True
    assert state["Prescription.count"] == 1

    overdose = call(
        client,
        "/api/issue_prescription",
        {"encounter_id": encounter_id, "drug": "Amoxicillin", "dose_mg": 9000},
    )
    assert overdose.status_code == 400
    assert "dose_mg" in overdose.get_json()["error"]

    empty_drug = call(
        client,
        "/api/issue_prescription",
        {"encounter_id": encounter_id, "drug": "   ", "dose_mg": 500},
    )
    assert empty_drug.status_code == 400


def test_close_encounter_flow(client):
    encounter_id = start_encounter(client)
    closed = call(
        client,
        "/api/close_encounter",
        {"encounter_id": encounter_id, "summary": "Resolved"},
    )
    assert closed.status_code == 200
    assert closed.get_json()["outputs"]["closed"] is True
    state = client.get("/state").get_json()["state"]
    assert state["Encounter.active"] is False
    assert state["Encounter.closed"] is True

    # A new encounter can start once the previous one is closed.
    again = start_encounter(client, "MRN-2")
    assert again.startswith("ENC-")


def test_ui_pages_render_with_stable_element_ids(client):
    home = client.get("/ui/")
    assert home.status_code == 200
    assert 'id="module_title"' in home.get_data(as_text=True)

    new_page = client.get("/ui/encounters/new")
    text = new_page.get_data(as_text=True)
    assert 'id="encounter_form"' in text
    assert 'id="submit_button"' in text
    assert 'id="result_output"' in text

    encounters = client.get("/ui/encounters")
    assert encounters.status_code == 200
    assert 'id="encounter_table"' in encounters.get_data(as_text=True)

    capabilities = client.get("/ui/capabilities")
    assert "EHR-StartEncounter" in capabilities.get_data(as_text=True)


def test_ui_form_submission_uses_the_gui_capability(client):
    response = client.post(
        "/ui/encounters/new",
        data={"patient_mrn": "MRN-FORM", "clinician": "Dr Rivera", "visit_type": "FOLLOW_UP"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["capability"] == "EHR-Form"
    listing = client.get("/ui/encounters").get_data(as_text=True)
    assert "MRN-FORM" in listing


def test_encounter_detail_page_and_missing_encounter(client):
    encounter_id = start_encounter(client, "MRN-DETAIL")
    detail = client.get("/ui/encounters/%s" % encounter_id)
    assert detail.status_code == 200
    text = detail.get_data(as_text=True)
    assert 'id="vitals_form"' in text
    assert 'id="prescription_form"' in text
    assert 'id="close_form"' in text
    missing = client.get("/ui/encounters/ENC-NOPE")
    assert missing.status_code == 404


def test_served_pages_have_no_external_assets(client):
    for path in ["/ui/", "/ui/encounters", "/ui/encounters/new", "/ui/capabilities"]:
        text = client.get(path).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
    for asset in ["/ui/static/style.css", "/ui/static/app.js"]:
        text = client.get(asset).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
