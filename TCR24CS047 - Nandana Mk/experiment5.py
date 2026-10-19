from data.capabilities import capabilities
from embeddings.encoder import Encoder
from embeddings.similarity import Similarity


def run():

    fast = capabilities[10]
    slow = capabilities[11]

    print("=" * 50)
    print("EXPERIMENT 5")
    print("Operational Attributes")
    print("=" * 50)

    fast_vector = Encoder.encode_capability(fast)
    slow_vector = Encoder.encode_capability(slow)

    print("\nFast Payment")
    print(fast_vector)

    print("\nSlow Payment")
    print(slow_vector)

    print("\nCosine Similarity")

    print(
        Similarity.cosine(
            fast_vector,
            slow_vector
        )
    )

    print("\nEuclidean Distance")

    print(
        Similarity.euclidean(
            fast_vector,
            slow_vector
        )
    )