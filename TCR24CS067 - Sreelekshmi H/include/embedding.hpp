#ifndef EMBEDDING_HPP
#define EMBEDDING_HPP

#include "types.hpp"
#include <vector>

std::vector<double> encodeCapability(const Capability& capability);

std::vector<double> encodeState(const State& state);

std::vector<double> encodeGoal(const Goal& goal);
#endif