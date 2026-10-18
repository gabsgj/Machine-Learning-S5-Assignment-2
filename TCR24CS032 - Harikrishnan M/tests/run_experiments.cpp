#include <iostream>
#include <cassert>
#include <cmath>
#include "Capability.hpp"
#include "Embedding.hpp"

void test_compatibility()
{
    std::cout << "[RUNNING] Compatibility Score Test..." << std::endl;
    EmbeddingFramework framework(3);
    Capability c1("C1", "Cap1", "API", {1, 0, 0}, {0, 1, 0}, 10, 0.9, 0.9);
    Capability c2("C2", "Cap2", "API", {0, 1, 0}, {0, 0, 1}, 10, 0.9, 0.9);

    double score = framework.compute_compatibility(c1, c2);
    assert(std::abs(score - 1.0) < 1e-6);
    std::cout << "  -> Compatibility Test Passed! Score = " << score << std::endl;
}

void test_composition_math()
{
    std::cout << "[RUNNING] Composition Math Test..." << std::endl;
    EmbeddingFramework framework(3);
    Capability c1("C1", "Cap1", "API", {0.8, 0.2, 0.0}, {0.5, 0.9, 0.0}, 15.0, 0.95, 0.90);
    Capability c2("C2", "Cap2", "DB", {0.0, 0.4, 0.6}, {0.0, 0.0, 1.0}, 5.0, 0.98, 0.99);

    Capability c12 = framework.compose(c1, c2);

    // p12 = max(p1, max(0, p2 - e1))
    // index 0: max(0.8, max(0, 0.0 - 0.5)) = 0.8
    // index 1: max(0.2, max(0, 0.4 - 0.9)) = 0.2
    // index 2: max(0.0, max(0, 0.6 - 0.0)) = 0.6
    assert(std::abs(c12.preconditions[0] - 0.8) < 1e-6);
    assert(std::abs(c12.preconditions[1] - 0.2) < 1e-6);
    assert(std::abs(c12.preconditions[2] - 0.6) < 1e-6);

    // e12 = max(e1, e2)
    assert(std::abs(c12.effects[2] - 1.0) < 1e-6);

    // Attributes
    assert(std::abs(c12.cost - 20.0) < 1e-6);
    assert(std::abs(c12.reliability - (0.95 * 0.98)) < 1e-6);
    assert(std::abs(c12.availability - 0.90) < 1e-6);

    std::cout << "  -> Composition Math Test Passed!" << std::endl;
}

void test_alternative_implementations()
{
    std::cout << "[RUNNING] Alternative Implementations Similarity Test..." << std::endl;
    Capability c_api("C_API", "Auth API", "API", {1, 0, 0}, {0, 1, 0}, 1.0, 0.99, 0.99);
    Capability c_db("C_DB", "Auth DB", "DB", {1, 0, 0}, {0, 1, 0}, 0.2, 0.95, 0.90);

    auto v1 = c_api.to_embedding_vector();
    auto v2 = c_db.to_embedding_vector();

    double sim = EmbeddingFramework::cosine_similarity(v1, v2);
    std::cout << "  -> Cosine Similarity (API vs DB implementation): " << sim << std::endl;
    assert(sim > 0.85); // High functional similarity despite operational variance
}

int main()
{
    std::cout << "==========================================" << std::endl;
    std::cout << " Running Capability Composition Unit Tests " << std::endl;
    std::cout << "==========================================" << std::endl;

    test_compatibility();
    test_composition_math();
    test_alternative_implementations();

    std::cout << "\nAll Experimental Suite Tests Passed Successfully!" << std::endl;
    return 0;
}