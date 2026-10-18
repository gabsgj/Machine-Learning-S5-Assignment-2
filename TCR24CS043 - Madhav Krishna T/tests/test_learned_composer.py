from pathlib import Path
import json
import numpy as np

from src.learned_composer import LearnedBlockComposer, build_training_pairs
from src.dataset import load_dataset
from src.encoder import encode_capability

ROOT = Path(__file__).resolve().parents[1]


def test_training_pairs_and_prediction_shape():
    _, caps = load_dataset(ROOT / "data" / "expanded_application.json")
    split = json.loads((ROOT / "data" / "composition_split.json").read_text(encoding="utf-8"))
    pairs, targets = build_training_pairs(caps, [tuple(x) for x in split["training_pairs"]])
    model = LearnedBlockComposer()
    report = model.fit(pairs, targets)
    assert report.train_pairs == len(pairs)
    pred = model.predict(encode_capability(caps["C1"]), encode_capability(caps["C2"]))
    assert pred.shape == (128,)
    assert abs(float(np.linalg.norm(pred)) - 1.0) < 1e-5


def test_composer_requires_fit():
    _, caps = load_dataset(ROOT / "data" / "expanded_application.json")
    model = LearnedBlockComposer()
    try:
        model.predict(encode_capability(caps["C1"]), encode_capability(caps["C2"]))
    except RuntimeError:
        return
    raise AssertionError("Prediction should require a fitted model")
