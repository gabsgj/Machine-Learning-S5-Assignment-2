#include "Embedding.h"
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

using namespace capembed;

DataSpec data(const std::string& name, const std::string& type = "STRING",
              const std::string& domain = "ANY", bool required = true) {
    return {name, type, domain, required};
}

Capability createOrderAPI() {
    Capability c;
    c.name = "CreateOrder_API";
    c.type = CapabilityType::API;
    c.mechanism = "POST /orders";
    c.inputs = {data("cart_id", "UUID", "validUUIDs")};
    c.outputs = {data("order_id", "UUID", "validUUIDs")};
    c.preconditions = {{"Cart.exists", "true"}};
    c.effects = {{"Order.exists", "true"}, {"Order.status", "CREATED"}};
    c.constraints = {"quantity>0", "quantity<=inventory_available"};
    c.resources = {"ORDER_DB", "NETWORK"};
    c.cost = 15.0; c.reliability = 0.99; c.availability = 0.995;
    return c;
}

Capability makePaymentAPI() {
    Capability c;
    c.name = "MakePayment_API";
    c.type = CapabilityType::API;
    c.mechanism = "POST /payments";
    c.inputs = {data("order_id", "UUID", "validUUIDs")};
    c.outputs = {data("payment_id", "UUID", "validUUIDs")};
    c.preconditions = {{"Order.exists", "true"}};
    c.effects = {{"Payment.status", "SUCCESS"}};
    c.constraints = {"payment_amount<=transaction_limit"};
    c.resources = {"PAYMENT_GATEWAY", "NETWORK"};
    c.cost = 25.0; c.reliability = 0.98; c.availability = 0.990;
    return c;
}

Capability sendNotification() {
    Capability c;
    c.name = "SendNotification";
    c.type = CapabilityType::SERVICE;
    c.mechanism = "NOTIFICATION_SERVICE";
    c.inputs = {data("payment_id", "UUID", "validUUIDs")};
    c.outputs = {data("notification_id", "UUID", "validUUIDs")};
    c.preconditions = {{"Payment.status", "SUCCESS"}};
    c.effects = {{"Notification.sent", "true"}};
    c.resources = {"EXTERNAL_SERVICE", "NETWORK"};
    c.cost = 5.0; c.reliability = 0.995; c.availability = 0.999;
    return c;
}

Capability cancelCart() {
    Capability c;
    c.name = "CancelCart";
    c.type = CapabilityType::FUNCTION;
    c.mechanism = "CANCEL_CART";
    c.preconditions = {{"Order.exists", "false"}};
    c.effects = {{"Cart.exists", "false"}};
    c.cost = 3.0; c.reliability = 0.99; c.availability = 0.99;
    return c;
}

Capability playMusic() {
    Capability c;
    c.name = "PlayMusic";
    c.type = CapabilityType::SERVICE;
    c.mechanism = "AUDIO";
    c.preconditions = {{"User.authenticated", "true"}};
    c.effects = {{"Error", "false"}};
    c.resources = {"EXTERNAL_SERVICE"};
    c.cost = 1.0; c.reliability = 0.99; c.availability = 0.99;
    return c;
}

Capability createOrderGUI() {
    auto c = createOrderAPI();
    c.name = "CreateOrder_GUI";
    c.type = CapabilityType::GUI;
    c.mechanism = "CLICK submit_button";
    c.cost = 12.0; c.reliability = 0.97; c.availability = 0.99;
    return c;
}

Capability createOrderDB() {
    auto c = createOrderAPI();
    c.name = "CreateOrder_DATABASE";
    c.type = CapabilityType::DATABASE;
    c.mechanism = "INSERT orders";
    c.cost = 8.0; c.reliability = 0.995; c.availability = 0.998;
    return c;
}

void printCapability(const Capability& c) {
    std::cout << c.name << "\n"
              << "  cost=" << c.cost
              << ", reliability=" << c.reliability
              << ", availability=" << c.availability << "\n";
}

int main() {
    EmbeddingEngine engine;
    std::cout << std::fixed << std::setprecision(4);

    std::cout << "==============================================\n";
    std::cout << "Assignment 2: Capability Embedding Experiments\n";
    std::cout << "==============================================\n\n";

    // Experiment 1
    std::cout << "[Experiment 1] Capability Compatibility\n";
    auto create = createOrderAPI();
    auto pay = makePaymentAPI();
    auto cancel = cancelCart();

    auto r1 = engine.checkCompatibility(create, pay);
    auto r2 = engine.checkCompatibility(create, cancel);

    std::cout << "CreateOrder -> MakePayment: "
              << (r1.compatible ? "TRUE" : "FALSE") << "\n";
    std::cout << "  " << r1.explanation << "\n";
    std::cout << "CreateOrder -> CancelCart: "
              << (r2.compatible ? "TRUE" : "FALSE") << "\n";
    std::cout << "  " << r2.explanation << "\n\n";

    assert(r1.compatible);
    assert(!r2.compatible);

    // Experiment 2
    std::cout << "[Experiment 2] Sequential Capability Composition\n";
    auto notify = sendNotification();
    auto complete = engine.composeChain({create, pay, notify});
    printCapability(complete);

    std::cout << "Combined cost = 15 + 25 + 5 = " << complete.cost << "\n";
    std::cout << "Combined reliability = 0.99 * 0.98 * 0.995 = "
              << complete.reliability << "\n";
    std::cout << "Combined availability = 0.995 * 0.990 * 0.999 = "
              << complete.availability << "\n";

    auto direct = engine.compose(engine.compose(create, pay), notify);
    auto chainVector = engine.encodeCapability(complete);
    auto directVector = engine.encodeCapability(direct);
    std::cout << "Cosine similarity (chain vs direct composition) = "
              << engine.cosineSimilarity(chainVector, directVector) << "\n\n";

    assert(std::fabs(complete.cost - 45.0) < 1e-9);
    assert(std::fabs(complete.reliability - 0.965349) < 1e-6);
    assert(std::fabs(complete.availability - 0.984065) < 1e-6);
    assert(engine.cosineSimilarity(chainVector, directVector) > 0.9999);

    // Experiment 3
    std::cout << "[Experiment 3] Alternative Implementations\n";
    auto gui = createOrderGUI();
    auto db = createOrderDB();
    std::vector<Capability> alts = {create, gui, db};

    std::cout << "Similarity matrix:\n       API     GUI     DB\n";
    for (std::size_t i = 0; i < alts.size(); ++i) {
        std::cout << (i == 0 ? "API " : i == 1 ? "GUI " : "DB  ");
        for (std::size_t j = 0; j < alts.size(); ++j)
            std::cout << std::setw(8)
                      << engine.cosineSimilarity(engine.encodeCapability(alts[i]),
                                                 engine.encodeCapability(alts[j]));
        std::cout << "\n";
    }
    std::cout << "Interpretation: same functional signature remains similar, "
                 "while type and operational attributes differentiate implementations.\n\n";

    // Experiment 4
    std::cout << "[Experiment 4] Goal Relevance\n";
    Goal goal{{{"Payment.status", "SUCCESS"}}};
    double paymentRel = engine.goalRelevance(pay, goal);
    double musicRel = engine.goalRelevance(playMusic(), goal);

    std::cout << "goalRelevance(MakePayment, Goal) = " << paymentRel << "\n";
    std::cout << "goalRelevance(PlayMusic, Goal) = " << musicRel << "\n\n";

    assert(std::fabs(paymentRel - 1.0) < 1e-9);
    assert(std::fabs(musicRel) < 1e-9);

    // Experiment 5
    std::cout << "[Experiment 5] Operational Attributes Influence\n";
    Capability baseline = create;
    baseline.name = "Baseline";
    Capability highCost = baseline; highCost.name = "HighCost"; highCost.cost = 250;
    Capability lowReliability = baseline; lowReliability.name = "LowReliability"; lowReliability.reliability = 0.40;
    Capability lowAvailability = baseline; lowAvailability.name = "LowAvailability"; lowAvailability.availability = 0.50;
    Capability budget = baseline; budget.name = "BudgetTier";
    budget.cost = 1; budget.reliability = 0.70; budget.availability = 0.80;

    for (const auto& c : {baseline, highCost, lowReliability, lowAvailability, budget}) {
        auto v = engine.encodeCapability(c);
        std::cout << std::setw(18) << c.name
                  << " cost=" << std::setw(6) << c.cost
                  << " rel=" << std::setw(6) << c.reliability
                  << " avail=" << std::setw(6) << c.availability
                  << " similarity_to_baseline="
                  << engine.cosineSimilarity(engine.encodeCapability(baseline), v)
                  << "\n";
    }

    std::cout << "\n[Vector dimensions] " << EMBEDDING_DIM << "\n";
    std::cout << "[All assertions passed]\n";
    return 0;
}
