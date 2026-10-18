#pragma once
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>

namespace capembed {

enum class CapabilityType {
    API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE
};

std::string capabilityTypeName(CapabilityType type);

struct State {
    std::unordered_map<std::string, std::string> values;
};

struct Goal {
    std::unordered_map<std::string, std::string> conditions;
};

struct DataSpec {
    std::string name;
    std::string type;
    std::string domain;
    bool required = true;

    bool operator==(const DataSpec& other) const {
        return name == other.name && type == other.type && domain == other.domain &&
               required == other.required;
    }
};

struct Capability {
    std::string name;
    CapabilityType type = CapabilityType::FUNCTION;
    std::string mechanism;

    std::vector<DataSpec> inputs;
    std::vector<DataSpec> outputs;

    std::unordered_map<std::string, std::string> preconditions;
    std::unordered_map<std::string, std::string> effects;

    std::vector<std::string> constraints;
    std::vector<std::string> resources;

    double cost = 0.0;
    double reliability = 1.0;
    double availability = 1.0;
};

} // namespace capembed
