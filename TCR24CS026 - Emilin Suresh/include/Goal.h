#ifndef GOAL_H
#define GOAL_H

#include <string>
#include <unordered_map>

class Goal
{
private:
    std::unordered_map<std::string, std::string> conditions;

public:
    void addCondition(
        const std::string& variable,
        const std::string& value
    );

    bool isSatisfiedBy(
        const std::unordered_map<std::string, std::string>& state
    ) const;

    const std::unordered_map<std::string, std::string>&
    getConditions() const;
};

#endif