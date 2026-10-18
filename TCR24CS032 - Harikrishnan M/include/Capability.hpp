#ifndef CAPABILITY_HPP
#define CAPABILITY_HPP

#include <string>
#include <vector>

class Capability
{
public:
    std::string id;
    std::string name;
    std::string implementation_type; // e.g., "API", "DB", "LOCAL"

    std::vector<double> preconditions; // Dimension d
    std::vector<double> effects;       // Dimension d

    double cost;         // Operational cost
    double reliability;  // Operational reliability [0.0, 1.0]
    double availability; // Operational availability [0.0, 1.0]

    Capability();
    Capability(std::string id, std::string name, std::string type,
               std::vector<double> preconditions, std::vector<double> effects,
               double cost, double reliability, double availability);

    size_t get_state_dimension() const;
    std::vector<double> to_embedding_vector() const; // Vector of dimension 2d + 3
};

#endif // CAPABILITY_HPP