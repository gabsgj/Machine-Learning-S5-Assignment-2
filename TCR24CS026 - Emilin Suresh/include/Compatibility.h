#ifndef COMPATIBILITY_H
#define COMPATIBILITY_H

#include "Capability.h"

struct CompatibilityResult
{
    bool compatible;

    double preconditionEffectScore;
    double inputOutputScore;
    double resourceScore;

    double finalScore;
};

class Compatibility
{
private:

    static double calculatePreconditionEffectScore(
        const Capability& first,
        const Capability& second
    );

    static double calculateInputOutputScore(
        const Capability& first,
        const Capability& second
    );

    static double calculateResourceScore(
        const Capability& first,
        const Capability& second
    );

public:

    static CompatibilityResult evaluate(
        const Capability& first,
        const Capability& second
    );
};

#endif