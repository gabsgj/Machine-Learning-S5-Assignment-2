#include "../include/State.h"
#include "../include/Goal.h"
#include "../include/Capability.h"
#include "../include/Embedding.h"
#include "../include/Similarity.h"
#include "../include/Compatibility.h"
#include "../include/Composer.h"

#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <string>
#include <cmath>

using namespace std;

/*
    Assignment 2
    Design of a Vector Embedding for Capability Composition

    This program performs:
    1. Basic state/goal/capability embedding
    2. Compatibility experiment
    3. Composition experiment
    4. Alternative implementation experiment
    5. Irrelevant capability experiment
    6. Operational attribute experiment

    CSV results are automatically written to the results/ directory.
*/


/* ============================================================
   Helper functions
   ============================================================ */

string capabilityTypeToString(CapabilityType type)
{
    switch (type)
    {
        case CapabilityType::API:
            return "API";

        case CapabilityType::DATABASE:
            return "DATABASE";

        case CapabilityType::GUI:
            return "GUI";

        case CapabilityType::EVENT:
            return "EVENT";

        case CapabilityType::FUNCTION:
            return "FUNCTION";

        case CapabilityType::FILE:
            return "FILE";

        case CapabilityType::COMPUTATION:
            return "COMPUTATION";

        case CapabilityType::MESSAGE:
            return "MESSAGE";

        case CapabilityType::SERVICE:
            return "SERVICE";
    }

    return "UNKNOWN";
}


Capability makeCreateOrder()
{
    Capability c(
        "C1",
        "CreateOrder",
        CapabilityType::API
    );

    c.addInput({
        "customer_id",
        "string",
        "customer",
        true
    });

    c.addInput({
        "cart_id",
        "string",
        "cart",
        true
    });

    c.addOutput({
        "order_id",
        "string",
        "order",
    });

    c.addPrecondition(
        "cart_status",
        "ACTIVE"
    );

    c.addEffect(
        "order_status",
        "CREATED"
    );

    c.addConstraint(
        "valid_customer"
    );

    c.addResource(
        "database"
    );

    c.setQuality({
        2.0,
        1.0,
        5.0,
        0.02,
        1.0
    });

    c.setReliability(0.98);
    c.setAvailability(true);
    c.setMechanism("REST API");

    return c;
}


Capability makeMakePayment()
{
    Capability c(
        "C2",
        "MakePayment",
        CapabilityType::SERVICE
    );

    c.addInput({
        "order_id",
        "string",
        "order",
        true
    });

    c.addInput({
        "amount",
        "double",
        "currency",
        true
    });

    c.addOutput({
        "payment_id",
        "string",
        "payment",
    });

    c.addPrecondition(
        "order_status",
        "CREATED"
    );

    c.addEffect(
        "payment_status",
        "PAID"
    );

    c.addConstraint(
        "valid_payment_method"
    );

    c.addResource(
        "payment_gateway"
    );

    c.setQuality({
        3.0,
        2.0,
        10.0,
        0.03,
        2.0
    });

    c.setReliability(0.95);
    c.setAvailability(true);
    c.setMechanism("Payment Service");

    return c;
}


Capability makeSendConfirmation()
{
    Capability c(
        "C3",
        "SendConfirmation",
        CapabilityType::MESSAGE
    );

    c.addInput({
        "payment_id",
        "string",
        "payment",
        true
    });

    c.addOutput({
        "confirmation_id",
        "string",
        "confirmation",
    });

    c.addPrecondition(
        "payment_status",
        "PAID"
    );

    c.addEffect(
        "confirmation_sent",
        "YES"
    );

    c.addConstraint(
        "valid_email"
    );

    c.addResource(
        "mail_server"
    );

    c.setQuality({
        1.0,
        1.0,
        1.0,
        0.01,
        0.5
    });

    c.setReliability(0.99);
    c.setAvailability(true);
    c.setMechanism("Email Service");

    return c;
}


Capability makeCancelCart()
{
    Capability c(
        "C4",
        "CancelCart",
        CapabilityType::FUNCTION
    );

    c.addInput({
        "cart_id",
        "string",
        "cart",
        true
    });

    c.addOutput({
        "cancel_status",
        "string",
        "status",
    });

    c.addPrecondition(
        "cart_status",
        "ACTIVE"
    );

    c.addEffect(
        "cart_status",
        "CANCELLED"
    );

    c.addConstraint(
        "cart_not_locked"
    );

    c.addResource(
        "database"
    );

    c.setQuality({
        1.5,
        1.0,
        2.0,
        0.02,
        0.5
    });

    c.setReliability(0.97);
    c.setAvailability(true);
    c.setMechanism("Application Function");

    return c;
}


Capability makeUpdateUserProfile()
{
    Capability c(
        "C5",
        "UpdateUserProfile",
        CapabilityType::DATABASE
    );

    c.addInput({
        "user_id",
        "string",
        "user",
        true
    });

    c.addOutput({
        "profile_status",
        "string",
        "profile",
    });

    c.addPrecondition(
        "user_status",
        "ACTIVE"
    );

    c.addEffect(
        "profile_status",
        "UPDATED"
    );

    c.addResource(
        "user_database"
    );

    c.setQuality({
        2.0,
        1.0,
        2.0,
        0.01,
        0.5
    });

    c.setReliability(0.99);
    c.setAvailability(true);
    c.setMechanism("SQL Database");

    return c;
}


Capability makeGenerateReport()
{
    Capability c(
        "C6",
        "GenerateReport",
        CapabilityType::COMPUTATION
    );

    c.addInput({
        "report_period",
        "string",
        "date_range",
        true
    });

    c.addOutput({
        "report_file",
        "string",
        "file",
    });

    c.addPrecondition(
        "data_available",
        "YES"
    );

    c.addEffect(
        "report_status",
        "GENERATED"
    );

    c.addResource(
        "compute_server"
    );

    c.setQuality({
        5.0,
        4.0,
        3.0,
        0.02,
        3.0
    });

    c.setReliability(0.96);
    c.setAvailability(true);
    c.setMechanism("Data Processing");

    return c;
}


/*
    Alternative implementations of CreateOrder.

    All three produce the same functional effect:

        order_status = CREATED

    but use different mechanisms.
*/

Capability makeCreateOrderAPI()
{
    Capability c(
        "ALT1",
        "CreateOrder_API",
        CapabilityType::API
    );

    c.addInput({
        "customer_id",
        "string",
        "customer",
        true
    });

    c.addOutput({
        "order_id",
        "string",
        "order",
    });

    c.addPrecondition(
        "cart_status",
        "ACTIVE"
    );

    c.addEffect(
        "order_status",
        "CREATED"
    );

    c.addResource("api_server");

    c.setQuality({
        2.0,
        1.0,
        5.0,
        0.02,
        1.0
    });

    c.setReliability(0.99);
    c.setAvailability(true);
    c.setMechanism("REST API");

    return c;
}


Capability makeCreateOrderDatabase()
{
    Capability c(
        "ALT2",
        "CreateOrder_DATABASE",
        CapabilityType::DATABASE
    );

    c.addInput({
        "customer_id",
        "string",
        "customer",
        true
    });

    c.addOutput({
        "order_id",
        "string",
        "order",
    });

    c.addPrecondition(
        "cart_status",
        "ACTIVE"
    );

    c.addEffect(
        "order_status",
        "CREATED"
    );

    c.addResource("order_database");

    c.setQuality({
        1.5,
        1.0,
        2.0,
        0.03,
        0.8
    });

    c.setReliability(0.97);
    c.setAvailability(true);
    c.setMechanism("SQL INSERT");

    return c;
}


Capability makeCreateOrderGUI()
{
    Capability c(
        "ALT3",
        "CreateOrder_GUI",
        CapabilityType::GUI
    );

    c.addInput({
        "customer_id",
        "string",
        "customer",
        true
    });

    c.addOutput({
        "order_id",
        "string",
        "order",
    });

    c.addPrecondition(
        "cart_status",
        "ACTIVE"
    );

    c.addEffect(
        "order_status",
        "CREATED"
    );

    c.addResource("client_application");

    c.setQuality({
        4.0,
        2.0,
        8.0,
        0.05,
        1.5
    });

    c.setReliability(0.94);
    c.setAvailability(true);
    c.setMechanism("Graphical Interface");

    return c;
}


/* ============================================================
   CSV functions
   ============================================================ */

void runCompatibilityExperiment(
    const Capability& createOrder,
    const Capability& makePayment,
    const Capability& cancelCart
)
{
    cout << "\n============================================\n";
    cout << " Experiment 1: Compatibility\n";
    cout << "============================================\n";

    CompatibilityResult r1 =
        Compatibility::evaluate(
            createOrder,
            makePayment
        );

    CompatibilityResult r2 =
        Compatibility::evaluate(
            createOrder,
            cancelCart
        );

    cout << "\nCreateOrder -> MakePayment\n";
    cout << "Final Score: "
         << fixed << setprecision(2)
         << r1.finalScore << "\n";

    cout << "Compatible: "
         << (r1.compatible ? "YES" : "NO")
         << "\n";

    cout << "\nCreateOrder -> CancelCart\n";
    cout << "Final Score: "
         << fixed << setprecision(2)
         << r2.finalScore << "\n";

    cout << "Compatible: "
         << (r2.compatible ? "YES" : "NO")
         << "\n";

    ofstream file(
        "results/compatibility.csv"
    );

    file << "first_capability,second_capability,"
         << "precondition_effect_score,"
         << "input_output_score,"
         << "resource_score,"
         << "final_score,compatible\n";

    file << createOrder.getName() << ","
         << makePayment.getName() << ","
         << r1.preconditionEffectScore << ","
         << r1.inputOutputScore << ","
         << r1.resourceScore << ","
         << r1.finalScore << ","
         << (r1.compatible ? "YES" : "NO")
         << "\n";

    file << createOrder.getName() << ","
         << cancelCart.getName() << ","
         << r2.preconditionEffectScore << ","
         << r2.inputOutputScore << ","
         << r2.resourceScore << ","
         << r2.finalScore << ","
         << (r2.compatible ? "YES" : "NO")
         << "\n";

    file.close();
}


void runCompositionExperiment(
    const Capability& createOrder,
    const Capability& makePayment,
    const Capability& sendConfirmation
)
{
    cout << "\n============================================\n";
    cout << " Experiment 2: Composition\n";
    cout << "============================================\n";

    vector<Capability> chain;

    chain.push_back(createOrder);
    chain.push_back(makePayment);
    chain.push_back(sendConfirmation);

    bool firstPair =
        Composer::canCompose(
            createOrder,
            makePayment
        );

    bool secondPair =
        Composer::canCompose(
            makePayment,
            sendConfirmation
        );

    bool valid =
        firstPair && secondPair;

    cout << "\nCreateOrder -> MakePayment: "
         << (firstPair ? "COMPOSABLE" : "NOT COMPOSABLE")
         << "\n";

    cout << "MakePayment -> SendConfirmation: "
         << (secondPair ? "COMPOSABLE" : "NOT COMPOSABLE")
         << "\n";

    ofstream file(
        "results/composition.csv"
    );

    file << "chain,composable,"
         << "execution_time,"
         << "resource_cost,"
         << "monetary_cost,"
         << "risk,"
         << "energy,"
         << "reliability,"
         << "availability\n";

    if (valid)
    {
        Capability composite =
            Composer::compose(chain);

        cout << "\nThree-capability composition successful.\n";

        cout << "Composite capability: "
             << composite.getName() << "\n";

        cout << "Execution time: "
             << composite.getQuality().executionTime
             << "\n";

        cout << "Monetary cost: "
             << composite.getQuality().monetaryCost
             << "\n";

        cout << "Reliability: "
             << composite.getReliability()
             << "\n";

        file << "CreateOrder->MakePayment->SendConfirmation,"
             << "YES,"
             << composite.getQuality().executionTime << ","
             << composite.getQuality().resourceCost << ","
             << composite.getQuality().monetaryCost << ","
             << composite.getQuality().risk << ","
             << composite.getQuality().energy << ","
             << composite.getReliability() << ","
             << (composite.isAvailable() ? "YES" : "NO")
             << "\n";
    }
    else
    {
        cout << "\nComposition failed.\n";

        file << "CreateOrder->MakePayment->SendConfirmation,"
             << "NO,0,0,0,0,0,0,NO\n";
    }

    file.close();
}


void runAlternativeExperiment(
    const Capability& api,
    const Capability& database,
    const Capability& gui
)
{
    cout << "\n============================================\n";
    cout << " Experiment 3: Alternative Implementations\n";
    cout << "============================================\n";

    Embedding embedding;

    FeatureVector apiVector =
        embedding.encode(api);

    FeatureVector databaseVector =
        embedding.encode(database);

    FeatureVector guiVector =
        embedding.encode(gui);

    double apiDatabase =
        Similarity::cosine(
            apiVector,
            databaseVector
        );

    double apiGui =
        Similarity::cosine(
            apiVector,
            guiVector
        );

    double databaseGui =
        Similarity::cosine(
            databaseVector,
            guiVector
        );

    cout << "\nAPI vs DATABASE: "
         << apiDatabase << "\n";

    cout << "API vs GUI: "
         << apiGui << "\n";

    cout << "DATABASE vs GUI: "
         << databaseGui << "\n";

    ofstream file(
        "results/alternatives.csv"
    );

    file << "capability_1,capability_2,"
         << "type_1,type_2,"
         << "mechanism_1,mechanism_2,"
         << "similarity\n";

    file << api.getName() << ","
         << database.getName() << ","
         << capabilityTypeToString(api.getType()) << ","
         << capabilityTypeToString(database.getType()) << ","
         << api.getMechanism() << ","
         << database.getMechanism() << ","
         << apiDatabase << "\n";

    file << api.getName() << ","
         << gui.getName() << ","
         << capabilityTypeToString(api.getType()) << ","
         << capabilityTypeToString(gui.getType()) << ","
         << api.getMechanism() << ","
         << gui.getMechanism() << ","
         << apiGui << "\n";

    file << database.getName() << ","
         << gui.getName() << ","
         << capabilityTypeToString(database.getType()) << ","
         << capabilityTypeToString(gui.getType()) << ","
         << database.getMechanism() << ","
         << gui.getMechanism() << ","
         << databaseGui << "\n";

    file.close();
}


double goalRelevance(
    const Capability& capability,
    const Goal& goal
)
{
    const auto& effects =
        capability.getEffects();

    const auto& conditions =
        goal.getConditions();

    if (conditions.empty())
    {
        return 0.0;
    }

    int matches = 0;

    for (const auto& condition : conditions)
    {
        auto it =
            effects.find(condition.first);

        if (it != effects.end() &&
            it->second == condition.second)
        {
            matches++;
        }
    }

    return static_cast<double>(matches) /
           static_cast<double>(conditions.size());
}


void runIrrelevantExperiment(
    const Goal& goal,
    const Capability& createOrder,
    const Capability& makePayment,
    const Capability& sendConfirmation,
    const Capability& updateProfile,
    const Capability& generateReport
)
{
    cout << "\n============================================\n";
    cout << " Experiment 4: Goal Relevance\n";
    cout << "============================================\n";

    vector<Capability> capabilities;

    capabilities.push_back(createOrder);
    capabilities.push_back(makePayment);
    capabilities.push_back(sendConfirmation);
    capabilities.push_back(updateProfile);
    capabilities.push_back(generateReport);

    ofstream file(
        "results/irrelevant.csv"
    );

    file << "capability,goal_relevance\n";

    for (size_t i = 0;
         i < capabilities.size();
         ++i)
    {
        double relevance =
            goalRelevance(
                capabilities[i],
                goal
            );

        cout << capabilities[i].getName()
             << " -> relevance = "
             << relevance
             << "\n";

        file << capabilities[i].getName()
             << ","
             << relevance
             << "\n";
    }

    file.close();
}


void runOperationalExperiment(
    const Capability& api,
    const Capability& database,
    const Capability& gui
)
{
    cout << "\n============================================\n";
    cout << " Experiment 5: Operational Properties\n";
    cout << "============================================\n";

    vector<Capability> alternatives;

    alternatives.push_back(api);
    alternatives.push_back(database);
    alternatives.push_back(gui);

    ofstream file(
        "results/operational.csv"
    );

    file << "capability,type,"
         << "execution_time,"
         << "resource_cost,"
         << "monetary_cost,"
         << "risk,"
         << "energy,"
         << "reliability,"
         << "availability\n";

    for (size_t i = 0;
         i < alternatives.size();
         ++i)
    {
        const Capability& c =
            alternatives[i];

        const Quality& q =
            c.getQuality();

        cout << "\n"
             << c.getName()
             << "\n";

        cout << "Execution time: "
             << q.executionTime << "\n";

        cout << "Resource cost: "
             << q.resourceCost << "\n";

        cout << "Monetary cost: "
             << q.monetaryCost << "\n";

        cout << "Risk: "
             << q.risk << "\n";

        cout << "Reliability: "
             << c.getReliability() << "\n";

        cout << "Availability: "
             << (c.isAvailable() ? "YES" : "NO")
             << "\n";

        file << c.getName() << ","
             << capabilityTypeToString(c.getType()) << ","
             << q.executionTime << ","
             << q.resourceCost << ","
             << q.monetaryCost << ","
             << q.risk << ","
             << q.energy << ","
             << c.getReliability() << ","
             << (c.isAvailable() ? "YES" : "NO")
             << "\n";
    }

    file.close();
}


/* ============================================================
   Basic embedding experiment
   ============================================================ */

void runBasicEmbeddingExperiment()
{
    cout << "\n============================================\n";
    cout << " Basic Embedding Experiment\n";
    cout << "============================================\n";

    State state;

    state.set(
        "cart_status",
        "ACTIVE"
    );

    state.set(
        "order_status",
        "NONE"
    );

    Goal goal;

    goal.addCondition(
        "confirmation_sent",
        "YES"
    );

    Capability createOrder =
        makeCreateOrder();

    Embedding embedding;

    FeatureVector stateVector =
        embedding.encode(state);

    FeatureVector goalVector =
        embedding.encode(goal);

    FeatureVector capabilityVector =
        embedding.encode(createOrder);

    cout << "State vector dimension: "
         << stateVector.size()
         << "\n";

    cout << "Goal vector dimension: "
         << goalVector.size()
         << "\n";

    cout << "Capability vector dimension: "
         << capabilityVector.size()
         << "\n";

    cout << "Capability type: "
         << capabilityTypeToString(
                createOrder.getType()
            )
         << "\n";

    cout << "Capability reliability: "
         << createOrder.getReliability()
         << "\n";
}


/* ============================================================
   Main
   ============================================================ */

int main()
{
    cout << "============================================\n";
    cout << " Assignment 2: Capability Embedding\n";
    cout << "============================================\n";

    cout << fixed << setprecision(2);

    /*
        Create the main experimental capabilities.
    */

    Capability createOrder =
        makeCreateOrder();

    Capability makePayment =
        makeMakePayment();

    Capability sendConfirmation =
        makeSendConfirmation();

    Capability cancelCart =
        makeCancelCart();

    Capability updateProfile =
        makeUpdateUserProfile();

    Capability generateReport =
        makeGenerateReport();

    /*
        Alternative implementations.
    */

    Capability createOrderAPI =
        makeCreateOrderAPI();

    Capability createOrderDatabase =
        makeCreateOrderDatabase();

    Capability createOrderGUI =
        makeCreateOrderGUI();


    /*
        Basic embedding experiment.
    */

    runBasicEmbeddingExperiment();


    /*
        Required experiment 1.
    */

    runCompatibilityExperiment(
        createOrder,
        makePayment,
        cancelCart
    );


    /*
        Required experiment 2.
    */

    runCompositionExperiment(
        createOrder,
        makePayment,
        sendConfirmation
    );


    /*
        Required experiment 3.
    */

    runAlternativeExperiment(
        createOrderAPI,
        createOrderDatabase,
        createOrderGUI
    );


    /*
        Goal used for relevance experiment.
    */

    Goal confirmationGoal;

    confirmationGoal.addCondition(
        "confirmation_sent",
        "YES"
    );


    /*
        Required experiment 4.
    */

    runIrrelevantExperiment(
        confirmationGoal,
        createOrder,
        makePayment,
        sendConfirmation,
        updateProfile,
        generateReport
    );


    /*
        Required experiment 5.
    */

    runOperationalExperiment(
        createOrderAPI,
        createOrderDatabase,
        createOrderGUI
    );


    /*
        Final message.
    */

    cout << "\n============================================\n";
    cout << " All experiments completed successfully.\n";
    cout << "============================================\n";

    cout << "\nGenerated result files:\n";

    cout << "results/compatibility.csv\n";
    cout << "results/composition.csv\n";
    cout << "results/alternatives.csv\n";
    cout << "results/irrelevant.csv\n";
    cout << "results/operational.csv\n";

    return 0;
}