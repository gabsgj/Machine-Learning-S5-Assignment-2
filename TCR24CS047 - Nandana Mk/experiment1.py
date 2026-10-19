from data.capabilities import capabilities
from embeddings.composer import Composer
from embeddings.encoder import Encoder


def run():

    create_order = capabilities[0]
    make_payment = capabilities[1]
    cancel_cart = capabilities[3]

    print("=" * 50)
    print("EXPERIMENT 1")
    print("Capability Compatibility")
    print("=" * 50)

    print("\nCreateOrder Vector")
    print(Encoder.encode_capability(create_order))

    print("\nMakePayment Vector")
    print(Encoder.encode_capability(make_payment))

    print("\nCancelCart Vector")
    print(Encoder.encode_capability(cancel_cart))

    print("\nCompatibility Results")

    print(
        "CreateOrder -> MakePayment :",
        Composer.are_compatible(create_order, make_payment)
    )

    print(
        "CreateOrder -> CancelCart :",
        Composer.are_compatible(create_order, cancel_cart)
    )