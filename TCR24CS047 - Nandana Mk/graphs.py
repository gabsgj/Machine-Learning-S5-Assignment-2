import matplotlib.pyplot as plt


class Graphs:

    @staticmethod
    def similarity_bar(labels, values, title):

        plt.figure(figsize=(8, 5))

        plt.bar(labels, values)

        plt.title(title)

        plt.xlabel("Comparison")

        plt.ylabel("Cosine Similarity")

        plt.ylim(0, 1)

        plt.grid(axis="y", linestyle="--", alpha=0.6)

        plt.tight_layout()

        plt.savefig("results/" + title.replace(" ", "_") + ".png")

        plt.show()

    @staticmethod
    def execution_time_bar(labels, values):

        plt.figure(figsize=(8, 5))

        plt.bar(labels, values)

        plt.title("Execution Time Comparison")

        plt.xlabel("Capability")

        plt.ylabel("Execution Time (ms)")

        plt.grid(axis="y", linestyle="--", alpha=0.6)

        plt.tight_layout()

        plt.savefig("results/Execution_Time.png")

        plt.show()

    @staticmethod
    def reliability_bar(labels, values):

        plt.figure(figsize=(8, 5))

        plt.bar(labels, values)

        plt.title("Reliability Comparison")

        plt.xlabel("Capability")

        plt.ylabel("Reliability")

        plt.ylim(0.9, 1.0)

        plt.grid(axis="y", linestyle="--", alpha=0.6)

        plt.tight_layout()

        plt.savefig("results/Reliability.png")

        plt.show()