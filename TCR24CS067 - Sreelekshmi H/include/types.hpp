#ifndef TYPES_HPP
#define TYPES_HPP

#include <string>
#include <vector>

struct Capability {
    std::string name;

    std::vector<std::string> inputs;
    std::vector<std::string> outputs;

    std::vector<std::string> preconditions;
    std::vector<std::string> effects;

    double cost;
    double reliability;
};

struct State {
    std::vector<std::string> facts;
};

struct Goal {
    std::vector<std::string> facts;
};

#endif