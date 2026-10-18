#ifndef TYPES_H
#define TYPES_H

#include <string>
#include <vector>

using FeatureVector = std::vector<double>;

enum class CapabilityType
{
    API,
    DATABASE,
    GUI,
    EVENT,
    FUNCTION,
    FILE,
    COMPUTATION,
    MESSAGE,
    SERVICE
};

#endif