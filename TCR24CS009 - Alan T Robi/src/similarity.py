import numpy as np
from typing import Optional
from src.encoder import CapabilityEncoder
from src.capability import Capability

def cosine_similarity(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute standard Cosine Similarity between two numerical vectors x and y:
    sim(x, y) = (x . y) / (||x||2 * ||y||2)
    """
    norm_x = np.linalg.norm(x)
    norm_y = np.linalg.norm(y)
    if norm_x == 0.0 or norm_y == 0.0:
        return 0.0
    val = np.dot(x, y) / (norm_x * norm_y)
    return float(np.clip(val, -1.0, 1.0))

def similarity(x: np.ndarray, y: np.ndarray) -> float:
    """Wrapper for cosine similarity between vector representations x and y."""
    return cosine_similarity(x, y)

def subvector_similarity(
    vec1: np.ndarray, 
    vec2: np.ndarray, 
    encoder: CapabilityEncoder, 
    block_name: str
) -> float:
    """Compute cosine similarity restricted to a specific structural block."""
    sub1 = encoder.get_subvector(vec1, block_name)
    sub2 = encoder.get_subvector(vec2, block_name)
    return cosine_similarity(sub1, sub2)

def functional_similarity(
    vec1: np.ndarray, 
    vec2: np.ndarray, 
    encoder: CapabilityEncoder
) -> float:
    """
    Compute functional resemblance by evaluating similarity over 
    Inputs, Outputs, Preconditions, and Effects sub-vectors only.
    """
    func_blocks = ["inputs", "outputs", "preconditions", "effects"]
    sub1_parts = [encoder.get_subvector(vec1, b) for b in func_blocks]
    sub2_parts = [encoder.get_subvector(vec2, b) for b in func_blocks]
    
    f1 = np.concatenate(sub1_parts)
    f2 = np.concatenate(sub2_parts)
    return cosine_similarity(f1, f2)
