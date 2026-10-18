from pathlib import Path
import json

from experiments.phase08_final_evaluation import ROOT


def test_final_split_exists():
    path = ROOT / "data" / "composition_split.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data["training_pairs"]) == 8
    assert len(data["heldout_direct_pairs"]) == 4
    assert len(data["evaluation_chains"]) == 9


def test_final_result_directory_exists():
    assert (ROOT / "results" / "final_v2_1").exists()
