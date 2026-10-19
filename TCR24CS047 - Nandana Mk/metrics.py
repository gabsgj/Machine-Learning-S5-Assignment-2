from embeddings.similarity import Similarity


class Metrics:

    @staticmethod
    def cosine(vec1, vec2):
        return Similarity.cosine(vec1, vec2)

    @staticmethod
    def euclidean(vec1, vec2):
        return Similarity.euclidean(vec1, vec2)

    @staticmethod
    def compare(name1, vec1, name2, vec2):

        cosine = Metrics.cosine(vec1, vec2)
        euclidean = Metrics.euclidean(vec1, vec2)

        print("=" * 50)
        print(f"{name1} vs {name2}")
        print("=" * 50)
        print(f"Cosine Similarity : {cosine:.4f}")
        print(f"Euclidean Distance: {euclidean:.4f}")

        return {
            "cosine": cosine,
            "euclidean": euclidean
        }