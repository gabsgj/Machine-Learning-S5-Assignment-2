#include "careweave/adapter/runner.hpp"

#include <set>
#include <sstream>

namespace careweave {
namespace adapter {

AdapterResult AdapterRunner::run(const AdapterDefinition& def,
                                 const std::map<std::string, core::Value>& inputs) {
  AdapterResult result;
  std::map<std::string, core::Value> payload;
  std::set<std::string> boundInputs;
  for (const auto& mapping : def.inputMap) {
    const auto it = inputs.find(mapping.from);
    if (it == inputs.end()) {
      // An optional requirement input the caller omitted is simply not sent; only a missing
      // required input stops the run.
      if (!mapping.required) continue;
      result.error = "missing requirement input \"" + mapping.from + "\"";
      return result;
    }
    core::Value converted;
    std::string err;
    if (!applyTransform(mapping.transform, it->second, &converted, &err)) {
      result.error = "input \"" + mapping.from + "\": " + err;
      result.trace.push_back("input " + mapping.render() + " failed: " + err);
      return result;
    }
    payload[mapping.to] = converted;
    boundInputs.insert(mapping.from);
    result.trace.push_back("input " + mapping.render() + " value=" + converted.toString());
  }
  for (const auto& input : inputs) {
    if (boundInputs.count(input.first) == 0) {
      result.error = "input \"" + input.first + "\" is not bound by this adapter";
      return result;
    }
  }
  result.transportAttempted = true;
  TransportResult transportResult = transport_.invoke(def, payload);
  result.trace.insert(result.trace.end(), transportResult.trace.begin(),
                      transportResult.trace.end());
  result.providerOutputs = transportResult.outputs;
  result.status = transportResult.status;
  if (!transportResult.ok) {
    result.error = transportResult.error;
    return result;
  }
  for (const auto& mapping : def.outputMap) {
    const auto it = transportResult.outputs.find(mapping.from);
    if (it == transportResult.outputs.end()) {
      result.error = "provider output \"" + mapping.from + "\" is missing from the response";
      return result;
    }
    core::Value converted;
    std::string err;
    if (!applyTransform(mapping.transform, it->second, &converted, &err)) {
      result.error = "output \"" + mapping.from + "\": " + err;
      return result;
    }
    result.outputs[mapping.to] = converted;
    result.trace.push_back("output " + mapping.render() + " value=" + converted.toString());
  }
  result.ok = true;
  return result;
}

std::string AdapterResult::render() const {
  std::ostringstream os;
  os << (ok ? "adapter call ok" : "adapter call failed") << " (status " << status << ")\n";
  if (!error.empty()) os << "  error: " << error << "\n";
  for (const auto& kv : outputs) os << "  output " << kv.first << " = " << kv.second.toString() << "\n";
  for (const auto& line : trace) os << "  trace: " << line << "\n";
  return os.str();
}

}  // namespace adapter
}  // namespace careweave
