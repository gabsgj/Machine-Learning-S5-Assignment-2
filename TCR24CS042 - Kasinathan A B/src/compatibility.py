"""
compatibility.py
================
Utilities for computing and displaying pairwise compatibility scores between
capabilities within or across domains.

This module wraps encode.compatibility() and provides:
  - pairwise_compatibility_matrix() : compute an N×N matrix
  - print_compatibility_table()     : pretty-print the matrix
  - rank_by_compatibility()         : rank successors for a given capability
"""

import numpy as np
from .encode import encode_capability, compatibility, similarity


def pairwise_compatibility_matrix(caps: list[dict],
                                  state_vars: list[str]) -> np.ndarray:
    """
    Compute an N×N matrix where entry [i, j] is compatibility(caps[i], caps[j]).

    compatibility[i, j] > 0  => cap i can usefully precede cap j
    compatibility[i, j] < 0  => cap i's effects contradict cap j's preconditions
    compatibility[i, j] = 0  => no meaningful sequential relationship

    Parameters
    ----------
    caps       : list of capability dicts
    state_vars : domain state-variable vocabulary

    Returns
    -------
    np.ndarray of shape (N, N)
    """
    n    = len(caps)
    vecs = [encode_capability(c, state_vars) for c in caps]
    mat  = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            mat[i, j] = compatibility(vecs[i], vecs[j])
    return mat


def print_compatibility_table(caps: list[dict], state_vars: list[str],
                               title: str = "Compatibility Matrix") -> None:
    """
    Pretty-print a compatibility matrix with row/column headers.

    Rows  = predecessor capabilities (effect provider)
    Cols  = successor  capabilities  (precondition consumer)
    """
    names = [c["name"] for c in caps]
    mat   = pairwise_compatibility_matrix(caps, state_vars)
    col_w = max(max(len(n) for n in names), 8)
    row_w = max(len(n) for n in names)

    print(f"\n  {title}")
    print(f"  {'':>{row_w}}  " +
          "  ".join(f"{n:>{col_w}}" for n in names))
    print(f"  {'-'*row_w}  " +
          "  ".join("-"*col_w for _ in names))
    for i, row_name in enumerate(names):
        scores = "  ".join(f"{mat[i, j]:>{col_w}.4f}" for j in range(len(names)))
        print(f"  {row_name:>{row_w}}  {scores}")
    print()


def rank_by_compatibility(source_cap: dict, candidate_caps: list[dict],
                          state_vars: list[str]) -> list[tuple[str, float, float]]:
    """
    Rank candidate capabilities by how well they can follow source_cap.

    Returns a list of (name, compatibility_score, similarity_score) tuples
    sorted by compatibility_score descending.
    """
    src_vec = encode_capability(source_cap, state_vars)
    results = []
    for cap in candidate_caps:
        if cap["name"] == source_cap["name"]:
            continue
        tgt_vec = encode_capability(cap, state_vars)
        comp    = compatibility(src_vec, tgt_vec)
        sim     = similarity(src_vec, tgt_vec)
        results.append((cap["name"], comp, sim))
    results.sort(key=lambda x: x[1], reverse=True)
    return results
