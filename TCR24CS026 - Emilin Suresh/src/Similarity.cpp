#include "../include/Similarity.h"

#include <cmath>

double Similarity::cosine(
    const FeatureVector& a,
    const FeatureVector& b
)
{
    if (a.size() != b.size() ||
        a.empty())
    {
        return 0.0;
    }

    double dot = 0.0;
    double normA = 0.0;
    double normB = 0.0;

    for (std::size_t i = 0;
         i < a.size();
         ++i)
    {
        dot += a[i] * b[i];

        normA +=
            a[i] * a[i];

        normB +=
            b[i] * b[i];
    }

    if (normA == 0.0 ||
        normB == 0.0)
    {
        return 0.0;
    }

    return dot /
        (
            std::sqrt(normA) *
            std::sqrt(normB)
        );
}