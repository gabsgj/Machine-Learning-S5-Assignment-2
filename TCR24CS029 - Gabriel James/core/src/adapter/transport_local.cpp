#include <fstream>
#include <sstream>

#include "careweave/adapter/expression.hpp"
#include "careweave/adapter/transport.hpp"
#include "careweave/core/value_json.hpp"
#include "nlohmann/json.hpp"

namespace careweave {
namespace adapter {

TransportResult FileTransport::invoke(const AdapterDefinition& def,
                                      const std::map<std::string, core::Value>& payload) {
  TransportResult result;
  if (def.filePath.empty()) {
    result.error = "adapter has no file path";
    return result;
  }
  if (def.fileFormat != "json") {
    result.error = "file format \"" + def.fileFormat + "\" is not supported";
    return result;
  }
  if (def.fileOperation == "write") {
    nlohmann::json j = nlohmann::json::object();
    for (const auto& kv : payload) j[kv.first] = core::valueToJson(kv.second);
    std::ofstream out(def.filePath, std::ios::binary | std::ios::trunc);
    if (!out.is_open()) {
      result.error = "cannot open \"" + def.filePath + "\" for writing";
      return result;
    }
    const std::string body = j.dump(2) + "\n";
    out << body;
    out.close();
    if (!out) {
      result.error = "writing \"" + def.filePath + "\" failed";
      return result;
    }
    result.trace.push_back("file write " + def.filePath);
    result.outputs["path"] = core::Value(def.filePath);
    result.outputs["bytes"] = core::Value(static_cast<int64_t>(body.size()));
    result.ok = true;
    return result;
  }
  if (def.fileOperation == "read") {
    std::ifstream in(def.filePath, std::ios::binary);
    if (!in.is_open()) {
      result.error = "cannot open \"" + def.filePath + "\" for reading";
      return result;
    }
    std::ostringstream buffer;
    buffer << in.rdbuf();
    nlohmann::json j = nlohmann::json::parse(buffer.str(), nullptr, false);
    if (j.is_discarded() || !j.is_object()) {
      result.error = "\"" + def.filePath + "\" must contain a JSON object";
      return result;
    }
    for (auto it = j.begin(); it != j.end(); ++it) {
      core::Value v;
      std::string err;
      if (!core::jsonToValue(it.value(), &v, &err)) {
        result.error = "entry \"" + it.key() + "\": " + err;
        return result;
      }
      result.outputs.emplace(it.key(), std::move(v));
    }
    result.trace.push_back("file read " + def.filePath);
    result.ok = true;
    return result;
  }
  result.error = "unknown file operation \"" + def.fileOperation + "\"";
  return result;
}

TransportResult ComputationTransport::invoke(const AdapterDefinition& def,
                                             const std::map<std::string, core::Value>& payload) {
  TransportResult result;
  if (def.computations.empty()) {
    result.error = "adapter has no computations";
    return result;
  }
  std::map<std::string, core::Value> context = payload;
  for (const auto& computation : def.computations) {
    double value = 0.0;
    std::string err;
    if (!evaluateExpression(computation.second, context, &value, &err)) {
      result.error = "computation \"" + computation.first + "\": " + err;
      return result;
    }
    result.trace.push_back("computation " + computation.first + " = " + computation.second + " -> " +
                           core::Value(value).toString());
    context[computation.first] = core::Value(value);
    result.outputs[computation.first] = core::Value(value);
  }
  result.ok = true;
  return result;
}

void HandlerRegistry::add(const std::string& name, LocalHandler handler) {
  handlers_[name] = std::move(handler);
}

bool HandlerRegistry::has(const std::string& name) const {
  return handlers_.find(name) != handlers_.end();
}

LocalHandler HandlerRegistry::get(const std::string& name) const {
  const auto it = handlers_.find(name);
  return it == handlers_.end() ? LocalHandler() : it->second;
}

std::vector<std::string> HandlerRegistry::namesSorted() const {
  std::vector<std::string> names;
  names.reserve(handlers_.size());
  for (const auto& kv : handlers_) names.push_back(kv.first);
  return names;
}

TransportResult LocalTransport::invoke(const AdapterDefinition& def,
                                       const std::map<std::string, core::Value>& payload) {
  TransportResult result;
  if (def.handler.empty()) {
    result.error = "adapter has no handler name";
    return result;
  }
  const LocalHandler handler = registry_.get(def.handler);
  if (!handler) {
    result.error = "no local handler registered under \"" + def.handler + "\"";
    return result;
  }
  result = handler(payload);
  result.trace.insert(result.trace.begin(), "local handler " + def.handler);
  return result;
}

std::unique_ptr<Transport> makeTransport(const std::string& kind, HandlerRegistry* registry,
                                         double timeoutSeconds) {
  if (kind == "http") return std::unique_ptr<Transport>(new HttpTransport(timeoutSeconds));
  if (kind == "form") return std::unique_ptr<Transport>(new FormTransport(timeoutSeconds));
  if (kind == "sqlite") return std::unique_ptr<Transport>(new SqliteTransport());
  if (kind == "file") return std::unique_ptr<Transport>(new FileTransport());
  if (kind == "computation") return std::unique_ptr<Transport>(new ComputationTransport());
  if (kind == "local") {
    if (registry == nullptr) return nullptr;
    return std::unique_ptr<Transport>(new LocalTransport(*registry));
  }
  return nullptr;
}

}  // namespace adapter
}  // namespace careweave
