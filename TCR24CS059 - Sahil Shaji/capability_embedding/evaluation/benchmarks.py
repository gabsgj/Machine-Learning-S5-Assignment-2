"""
Benchmarking and Consistency Evaluation (Section 8 Evaluation Criteria).
Profiles encoding latency, composition throughput, memory storage footprint, and consistency.
"""

import time
import sys
from typing import Dict, Any, List
import numpy as np

from ..embedding.encoder import CapabilityEmbeddingSystem
from ..embedding.algebra import compose_embeddings
from ..core.capability import Capability
from ..core.types import CapabilityType


def benchmark_system_performance(system: CapabilityEmbeddingSystem, sample_caps: List[Capability], num_runs: int = 1000) -> Dict[str, Any]:
    """
    Profiles computational and storage requirements (Section 8: Efficiency).
    Measures:
      - Mean encoding latency (microseconds)
      - Mean composition latency (microseconds)
      - Storage footprint per vector (bytes)
      - Throughput (operations per second)
    """
    if len(sample_caps) < 2:
        raise ValueError("Need at least 2 capabilities for benchmarking.")

    # 1. Encoding benchmark
    c0 = sample_caps[0]
    t0 = time.perf_counter()
    for _ in range(num_runs):
        _ = system.encode_capability(c0)
    t1 = time.perf_counter()
    avg_encode_us = ((t1 - t0) / num_runs) * 1e6
    encode_throughput = num_runs / (t1 - t0)

    # 2. Composition benchmark
    z0 = system.encode_capability(sample_caps[0])
    z1 = system.encode_capability(sample_caps[1])
    t0 = time.perf_counter()
    for _ in range(num_runs):
        _ = compose_embeddings(z0, z1)
    t1 = time.perf_counter()
    avg_compose_us = ((t1 - t0) / num_runs) * 1e6
    compose_throughput = num_runs / (t1 - t0)

    # 3. Storage footprint
    vector_bytes = z0.raw.nbytes
    layout_bytes = sys.getsizeof(z0.layout)

    return {
        "num_runs": num_runs,
        "total_vector_dim": z0.layout.total_dim,
        "avg_encode_latency_us": round(avg_encode_us, 2),
        "encode_throughput_ops_sec": round(encode_throughput, 1),
        "avg_compose_latency_us": round(avg_compose_us, 2),
        "compose_throughput_ops_sec": round(compose_throughput, 1),
        "raw_vector_bytes": vector_bytes,
        "total_object_bytes": sys.getsizeof(z0) + vector_bytes + layout_bytes
    }
