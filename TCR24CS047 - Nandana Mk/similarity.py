import numpy as np


class Similarity:

    @staticmethod
    def cosine(v1, v2):

        numerator = np.dot(v1, v2)

        denominator = np.linalg.norm(v1) * np.linalg.norm(v2)

        if denominator == 0:
            return 0

        return numerator / denominator

    @staticmethod
    def euclidean(v1, v2):

        return np.linalg.norm(v1 - v2)