from data.capabilities import capabilities
from embeddings.encoder import Encoder
from evaluation.metrics import Metrics
from evaluation.visualizer import Visualizer


class Evaluator:

    @staticmethod
    def evaluate():

        print("=" * 60)
        print("FINAL EVALUATION")
        print("=" * 60)

        # Capabilities used in Experiment 3
        api = capabilities[4]
        gui = capabilities[5]
        database = capabilities[6]

        api_vector = Encoder.encode_capability(api)
        gui_vector = Encoder.encode_capability(gui)
        db_vector = Encoder.encode_capability(database)

        # Pairwise comparison
        Metrics.compare("API", api_vector, "GUI", gui_vector)
        Metrics.compare("API", api_vector, "DATABASE", db_vector)
        Metrics.compare("GUI", gui_vector, "DATABASE", db_vector)

        # Similarity Matrix
        matrix = [
            [
                1.0,
                Metrics.cosine(api_vector, gui_vector),
                Metrics.cosine(api_vector, db_vector)
            ],
            [
                Metrics.cosine(gui_vector, api_vector),
                1.0,
                Metrics.cosine(gui_vector, db_vector)
            ],
            [
                Metrics.cosine(db_vector, api_vector),
                Metrics.cosine(db_vector, gui_vector),
                1.0
            ]
        ]

        labels = ["API", "GUI", "DATABASE"]

        Visualizer.similarity_matrix(labels, matrix)
        Visualizer.heatmap(labels, matrix)

        print("\nEvaluation Completed Successfully!")