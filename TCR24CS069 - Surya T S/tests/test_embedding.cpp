#include "../include/types.hpp"
#include "../include/embedding.hpp"
#include "../include/json_loader.hpp"
#include <iostream>
#include <cassert>
#include <cmath>

using namespace capability_embedding;

int g_passedTests = 0;
int g_failedTests = 0;

void testAssert(bool condition, const std::string& testName) {
    if (condition) {
        std::cout << "[PASS] " << testName << "\n";
        g_passedTests++;
    } else {
        std::cerr << "[FAIL] " << testName << "\n";
        g_failedTests++;
    }
}

int main() {
    std::cout << "======================================================================\n";
    std::cout << "AUTOMATED UNIT TEST SUITE: VECTOR EMBEDDING & CAPABILITY COMPOSITION\n";
    std::cout << "======================================================================\n";

    VectorEmbeddingEngine engine;
    ApplicationProblem app = JsonLoader::loadApplication("data/ecommerce_basic.json");

    const Capability* cCreate = nullptr;
    const Capability* cPay = nullptr;
    const Capability* cNotify = nullptr;
    const Capability* cCancel = nullptr;

    for (const auto& c : app.capabilities) {
        if (c.id == "CreateOrder") cCreate = &c;
        if (c.id == "MakePayment") cPay = &c;
        if (c.id == "SendNotification") cNotify = &c;
        if (c.id == "CancelCart") cCancel = &c;
    }

    assert(cCreate && cPay && cNotify && cCancel);

    // -------------------------------------------------------------------------
    // Test 1: State encoding dimension & bipolar values
    // -------------------------------------------------------------------------
    {
        auto sVec = engine.encodeState(app.initialState);
        bool validDim = (sVec.size() == 11);
        bool validValues = true;
        for (double v : sVec) {
            if (std::abs(v - 1.0) > 1e-6 && std::abs(v - (-1.0)) > 1e-6) {
                validValues = false;
            }
        }
        testAssert(validDim && validValues, "1. State encoding dimension == 11 and values in {-1, +1}");
    }

    // -------------------------------------------------------------------------
    // Test 2: Goal encoding dimension & ternary values
    // -------------------------------------------------------------------------
    {
        auto gVec = engine.encodeGoal(app.goal);
        bool validDim = (gVec.size() == 11);
        bool validValues = true;
        for (double v : gVec) {
            if (std::abs(v) > 1e-6 && std::abs(v - 1.0) > 1e-6 && std::abs(v - (-1.0)) > 1e-6) {
                validValues = false;
            }
        }
        // order_exists is index 5, payment_success is index 7, notification_sent is index 8
        bool correctGoals = (std::abs(gVec[5] - 1.0) < 1e-6 &&
                             std::abs(gVec[7] - 1.0) < 1e-6 &&
                             std::abs(gVec[8] - 1.0) < 1e-6 &&
                             std::abs(gVec[0]) < 1e-6);
        testAssert(validDim && validValues && correctGoals, "2. Goal encoding dimension == 11 and ternary values in {-1, 0, +1}");
    }

    // -------------------------------------------------------------------------
    // Test 3: CreateOrder capability vector encoding
    // -------------------------------------------------------------------------
    {
        auto v = engine.encodeCapability(*cCreate);
        bool validDim = (v.size() == 36);
        // Precondition block (0-10): cart_exists(idx 2)==+1, cart_has_items(idx 3)==+1
        bool preOk = (std::abs(v[2] - 1.0) < 1e-6 && std::abs(v[3] - 1.0) < 1e-6);
        // Effect block (11-21): order_exists(11+5=16)==+1, order_created(11+6=17)==+1
        bool effOk = (std::abs(v[16] - 1.0) < 1e-6 && std::abs(v[17] - 1.0) < 1e-6);
        testAssert(validDim && preOk && effOk, "3. CreateOrder vector correctly encodes preconditions and effects");
    }

    // -------------------------------------------------------------------------
    // Test 4: MakePayment capability vector encoding
    // -------------------------------------------------------------------------
    {
        auto v = engine.encodeCapability(*cPay);
        bool validDim = (v.size() == 36);
        // Precondition: order_exists(idx 5)==+1
        bool preOk = (std::abs(v[5] - 1.0) < 1e-6);
        // Effect: payment_success(idx 11+7=18)==+1
        bool effOk = (std::abs(v[18] - 1.0) < 1e-6);
        testAssert(validDim && preOk && effOk, "4. MakePayment vector correctly encodes preconditions and effects");
    }

    // -------------------------------------------------------------------------
    // Test 5: Cosine similarity reflexivity, symmetry, and zero-vector safety
    // -------------------------------------------------------------------------
    {
        auto v1 = engine.encodeCapability(*cCreate);
        auto v2 = engine.encodeCapability(*cPay);
        std::vector<double> zeroVec(36, 0.0);

        double selfSim = VectorEmbeddingEngine::similarity(v1, v1);
        double sim12 = VectorEmbeddingEngine::similarity(v1, v2);
        double sim21 = VectorEmbeddingEngine::similarity(v2, v1);
        double zeroSim = VectorEmbeddingEngine::similarity(v1, zeroVec);

        bool reflexive = std::abs(selfSim - 1.0) < 1e-6;
        bool symmetric = std::abs(sim12 - sim21) < 1e-6;
        bool safeZero = std::abs(zeroSim) < 1e-6;

        testAssert(reflexive && symmetric && safeZero, "5. Cosine similarity reflexivity, symmetry, and zero-vector safety");
    }

    // -------------------------------------------------------------------------
    // Test 6: CreateOrder -> MakePayment compatibility == +1.0000
    // -------------------------------------------------------------------------
    {
        double comp = engine.compatibility(*cCreate, *cPay);
        testAssert(std::abs(comp - 1.0) < 1e-6, "6. Precondition-effect compatibility: CreateOrder -> MakePayment == +1.0000");
    }

    // -------------------------------------------------------------------------
    // Test 7: CreateOrder -> CancelCart compatibility == -1.0000
    // -------------------------------------------------------------------------
    {
        double comp = engine.compatibility(*cCreate, *cCancel);
        testAssert(std::abs(comp - (-1.0)) < 1e-6, "7. Precondition-effect incompatibility: CreateOrder -> CancelCart == -1.0000");
    }

    // -------------------------------------------------------------------------
    // Test 8: Capability composition: Internal precondition satisfaction & pruning
    // -------------------------------------------------------------------------
    {
        Capability comp12 = engine.compose(*cCreate, *cPay);
        bool hasCartPre = false;
        bool hasOrderPre = false;
        for (const auto& p : comp12.preconditions) {
            if (p.variable == "cart_exists") hasCartPre = true;
            if (p.variable == "order_exists") hasOrderPre = true;
        }
        testAssert(hasCartPre && !hasOrderPre, "8. Capability composition prunes internally satisfied preconditions");
    }

    // -------------------------------------------------------------------------
    // Test 9: Reliability multiplication
    // -------------------------------------------------------------------------
    {
        Capability comp12 = engine.compose(*cCreate, *cPay);
        double expectedRel = cCreate->reliability * cPay->reliability;
        testAssert(std::abs(comp12.reliability - expectedRel) < 1e-7, "9. Operational reliability aggregates multiplicatively");
    }

    // -------------------------------------------------------------------------
    // Test 10: Operational cost aggregation (additive)
    // -------------------------------------------------------------------------
    {
        Capability comp12 = engine.compose(*cCreate, *cPay);
        double expectedTime = cCreate->qos.timeCostMs + cPay->qos.timeCostMs;
        double expectedMoney = cCreate->qos.moneyCost + cPay->qos.moneyCost;
        double expectedResource = cCreate->qos.resourceCost + cPay->qos.resourceCost;

        bool timeOk = std::abs(comp12.qos.timeCostMs - expectedTime) < 1e-6;
        bool moneyOk = std::abs(comp12.qos.moneyCost - expectedMoney) < 1e-6;
        bool resOk = std::abs(comp12.qos.resourceCost - expectedResource) < 1e-6;

        testAssert(timeOk && moneyOk && resOk, "10. Operational latency, monetary cost, and resources aggregate additively");
    }

    // -------------------------------------------------------------------------
    // Test 11: Availability aggregation
    // -------------------------------------------------------------------------
    {
        Capability cUnavail = *cCreate;
        cUnavail.availability = 0.0;
        Capability compNormal = engine.compose(*cCreate, *cPay);
        Capability compBlocked = engine.compose(cUnavail, *cPay);

        bool normalAvail = (compNormal.availability > 0.5);
        bool blockedAvail = (compBlocked.availability < 0.5);

        testAssert(normalAvail && blockedAvail, "11. Composite availability reflects conjunction of component availability");
    }

    // -------------------------------------------------------------------------
    // Test 12: Input-Output Compatibility
    // -------------------------------------------------------------------------
    {
        double ioMatch = engine.inputOutputCompatibility(*cCreate, *cPay);
        double ioNoMatch = engine.inputOutputCompatibility(*cCancel, *cPay);

        bool matchOk = std::abs(ioMatch - 1.0) < 1e-6;      // cPay requires order_id:UUID, cCreate outputs order_id:UUID
        bool noMatchOk = std::abs(ioNoMatch - 0.0) < 1e-6;   // cCancel produces nothing

        testAssert(matchOk && noMatchOk, "12. Input-output compatibility matches port signatures correctly");
    }

    std::cout << "\n======================================================================\n";
    std::cout << "TEST SUMMARY: " << g_passedTests << " PASSED, " << g_failedTests << " FAILED\n";
    std::cout << "======================================================================\n";

    return (g_failedTests == 0) ? 0 : 1;
}
