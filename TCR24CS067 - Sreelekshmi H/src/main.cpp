#include <iostream>
#include "types.hpp"
#include "embedding.hpp"
#include "composition.hpp"
#include "similarity.hpp"
int main() {

    Capability createOrder;

    createOrder.name = "CreateOrder";
    createOrder.inputs = {"cart_id"};
    createOrder.outputs = {"order_id"};
    createOrder.preconditions = {"cart_exists"};
    createOrder.effects = {"order_exists"};
    createOrder.cost = 0.01;
    createOrder.reliability = 0.99;


    Capability makePayment;

    makePayment.name = "MakePayment";
    makePayment.inputs = {"order_id"};
    makePayment.outputs = {"payment_id"};
    makePayment.preconditions = {"order_exists"};
    makePayment.effects = {"payment_success"};
    makePayment.cost = 0.05;
    makePayment.reliability = 0.98;


    std::vector<double> orderVector = encodeCapability(createOrder);
    std::vector<double> paymentVector = encodeCapability(makePayment);

    State currentState;

currentState.facts = {
    "cart_exists"
};

Goal purchaseGoal;

purchaseGoal.facts = {
    "payment_success"
};

if (goalSatisfied(makePayment, purchaseGoal)) {
    std::cout << "MakePayment -> Goal: Relevant\n";
}
else {
    std::cout << "MakePayment -> Goal: Not relevant\n";
}

if (goalSatisfied(createOrder, purchaseGoal)) {
    std::cout << "CreateOrder -> Goal: Relevant\n";
}
else {
    std::cout << "CreateOrder -> Goal: Not relevant\n";
}

std::vector<double> stateVector = encodeState(currentState);
std::vector<double> goalVector = encodeGoal(purchaseGoal);


    std::cout << "CreateOrder vector: [";

    for (int i = 0; i < orderVector.size(); i++) {
        std::cout << orderVector[i];

        if (i < orderVector.size() - 1)
            std::cout << ", ";
    }

    std::cout << "]\n";


    std::cout << "MakePayment vector: [";

    for (int i = 0; i < paymentVector.size(); i++) {
        std::cout << paymentVector[i];

        if (i < paymentVector.size() - 1)
            std::cout << ", ";
    }

    std::cout << "]\n";
    
    if (canCompose(createOrder, makePayment)) {
    std::cout << "CreateOrder -> MakePayment: Compatible\n";
}
else {
    std::cout << "CreateOrder -> MakePayment: Not compatible\n";
}

Capability confirmOrder;

confirmOrder.name = "ConfirmOrder";
confirmOrder.inputs = {"payment_id"};
confirmOrder.outputs = {"confirmation_id"};
confirmOrder.preconditions = {"payment_success"};
confirmOrder.effects = {"order_confirmed"};
confirmOrder.cost = 0.02;
confirmOrder.reliability = 0.99;

if (canCompose(makePayment, confirmOrder)) {
    std::cout << "MakePayment -> ConfirmOrder: Compatible\n";
}
else {
    std::cout << "MakePayment -> ConfirmOrder: Not compatible\n";
}

Capability cancelCart;

cancelCart.name = "CancelCart";
cancelCart.inputs = {"cart_id"};
cancelCart.outputs = {};
cancelCart.preconditions = {"cart_exists"};
cancelCart.effects = {"order_cancelled"};
cancelCart.cost = 0.02;
cancelCart.reliability = 0.97;

if (canCompose(createOrder, cancelCart)) {
    std::cout << "CreateOrder -> CancelCart: Compatible\n";
}
else {
    std::cout << "CreateOrder -> CancelCart: Not compatible\n";
}


if (canCompose(createOrder, makePayment)) {

    Capability completePurchase = compose(createOrder, makePayment);

    std::cout << "\nComposite Capability: "
              << completePurchase.name << "\n";

    std::cout << "Cost: "
              << completePurchase.cost << "\n";

    std::cout << "Reliability: "
              << completePurchase.reliability << "\n";
}

double similarity = cosineSimilarity(orderVector, paymentVector);

std::cout << "Similarity(CreateOrder, MakePayment): "
          << similarity << "\n";

Capability sendEmail;

sendEmail.name = "SendEmail";
sendEmail.inputs = {"email_address", "message"};
sendEmail.outputs = {"email_id"};
sendEmail.preconditions = {"email_address_available"};
sendEmail.effects = {"email_sent"};
sendEmail.cost = 0.03;
sendEmail.reliability = 0.95;

if (canCompose(createOrder, sendEmail)) {
    std::cout << "CreateOrder -> SendEmail: Compatible\n";
}
else {
    std::cout << "CreateOrder -> SendEmail: Not compatible\n";
}

std::vector<double> cancelVector = encodeCapability(cancelCart);
std::vector<double> emailVector = encodeCapability(sendEmail);

std::cout << "Similarity(CreateOrder, CancelCart): "
          << cosineSimilarity(orderVector, cancelVector) << "\n";

std::cout << "Similarity(CreateOrder, SendEmail): "
          << cosineSimilarity(orderVector, emailVector) << "\n";
 
if (canCompose(makePayment, confirmOrder)) {

    Capability purchaseWithConfirmation =
        compose(
            compose(createOrder, makePayment),
            confirmOrder
        );

    std::cout << "\nThree-Step Composite Capability: "
              << purchaseWithConfirmation.name << "\n";

    std::cout << "Cost: "
              << purchaseWithConfirmation.cost << "\n";

    std::cout << "Reliability: "
              << purchaseWithConfirmation.reliability << "\n";
} 

std::cout << "State vector: [";

for (int i = 0; i < stateVector.size(); i++) {

    std::cout << stateVector[i];

    if (i < stateVector.size() - 1)
        std::cout << ", ";
}

std::cout << "]\n";


std::cout << "Goal vector: [";

for (int i = 0; i < goalVector.size(); i++) {

    std::cout << goalVector[i];

    if (i < goalVector.size() - 1)
        std::cout << ", ";
}

std::cout << "]\n";
 
          return 0;
}


