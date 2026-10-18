import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.capability_embedding import CapabilityEmbedder, capability_from_dict


def load():
    with open(ROOT / "data" / "dataset.json", encoding="utf-8") as f:
        return json.load(f)


def main():
    data = load()
    emb = CapabilityEmbedder()
    caps = {x["name"]: capability_from_dict(x) for x in data["capabilities"]}
    goal = data["application"]["goal"]

    print("=" * 72)
    print("ASSIGNMENT 2 - VECTOR EMBEDDING FOR CAPABILITY COMPOSITION")
    print("=" * 72)
    print("Embedding dimension:", emb.dim)

    # 1. Capability compatibility
    print("\n1. CAPABILITY COMPATIBILITY")
    pairs = [("CreateOrder", "MakePayment"),
             ("CreateOrder", "CancelCart"),
             ("CreateOrder", "SendNotification")]
    for a, b in pairs:
        score, reasons = emb.compatibility(caps[a], caps[b])
        print(f"{a:16s} -> {b:18s} score={score:.3f} | {'; '.join(reasons)}")

    # 2. Composition
    print("\n2. CAPABILITY COMPOSITION")
    comp = emb.compose([caps["CreateOrder"], caps["MakePayment"], caps["SendNotification"]])
    print("Composite:", comp["name"])
    print("Valid:", comp["valid"])
    print("Links:")
    for link in comp["links"]:
        print(" ", link["from"], "->", link["to"], f"score={link['score']:.3f}")

    # 3. Alternative implementations
    print("\n3. ALTERNATIVE IMPLEMENTATIONS")
    a = emb.encode_capability(caps["CreateOrder"])
    for name in ["CreateOrderDB", "CreateOrderGUI", "ViewProfile"]:
        b = emb.encode_capability(caps[name])
        print(f"CreateOrder similarity with {name:15s}: {emb.similarity(a,b):.3f}")

    # 4. Irrelevant capabilities / goal relevance
    print("\n4. GOAL RELEVANCE")
    for name, c in caps.items():
        print(f"{name:18s}: {emb.goal_relevance(c, goal):.3f}")

    # 5. Operational attributes
    print("\n5. OPERATIONAL ATTRIBUTES")
    for name in ["CreateOrder", "CreateOrderDB", "CreateOrderGUI", "MakePayment"]:
        c = caps[name]
        print(f"{name:18s}: reliability={c.reliability:.3f}, availability={c.availability:.3f}, "
              f"time={c.cost['time']}, money={c.cost['money']}, risk={c.cost['risk']}")

    print("\nConclusion: functional relationships are encoded primarily through state, "
          "precondition, effect, I/O, constraint and resource features; implementation "
          "mechanisms are represented separately with lower weight.")

if __name__ == "__main__":
    main()
