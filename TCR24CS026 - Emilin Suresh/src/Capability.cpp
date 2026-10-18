#include "../include/Capability.h"

Capability::Capability()
    : type(CapabilityType::FUNCTION),
      reliability(1.0),
      available(true)
{
    quality = {0.0, 0.0, 0.0, 0.0, 0.0};
}

Capability::Capability(
    const std::string& id_,
    const std::string& name_,
    CapabilityType type_
)
    : id(id_),
      name(name_),
      type(type_),
      reliability(1.0),
      available(true)
{
    quality = {0.0, 0.0, 0.0, 0.0, 0.0};
}

void Capability::addInput(const Input& input)
{
    inputs.push_back(input);
}

void Capability::addOutput(const Output& output)
{
    outputs.push_back(output);
}

void Capability::addPrecondition(
    const std::string& variable,
    const std::string& value
)
{
    preconditions[variable] = value;
}

void Capability::addEffect(
    const std::string& variable,
    const std::string& value
)
{
    effects[variable] = value;
}

void Capability::addConstraint(
    const std::string& constraint
)
{
    constraints.push_back(constraint);
}

void Capability::addResource(
    const std::string& resource
)
{
    resources.push_back(resource);
}

void Capability::setQuality(
    const Quality& quality_
)
{
    quality = quality_;
}

void Capability::setReliability(
    double reliability_
)
{
    if (reliability_ < 0.0)
    {
        reliability = 0.0;
    }
    else if (reliability_ > 1.0)
    {
        reliability = 1.0;
    }
    else
    {
        reliability = reliability_;
    }
}

void Capability::setAvailability(
    bool available_
)
{
    available = available_;
}

void Capability::setMechanism(
    const std::string& mechanism_
)
{
    mechanism = mechanism_;
}

const std::string& Capability::getId() const
{
    return id;
}

const std::string& Capability::getName() const
{
    return name;
}

CapabilityType Capability::getType() const
{
    return type;
}

const std::vector<Input>& Capability::getInputs() const
{
    return inputs;
}

const std::vector<Output>& Capability::getOutputs() const
{
    return outputs;
}

const std::unordered_map<std::string, std::string>&
Capability::getPreconditions() const
{
    return preconditions;
}

const std::unordered_map<std::string, std::string>&
Capability::getEffects() const
{
    return effects;
}

const std::vector<std::string>&
Capability::getConstraints() const
{
    return constraints;
}

const std::vector<std::string>&
Capability::getResources() const
{
    return resources;
}

const Quality& Capability::getQuality() const
{
    return quality;
}

double Capability::getReliability() const
{
    return reliability;
}

bool Capability::isAvailable() const
{
    return available;
}

const std::string& Capability::getMechanism() const
{
    return mechanism;
}