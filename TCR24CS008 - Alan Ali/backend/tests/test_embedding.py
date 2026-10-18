from app.embedding import EmbeddingEncoder, capability_similarity, sparse_cosine
from app.models.formal import Goal, Predicate, State
from app.experiments.runner import load_default_scenario


def test_state_encoding_names_values():
    encoded = EmbeddingEncoder().encode_state(State(id="s", values={"Cart.exists": True}))
    assert encoded == {"state:Cart.exists=true": 1.0}


def test_goal_encoding_preserves_operator():
    encoded = EmbeddingEncoder().encode_goal(Goal(id="g", conditions=[Predicate(name="Cart.count", operator=">", value=0)]))
    assert encoded == {"goal:Cart.count>0": 1.0}


def test_capability_encoding_covers_formal_sections():
    cap = load_default_scenario().capabilities[0]
    encoded = EmbeddingEncoder().encode_capability(cap)
    for prefix in ("identity:", "type:", "io:input:", "io:output:", "condition:", "effect:", "constraint:", "resource:", "mechanism:", "operational:"):
        assert any(key.startswith(prefix) for key in encoded)


def test_cosine_identical_and_orthogonal():
    assert sparse_cosine({"x": 1}, {"x": 1}) == 1
    assert sparse_cosine({"x": 1}, {"y": 1}) == 0


def test_alternative_implementations_share_function_and_differ_in_identity():
    scenario = load_default_scenario()
    api, database, gui = scenario.capabilities[0], scenario.capabilities[3], scenario.capabilities[4]
    encoder = EmbeddingEncoder()
    api_db = sparse_cosine(encoder.encode_capability(api), encoder.encode_capability(database))
    api_gui = sparse_cosine(encoder.encode_capability(api), encoder.encode_capability(gui))
    unrelated = sparse_cosine(encoder.encode_capability(api), encoder.encode_capability(scenario.capabilities[-1]))
    assert api_db > 0 and api_gui > 0
    assert api_db < 1 and api_gui < 1
    assert api_db > unrelated


def test_section_weighted_similarity_separates_alternatives_from_other_function():
    scenario = load_default_scenario()
    caps = {cap.id: cap for cap in scenario.capabilities}
    encoder = EmbeddingEncoder()
    alternatives = capability_similarity(encoder, caps["create-order-api"], caps["create-order-db"])["similarity"]
    different_function = capability_similarity(encoder, caps["create-order-api"], caps["make-payment"])["similarity"]
    assert alternatives > different_function

