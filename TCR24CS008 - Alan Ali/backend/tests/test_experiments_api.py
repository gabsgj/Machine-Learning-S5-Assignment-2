from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from app.main import app
from app.models.formal import ApplicationScenario, Capability
from app.experiments.runner import load_default_scenario, run_all_experiments

client = TestClient(app)


def test_required_experiments_return_measured_results():
    output = run_all_experiments()
    results = {row["id"]: row["results"] for row in output["experiments"]}
    assert results["compatibility"]["compatible_pair"]["compatible"]
    assert not results["compatibility"]["incompatible_pair"]["compatible"]
    assert len(results["three_capability_composition"]["component_ids"]) == 3
    sims = results["alternative_implementations"]["functional_similarity"]
    assert sims["api_database"] != sims["api_gui"]
    assert len(results["goal_relevance"]["capabilities"]) == 7
    assert results["operational_properties"]["chain_reliability"] > 0
    relevance = {row["capability_id"]: row for row in results["goal_relevance"]["capabilities"]}
    assert relevance["create-order-api"]["goal_effect_similarity"] > 0
    assert relevance["refresh-catalog"]["goal_effect_similarity"] == 0


def test_two_capability_scenario_reports_compatible_pair_and_skips_other_groups():
    commerce = load_default_scenario()
    scenario = ApplicationScenario(id="pair", name="Pair", capabilities=[commerce.capabilities[0], commerce.capabilities[1]])
    output = run_all_experiments(scenario)
    groups = {row["id"]: row for row in output["experiments"]}
    assert groups["compatibility"]["results"]["compatible_pair"]["compatible"]
    assert all(row.get("skipped") for key, row in groups.items() if key != "compatibility")


def test_empty_capability_scenario_skips_without_crashing():
    scenario = ApplicationScenario(id="empty", name="Empty")
    output = run_all_experiments(scenario)
    groups = {row["id"]: row for row in output["experiments"]}
    assert all("skipped" in row for row in groups.values())
    assert len(groups) == 7


def test_api_health_scenario_encoding_and_experiments():
    assert client.get("/api/health").json()["status"] == "ok"
    assert len(client.get("/api/scenario").json()["capabilities"]) == 7
    capability = load_default_scenario().capabilities[0].model_dump()
    encoded = client.post("/api/encode/capability", json=capability)
    assert encoded.status_code == 200 and encoded.json()["dimension_count"] > 0
    assert client.get("/api/experiments").status_code == 200


def test_api_composition_and_failure_are_explained():
    caps = [cap.model_dump() for cap in load_default_scenario().capabilities[:3]]
    assert client.post("/api/compose", json={"capabilities": caps}).status_code == 200
    failed = client.post("/api/compose", json={"capabilities": [caps[0], load_default_scenario().capabilities[5].model_dump()]})
    assert failed.status_code == 422
    assert "diagnostics" in failed.json()["detail"]


def test_invalid_input_and_missing_required_fields_rejected():
    with pytest.raises(ValidationError):
        Capability.model_validate({"id": "missing-name", "type": "API", "reliability": 0.9})
    response = client.post("/api/encode/state", json={"id": "s"})
    assert response.status_code == 422


def test_out_of_range_operational_input_rejected():
    body = load_default_scenario().capabilities[0].model_dump()
    body["reliability"] = 1.1
    assert client.post("/api/encode/capability", json=body).status_code == 422


def test_state_goal_truth_evaluation():
    response = client.post("/api/state-goal", json={"state": {"id": "done", "values": {"Order.exists": True}},
                                                    "goal": {"id": "order", "conditions": [{"name": "Order.exists", "value": True}]}})
    assert response.status_code == 200 and response.json()["satisfied"]


def test_applicability_reports_state_precondition_evidence():
    scenario = load_default_scenario()
    response = client.post("/api/applicability", json={"state": scenario.states[0].model_dump(),
        "capability": scenario.capabilities[0].model_dump()})
    assert response.status_code == 200
    assert response.json()["applicable"]
    assert len(response.json()["evidence"]) == 3
