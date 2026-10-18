"""Module tests for the patient registry.

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
    app = create_app(db_path=str(tmp_path / "registry.db"))
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def call(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def register(client, mrn="MRN-1", name="Ada Lovelace"):
    response = call(client, "/api/register_patient", {"mrn": mrn, "full_name": name})
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["outputs"]["patient_id"]


def test_health_reports_module_identity(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok"
    assert body["module"] == "patient-registry"
    assert body["port"] == 5001


def test_spec_matches_the_implemented_routes(client):
    spec = client.get("/spec").get_json()
    assert spec["module"]["module_id"] == "patient-registry"
    assert len(spec["capabilities"]) == 6
    api_endpoints = {
        capability["mechanism"]["endpoint"]
        for capability in spec["capabilities"]
        if capability["mechanism"]["kind"] == "API"
    }
    registered = {rule.rule for rule in client.application.url_map.iter_rules()}
    assert api_endpoints.issubset(registered), api_endpoints - registered
    for capability in spec["capabilities"]:
        assert capability["mechanism"]["kind"] == capability["type"]
        declared = {variable["name"] for variable in spec["state_schema"]}
        for effect in capability["effects"]:
            assert effect["variable"] in declared


def test_register_and_lookup(client):
    patient_id = register(client, "MRN-77", "Ada Lovelace")
    state = client.get("/state").get_json()["state"]
    assert state["Patient.registered"] is True

    by_id = call(client, "/api/lookup_patient", {"patient_id": patient_id}).get_json()
    assert by_id["status"] == "ok"
    assert by_id["outputs"]["mrn"] == "MRN-77"
    assert by_id["outputs"]["full_name"] == "Ada Lovelace"
    assert by_id["outputs"]["admitted"] is False
    assert by_id["outputs"]["allergy_count"] == 0

    by_mrn = call(client, "/api/lookup_patient", {"mrn": "MRN-77"}).get_json()
    assert by_mrn["outputs"]["patient_id"] == patient_id


def test_register_rejects_duplicates_and_missing_inputs(client):
    register(client, "MRN-88")
    duplicate = call(client, "/api/register_patient", {"mrn": "MRN-88", "full_name": "Other"})
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.get_json()["error"]

    missing = call(client, "/api/register_patient", {"mrn": "MRN-89"})
    assert missing.status_code == 400
    assert "full_name" in missing.get_json()["error"]

    empty = call(client, "/api/register_patient", {"mrn": "   ", "full_name": "X"})
    assert empty.status_code == 400


def test_admit_and_discharge_flow(client):
    patient_id = register(client)
    admit = call(client, "/api/admit_patient", {"patient_id": patient_id, "ward": "Ward A"})
    assert admit.status_code == 200
    admission_id = admit.get_json()["outputs"]["admission_id"]
    assert client.get("/state").get_json()["state"]["Patient.admitted"] is True

    second = call(client, "/api/admit_patient", {"patient_id": patient_id, "ward": "Ward B"})
    assert second.status_code == 409
    assert "already admitted" in second.get_json()["error"]

    discharge = call(client, "/api/discharge_patient", {"admission_id": admission_id})
    assert discharge.status_code == 200
    assert discharge.get_json()["outputs"]["discharged"] is True
    assert client.get("/state").get_json()["state"]["Patient.admitted"] is False

    again = call(client, "/api/discharge_patient", {"admission_id": admission_id})
    assert again.status_code == 409
    unknown = call(client, "/api/discharge_patient", {"admission_id": "ADM-NOPE"})
    assert unknown.status_code == 404


def test_admit_requires_a_registered_patient(client):
    response = call(client, "/api/admit_patient", {"patient_id": "PAT-NOPE", "ward": "Ward A"})
    assert response.status_code == 404
    assert "unknown patient" in response.get_json()["error"]


def test_flag_allergy_validates_severity_and_updates_state(client):
    patient_id = register(client)
    bad = call(
        client,
        "/api/flag_allergy",
        {"patient_id": patient_id, "allergen": "Peanut", "severity": "EXTREME"},
    )
    assert bad.status_code == 400
    assert "severity" in bad.get_json()["error"]

    unknown = call(
        client,
        "/api/flag_allergy",
        {"patient_id": "PAT-NOPE", "allergen": "Peanut", "severity": "MILD"},
    )
    assert unknown.status_code == 404

    ok = call(
        client,
        "/api/flag_allergy",
        {"patient_id": patient_id, "allergen": "Penicillin", "severity": "SEVERE"},
    )
    assert ok.status_code == 200
    assert ok.get_json()["outputs"]["flagged"] is True
    assert client.get("/state").get_json()["state"]["Patient.allergy_flagged"] is True
    lookup = call(client, "/api/lookup_patient", {"patient_id": patient_id}).get_json()
    assert lookup["outputs"]["allergy_count"] == 1


def test_lookup_requires_an_identifier(client):
    response = call(client, "/api/lookup_patient", {})
    assert response.status_code == 400
    assert "patient_id" in response.get_json()["error"]


def test_bed_capacity_is_enforced(client):
    ids = [register(client, "MRN-%d" % index) for index in range(1, 10)]
    for index, patient_id in enumerate(ids[:8]):
        response = call(client, "/api/admit_patient", {"patient_id": patient_id, "ward": "Ward A"})
        assert response.status_code == 200, "admission %d failed" % index
    overflow = call(client, "/api/admit_patient", {"patient_id": ids[8], "ward": "Ward A"})
    assert overflow.status_code == 409
    assert "no bed available" in overflow.get_json()["error"]
    assert client.get("/state").get_json()["state"]["Ward.bed_available"] is False


def test_ui_pages_render_with_stable_element_ids(client):
    home = client.get("/ui/")
    assert home.status_code == 200
    text = home.get_data(as_text=True)
    assert 'id="module_title"' in text
    assert "Patient Registry" in text

    new_page = client.get("/ui/patients/new")
    assert new_page.status_code == 200
    new_text = new_page.get_data(as_text=True)
    assert 'id="patient_form"' in new_text
    assert 'id="submit_button"' in new_text
    assert 'id="result_output"' in new_text

    capabilities = client.get("/ui/capabilities")
    assert capabilities.status_code == 200
    assert "PR-Register" in capabilities.get_data(as_text=True)


def test_ui_form_submission_uses_the_gui_capability(client):
    response = client.post(
        "/ui/patients/new",
        data={"mrn": "MRN-FORM-1", "full_name": "Grace Hopper"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["capability"] == "PR-Form"
    lookup = call(client, "/api/lookup_patient", {"mrn": "MRN-FORM-1"}).get_json()
    assert lookup["status"] == "ok"


def test_patient_detail_page_and_missing_patient(client):
    patient_id = register(client, "MRN-DETAIL", "Alan Turing")
    detail = client.get("/ui/patients/%s" % patient_id)
    assert detail.status_code == 200
    text = detail.get_data(as_text=True)
    assert "Alan Turing" in text
    assert 'id="admit_form"' in text
    assert 'id="allergy_form"' in text
    missing = client.get("/ui/patients/PAT-NOPE")
    assert missing.status_code == 404


def test_served_pages_have_no_external_assets(client):
    for path in ["/ui/", "/ui/patients", "/ui/patients/new", "/ui/capabilities"]:
        text = client.get(path).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
    for asset in ["/ui/static/style.css", "/ui/static/app.js"]:
        text = client.get(asset).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
