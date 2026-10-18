#include "../include/Embedding.h"

#include <algorithm>
#include <cmath>
#include <functional>

namespace
{
    const int TYPE_FEATURES = 9;
    const int COUNT_FEATURES = 6;

    const int PRECONDITION_FEATURES = 32;
    const int EFFECT_FEATURES = 32;
    const int IO_FEATURES = 16;
    const int RESOURCE_FEATURES = 16;

    const int QUALITY_FEATURES = 5;
    const int OPERATIONAL_FEATURES = 2;

    const int MECHANISM_FEATURES = 16;

    const int CAPABILITY_DIMENSION =
        TYPE_FEATURES +
        COUNT_FEATURES +
        PRECONDITION_FEATURES +
        EFFECT_FEATURES +
        IO_FEATURES +
        RESOURCE_FEATURES +
        QUALITY_FEATURES +
        OPERATIONAL_FEATURES +
        MECHANISM_FEATURES;

    const int STATE_DIMENSION = 64;
}

FeatureVector Embedding::encodeToken(
    const std::string& token,
    int bucketCount
) const
{
    FeatureVector result(bucketCount, 0.0);

    std::size_t hashValue =
        std::hash<std::string>{}(token);

    int index =
        static_cast<int>(hashValue % bucketCount);

    result[index] = 1.0;

    return result;
}

void Embedding::addHashedFeatures(
    FeatureVector& vector,
    const std::string& token,
    int startIndex,
    int bucketCount
) const
{
    std::size_t hashValue =
        std::hash<std::string>{}(token);

    int index =
        static_cast<int>(hashValue % bucketCount);

    vector[startIndex + index] += 1.0;
}

int Embedding::capabilityTypeIndex(
    CapabilityType type
) const
{
    return static_cast<int>(type);
}

FeatureVector Embedding::encode(
    const State& state
) const
{
    FeatureVector vector(
        STATE_DIMENSION,
        0.0
    );

    int position = 0;

    for (const auto& item : state.getVariables())
    {
        std::string token =
            item.first + "=" + item.second;

        std::size_t hashValue =
            std::hash<std::string>{}(token);

        int index =
            static_cast<int>(
                hashValue % 32
            );

        vector[index] += 1.0;
    }

    return vector;
}

FeatureVector Embedding::encode(
    const Goal& goal
) const
{
    FeatureVector vector(
        STATE_DIMENSION,
        0.0
    );

    for (const auto& condition :
         goal.getConditions())
    {
        std::string token =
            condition.first +
            "=" +
            condition.second;

        std::size_t hashValue =
            std::hash<std::string>{}(token);

        int index =
            static_cast<int>(
                hashValue % 32
            );

        vector[index] += 1.0;
    }

    return vector;
}

FeatureVector Embedding::encode(
    const Capability& capability
) const
{
    FeatureVector vector(
        CAPABILITY_DIMENSION,
        0.0
    );

    int position = 0;

    // ------------------------------------------------
    // 1. Capability type - one hot encoding
    // ------------------------------------------------

    int typeIndex =
        capabilityTypeIndex(
            capability.getType()
        );

    if (typeIndex >= 0 &&
        typeIndex < TYPE_FEATURES)
    {
        vector[position + typeIndex] = 1.0;
    }

    position += TYPE_FEATURES;

    // ------------------------------------------------
    // 2. Structural features
    // ------------------------------------------------

    vector[position++] =
        static_cast<double>(
            capability.getInputs().size()
        );

    vector[position++] =
        static_cast<double>(
            capability.getOutputs().size()
        );

    vector[position++] =
        static_cast<double>(
            capability.getPreconditions().size()
        );

    vector[position++] =
        static_cast<double>(
            capability.getEffects().size()
        );

    vector[position++] =
        static_cast<double>(
            capability.getConstraints().size()
        );

    vector[position++] =
        static_cast<double>(
            capability.getResources().size()
        );

    // ------------------------------------------------
    // 3. Preconditions
    // ------------------------------------------------

    int preconditionStart = position;

    for (const auto& condition :
         capability.getPreconditions())
    {
        std::string token =
            condition.first +
            "=" +
            condition.second;

        addHashedFeatures(
            vector,
            token,
            preconditionStart,
            PRECONDITION_FEATURES
        );
    }

    position += PRECONDITION_FEATURES;

    // ------------------------------------------------
    // 4. Effects
    // ------------------------------------------------

    int effectStart = position;

    for (const auto& effect :
         capability.getEffects())
    {
        std::string token =
            effect.first +
            "=" +
            effect.second;

        addHashedFeatures(
            vector,
            token,
            effectStart,
            EFFECT_FEATURES
        );
    }

    position += EFFECT_FEATURES;

    // ------------------------------------------------
    // 5. Input/output features
    // ------------------------------------------------

    int ioStart = position;

    for (const auto& input :
         capability.getInputs())
    {
        std::string token =
            "INPUT:" +
            input.name +
            ":" +
            input.type +
            ":" +
            input.domain;

        addHashedFeatures(
            vector,
            token,
            ioStart,
            IO_FEATURES
        );
    }

    for (const auto& output :
         capability.getOutputs())
    {
        std::string token =
            "OUTPUT:" +
            output.name +
            ":" +
            output.type +
            ":" +
            output.domain;

        addHashedFeatures(
            vector,
            token,
            ioStart,
            IO_FEATURES
        );
    }

    position += IO_FEATURES;

    // ------------------------------------------------
    // 6. Resources
    // ------------------------------------------------

    int resourceStart = position;

    for (const auto& resource :
         capability.getResources())
    {
        addHashedFeatures(
            vector,
            resource,
            resourceStart,
            RESOURCE_FEATURES
        );
    }

    position += RESOURCE_FEATURES;

    // ------------------------------------------------
    // 7. Quality
    // ------------------------------------------------

    const Quality& quality =
        capability.getQuality();

    vector[position++] =
        quality.executionTime;

    vector[position++] =
        quality.resourceCost;

    vector[position++] =
        quality.monetaryCost;

    vector[position++] =
        quality.risk;

    vector[position++] =
        quality.energy;

    // ------------------------------------------------
    // 8. Operational properties
    // ------------------------------------------------

    vector[position++] =
        capability.getReliability();

    vector[position++] =
        capability.isAvailable()
            ? 1.0
            : 0.0;

    // ------------------------------------------------
    // 9. Mechanism
    // ------------------------------------------------

    int mechanismStart = position;

    addHashedFeatures(
        vector,
        capability.getMechanism(),
        mechanismStart,
        MECHANISM_FEATURES
    );

    return vector;
}