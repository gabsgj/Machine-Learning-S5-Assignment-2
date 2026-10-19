from data.capabilities import capabilities
from embeddings.encoder import Encoder
from embeddings.similarity import Similarity


def run():

    create_order = capabilities[0]

    play_music = capabilities[7]
    change_theme = capabilities[8]
    backup_logs = capabilities[9]

    print("=" * 50)
    print("EXPERIMENT 4")
    print("Irrelevant Capabilities")
    print("=" * 50)

    order_vector = Encoder.encode_capability(create_order)

    for capability in [play_music, change_theme, backup_logs]:

        vector = Encoder.encode_capability(capability)

        similarity = Similarity.cosine(order_vector, vector)

        print(f"\n{capability.name}")

        print(vector)

        print("Similarity:", similarity)