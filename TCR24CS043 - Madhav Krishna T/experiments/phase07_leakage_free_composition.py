"""Phase 07 — Leakage-Free Learned Composition.

The composer receives only atomic or previously predicted vectors and vector-derived relation features."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dataset import load_dataset
from src.learned_composer import LearnedBlockComposer, build_training_pairs, gold_chain_vectors, predict_chain_vectors
from src.encoder import cosine, encode_capability
from src.final_model import compose_formal_v2

DATA = ROOT / "data" / "expanded_application.json"
SPLIT = ROOT / "data" / "composition_split.json"
OUT_JSON = ROOT / "results" / "final_v2_1" / "phase07_leakage_free_composition.json"
OUT_MD = ROOT / "results" / "final_v2_1" / "phase07_leakage_free_composition.md"


def main() -> None:
    data, caps = load_dataset(DATA)
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    train_ids = [tuple(x) for x in split["training_pairs"]]
    heldout = [tuple(x) for x in split["heldout_direct_pairs"]]

    train_pairs, targets = build_training_pairs(caps, train_ids)
    composer = LearnedBlockComposer(ridge_lambda=1e-2)
    fit = composer.fit(train_pairs, targets)

    heldout_rows = []
    for source_id, target_id in heldout:
        source = caps[source_id]
        target = caps[target_id]
        gold = encode_capability(compose_formal_v2(source, target))
        s = encode_capability(source)
        t = encode_capability(target)
        pred = composer.predict(s, t)
        heldout_rows.append({
            "pair": f"{source_id}->{target_id}",
            "consistency": float(cosine(pred, gold)),
        })

    chains = []
    for chain_info in split["evaluation_chains"]:
        chain = chain_info["capabilities"]
        predicted = predict_chain_vectors(composer, caps, chain)
        gold = gold_chain_vectors(caps, chain)
        prefix = [float(cosine(p, g)) for p, g in zip(predicted, gold)]
        chains.append({
            "id": chain_info["id"],
            "length": len(chain),
            "prefix_consistency": prefix,
            "final_consistency": prefix[-1],
        })

    nontrivial = [r["final_consistency"] for r in chains if r["length"] > 1]
    heldout_mean = float(np.mean([r["consistency"] for r in heldout_rows]))
    chain_mean = float(np.mean(nontrivial))
    payload = {
        "model": "SCE-128-v2.1-learned-block-composer",
        "leakage_note": "Prediction uses only atomic/predicted vectors and vector-only relation features; independently encoded formal composites are evaluation targets only.",
        "training": {
            "pair_count": fit.train_pairs,
            "train_mean_cosine": fit.train_mean_cosine,
            "ridge_lambda": fit.ridge_lambda,
            "pairs": [f"{a}->{b}" for a,b in train_ids],
        },
        "heldout_direct_pairs": heldout_rows,
        "heldout_direct_mean": heldout_mean,
        "chains": chains,
        "mean_final_chain_consistency": chain_mean,
        "min_final_chain_consistency": float(min(nontrivial)),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# SCE-128 v2.1 Experiment 6 — Leakage-Free Learned Composition",
        "",
        f"Training pairs: {fit.train_pairs}",
        f"Training mean cosine: {fit.train_mean_cosine:.4f}",
        f"Held-out direct-pair mean: {heldout_mean:.4f}",
        f"Mean final chain consistency: {chain_mean:.4f}",
        f"Minimum final chain consistency: {min(nontrivial):.4f}",
        "",
        "## Held-out direct pairs",
    ]
    for row in heldout_rows:
        lines.append(f"- {row['pair']}: {row['consistency']:.4f}")
    lines += ["", "## Recursive chains"]
    for row in chains:
        lines.append(f"- {row['id']} (L={row['length']}): final={row['final_consistency']:.4f}; prefixes={[round(x,4) for x in row['prefix_consistency']]}")
    lines += ["", "## Methodological note", "The formal composite is encoded separately and is never supplied to the prediction step. This avoids the v2 leakage that made composition consistency trivially equal to 1.0."]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("=" * 78); print("PHASE 07 — LEAKAGE-FREE LEARNED COMPOSITION"); print("=" * 78)
    print(f"Training pairs: {fit.train_pairs} train_mean={fit.train_mean_cosine:.4f}")
    print("Held-out direct pairs:")
    for row in heldout_rows:
        print(f"  {row['pair']}: consistency={row['consistency']:.4f}")
    print(f"Held-out direct mean: {heldout_mean:.4f}")
    print("Recursive chains:")
    for row in chains:
        print(f"  {row['id']}: length={row['length']} final={row['final_consistency']:.4f}")
        print("    prefixes:")
        for i, val in enumerate(row['prefix_consistency'], start=1):
            print(f"      L{i}: {val:.4f}")
    print(f"Mean final chain consistency: {chain_mean:.4f}")
    print(f"Min final chain consistency: {min(nontrivial):.4f}")
    print(f"JSON: {OUT_JSON}")
    print(f"Report: {OUT_MD}")

if __name__ == "__main__":
    main()
