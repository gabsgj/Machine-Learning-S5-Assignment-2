from src.evaluation import exact_contract_match
from src.dataset import load_dataset


def test_create_order_variants_share_contract():
    _, caps = load_dataset("data/expanded_application.json")
    assert exact_contract_match(caps["C4_API"], caps["C4_DB"])
    assert exact_contract_match(caps["C4_API"], caps["C4_GUI"])
    assert exact_contract_match(caps["C4_DB"], caps["C4_GUI"])


def test_create_order_variants_have_distinct_mechanisms():
    _, caps = load_dataset("data/expanded_application.json")
    mechanisms = [
        tuple(sorted(caps[cid].mechanism.items())) for cid in ["C4_API", "C4_DB", "C4_GUI"]
    ]
    assert len(set(mechanisms)) == 3
