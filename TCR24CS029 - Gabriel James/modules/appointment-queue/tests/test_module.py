"""Module tests for the appointment queue.

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
    app = create_app(db_path=str(tmp_path / "queue.db"))
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def call(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def create(client, mrn="MRN-1", priority=None):
    payload = {"patient_mrn": mrn}
    if priority is not None:
        payload["priority"] = priority
    response = call(client, "/api/create_ticket", payload)
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["outputs"]["ticket_id"]


def test_health_reports_module_identity(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok"
    assert body["module"] == "appointment-queue"
    assert body["port"] == 5002


def test_spec_matches_the_implemented_routes(client):
    spec = client.get("/spec").get_json()
    assert spec["module"]["module_id"] == "appointment-queue"
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
    assert state == {"Ticket.open": False, "Ticket.triaged": False, "Queue.length": 0}


def test_create_ticket_numbers_tickets_and_updates_state(client):
    first = call(client, "/api/create_ticket", {"patient_mrn": "MRN-1", "reason": "Fever"})
    assert first.status_code == 200
    assert first.get_json()["outputs"]["ticket_no"] == 1
    assert first.get_json()["effects"] == [
        {"variable": "Ticket.open", "op": "SET", "value": True},
        {"variable": "Queue.length", "op": "INCREMENT", "value": 1},
    ]
    second = call(client, "/api/create_ticket", {"patient_mrn": "MRN-2", "priority": "HIGH"})
    assert second.get_json()["outputs"]["ticket_no"] == 2
    state = client.get("/state").get_json()["state"]
    assert state["Ticket.open"] is True
    assert state["Queue.length"] == 2


def test_create_ticket_validates_inputs(client):
    missing = call(client, "/api/create_ticket", {"reason": "Fever"})
    assert missing.status_code == 400
    assert "patient_mrn" in missing.get_json()["error"]
    bad_priority = call(
        client, "/api/create_ticket", {"patient_mrn": "MRN-1", "priority": "SOON"}
    )
    assert bad_priority.status_code == 400
    assert "priority" in bad_priority.get_json()["error"]


def test_call_next_respects_priority_then_arrival_order(client):
    low = create(client, "MRN-LOW", "LOW")
    normal = create(client, "MRN-NORMAL", "NORMAL")
    urgent = create(client, "MRN-URGENT", "EMERGENCY")

    called = call(client, "/api/call_next_ticket", {"desk": "Desk 1"})
    assert called.status_code == 200
    assert called.get_json()["outputs"]["ticket_id"] == urgent
    assert called.get_json()["outputs"]["priority"] == "EMERGENCY"

    second = call(client, "/api/call_next_ticket", {}).get_json()
    assert second["outputs"]["ticket_id"] == normal
    assert client.get("/state").get_json()["state"]["Queue.length"] == 1

    third = call(client, "/api/call_next_ticket", {}).get_json()
    assert third["outputs"]["ticket_id"] == low
    assert client.get("/state").get_json()["state"]["Ticket.open"] is False

    empty = call(client, "/api/call_next_ticket", {})
    assert empty.status_code == 409
    assert "empty" in empty.get_json()["error"]


def test_update_triage_only_for_waiting_tickets(client):
    ticket_id = create(client, "MRN-1", "LOW")
    updated = call(
        client,
        "/api/update_triage",
        {"ticket_id": ticket_id, "priority": "HIGH", "notes": "Pain scale 7"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["outputs"]["updated"] is True
    state = client.get("/state").get_json()["state"]
    assert state["Ticket.triaged"] is True

    detail = client.get("/ui/tickets/%s" % ticket_id).get_data(as_text=True)
    assert "HIGH" in detail
    assert "Pain scale 7" in detail

    call(client, "/api/cancel_ticket", {"ticket_id": ticket_id})
    closed = call(client, "/api/update_triage", {"ticket_id": ticket_id, "priority": "LOW"})
    assert closed.status_code == 409
    unknown = call(client, "/api/update_triage", {"ticket_id": "TKT-NOPE", "priority": "LOW"})
    assert unknown.status_code == 404
    bad = call(client, "/api/update_triage", {"ticket_id": ticket_id, "priority": "URGENT"})
    assert bad.status_code == 400


def test_cancel_ticket_removes_it_from_the_queue(client):
    ticket_id = create(client, "MRN-1")
    cancelled = call(client, "/api/cancel_ticket", {"ticket_id": ticket_id, "reason": "Left"})
    assert cancelled.status_code == 200
    assert cancelled.get_json()["outputs"]["cancelled"] is True
    assert client.get("/state").get_json()["state"]["Queue.length"] == 0
    again = call(client, "/api/cancel_ticket", {"ticket_id": ticket_id})
    assert again.status_code == 409
    unknown = call(client, "/api/cancel_ticket", {"ticket_id": "TKT-NOPE"})
    assert unknown.status_code == 404


def test_ui_pages_render_with_stable_element_ids(client):
    home = client.get("/ui/")
    assert home.status_code == 200
    assert 'id="module_title"' in home.get_data(as_text=True)

    new_page = client.get("/ui/tickets/new")
    text = new_page.get_data(as_text=True)
    assert 'id="ticket_form"' in text
    assert 'id="submit_button"' in text
    assert 'id="result_output"' in text

    queue = client.get("/ui/tickets")
    assert queue.status_code == 200
    assert 'id="call_next_form"' in queue.get_data(as_text=True)

    capabilities = client.get("/ui/capabilities")
    assert "AQ-CreateTicket" in capabilities.get_data(as_text=True)


def test_ui_form_submission_uses_the_gui_capability(client):
    response = client.post(
        "/ui/tickets/new",
        data={"patient_mrn": "MRN-FORM", "reason": "Form", "priority": "HIGH"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["capability"] == "AQ-Form"
    listing = client.get("/ui/tickets").get_data(as_text=True)
    assert "MRN-FORM" in listing


def test_ticket_detail_page_and_missing_ticket(client):
    ticket_id = create(client, "MRN-DETAIL")
    detail = client.get("/ui/tickets/%s" % ticket_id)
    assert detail.status_code == 200
    text = detail.get_data(as_text=True)
    assert 'id="triage_form"' in text
    assert 'id="cancel_form"' in text
    missing = client.get("/ui/tickets/TKT-NOPE")
    assert missing.status_code == 404


def test_served_pages_have_no_external_assets(client):
    for path in ["/ui/", "/ui/tickets", "/ui/tickets/new", "/ui/capabilities"]:
        text = client.get(path).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
    for asset in ["/ui/static/style.css", "/ui/static/app.js"]:
        text = client.get(asset).get_data(as_text=True)
        assert "http://" not in text
        assert "https://" not in text
