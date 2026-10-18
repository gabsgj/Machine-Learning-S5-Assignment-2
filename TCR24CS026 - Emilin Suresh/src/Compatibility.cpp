#include "../include/Compatibility.h"

#include <algorithm>
#include <set>

double Compatibility::calculatePreconditionEffectScore(
    const Capability& first,
    const Capability& second
)
{
    const auto& effects =
        first.getEffects();

    const auto& preconditions =
        second.getPreconditions();

    if (preconditions.empty())
    {
        return 1.0;
    }

    int matched = 0;

    for (const auto& precondition :
         preconditions)
    {
        auto it =
            effects.find(
                precondition.first
            );

        if (it != effects.end() &&
            it->second == precondition.second)
        {
            matched++;
        }
    }

    return static_cast<double>(matched) /
           static_cast<double>(
               preconditions.size()
           );
}

double Compatibility::calculateInputOutputScore(
    const Capability& first,
    const Capability& second
)
{
    const auto& outputs =
        first.getOutputs();

    const auto& inputs =
        second.getInputs();

    if (inputs.empty())
    {
        return 1.0;
    }

    if (outputs.empty())
    {
        return 0.0;
    }

    int matched = 0;

    for (const auto& input : inputs)
    {
        bool found = false;

        for (const auto& output : outputs)
        {
            bool nameMatches =
                input.name == output.name;

            bool typeMatches =
                input.type == output.type;

            bool domainMatches =
                input.domain == output.domain;

            if (nameMatches &&
                typeMatches &&
                domainMatches)
            {
                found = true;
                break;
            }
        }

        if (found)
        {
            matched++;
        }
    }

    return static_cast<double>(matched) /
           static_cast<double>(
               inputs.size()
           );
}

double Compatibility::calculateResourceScore(
    const Capability& first,
    const Capability& second
)
{
    const auto& firstResources =
        first.getResources();

    const auto& secondResources =
        second.getResources();

    /*
     * For this assignment, resources are treated
     * as non-exclusive unless explicitly represented
     * otherwise.
     *
     * Therefore:
     *
     * - No resources required by second -> 1.0
     * - Resources required by second and first is
     *   available -> 1.0
     * - If second is unavailable -> 0.0
     */

    if (!second.isAvailable())
    {
        return 0.0;
    }

    if (secondResources.empty())
    {
        return 1.0;
    }

    /*
     * We assume that the application environment
     * makes declared resources available.
     *
     * The resource list is still represented in
     * the embedding and can be used for analysis.
     */

    return 1.0;
}

CompatibilityResult Compatibility::evaluate(
    const Capability& first,
    const Capability& second
)
{
    CompatibilityResult result;

    result.preconditionEffectScore =
        calculatePreconditionEffectScore(
            first,
            second
        );

    result.inputOutputScore =
        calculateInputOutputScore(
            first,
            second
        );

    result.resourceScore =
        calculateResourceScore(
            first,
            second
        );

    /*
     * Weighted compatibility:
     *
     * 50% precondition/effect
     * 30% input/output
     * 20% resources
     */

    result.finalScore =
        0.50 *
        result.preconditionEffectScore

        +

        0.30 *
        result.inputOutputScore

        +

        0.20 *
        result.resourceScore;

    /*
     * Composition requires the important
     * functional relationships to hold.
     */

    result.compatible =
        result.preconditionEffectScore >= 1.0 &&
        result.inputOutputScore >= 1.0 &&
        result.resourceScore >= 1.0 &&
        second.isAvailable();

    return result;
}