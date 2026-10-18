#ifndef COMPOSITION_HPP
#define COMPOSITION_HPP

#include "types.hpp"

bool canCompose(const Capability& first, const Capability& second);

Capability compose(const Capability& first, const Capability& second);


bool goalSatisfied(
    const Capability& capability,
    const Goal& goal
);
#endif

