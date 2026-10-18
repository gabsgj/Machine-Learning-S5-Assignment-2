#include "composition.hpp"

bool canCompose(const Capability& first, const Capability& second) {

    bool effectMatch = false;
    bool outputMatch = false;

    // Check effect -> precondition
    for (const std::string& effect : first.effects) {

        for (const std::string& precondition : second.preconditions) {

            if (effect == precondition) {
                effectMatch = true;
            }
        }
    }

    // Check output -> input
    for (const std::string& output : first.outputs) {

        for (const std::string& input : second.inputs) {

            if (output == input) {
                outputMatch = true;
            }
        }
    }

    return effectMatch && outputMatch;
}


Capability compose(const Capability& first, const Capability& second) {

    Capability result;

    result.name = first.name + "_" + second.name;

    result.inputs = first.inputs;
    result.outputs = second.outputs;

    result.preconditions = first.preconditions;
    result.effects = second.effects;

    result.cost = first.cost + second.cost;

    result.reliability = first.reliability * second.reliability;

    return result;
}

bool goalSatisfied(
    const Capability& capability,
    const Goal& goal
) {

    for (const std::string& effect : capability.effects) {

        for (const std::string& goalFact : goal.facts) {

            if (effect == goalFact) {
                return true;
            }
        }
    }

    return false;
}