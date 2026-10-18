#ifndef CAPABILITY_H
#define CAPABILITY_H

#include "types.h"

#include <string>
#include <vector>
#include <unordered_map>

struct Input
{
    std::string name;
    std::string type;
    std::string domain;
    bool required;
};

struct Output
{
    std::string name;
    std::string type;
    std::string domain;
};

struct Quality
{
    double executionTime;
    double resourceCost;
    double monetaryCost;
    double risk;
    double energy;
};

class Capability
{
private:
    std::string id;
    std::string name;

    CapabilityType type;

    std::vector<Input> inputs;
    std::vector<Output> outputs;

    std::unordered_map<std::string, std::string>
        preconditions;

    std::unordered_map<std::string, std::string>
        effects;

    std::vector<std::string> constraints;
    std::vector<std::string> resources;

    Quality quality;

    double reliability;
    bool available;

    std::string mechanism;

public:

    Capability();

    Capability(
        const std::string& id,
        const std::string& name,
        CapabilityType type
    );

    void addInput(const Input& input);

    void addOutput(const Output& output);

    void addPrecondition(
        const std::string& variable,
        const std::string& value
    );

    void addEffect(
        const std::string& variable,
        const std::string& value
    );

    void addConstraint(
        const std::string& constraint
    );

    void addResource(
        const std::string& resource
    );

    void setQuality(
        const Quality& quality
    );

    void setReliability(
        double reliability
    );

    void setAvailability(
        bool available
    );

    void setMechanism(
        const std::string& mechanism
    );

    const std::string& getId() const;

    const std::string& getName() const;

    CapabilityType getType() const;

    const std::vector<Input>& getInputs() const;

    const std::vector<Output>& getOutputs() const;

    const std::unordered_map<std::string, std::string>&
    getPreconditions() const;

    const std::unordered_map<std::string, std::string>&
    getEffects() const;

    const std::vector<std::string>&
    getConstraints() const;

    const std::vector<std::string>&
    getResources() const;

    const Quality& getQuality() const;

    double getReliability() const;

    bool isAvailable() const;

    const std::string& getMechanism() const;
};

#endif