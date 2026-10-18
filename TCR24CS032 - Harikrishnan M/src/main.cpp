#include <iostream>
#include <iomanip>
#include "Capability.hpp"
#include "Embedding.hpp"

int main()
{
    std::cout << "=== Capability Composition Framework Setup ===" << std::endl;

    size_t state_dim = 4; // d = 4
    EmbeddingFramework framework(state_dim);

    // Initialize Capability 1 (e.g., Data Fetcher API)
    Capability c1("C001", "FetchUserData", "API",
                  {1.0, 0.0, 0.0, 0.0}, // Preconditions (d=4)
                  {0.0, 1.0, 0.5, 0.0}, // Effects (d=4)
                  12.5,                 // Cost
                  0.99,                 // Reliability
                  0.95);                // Availability

    // Initialize Capability 2 (e.g., Data Transformer DB)
    Capability c2("C002", "TransformData", "DB",
                  {0.0, 1.0, 0.0, 0.0}, // Preconditions (d=4)
                  {0.0, 0.0, 1.0, 1.0}, // Effects (d=4)
                  5.0,                  // Cost
                  0.98,                 // Reliability
                  0.99);                // Availability

    std::cout << "C1 Dimension: " << c1.to_embedding_vector().size() << " (2d + 3 = 11)" << std::endl;

    double compat = framework.compute_compatibility(c1, c2);
    std::cout << "Compatibility Score <e1, p2>: " << compat << std::endl;

    Capability c12 = framework.compose(c1, c2);
    std::cout << "Composite ID: " << c12.id << std::endl;
    std::cout << "Composite Cost: $" << c12.cost << std::endl;
    std::cout << "Composite Reliability: " << c12.reliability * 100.0 << "%" << std::endl;

    return 0;
}