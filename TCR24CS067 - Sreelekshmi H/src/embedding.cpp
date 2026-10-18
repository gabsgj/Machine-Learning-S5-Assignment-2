#include "embedding.hpp"

std::vector<double> encodeCapability(const Capability& capability) {

  std::vector<double> vector = {
    0, 0, 0, 0,   // Preconditions
    0, 0, 0, 0,   // Effects
    0, 0, 0, 0,   // Inputs
    0, 0, 0, 0,   // Outputs
    0, 0           // Cost, Reliability
};

    // Preconditions
    for (const std::string& item : capability.preconditions) {

        if (item == "cart_exists")
            vector[0] = 1;

        if (item == "order_exists")
            vector[1] = 1;

        if (item == "payment_success")
            vector[2] = 1;

        if (item == "order_cancelled")
            vector[3] = 1;
    }

    // Effects
    for (const std::string& item : capability.effects) {

        if (item == "cart_exists")
            vector[4] = 1;

        if (item == "order_exists")
            vector[5] = 1;

        if (item == "payment_success")
            vector[6] = 1;

        if (item == "order_cancelled")
            vector[7] = 1;
    }

    // Inputs
    for (const std::string& item : capability.inputs) {

        if (item == "cart_id")
            vector[8] = 1;

        if (item == "order_id")
            vector[9] = 1;

        if (item == "payment_id")
            vector[10] = 1;

        if (item == "email_address")
            vector[11] = 1;
    }

    // Outputs
    for (const std::string& item : capability.outputs) {

        if (item == "order_id")
            vector[12] = 1;

        if (item == "payment_id")
            vector[13] = 1;

        if (item == "confirmation_id")
            vector[14] = 1;

        if (item == "email_id")
            vector[15] = 1;
    }
    
    // Operational properties
vector[16] = capability.cost;
vector[17] = capability.reliability;


    return vector;
}

std::vector<double> encodeState(const State& state) {

    std::vector<double> vector = {
        0, 0, 0, 0
    };

    for (const std::string& fact : state.facts) {

        if (fact == "cart_exists")
            vector[0] = 1;

        if (fact == "order_exists")
            vector[1] = 1;

        if (fact == "payment_success")
            vector[2] = 1;

        if (fact == "order_cancelled")
            vector[3] = 1;
    }

    return vector;
}


std::vector<double> encodeGoal(const Goal& goal) {

    std::vector<double> vector = {
        0, 0, 0, 0
    };

    for (const std::string& fact : goal.facts) {

        if (fact == "cart_exists")
            vector[0] = 1;

        if (fact == "order_exists")
            vector[1] = 1;

        if (fact == "payment_success")
            vector[2] = 1;

        if (fact == "order_cancelled")
            vector[3] = 1;
    }

    return vector;
}