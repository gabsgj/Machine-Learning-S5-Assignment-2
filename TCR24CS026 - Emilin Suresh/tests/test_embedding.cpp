#include "../include/State.h"
#include "../include/Goal.h"
#include "../include/Capability.h"
#include "../include/Embedding.h"
#include "../include/Similarity.h"
#include "../include/Compatibility.h"
#include "../include/Composer.h"

#include <iostream>
#include <vector>
#include <cmath>

using namespace std;


Capability createOrder()
{
    Capability c(
        "T1",
        "CreateOrder",
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
        "order"
    });

    c.addPrecondition(
        "cart_status",
        "ACTIVE"
    );

    c.addEffect(
        "order_status",
        "CREATED"
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

    return c;
}


Capability makePayment()
{
    Capability c(
        "T2",
        "MakePayment",
        CapabilityType::SERVICE
    );

    c.addInput({
        "order_id",
        "string",
        "order",
        true
    });

    c.addOutput({
        "payment_id",
        "string",
        "payment"
    });

    c.addPrecondition(
        "order_status",
        "CREATED"
    );

    c.addEffect(
        "payment_status",
        "PAID"
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

    return c;
}


Capability cancelCart()
{
    Capability c(
        "T3",
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
        "status",
        "string",
        "status"
    });

    c.addPrecondition(
        "cart_status",
        "ACTIVE"
    );

    c.addEffect(
        "cart_status",
        "CANCELLED"
    );

    c.addResource(
        "database"
    );

    c.setQuality({
        1.0,
        1.0,
        2.0,
        0.02,
        0.5
    });

    c.setReliability(0.97);
    c.setAvailability(true);

    return c;
}


int main()
{
    cout << "Running Assignment 2 tests...\n\n";

    Embedding embedding;

    /*
        Test 1: State encoding
    */

    State state;

    state.set(
        "cart_status",
        "ACTIVE"
    );

    FeatureVector stateVector =
        embedding.encode(state);

    if (stateVector.empty())
    {
        cout << "FAIL: State encoding\n";
        return 1;
    }

    cout << "PASS: State encoding\n";


    /*
        Test 2: Goal encoding
    */

    Goal goal;

    goal.addCondition(
        "confirmation_sent",
        "YES"
    );

    FeatureVector goalVector =
        embedding.encode(goal);

    if (goalVector.empty())
    {
        cout << "FAIL: Goal encoding\n";
        return 1;
    }

    cout << "PASS: Goal encoding\n";


    /*
        Test 3: Capability encoding
    */

    Capability c1 =
        createOrder();

    FeatureVector capabilityVector =
        embedding.encode(c1);

    if (capabilityVector.empty())
    {
        cout << "FAIL: Capability encoding\n";
        return 1;
    }

    cout << "PASS: Capability encoding\n";


    /*
        Test 4: Cosine similarity
    */

    double similarity =
        Similarity::cosine(
            capabilityVector,
            capabilityVector
        );

    if (fabs(similarity - 1.0) > 0.0001)
    {
        cout << "FAIL: Cosine similarity\n";
        return 1;
    }

    cout << "PASS: Cosine similarity\n";


    /*
        Test 5: Compatible capabilities
    */

    Capability c2 =
        makePayment();

    CompatibilityResult compatible =
        Compatibility::evaluate(
            c1,
            c2
        );

    if (!compatible.compatible)
    {
        cout << "FAIL: CreateOrder -> MakePayment\n";
        return 1;
    }

    cout << "PASS: CreateOrder -> MakePayment\n";


    /*
        Test 6: Incompatible capabilities
    */

    Capability c3 =
        cancelCart();

    CompatibilityResult incompatible =
        Compatibility::evaluate(
            c1,
            c3
        );

    if (incompatible.compatible)
    {
        cout << "FAIL: CreateOrder -> CancelCart\n";
        return 1;
    }

    cout << "PASS: CreateOrder -> CancelCart\n";


    /*
        Test 7: Composition
    */

    if (!Composer::canCompose(c1, c2))
    {
        cout << "FAIL: Capability composition\n";
        return 1;
    }

    cout << "PASS: Capability composition\n";


    cout << "\nAll tests passed successfully.\n";

    return 0;
}