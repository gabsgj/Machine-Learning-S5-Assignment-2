#include "../include/State.h"

void State::set(
    const std::string& name,
    const std::string& value
)
{
    variables[name] = value;
}

bool State::has(
    const std::string& name
) const
{
    return variables.find(name) != variables.end();
}

std::string State::get(
    const std::string& name
) const
{
    auto it = variables.find(name);

    if (it == variables.end())
    {
        return "";
    }

    return it->second;
}

const std::unordered_map<std::string, std::string>&
State::getVariables() const
{
    return variables;
}