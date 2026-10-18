#include "similarity.hpp"
#include <cmath>

double cosineSimilarity(
    const std::vector<double>& a,
    const std::vector<double>& b
) {

    double dotProduct = 0;
    double magnitudeA = 0;
    double magnitudeB = 0;

    for (int i = 0; i < a.size(); i++) {

        dotProduct += a[i] * b[i];

        magnitudeA += a[i] * a[i];

        magnitudeB += b[i] * b[i];
    }

    if (magnitudeA == 0 || magnitudeB == 0)
        return 0;

    return dotProduct /
           (std::sqrt(magnitudeA) * std::sqrt(magnitudeB));
}