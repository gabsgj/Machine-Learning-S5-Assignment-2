#pragma once

#include "types.hpp"
#include "../third_party/json.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>

namespace capability_embedding {

using json = nlohmann::json;

class JsonLoader {
public:
    static ApplicationProblem loadApplication(const std::string& filePath) {
        std::ifstream file(filePath);
        if (!file.is_open()) {
            throw std::runtime_error("Could not open JSON file: " + filePath);
        }

        json j;
        file >> j;

        ApplicationProblem app;
        app.applicationName = j.value("applicationName", "Ecommerce_Application");
        app.domain = j.value("domain", "E-Commerce");

        // Parse initial state
        if (j.contains("initialState") && j["initialState"].is_object()) {
            for (auto it = j["initialState"].begin(); it != j["initialState"].end(); ++it) {
                app.initialState.set(it.key(), it.value().get<bool>());
            }
        }

        // Parse goal
        if (j.contains("goal") && j["goal"].is_array()) {
            for (const auto& gItem : j["goal"]) {
                Condition cond;
                cond.variable = gItem.value("variable", "");
                cond.expectedValue = gItem.value("expectedValue", true);
                app.goal.conditions.push_back(cond);
            }
        }

        // Parse resources
        if (j.contains("resources") && j["resources"].is_array()) {
            for (const auto& r : j["resources"]) {
                app.resources.push_back(r.get<std::string>());
            }
        }

        // Parse global constraints
        if (j.contains("globalConstraints") && j["globalConstraints"].is_array()) {
            for (const auto& gc : j["globalConstraints"]) {
                app.globalConstraints.push_back(gc.get<std::string>());
            }
        }

        // Parse capabilities
        if (j.contains("capabilities") && j["capabilities"].is_array()) {
            for (const auto& cItem : j["capabilities"]) {
                app.capabilities.push_back(parseCapability(cItem));
            }
        }

        return app;
    }

    static std::vector<Capability> loadCapabilities(const std::string& filePath) {
        std::ifstream file(filePath);
        if (!file.is_open()) {
            throw std::runtime_error("Could not open JSON file: " + filePath);
        }

        json j;
        file >> j;
        std::vector<Capability> caps;
        if (j.contains("capabilities") && j["capabilities"].is_array()) {
            for (const auto& cItem : j["capabilities"]) {
                caps.push_back(parseCapability(cItem));
            }
        }
        return caps;
    }

private:
    static Capability parseCapability(const json& cItem) {
        Capability c;
        c.id = cItem.value("id", "");
        c.name = cItem.value("name", "");
        c.description = cItem.value("description", "");
        c.type = cItem.value("type", "API");
        c.mechanism = cItem.value("mechanism", "");
        c.reliability = cItem.value("reliability", 0.99);
        c.availability = cItem.value("availability", 1.0);

        // Inputs
        if (cItem.contains("inputs") && cItem["inputs"].is_array()) {
            for (const auto& inItem : cItem["inputs"]) {
                Port p;
                p.name = inItem.value("name", "");
                p.type = inItem.value("type", "string");
                p.domain = inItem.value("domain", "");
                p.required = inItem.value("required", true);
                c.inputs.push_back(p);
            }
        }

        // Outputs
        if (cItem.contains("outputs") && cItem["outputs"].is_array()) {
            for (const auto& outItem : cItem["outputs"]) {
                Port p;
                p.name = outItem.value("name", "");
                p.type = outItem.value("type", "string");
                p.domain = outItem.value("domain", "");
                p.required = false;
                c.outputs.push_back(p);
            }
        }

        // Preconditions
        if (cItem.contains("preconditions") && cItem["preconditions"].is_array()) {
            for (const auto& pItem : cItem["preconditions"]) {
                Condition cond;
                cond.variable = pItem.value("variable", "");
                cond.expectedValue = pItem.value("expectedValue", true);
                c.preconditions.push_back(cond);
            }
        }

        // Effects
        if (cItem.contains("effects") && cItem["effects"].is_array()) {
            for (const auto& eItem : cItem["effects"]) {
                Effect eff;
                eff.variable = eItem.value("variable", "");
                eff.value = eItem.value("value", true);
                c.effects.push_back(eff);
            }
        }

        // Constraints
        if (cItem.contains("constraints") && cItem["constraints"].is_array()) {
            for (const auto& k : cItem["constraints"]) {
                c.constraints.push_back(k.get<std::string>());
            }
        }

        // Resources
        if (cItem.contains("resources") && cItem["resources"].is_array()) {
            for (const auto& r : cItem["resources"]) {
                c.resources.push_back(r.get<std::string>());
            }
        }

        // QoS
        if (cItem.contains("qos") && cItem["qos"].is_object()) {
            const auto& q = cItem["qos"];
            c.qos.timeCostMs = q.value("timeCostMs", 100.0);
            c.qos.moneyCost = q.value("moneyCost", 0.01);
            c.qos.resourceCost = q.value("resourceCost", 1.0);
            c.qos.risk = q.value("risk", 0.05);
        }

        return c;
    }
};

} // namespace capability_embedding
