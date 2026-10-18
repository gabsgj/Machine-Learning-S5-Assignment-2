from pathlib import Path
import json

from src.compatibility import compatibility
from src.formal_composition import compose_many
from src.data_models import capability_from_dict

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "expanded_application.json"


def load():
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    return raw, {item["id"]: capability_from_dict(item) for item in raw["capabilities"]}


def test_expanded_dataset_has_expected_size():
    raw, caps = load()
    assert len(caps) == 18
    assert raw["metadata"]["logical_capability_count"] == 15


def test_expected_relations_match_symbolic_rules():
    raw, caps = load()
    for relation in raw["expected_relations"]:
        predicted = compatibility(caps[relation["from"]], caps[relation["to"]]).compatible
        expected = relation["relation"] == "compatible"
        assert predicted == expected, relation


def test_purchase_success_chain_composes():
    _, caps = load()
    chain = [caps[cid] for cid in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]]
    composite = compose_many(chain)
    assert composite.reliability > 0
    assert any(e.attribute == "Notification.sent" and e.value is True for e in composite.effects)


def test_cancel_release_chain_composes():
    _, caps = load()
    composite = compose_many([caps["C4"], caps["C9"], caps["C10"]])
    assert composite.reliability > 0
    assert any(e.attribute == "Inventory.reserved" and e.value is False for e in composite.effects)
