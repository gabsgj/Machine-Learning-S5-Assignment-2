#pragma once
#include "types.hpp"
#include "json.hpp"
#include <fstream>
#include <stdexcept>
#include <set>
#include <unordered_map>
#include <cmath>

namespace capability {
using json=nlohmann::json;
inline Value parseValue(const json&j){if(j.is_boolean())return j.get<bool>();if(j.is_number())return j.get<double>();return j.get<std::string>();}
inline Condition parseCondition(const json&j){return {j.at("variable"),j.at("op"),parseValue(j.at("expectedValue"))};}
inline Port parsePort(const json&j){return {j.at("name"),j.at("type"),j.value("domain",""),j.value("required",true)};}
inline Capability parseCapability(const json&j){
    Capability c;c.id=j.at("id");c.name=j.at("name");c.description=j.value("description","");c.type=j.value("type","SERVICE");c.mechanism=j.value("mechanism","");
    if(j.contains("inputs"))for(auto&x:j["inputs"])c.inputs.push_back(parsePort(x));
    if(j.contains("outputs"))for(auto&x:j["outputs"])c.outputs.push_back(parsePort(x));
    if(j.contains("preconditions"))for(auto&x:j["preconditions"])c.preconditions.push_back(parseCondition(x));
    if(j.contains("constraints"))for(auto&x:j["constraints"])c.constraints.push_back(parseCondition(x));
    if(j.contains("effects"))for(auto&x:j["effects"])c.effects.push_back({x.at("variable"),x.at("op"),parseValue(x.at("value"))});
    if(j.contains("resources"))for(auto&x:j["resources"])c.resources.push_back(x.get<std::string>());
    if(j.contains("qos")){c.qos.timeMs=j["qos"].value("timeMs",0.0);c.qos.money=j["qos"].value("money",0.0);c.qos.resource=j["qos"].value("resource",0.0);c.qos.risk=j["qos"].value("risk",0.0);}
    c.reliability=j.value("reliability",.99);c.availability=j.value("availability",1.0);return c;
}
inline Problem loadProblem(const std::string&path){
    std::ifstream f(path);if(!f)throw std::runtime_error("Cannot open "+path);json j;f>>j;Problem p;p.name=j.value("problemName","");p.domain=j.value("domain","");p.description=j.value("description","");
    for(auto&[k,v]:j["initialState"].items())p.initial.vars[k]=parseValue(v);
    if(j.contains("goal"))for(auto&x:j["goal"])p.goal.conditions.push_back(parseCondition(x));
    if(j.contains("globalConstraints"))for(auto&x:j["globalConstraints"])p.globalConstraints.push_back(parseCondition(x));
    if(j.contains("resources"))for(auto&x:j["resources"])p.resources.push_back(x.get<std::string>());
    for(auto&x:j["capabilities"]) p.capabilities.push_back(parseCapability(x));
    return p;
}
}
