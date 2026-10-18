import numpy as np

from src.capability_embedding import similarity


def test_similarity_is_symmetric():
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 1.0, 4.0])
    assert np.isclose(similarity(x, y), similarity(y, x))


def test_similarity_of_identical_nonzero_vectors_is_one():
    x = np.array([1.0, -2.0, 3.0])
    assert np.isclose(similarity(x, x), 1.0)


def test_similarity_of_orthogonal_vectors_is_zero():
    x = np.array([1.0, 0.0])
    y = np.array([0.0, 1.0])
    assert np.isclose(similarity(x, y), 0.0)
