from data.capabilities import capabilities
from embeddings.composer import Composer
from embeddings.encoder import Encoder
from embeddings.similarity import Similarity


def run():

    create_order = capabilities[0]
    make_payment = capabilities[1]

    print("=" * 50)
    print("EXPERIMENT 2")
    print("Capability Composition")
    print("=" * 50)

    composite = Composer.compose(create_order, make_payment)

    if composite is None:
        print("Composition Failed")
        return

    print("\nComposite Capability")
    print(composite)

    print("\nCreateOrder Vector")
    print(Encoder.encode_capability(create_order))

    print("\nMakePayment Vector")
    print(Encoder.encode_capability(make_payment))

    print("\nComposite Vector")
    print(Encoder.encode_capability(composite))

    print("\nSimilarity Scores")

    print(
        "CreateOrder vs Composite:",
        Similarity.cosine(
            Encoder.encode_capability(create_order),
            Encoder.encode_capability(composite)
        )
    )

    print(
        "MakePayment vs Composite:",
        Similarity.cosine(
            Encoder.encode_capability(make_payment),
            Encoder.encode_capability(composite)
        )
    )

    print(
        "Euclidean Distance:",
        Similarity.euclidean(
            Encoder.encode_capability(create_order),
            Encoder.encode_capability(composite)
        )
    )