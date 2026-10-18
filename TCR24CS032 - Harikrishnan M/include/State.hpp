#ifndef STATE_HPP
#define STATE_HPP

#include <vector>
#include <string>

struct State
{
    std::string state_id;
    std::vector<double> feature_vector;

    State() = default;
    State(std::string id, std::vector<double> vec)
        : state_id(std::move(id)), feature_vector(std::move(vec)) {}
};

#endif // STATE_HPP