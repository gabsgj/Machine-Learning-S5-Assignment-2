"""Final SCE-128 smoke test / capability summary."""
from __future__ import annotations

from pathlib import Path

from .compatibility import compatibility
from .dataset import load_dataset
from .encoder import capability_blocks, cosine, encode_capability
from .final_model import blockwise_similarity_v2, goal_relevance_v2
from .learned_composer import LearnedBlockComposer, build_training_pairs
from .schema import Condition
import json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "expanded_application.json"
SPLIT = ROOT / "data" / "composition_split.json"


def main() -> None:
    raw, caps = load_dataset(DATA)
    vectors = {cid: encode_capability(cap) for cid, cap in caps.items()}
    goal = [Condition(**x) for x in raw["goal"]]

    print("=" * 78)
    print("SCE-128 v2.1 — PROJECT SMOKE TEST")
    print("=" * 78)
    print(f"Capabilities                         : {len(caps)}")
    print("Vector dimension                     : 128")
    print("Initial formal model                : S = state variables, G = goal predicates")
    print("Capability representation            : T/I/O/P/E/K/R/Q/Reli/A/M")
    print()
    print("SELECTED CAPABILITY PAIRS")
    for a, b in [("C4", "C5"), ("C4_API", "C4_DB")]:
        raw_sim = cosine(vectors[a], vectors[b])
        block_sim = blockwise_similarity_v2(vectors[a], vectors[b])
        rel = compatibility(caps[a], caps[b])
        print(f"  {a:8s} ↔ {b:8s} | raw={raw_sim:.4f} blockwise={block_sim:.4f} compat={rel.compatible} score={rel.score:.4f}")

    print("\nGOAL RELEVANCE SAMPLE")
    for cid in ["C4", "C9", "C7"]:
        score = goal_relevance_v2(caps[cid], goal, caps)
        print(f"  {cid:8s} {caps[cid].name:20s} score={score['score']:.4f} reachable={int(score['backward_goal_reachability'])}")

    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    train_pairs, targets = build_training_pairs(caps, [tuple(x) for x in split["training_pairs"]])
    composer = LearnedBlockComposer()
    fit = composer.fit(train_pairs, targets)
    print("\nLEARNED COMPOSITION MODEL")
    print(f"  Training pairs                      : {fit.train_pairs}")
    print(f"  Training mean cosine               : {fit.train_mean_cosine:.4f}")
    print("  Prediction input                   : vectors + vector-derived relations only")
    print("  Formal composite supplied to model : no")

    print("\nBlock dimensions")
    for name, block in capability_blocks(vectors["C4"]).items():
        print(f"  {name:14s}: {len(block):2d}")
    print("=" * 78)


if __name__ == "__main__":
    main()
