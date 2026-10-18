#ifndef STATE_H
#define STATE_H

#include <string>
#include <unordered_map>
#include <vector>

class State
{
private:
    std::unordered_map<std::string, std::string> variables;

public:
    void set(
        const std::string& name,
        const std::string& value
    );

    bool has(
        const std::string& name
    ) const;

    std::string get(
        const std::string& name
    ) const;

    const std::unordered_map<std::string, std::string>&
    getVariables() const;
};

#endif