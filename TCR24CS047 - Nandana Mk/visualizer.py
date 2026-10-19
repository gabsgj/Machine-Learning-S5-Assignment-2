import matplotlib.pyplot as plt
import numpy as np


class Visualizer:

    @staticmethod
    def similarity_matrix(labels, matrix):

        print("\nSimilarity Matrix")
        print("-" * 50)

        print("          ", end="")
        for label in labels:
            print(f"{label:>12}", end="")
        print()

        for i, row in enumerate(matrix):
            print(f"{labels[i]:<10}", end="")
            for value in row:
                print(f"{value:12.4f}", end="")
            print()

    @staticmethod
    def heatmap(labels, matrix):

        plt.figure(figsize=(7, 6))

        plt.imshow(matrix, cmap="YlGnBu")

        plt.colorbar(label="Cosine Similarity")

        plt.xticks(np.arange(len(labels)), labels, rotation=45)

        plt.yticks(np.arange(len(labels)), labels)

        plt.title("Capability Similarity Heatmap")

        plt.tight_layout()

        plt.savefig("results/Similarity_Heatmap.png")

        plt.show()