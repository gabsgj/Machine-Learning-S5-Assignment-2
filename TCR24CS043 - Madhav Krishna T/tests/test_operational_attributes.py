from dataclasses import replace
from pathlib import Path

from src.dataset import load_dataset
from src.encoder import capability_blocks, cosine, encode_capability


def test_operational_variants_change_only_operational_attributes():
    root = Path(__file__).resolve().parents[1]
    _, caps = load_dataset(root / "data" / "expanded_application.json")
    base = caps["C5"]
    variants = {
        "reliability": replace(base, reliability=0.70),
        "availability": replace(base, availability=0),
        "risk": replace(base, quality=replace(base.quality, risk=0.85)),
    }
    base_vec = encode_capability(base)
    for variant in variants.values():
        vec = encode_capability(variant)
        blocks_a = capability_blocks(base_vec)
        blocks_b = capability_blocks(vec)
        functional_a = sum((blocks_a[k] * blocks_b[k]).sum() for k in blocks_a if k != "operational")
        # The normalized block-wise vectors are concatenated from deterministic
        # blocks, so each non-operational block should remain unchanged.
        for key in blocks_a:
            if key != "operational":
                assert cosine(blocks_a[key], blocks_b[key]) > 0.9999
        assert cosine(blocks_a["operational"], blocks_b["operational"]) < 0.9999
        assert functional_a == functional_a  # finite-value smoke check


def test_operational_experiment_isolation_is_obvious():
    root = Path(__file__).resolve().parents[1]
    _, caps = load_dataset(root / "data" / "expanded_application.json")
    base = caps["C5"]
    unreliable = replace(base, reliability=0.70)
    a = capability_blocks(encode_capability(base))
    b = capability_blocks(encode_capability(unreliable))
    assert cosine(a["function"], b["function"]) > 0.9999
    assert cosine(a["input"], b["input"]) > 0.9999
    assert cosine(a["effect"], b["effect"]) > 0.9999
