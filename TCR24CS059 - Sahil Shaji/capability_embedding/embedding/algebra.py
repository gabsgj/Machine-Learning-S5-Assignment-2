"""
Compositional Vector Algebra (Section 5 & 6, Deliverable 1 & 2).
Defines closed-form vector space operators for capability composition:
  compose_embeddings(z1, z2) -> z_composite
  compose_vector_sequence([z1, z2, ..., zn]) -> z_composite
"""

from typing import List, Sequence, Optional, Tuple
import numpy as np

from .vector_space import MultiFacetedEmbedding, SubspaceLayout
from ..core.types import CapabilityType


def compose_embeddings(
    z1: MultiFacetedEmbedding,
    z2: MultiFacetedEmbedding,
    name: Optional[str] = None
) -> MultiFacetedEmbedding:
    """
    Algebraic vector composition operator: z12 = z2 o z1 (First z1, then z2).
    Operates directly on the embedding vectors in R^D preserving:
      - Effect masking and accumulation
      - Weakest precondition satisfaction and pass-through
      - Additive log-operational attributes (cost, latency, log-reliability)
      - IO dataflow tracking
    """
    layout = z1.layout
    if layout.total_dim != z2.layout.total_dim:
        if z1.layout.total_dim < z2.layout.total_dim:
            z1 = z1.align_to_layout(z2.layout)
            layout = z2.layout
        else:
            z2 = z2.align_to_layout(z1.layout)
            layout = z1.layout

    vec = np.zeros(layout.total_dim, dtype=np.float64)

    # 1. Effect Subspace Composition
    # Effects of z2 override effects of z1; non-overwritten effects of z1 persist
    m_e1 = z1.eff_mask
    e_val1 = z1.eff_values
    m_e2 = z2.eff_mask
    e_val2 = z2.eff_values

    # Composite effect mask
    m_e12 = np.clip(m_e1 + m_e2, 0.0, 1.0)
    # Composite effect values: z2 overrides where m_e2 == 1, otherwise z1 persists
    e_val12 = m_e2 * e_val2 + (1.0 - m_e2) * (m_e1 * e_val1)

    vec[layout.eff_val_slice] = e_val12
    vec[layout.eff_mask_slice] = m_e12

    # 2. Precondition Subspace Composition (Weakest Precondition)
    # z1 preconditions are always required
    m_p1 = z1.req_mask
    p_val1 = z1.req_values
    m_p2 = z2.req_mask
    p_val2 = z2.req_values

    m_p12 = np.copy(m_p1)
    p_val12 = np.copy(p_val1)

    ds = layout.num_state_vars
    for k in range(ds):
        if m_p1[k] > 0:
            # Already in z1 preconditions
            pass
        elif m_p2[k] > 0:
            # z2 requires variable k
            if m_e1[k] > 0:
                # z1 touches variable k!
                # If z1 produces what z2 needs, precondition is satisfied internally!
                if abs(e_val1[k] - p_val2[k]) < 1e-4:
                    # Satisfied internally: does not appear in composite external preconditions
                    m_p12[k] = 0.0
                    p_val12[k] = 0.0
                else:
                    # Incompatible effect conflict: flag with high negative coefficient
                    m_p12[k] = 1.0
                    p_val12[k] = -999.0
            else:
                # z1 does not touch variable k, so precondition passes through to composite
                m_p12[k] = 1.0
                p_val12[k] = p_val2[k]

    vec[layout.req_val_slice] = p_val12
    vec[layout.req_mask_slice] = m_p12

    # 3. Input-Output Subspace Composition
    # Composite input: z1 inputs + (z2 inputs - z1 outputs)
    io_in1 = z1.io_inputs
    io_out1 = z1.io_outputs
    io_in2 = z2.io_inputs
    io_out2 = z2.io_outputs

    # Approximate dataflow cancellation: inputs of z2 satisfied by outputs of z1
    unresolved_z2_in = np.maximum(0.0, io_in2 - 0.7 * io_out1)
    composite_in = io_in1 + unresolved_z2_in
    norm_in = np.linalg.norm(composite_in)
    if norm_in > 1e-12:
        composite_in /= norm_in
    vec[layout.io_in_slice] = composite_in

    composite_out = 0.5 * io_out1 + 0.8 * io_out2
    norm_out = np.linalg.norm(composite_out)
    if norm_out > 1e-12:
        composite_out /= norm_out
    vec[layout.io_out_slice] = composite_out

    # 4. Operational Quality Composition
    # Coordinates: [T, C_money, C_res, C_energy, -log(Rel), -log(Avail), Risk, Resources...]
    # In negative log space, reliability and availability compose strictly additively!
    ops1 = z1.operational_vector
    ops2 = z2.operational_vector
    composite_ops = np.zeros_like(ops1)

    # Additive costs, latencies, and log-dependabilities
    composite_ops[0] = ops1[0] + ops2[0]  # Latency
    composite_ops[1] = ops1[1] + ops2[1]  # Money
    composite_ops[2] = ops1[2] + ops2[2]  # Resource cost
    composite_ops[3] = ops1[3] + ops2[3]  # Energy
    composite_ops[4] = ops1[4] + ops2[4]  # -log(Rel)
    composite_ops[5] = ops1[5] + ops2[5]  # -log(Avail)
    # Risk union: 1 - (1 - r1)(1 - r2)
    r1, r2 = np.clip(ops1[6], 0.0, 1.0), np.clip(ops2[6], 0.0, 1.0)
    composite_ops[6] = 1.0 - (1.0 - r1) * (1.0 - r2)

    # Resource requirements union / sum
    num_scalars = layout.num_ops_scalars
    if len(ops1) > num_scalars:
        res1 = ops1[num_scalars:]
        res2 = ops2[num_scalars:]
        composite_ops[num_scalars:] = res1 + res2

    vec[layout.ops_slice] = composite_ops

    # 5. Implementation Mechanism
    # Composite capability is categorized as SERVICE (type index 8)
    impl_vec = np.zeros(layout.impl_dim, dtype=np.float64)
    impl_vec[min(8, layout.impl_dim - 1)] = 1.0  # SERVICE type
    # Blend sub-capability mechanism signatures
    impl_vec += 0.3 * (z1.implementation_vector + z2.implementation_vector)
    norm_impl = np.linalg.norm(impl_vec)
    if norm_impl > 1e-12:
        impl_vec /= norm_impl
    vec[layout.impl_slice] = impl_vec

    composite_name = name or f"({z2.name} o {z1.name})"
    return MultiFacetedEmbedding(vec, layout, name=composite_name, entity_type="composite_capability")


def compose_vector_sequence(
    embeddings: Sequence[MultiFacetedEmbedding],
    name: Optional[str] = None
) -> MultiFacetedEmbedding:
    """
    Sequentially compose an arbitrary sequence of embeddings:
      z_1..n = zn o ... o z2 o z1.
    """
    if not embeddings:
        raise ValueError("Cannot compose empty sequence of embeddings.")
    if len(embeddings) == 1:
        return embeddings[0]

    current = embeddings[0]
    for nxt in embeddings[1:]:
        current = compose_embeddings(current, nxt)

    if name:
        current.name = name
    return current
