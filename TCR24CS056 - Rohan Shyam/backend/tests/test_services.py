from app.embedding import EmbeddingEncoder
from app.experiments.runner import load_default_scenario
from app.services.applicability import capability_applicability
from app.services.formal_logic import satisfies
from app.services.relevance import goal_effect_analysis
from app.services.scenario import ScenarioStore, load_default_scenario as load_scenario


def test_scenario_store_supports_injected_scenario_files(tmp_path):
    source = load_default_scenario()
    path = tmp_path / "scenario.json"
    path.write_text(source.model_dump_json(), encoding="utf-8")

    store = ScenarioStore(load_scenario(path))
    assert store.get().id == source.id

    replacement = source.model_copy(update={"id": "replacement"})
    assert store.replace(replacement) is replacement
    assert store.get().id == "replacement"


def test_goal_effect_analysis_is_reusable_by_api_and_experiments():
    scenario = load_default_scenario()
    analysis = goal_effect_analysis(
        scenario.capabilities[0], scenario.goals[0], EmbeddingEncoder()
    )

    assert analysis["matched_goal_variables"] == ["Order.exists"]
    assert analysis["effect_overlap"] == 1
    assert analysis["goal_effect_coverage"] == 0.33333333
    assert analysis["relevant"] is True


def test_applicability_and_predicate_evaluation_handle_invalid_comparisons():
    scenario = load_default_scenario()
    applicable, evidence = capability_applicability(
        scenario.states[0], scenario.capabilities[0]
    )

    assert applicable is True
    assert len(evidence) == 3
    assert satisfies(1, ">", "not a number") is False
    assert satisfies("value", "in", None) is False
