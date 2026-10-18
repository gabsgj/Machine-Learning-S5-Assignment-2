import json
import numpy as np
from .models import Capability
from .embedding import VectorSpace

def run_experiments(json_path: str):
    # 1. Load benchmark constraints
    with open(json_path, 'r') as f:
        data = json.load(f)

    space = VectorSpace(data["state_vocabulary"])
    
    # 2. Encode all capabilities into R^{4n+3} vector space
    caps = {}
    for c_data in data["capabilities"]:
        cap = Capability(
            name=c_data["name"],
            type_val=c_data["type"],
            preconditions=c_data["preconditions"],
            effects=c_data["effects"],
            latency=c_data["latency"],
            cost=c_data["cost"],
            reliability=c_data["reliability"]
        )
        caps[cap.name] = space.encode_capability(cap)

    print("--- Experiment 1: Capability Compatibility ---")
    c1_c2 = space.compatibility_score(caps["InitSupabase"], caps["DeployNextjs"])
    print(f"InitSupabase -> DeployNextjs Compatibility: {c1_c2:.2f}")

    print("\n--- Experiment 2: Algebraic Composition ---")
    v_comp = space.algebraic_compose(caps["InitSupabase"], caps["DeployNextjs"])
    # Indexing into the mask portion to verify inherited preconditions
    print(f"Composite Precondition Mask: {v_comp[space.dim:2*space.dim]}")
    print(f"Composite Latency: {v_comp[-3]}ms")
    
    print("\n--- Experiment 3: Alternative Implementations ---")
    sim = space.functional_similarity(caps["DeployVercel"], caps["DeployRender"])
    print(f"Functional Similarity (Vercel vs Render): {sim:.2f}")

    print("\n--- Experiment 4: Irrelevant Capabilities ---")
    # Goal vector for AppLive = True
    goal_val, goal_mask = space._encode_subspace({"AppLive": True})
    goal_vec = np.concatenate([np.zeros(2*space.dim), goal_val, goal_mask, np.zeros(3)])
    relevance = space.functional_similarity(caps["InstallSteamGame"], goal_vec)
    print(f"Relevance of InstallSteamGame to 'AppLive': {relevance:.2f}")

    print("\n--- Experiment 5: Operational Attributes ---")
    rel_1 = caps["InitSupabase"][-1]
    rel_2 = caps["DeployNextjs"][-1]
    comp_rel = v_comp[-1]
    print(f"-ln(Rel_1) + -ln(Rel_2) = {rel_1:.4f} + {rel_2:.4f} = {comp_rel:.4f}")
    print(f"Equivalent Multiplied Probability (e^-comp_rel): {np.exp(-comp_rel):.4f}")