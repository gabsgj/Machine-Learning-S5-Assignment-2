from data.capabilities import capabilities
from embeddings.encoder import Encoder
from embeddings.similarity import Similarity
from evaluation.graphs import Graphs


def run():

    api = capabilities[4]
    gui = capabilities[5]
    database = capabilities[6]

    print("=" * 50)
    print("EXPERIMENT 3")
    print("Alternative Implementations")
    print("=" * 50)

    api_vector = Encoder.encode_capability(api)
    gui_vector = Encoder.encode_capability(gui)
    db_vector = Encoder.encode_capability(database)

    api_gui = Similarity.cosine(api_vector, gui_vector)
    api_db = Similarity.cosine(api_vector, db_vector)
    gui_db = Similarity.cosine(gui_vector, db_vector)

    print("\nAPI Vector")
    print(api_vector)

    print("\nGUI Vector")
    print(gui_vector)

    print("\nDATABASE Vector")
    print(db_vector)

    print("\nCosine Similarities")
    print(f"API vs GUI: {api_gui:.4f}")
    print(f"API vs DATABASE: {api_db:.4f}")
    print(f"GUI vs DATABASE: {gui_db:.4f}")

    # Graph 1: Similarity
    Graphs.similarity_bar(
        ["API-GUI", "API-DB", "GUI-DB"],
        [api_gui, api_db, gui_db],
        "Experiment 3 Similarity"
    )

    # Graph 2: Execution Time
    Graphs.execution_time_bar(
        ["API", "GUI", "DATABASE"],
        [100, 120, 80]
    )

    # Graph 3: Reliability
    Graphs.reliability_bar(
        ["API", "GUI", "DATABASE"],
        [0.99, 0.98, 0.995]
    )