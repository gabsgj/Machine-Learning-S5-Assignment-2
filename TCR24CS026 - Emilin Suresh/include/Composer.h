#ifndef COMPOSER_H
#define COMPOSER_H

#include "Capability.h"

#include <vector>

class Composer
{
public:

    static bool canCompose(
        const Capability& first,
        const Capability& second
    );

    static Capability compose(
        const std::vector<Capability>& capabilities
    );
};

#endif