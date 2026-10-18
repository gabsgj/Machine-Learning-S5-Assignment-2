#include "../include/Composer.h"

#include "../include/Compatibility.h"

#include <map>
#include <string>

bool Composer::canCompose(
    const Capability& first,
    const Capability& second
)
{
    CompatibilityResult result =
        Compatibility::evaluate(
            first,
            second
        );

    return result.compatible;
}

Capability Composer::compose(
    const std::vector<Capability>& capabilities
)
{
    if (capabilities.empty())
    {
        return Capability();
    }

    Capability composite(
        "COMPOSITE_001",
        "CompositeCapability",
        CapabilityType::FUNCTION
    );

    /*
     * ------------------------------------------------
     * 1. Check sequential compatibility
     * ------------------------------------------------
     */

    for (std::size_t i = 0;
         i + 1 < capabilities.size();
         ++i)
    {
        if (!canCompose(
                capabilities[i],
                capabilities[i + 1]))
        {
            return Capability();
        }
    }

    /*
     * ------------------------------------------------
     * 2. Initial preconditions
     * ------------------------------------------------
     *
     * External preconditions come from
     * the first capability.
     */

    for (const auto& condition :
         capabilities.front().getPreconditions())
    {
        composite.addPrecondition(
            condition.first,
            condition.second
        );
    }

    /*
     * ------------------------------------------------
     * 3. Final effects
     * ------------------------------------------------
     *
     * The effects of the last capability
     * represent the final result.
     */

    for (const auto& effect :
         capabilities.back().getEffects())
    {
        composite.addEffect(
            effect.first,
            effect.second
        );
    }

    /*
     * ------------------------------------------------
     * 4. External inputs
     * ------------------------------------------------
     */

    for (const auto& input :
         capabilities.front().getInputs())
    {
        composite.addInput(input);
    }

    /*
     * ------------------------------------------------
     * 5. Final outputs
     * ------------------------------------------------
     */

    for (const auto& output :
         capabilities.back().getOutputs())
    {
        composite.addOutput(output);
    }

    /*
     * ------------------------------------------------
     * 6. Combine constraints
     * ------------------------------------------------
     */

    for (const auto& capability :
         capabilities)
    {
        for (const auto& constraint :
             capability.getConstraints())
        {
            composite.addConstraint(
                constraint
            );
        }
    }

    /*
     * ------------------------------------------------
     * 7. Combine resources
     * ------------------------------------------------
     */

    for (const auto& capability :
         capabilities)
    {
        for (const auto& resource :
             capability.getResources())
        {
            composite.addResource(
                resource
            );
        }
    }

    /*
     * ------------------------------------------------
     * 8. Combine quality values
     * ------------------------------------------------
     */

    Quality totalQuality{
        0.0,
        0.0,
        0.0,
        0.0,
        0.0
    };

    for (const auto& capability :
         capabilities)
    {
        const Quality& q =
            capability.getQuality();

        totalQuality.executionTime +=
            q.executionTime;

        totalQuality.resourceCost +=
            q.resourceCost;

        totalQuality.monetaryCost +=
            q.monetaryCost;

        totalQuality.risk +=
            q.risk;

        totalQuality.energy +=
            q.energy;
    }

    /*
     * Risk is capped at 1.
     */

    if (totalQuality.risk > 1.0)
    {
        totalQuality.risk = 1.0;
    }

    composite.setQuality(
        totalQuality
    );

    /*
     * ------------------------------------------------
     * 9. Combined reliability
     * ------------------------------------------------
     *
     * Sequential reliability:
     *
     * R = R1 × R2 × ... × Rn
     */

    double reliability = 1.0;

    for (const auto& capability :
         capabilities)
    {
        reliability *=
            capability.getReliability();
    }

    composite.setReliability(
        reliability
    );

    /*
     * ------------------------------------------------
     * 10. Combined availability
     * ------------------------------------------------
     *
     * Composite is available only if
     * every capability is available.
     */

    bool available = true;

    for (const auto& capability :
         capabilities)
    {
        if (!capability.isAvailable())
        {
            available = false;
            break;
        }
    }

    composite.setAvailability(
        available
    );

    /*
     * ------------------------------------------------
     * 11. Mechanism
     * ------------------------------------------------
     */

    composite.setMechanism(
        "COMPOSITE"
    );

    return composite;
}