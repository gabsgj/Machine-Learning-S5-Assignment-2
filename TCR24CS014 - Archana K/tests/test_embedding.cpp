#include "Types.h"
#include "Embedding.h"
#include <iostream>
#include <iomanip>
#include <vector>
#include <cmath>
#include <cassert>

void printHeader(const std::string& title) {
    std::cout << "\n" << std::string(80, '=') << "\n";
    std::cout << "  " << title << "\n";
    std::cout << std::string(80, '=') << "\n";
}

void printSubHeader(const std::string& sub) {
    std::cout << "\n--- " << sub << " ---\n";
}

// ============================================================================
// Demonstration of State and Goal Modeling & Encoding
// ============================================================================
void runStateAndGoalDemo() {
    printHeader("STATE & GOAL FORMAL SPECIFICATION AND EMBEDDING");

    std::cout << "Embedding Layout Architecture:\n";
    std::cout << describeEmbeddingLayout() << "\n";

    // 1. Define State
    State state1;
    state1.set("User.authenticated", true);
    state1.set("Cart.exists", true);
    state1.set("Order.exists", false);

    std::cout << "Initial World " << state1.toString() << "\n\n";

    // 2. Define Goals
    Goal goal1("Order Creation Goal");
    goal1.addCondition("Order.exists", true);

    Goal goal2("Purchase Completion Goal");
    goal2.addCondition("Order.exists", true);
    goal2.addCondition("Payment.status", "SUCCESS");

    std::cout << goal1.toString() << "\n\n";
    std::cout << goal2.toString() << "\n\n";

    // 3. Encode into vectors
    std::vector<double> stateVec = encodeState(state1);
    std::vector<double> goal1Vec = encodeGoal(goal1);
    std::vector<double> goal2Vec = encodeGoal(goal2);

    printVector("State 1 Vector", stateVec, 16);
    printVector("Goal 1 Vector ", goal1Vec, 16);
    printVector("Goal 2 Vector ", goal2Vec, 16);

    std::cout << "\nState 1 satisfaction of Goal 1: "
              << (goal1.isSatisfied(state1) ? "SATISFIED" : "NOT SATISFIED") << "\n";
}

// ============================================================================
// EXPERIMENT 1: Capability Compatibility
// ============================================================================
void runExperiment1() {
    printHeader("EXPERIMENT 1: CAPABILITY COMPATIBILITY ANALYSIS");
    std::cout << "Objective: Test sequential pipeline compatibility (Output-Input & Effect-Precondition)\n";
    std::cout << "Expected: CreateOrder -> MakePayment is COMPATIBLE\n";
    std::cout << "          CreateOrder -> CancelCart is INCOMPATIBLE\n\n";

    // 1. CreateOrder
    Capability createOrder("CreateOrder", CapabilityType::API, "REST_HTTP_JSON");
    createOrder.addInput("cartId")
               .addInput("userId")
               .addOutput("orderId")
               .addOutput("amount")
               .addPrecondition("CartExists", true)
               .addEffect("OrderExists", true)
               .addConstraint("cart_not_empty")
               .addResource("ORDER_DB")
               .addResource("NETWORK")
               .setCost(15.0)
               .setReliability(0.99)
               .setAvailability(0.995);

    // 2. MakePayment
    Capability makePayment("MakePayment", CapabilityType::API, "PAYMENT_GATEWAY_RPC");
    makePayment.addInput("orderId")
               .addInput("amount")
               .addOutput("paymentId")
               .addOutput("receiptUrl")
               .addPrecondition("OrderExists", true)
               .addEffect("PaymentStatus", "SUCCESS")
               .addConstraint("valid_card")
               .addResource("PAYMENT_GATEWAY")
               .addResource("NETWORK")
               .setCost(25.0)
               .setReliability(0.98)
               .setAvailability(0.990);

    // 3. CancelCart
    Capability cancelCart("CancelCart", CapabilityType::API, "REST_HTTP_DELETE");
    cancelCart.addInput("cartId")
              .addOutput("cancellationStatus")
              .addPrecondition("OrderExists", false)
              .addEffect("CartExists", false)
              .addConstraint("cart_active")
              .addResource("CART_DB")
              .setCost(5.0)
              .setReliability(0.999)
              .setAvailability(0.999);

    std::cout << createOrder.toString() << "\n\n";
    std::cout << makePayment.toString() << "\n\n";
    std::cout << cancelCart.toString() << "\n\n";

    printSubHeader("Test 1.1: CreateOrder -> MakePayment");
    CompatibilityReport rep1 = checkCompatibility(createOrder, makePayment);
    std::cout << rep1.toString();
    bool comp1 = areCompatible(createOrder, makePayment);
    std::cout << ">> Result areCompatible(CreateOrder, MakePayment): "
              << (comp1 ? "TRUE (COMPATIBLE)" : "FALSE (INCOMPATIBLE)") << "\n";
    assert(comp1 == true);

    printSubHeader("Test 1.2: CreateOrder -> CancelCart");
    CompatibilityReport rep2 = checkCompatibility(createOrder, cancelCart);
    std::cout << rep2.toString();
    bool comp2 = areCompatible(createOrder, cancelCart);
    std::cout << ">> Result areCompatible(CreateOrder, CancelCart): "
              << (comp2 ? "TRUE (COMPATIBLE)" : "FALSE (INCOMPATIBLE)") << "\n";
    assert(comp2 == false);

    std::cout << "\n[Experiment 1 Passed]: Compatibility rules verified successfully!\n";
}

// ============================================================================
// EXPERIMENT 2: Capability Composition
// ============================================================================
void runExperiment2() {
    printHeader("EXPERIMENT 2: CAPABILITY COMPOSITION");
    std::cout << "Objective: Compose CreateOrder + MakePayment + SendNotification -> CompletePurchase\n";
    std::cout << "Verify merged inputs/outputs/preconditions/effects and combined operational attributes.\n\n";

    Capability createOrder("CreateOrder", CapabilityType::API, "REST_HTTP_JSON");
    createOrder.addInput("cartId")
               .addInput("userId")
               .addOutput("orderId")
               .addOutput("amount")
               .addPrecondition("CartExists", true)
               .addEffect("OrderExists", true)
               .addResource("ORDER_DB")
               .setCost(15.0)
               .setReliability(0.99)
               .setAvailability(0.995);

    Capability makePayment("MakePayment", CapabilityType::API, "PAYMENT_GATEWAY_RPC");
    makePayment.addInput("orderId")
               .addInput("amount")
               .addOutput("paymentId")
               .addOutput("receiptUrl")
               .addPrecondition("OrderExists", true)
               .addEffect("PaymentStatus", "SUCCESS")
               .addResource("PAYMENT_GATEWAY")
               .setCost(25.0)
               .setReliability(0.98)
               .setAvailability(0.990);

    Capability sendNotification("SendNotification", CapabilityType::MESSAGE, "SMTP_EMAIL_SERVICE");
    sendNotification.addInput("userId")
                    .addInput("paymentId")
                    .addOutput("notificationId")
                    .addPrecondition("PaymentStatus", "SUCCESS")
                    .addEffect("NotificationSent", true)
                    .addResource("NETWORK")
                    .setCost(5.0)
                    .setReliability(0.995)
                    .setAvailability(0.999);

    std::cout << "Step 1: Composing CreateOrder + MakePayment ...\n";
    Capability step1 = composeCapabilities(createOrder, makePayment);

    std::cout << "Step 2: Composing (CreateOrder + MakePayment) + SendNotification -> CompletePurchase ...\n";
    Capability completePurchase = composeCapabilities(step1, sendNotification, "CompletePurchase");

    std::cout << "\nResulting Composite Capability:\n";
    std::cout << completePurchase.toString() << "\n\n";

    // Theoretical operational calculations:
    // Cost: 15 + 25 + 5 = 45.0
    // Reliability: 0.99 * 0.98 * 0.995 = 0.965349
    // Availability: 0.995 * 0.990 * 0.999 = 0.984065
    std::cout << "Verification of Combined Operational Metrics:\n";
    std::cout << "  Expected Cost:         45.00  | Computed: " << completePurchase.cost << "\n";
    std::cout << "  Expected Reliability:  0.9653 | Computed: " << completePurchase.reliability << "\n";
    std::cout << "  Expected Availability: 0.9841 | Computed: " << completePurchase.availability << "\n";

    // Encode composite capability
    std::vector<double> compositeVec = encodeCapability(completePurchase);
    printVector("CompletePurchase Vector", compositeVec, 16);

    // Verify encodeCompositeCapability helper
    std::vector<double> helperVec = encodeCompositeCapability({createOrder, makePayment, sendNotification}, "CompletePurchase");
    double selfSim = similarity(compositeVec, helperVec);
    std::cout << "Cosine Similarity (direct composition vs chain helper): " << std::fixed << std::setprecision(6) << selfSim << "\n";
    assert(std::fabs(selfSim - 1.0) < 1e-6);

    std::cout << "\n[Experiment 2 Passed]: Composite capability synthesized and embedded successfully!\n";
}

// ============================================================================
// EXPERIMENT 3: Alternative Implementations
// ============================================================================
void runExperiment3() {
    printHeader("EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS");
    std::cout << "Objective: Compare CreateOrder implemented via API, GUI, and DATABASE.\n";
    std::cout << "Same functionality, different execution mechanisms and operational attributes.\n\n";

    // Common functionality
    auto configureCommon = [](Capability& cap) {
        cap.addInput("cartId")
           .addInput("userId")
           .addOutput("orderId")
           .addPrecondition("CartExists", true)
           .addEffect("OrderExists", true)
           .addConstraint("valid_user")
           .addConstraint("cart_not_empty")
           .addResource("ORDER_DB");
    };

    // 1. CreateOrder_API
    Capability orderAPI("CreateOrder_API", CapabilityType::API, "REST_HTTP_JSON");
    configureCommon(orderAPI);
    orderAPI.addResource("NETWORK")
            .setCost(15.0)
            .setReliability(0.99)
            .setAvailability(0.995);

    // 2. CreateOrder_GUI
    Capability orderGUI("CreateOrder_GUI", CapabilityType::GUI, "QT_DESKTOP_UI");
    configureCommon(orderGUI);
    orderGUI.addResource("DISPLAY")
            .setCost(75.0)  // higher user interaction / render latency
            .setReliability(0.92)
            .setAvailability(0.950);

    // 3. CreateOrder_DATABASE
    Capability orderDB("CreateOrder_DATABASE", CapabilityType::DATABASE, "SQL_STORED_PROCEDURE");
    configureCommon(orderDB);
    orderDB.setCost(5.0)    // direct high-speed internal database execution
           .setReliability(0.999)
           .setAvailability(0.999);

    std::vector<double> vAPI = encodeCapability(orderAPI);
    std::vector<double> vGUI = encodeCapability(orderGUI);
    std::vector<double> vDB  = encodeCapability(orderDB);

    printVector("v(CreateOrder_API)     ", vAPI, 12);
    printVector("v(CreateOrder_GUI)     ", vGUI, 12);
    printVector("v(CreateOrder_DATABASE)", vDB,  12);

    std::vector<std::string> labels = {"CreateOrder_API", "CreateOrder_GUI", "CreateOrder_DB"};
    std::vector<std::vector<double>> matrix(3, std::vector<double>(3, 0.0));

    std::vector<std::vector<double>> vecs = {vAPI, vGUI, vDB};
    for (size_t i = 0; i < 3; ++i) {
        for (size_t j = 0; j < 3; ++j) {
            matrix[i][j] = similarity(vecs[i], vecs[j]);
        }
    }

    std::cout << "\nPairwise Cosine Similarity Matrix:\n\n";
    printSimilarityMatrix(labels, matrix);

    std::cout << "\nAnalytical Observations:\n";
    std::cout << "1. High functional similarity (~" << std::setprecision(2) << matrix[0][2] * 100
              << "% between API and DB) reflects identical preconditions, effects, inputs, and outputs.\n";
    std::cout << "2. Differentiations arise from the capability type subspace (API vs GUI vs DATABASE),\n"
              << "   divergent resources (NETWORK vs DISPLAY), and operational metrics (cost/latency).\n";

    assert(matrix[0][0] > 0.999);
    assert(matrix[0][1] > 0.60 && matrix[0][1] < 1.0);
    assert(matrix[0][2] > 0.60 && matrix[0][2] < 1.0);

    std::cout << "\n[Experiment 3 Passed]: Alternative implementations successfully distinguished!\n";
}

// ============================================================================
// EXPERIMENT 4: Irrelevant Capability
// ============================================================================
void runExperiment4() {
    printHeader("EXPERIMENT 4: IRRELEVANT CAPABILITY & GOAL RELEVANCE");
    std::cout << "Objective: Test goal relevance of PlayMusic vs MakePayment for goal {PaymentStatus = SUCCESS}\n\n";

    // Target Goal
    Goal paymentGoal("Payment Success Goal");
    paymentGoal.addCondition("PaymentStatus", "SUCCESS");
    std::cout << paymentGoal.toString() << "\n\n";

    // Relevant Capability: MakePayment
    Capability makePayment("MakePayment", CapabilityType::API, "PAYMENT_GATEWAY_RPC");
    makePayment.addInput("orderId")
               .addInput("amount")
               .addOutput("paymentId")
               .addPrecondition("OrderExists", true)
               .addEffect("PaymentStatus", "SUCCESS")
               .setCost(20.0)
               .setReliability(0.99);

    // Irrelevant Capability: PlayMusic
    Capability playMusic("PlayMusic", CapabilityType::SERVICE, "AUDIO_STREAM_CORE");
    playMusic.addInput("trackId")
             .addInput("volume")
             .addOutput("playbackState")
             .addPrecondition("AudioDeviceReady", true)
             .addEffect("MusicPlaying", true)
             .addResource("AUDIO_DEVICE")
             .setCost(2.0)
             .setReliability(0.999);

    std::cout << makePayment.toString() << "\n\n";
    std::cout << playMusic.toString() << "\n\n";

    double relPayment = goalRelevance(makePayment, paymentGoal);
    double relMusic   = goalRelevance(playMusic, paymentGoal);

    std::cout << "================================================================\n";
    std::cout << "  Goal: { PaymentStatus = SUCCESS }\n";
    std::cout << "----------------------------------------------------------------\n";
    std::cout << "  Capability: MakePayment -> Goal Relevance: "
              << std::fixed << std::setprecision(4) << relPayment << " (HIGH / DIRECT SATISFACTION)\n";
    std::cout << "  Capability: PlayMusic   -> Goal Relevance: "
              << std::fixed << std::setprecision(4) << relMusic   << " (LOW / ORTHOGONAL / ZERO OVERLAP)\n";
    std::cout << "================================================================\n";

    assert(relPayment > 0.99);
    assert(relMusic < 1e-6);

    std::cout << "\n[Experiment 4 Passed]: Irrelevant capability produces zero goal relevance as expected!\n";
}

// ============================================================================
// EXPERIMENT 5: Operational Attributes Influence
// ============================================================================
void runExperiment5() {
    printHeader("EXPERIMENT 5: OPERATIONAL ATTRIBUTES INFLUENCE");
    std::cout << "Objective: Investigate how variations in Cost, Reliability, and Availability\n";
    std::cout << "affect capability embeddings and cosine similarity against a baseline service.\n\n";

    auto createTemplate = [](const std::string& name, double cost, double rel, double avail) {
        Capability c(name, CapabilityType::SERVICE, "CLOUD_MICROSERVICE");
        c.addInput("orderId")
         .addOutput("paymentReceipt")
         .addPrecondition("OrderExists", true)
         .addEffect("PaymentStatus", "SUCCESS")
         .setCost(cost)
         .setReliability(rel)
         .setAvailability(avail);
        return c;
    };

    // 1. Baseline Service
    Capability baseline = createTemplate("Service_Baseline", 10.0, 0.990, 0.995);

    // 2. High Cost / Premium Infrastructure
    Capability highCost = createTemplate("Service_HighCost", 250.0, 0.990, 0.995);

    // 3. Degraded Reliability
    Capability lowRel   = createTemplate("Service_LowReliability", 10.0, 0.400, 0.995);

    // 4. Degraded Availability
    Capability lowAvail = createTemplate("Service_LowAvailability", 10.0, 0.990, 0.500);

    // 5. Budget / Low Quality (Low cost, low reliability, low availability)
    Capability budget   = createTemplate("Service_BudgetTier", 1.0, 0.700, 0.800);

    std::vector<Capability> services = {baseline, highCost, lowRel, lowAvail, budget};
    std::vector<std::string> names;
    std::vector<std::vector<double>> vectors;

    for (const auto& s : services) {
        names.push_back(s.name);
        vectors.push_back(encodeCapability(s));
    }

    std::cout << std::left << std::setw(28) << "Service"
              << std::right << std::setw(10) << "Cost"
              << std::setw(14) << "Reliability"
              << std::setw(14) << "Availability"
              << std::setw(18) << "Sim to Baseline" << "\n";
    std::cout << std::string(84, '-') << "\n";

    for (size_t i = 0; i < services.size(); ++i) {
        double sim = similarity(vectors[0], vectors[i]);
        std::cout << std::left << std::setw(28) << services[i].name
                  << std::right << std::setw(10) << std::fixed << std::setprecision(1) << services[i].cost
                  << std::setw(14) << std::fixed << std::setprecision(3) << services[i].reliability
                  << std::setw(14) << std::fixed << std::setprecision(3) << services[i].availability
                  << std::setw(18) << std::fixed << std::setprecision(4) << sim << "\n";
    }

    std::cout << "\nFull Operational Pairwise Similarity Matrix:\n\n";
    std::vector<std::vector<double>> fullMatrix(services.size(), std::vector<double>(services.size(), 0.0));
    for (size_t i = 0; i < services.size(); ++i) {
        for (size_t j = 0; j < services.size(); ++j) {
            fullMatrix[i][j] = similarity(vectors[i], vectors[j]);
        }
    }
    printSimilarityMatrix(names, fullMatrix);

    std::cout << "\nOperational Analysis:\n";
    std::cout << "- When functional properties are held constant, operational divergence shifts the embedding\n"
              << "  vector angle, demonstrating that the embedding successfully encodes QoS trade-offs.\n";

    assert(fullMatrix[0][0] > 0.999);
    assert(fullMatrix[0][1] < 1.0);
    assert(fullMatrix[0][2] < 1.0);
    assert(fullMatrix[0][3] < 1.0);

    std::cout << "\n[Experiment 5 Passed]: Operational attributes influence demonstrated quantitatively!\n";
}

// ============================================================================
// Main Test Driver
// ============================================================================
int main() {
    std::cout << "\n";
    std::cout << "################################################################################\n";
    std::cout << "       ASSIGNMENT 2: VECTOR EMBEDDING FOR CAPABILITY COMPOSITION               \n";
    std::cout << "                 COMPREHENSIVE EXPERIMENTAL TEST SUITE                         \n";
    std::cout << "################################################################################\n";

    try {
        runStateAndGoalDemo();
        runExperiment1();
        runExperiment2();
        runExperiment3();
        runExperiment4();
        runExperiment5();

        std::cout << "\n";
        std::cout << "================================================================================\n";
        std::cout << "   ALL 5 EXPERIMENTS COMPLETED SUCCESSFULLY! ALL CRITERIA SATISFIED (100%)      \n";
        std::cout << "================================================================================\n\n";
    } catch (const std::exception& ex) {
        std::cerr << "\n[ERROR] Unhandled exception occurred: " << ex.what() << "\n";
        return 1;
    }

    return 0;
}
