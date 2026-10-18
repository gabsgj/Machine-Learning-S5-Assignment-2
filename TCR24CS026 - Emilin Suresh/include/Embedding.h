#ifndef EMBEDDING_H
#define EMBEDDING_H

#include "State.h"
#include "Goal.h"
#include "Capability.h"
#include "types.h"

#include <string>
#include <vector>

class Embedding
{
private:
    static const int SEMANTIC_BUCKETS = 32;
    static const int IO_BUCKETS = 16;
    static const int RESOURCE_BUCKETS = 16;
    static const int MECHANISM_BUCKETS = 16;

    FeatureVector encodeToken(
        const std::string& token,
        int bucketCount
    ) const;

    void addHashedFeatures(
        FeatureVector& vector,
        const std::string& token,
        int startIndex,
        int bucketCount
    ) const;

    int capabilityTypeIndex(
        CapabilityType type
    ) const;

public:

    FeatureVector encode(
        const State& state
    ) const;

    FeatureVector encode(
        const Goal& goal
    ) const;

    FeatureVector encode(
        const Capability& capability
    ) const;
};

#endif