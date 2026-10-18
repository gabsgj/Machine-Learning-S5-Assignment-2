#include "../include/Goal.h"

void Goal::addCondition(
    const std::string& variable,
    const std::string& value
)
{
    conditions[variable] = value;
}

bool Goal::isSatisfiedBy(
    const std::unordered_map<std::string, std::string>& state
) const
{
    for (const auto& condition : conditions)
    {
        auto it = state.find(condition.first);

        if (it == state.end())
        {
            return false;
        }

        if (it->second != condition.second)
        {
            return false;
        }
    }

    return true;
}

const std::unordered_map<std::string, std::string>&
Goal::getConditions() const
{
    return conditions;
}