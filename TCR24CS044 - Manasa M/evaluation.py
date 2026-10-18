import numpy as np
import matplotlib.pyplot as plt

from embedding import encode_capability, similarity


def print_vectors(capabilities):

    print("\n========== CAPABILITY VECTORS ==========\n")

    for capability in capabilities:

        vector = encode_capability(capability)

        print(capability.name)
        print(vector)
        print()


def compare_capabilities(capability1, capability2):

    vector1 = encode_capability(capability1)
    vector2 = encode_capability(capability2)

    score = similarity(vector1, vector2)

    return score


def plot_cost(capabilities):

    names = [c.name for c in capabilities]
    costs = [c.cost for c in capabilities]

    plt.figure(figsize=(10, 5))
    plt.bar(names, costs)
    plt.xlabel("Capability")
    plt.ylabel("Cost")
    plt.title("Capability Cost Comparison")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("results/cost.png")
    plt.close()


def plot_reliability(capabilities):

    names = [c.name for c in capabilities]
    reliability = [c.reliability for c in capabilities]

    plt.figure(figsize=(10, 5))
    plt.bar(names, reliability)
    plt.xlabel("Capability")
    plt.ylabel("Reliability")
    plt.title("Capability Reliability Comparison")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("results/reliability.png")
    plt.close()


def plot_similarity(capabilities):

    names = [c.name for c in capabilities]

    vectors = [
        encode_capability(c)
        for c in capabilities
    ]

    matrix = np.zeros(
        (len(capabilities), len(capabilities))
    )

    for i in range(len(capabilities)):

        for j in range(len(capabilities)):

            matrix[i][j] = similarity(
                vectors[i],
                vectors[j]
            )

    plt.figure(figsize=(8, 6))

    plt.imshow(matrix)

    plt.xticks(
        range(len(names)),
        names,
        rotation=45,
        ha="right"
    )

    plt.yticks(
        range(len(names)),
        names
    )

    plt.colorbar(label="Cosine Similarity")

    plt.title("Capability Similarity Matrix")

    plt.tight_layout()

    plt.savefig("results/similarity.png")

    plt.close()