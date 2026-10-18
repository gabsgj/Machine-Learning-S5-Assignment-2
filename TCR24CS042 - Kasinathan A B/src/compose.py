"""
compose.py
==========
Higher-level composition utilities that wrap encode.compose().

Functions here provide:
  - chain_capabilities()  : build a composite from a sequence of name-keyed caps
  - show_composition()    : print a detailed breakdown of a composed chain
"""

import numpy as np
from .encode import (
    compose, encode_capability, similarity,
    IDX_TYPE, IDX_IO, IDX_IOMATCH, IDX_RESOURCE,
    IDX_COST, IDX_RELY, IDX_PRECOND, IDX_EFFECT,
    CAPABILITY_TYPES, GLOBAL_RESOURCE_VOCAB
)


def _find_cap(name: str, caps: list[dict]) -> dict | None:
    """Return the first capability dict whose 'name' matches (case-insensitive)."""
    for c in caps:
        if c.get("name", "").lower() == name.lower():
            return c
    return None


def chain_capabilities(names: list[str], domain: dict) -> tuple[np.ndarray, list[dict]]:
    """
    Build a composite capability vector from an ordered list of capability names
    within a single domain.

    Parameters
    ----------
    names  : ordered list of capability names (as found in domain['capabilities'])
    domain : domain dict (from JSON)

    Returns
    -------
    (composite_vector, ordered_capability_dicts)
    """
    caps        = domain["capabilities"]
    state_vars  = domain["state_variables"]

    ordered_caps = []
    for name in names:
        cap = _find_cap(name, caps)
        if cap is None:
            raise ValueError(f"Capability '{name}' not found in domain "
                             f"'{domain['domain']}'")
        ordered_caps.append(cap)

    vecs = [encode_capability(c, state_vars) for c in ordered_caps]
    composite = compose(vecs, ordered_caps, state_vars)
    return composite, ordered_caps


def describe_vector(vec: np.ndarray, label: str = "Vector") -> str:
    """Return a human-readable string description of a capability vector."""
    lines = [f"  {label} ({len(vec)} dims):"]

    # Type
    type_slice = vec[IDX_TYPE[0]:IDX_TYPE[1]]
    hot_idx    = int(np.argmax(type_slice))
    cap_type   = CAPABILITY_TYPES[hot_idx] if type_slice[hot_idx] > 0 else "NONE"
    lines.append(f"    type           : {cap_type}")

    # IO
    io_slice = vec[IDX_IO[0]:IDX_IO[1]] * 10   # un-normalise
    lines.append(f"    inputs         : {io_slice[0]:.0f}  outputs: {io_slice[1]:.0f}  "
                 f"required: {io_slice[2]:.0f}  optional: {io_slice[3]:.0f}")
    lines.append(f"    io_name_match  : {vec[IDX_IOMATCH[0]]:.3f}")

    # Resources
    res_slice = vec[IDX_RESOURCE[0]:IDX_RESOURCE[1]]
    active_res = [GLOBAL_RESOURCE_VOCAB[i] for i, v in enumerate(res_slice) if v > 0.5]
    lines.append(f"    resources      : {active_res}")

    # Cost
    cost_slice = vec[IDX_COST[0]:IDX_COST[1]]
    fields     = ["time_ms", "money", "resource", "risk", "energy"]
    cost_str   = "  ".join(f"{f}={v:.3f}" for f, v in zip(fields, cost_slice))
    lines.append(f"    cost (normed)  : {cost_str}")

    # Reliability
    lines.append(f"    reliability    : {vec[IDX_RELY[0]]:.4f}")

    # Precondition
    pre_slice = vec[IDX_PRECOND[0]:IDX_PRECOND[1]]
    lines.append(f"    precondition   : {np.round(pre_slice, 1).tolist()}")

    # Effect
    eff_slice = vec[IDX_EFFECT[0]:IDX_EFFECT[1]]
    lines.append(f"    effect         : {np.round(eff_slice, 1).tolist()}")

    return "\n".join(lines)


def show_composition(names: list[str], domain: dict) -> None:
    """
    Print a detailed table showing individual and composite capability vectors,
    plus pairwise similarity scores.
    """
    state_vars = domain["state_variables"]
    composite, ordered_caps = chain_capabilities(names, domain)

    print(f"\n{'='*70}")
    print(f"  Composition chain: {' -> '.join(names)}")
    print(f"{'='*70}")

    individual_vecs = [encode_capability(c, state_vars) for c in ordered_caps]

    for cap, vec in zip(ordered_caps, individual_vecs):
        print(describe_vector(vec, label=cap["name"]))
        print()

    print(describe_vector(composite, label="COMPOSITE"))
    print()

    print("  Similarity(composite, individual):")
    print(f"  {'Capability':<30} {'Similarity':>12}")
    print(f"  {'-'*30} {'-'*12}")
    for cap, vec in zip(ordered_caps, individual_vecs):
        sim = similarity(composite, vec)
        print(f"  {cap['name']:<30} {sim:>12.4f}")
    print()
