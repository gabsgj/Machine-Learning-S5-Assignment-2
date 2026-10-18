#include "careweave/adapter/adapter.hpp"

#include <algorithm>
#include <cctype>
#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <limits>
#include <sstream>

#include "careweave/core/value_json.hpp"
#include "nlohmann/json.hpp"

namespace careweave {
namespace adapter {

namespace {

bool parseStrictInt(const std::string& s, int64_t* out) {
  if (s.empty()) return false;
  errno = 0;
  char* end = nullptr;
  const long long parsed = std::strtoll(s.c_str(), &end, 10);
  if (errno == ERANGE || end == nullptr || *end != '\0') return false;
  *out = static_cast<int64_t>(parsed);
  return true;
}

bool parseStrictDouble(const std::string& s, double* out) {
  if (s.empty()) return false;
  errno = 0;
  char* end = nullptr;
  const double parsed = std::strtod(s.c_str(), &end);
  if (errno == ERANGE || end == nullptr || *end != '\0' || !std::isfinite(parsed)) return false;
  *out = parsed;
  return true;
}

std::string lower(std::string s) {
  std::transform(s.begin(), s.end(), s.begin(),
                 [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
  return s;
}

std::string trimmed(const std::string& s) {
  size_t b = 0;
  size_t e = s.size();
  while (b < e && std::isspace(static_cast<unsigned char>(s[b])) != 0) ++b;
  while (e > b && std::isspace(static_cast<unsigned char>(s[e - 1])) != 0) --e;
  return s.substr(b, e - b);
}

std::string formatConfidence(double v) {
  std::ostringstream os;
  os << std::fixed << std::setprecision(4) << v;
  return os.str();
}

}  // namespace

std::string FieldMapping::render() const {
  return from + " -> " + to + " (" + transform + ")";
}

bool AdapterDefinition::operator==(const AdapterDefinition& o) const {
  return id == o.id && requirementId == o.requirementId && requirementName == o.requirementName &&
         targetModule == o.targetModule && targetCapabilityId == o.targetCapabilityId &&
         targetCapabilityName == o.targetCapabilityName && transportKind == o.transportKind &&
         baseUrl == o.baseUrl && endpoint == o.endpoint && method == o.method &&
         sqlitePath == o.sqlitePath && table == o.table && operation == o.operation &&
         filePath == o.filePath && fileOperation == o.fileOperation && fileFormat == o.fileFormat &&
         computations == o.computations && handler == o.handler && inputMap == o.inputMap &&
         outputMap == o.outputMap && confidence == o.confidence &&
         explanation == o.explanation;
}

std::string AdapterDefinition::render() const {
  std::ostringstream os;
  os << "adapter " << id << "\n";
  os << "  requirement: " << requirementName << " (" << requirementId << ")\n";
  os << "  target: " << targetCapabilityName << " (" << targetCapabilityId << ") in module "
     << targetModule << "\n";
  os << "  transport: " << transportKind;
  if (transportKind == "http" || transportKind == "form") {
    os << " " << method << " " << baseUrl << endpoint;
  } else if (transportKind == "sqlite") {
    os << " " << operation << " into " << table << " at " << sqlitePath;
  } else if (transportKind == "file") {
    os << " " << fileOperation << " " << filePath << " (" << fileFormat << ")";
  } else if (transportKind == "computation") {
    os << " with " << computations.size() << " expressions";
  } else if (transportKind == "local") {
    os << " handler " << handler;
  }
  os << "\n";
  os << "  confidence: " << formatConfidence(confidence) << "\n";
  os << "  inputs:\n";
  for (const auto& m : inputMap) os << "    " << m.render() << "\n";
  os << "  outputs:\n";
  for (const auto& m : outputMap) os << "    " << m.render() << "\n";
  if (!computations.empty()) {
    os << "  computations:\n";
    for (const auto& c : computations) os << "    " << c.first << " = " << c.second << "\n";
  }
  if (!explanation.empty()) {
    os << "  explanation:\n";
    for (const auto& line : explanation) os << "    " << line << "\n";
  }
  return os.str();
}

const std::vector<std::string>& knownTransforms() {
  static const std::vector<std::string> names = {"identity",  "to_string", "to_int", "to_real",
                                                 "to_bool",   "lowercase", "uppercase", "trim"};
  return names;
}

bool isKnownTransform(const std::string& name) {
  const auto& names = knownTransforms();
  return std::find(names.begin(), names.end(), name) != names.end();
}

bool applyTransform(const std::string& name, const core::Value& in, core::Value* out,
                    std::string* err) {
  if (name == "identity") {
    *out = in;
    return true;
  }
  if (name == "to_string") {
    *out = core::Value(in.toString());
    return true;
  }
  if (name == "to_int") {
    switch (in.type()) {
      case core::ValueType::BOOL:
        *out = core::Value(static_cast<int64_t>(in.asBool() ? 1 : 0));
        return true;
      case core::ValueType::INT:
        *out = in;
        return true;
      case core::ValueType::REAL: {
        const double d = in.asDouble();
        if (!std::isfinite(d) || d < static_cast<double>(std::numeric_limits<int64_t>::min()) ||
            d > static_cast<double>(std::numeric_limits<int64_t>::max())) {
          if (err) *err = "real out of integer range";
          return false;
        }
        *out = core::Value(static_cast<int64_t>(d));
        return true;
      }
      case core::ValueType::STRING: {
        int64_t parsed = 0;
        if (!parseStrictInt(in.asString(), &parsed)) {
          if (err) *err = "value \"" + in.asString() + "\" is not an integer";
          return false;
        }
        *out = core::Value(parsed);
        return true;
      }
      default:
        if (err) *err = "to_int does not convert lists";
        return false;
    }
  }
  if (name == "to_real") {
    switch (in.type()) {
      case core::ValueType::BOOL:
        *out = core::Value(in.asBool() ? 1.0 : 0.0);
        return true;
      case core::ValueType::INT:
        *out = core::Value(static_cast<double>(in.asInt()));
        return true;
      case core::ValueType::REAL:
        *out = in;
        return true;
      case core::ValueType::STRING: {
        double parsed = 0.0;
        if (!parseStrictDouble(in.asString(), &parsed)) {
          if (err) *err = "value \"" + in.asString() + "\" is not a real number";
          return false;
        }
        *out = core::Value(parsed);
        return true;
      }
      default:
        if (err) *err = "to_real does not convert lists";
        return false;
    }
  }
  if (name == "to_bool") {
    switch (in.type()) {
      case core::ValueType::BOOL:
        *out = in;
        return true;
      case core::ValueType::INT:
        *out = core::Value(in.asInt() != 0);
        return true;
      case core::ValueType::REAL:
        *out = core::Value(in.asDouble() != 0.0);
        return true;
      case core::ValueType::STRING: {
        const std::string s = lower(trimmed(in.asString()));
        if (s == "true" || s == "1" || s == "yes") {
          *out = core::Value(true);
          return true;
        }
        if (s == "false" || s == "0" || s == "no" || s.empty()) {
          *out = core::Value(false);
          return true;
        }
        if (err) *err = "value \"" + in.asString() + "\" is not a boolean";
        return false;
      }
      default:
        if (err) *err = "to_bool does not convert lists";
        return false;
    }
  }
  if (name == "lowercase" || name == "uppercase" || name == "trim") {
    if (in.type() != core::ValueType::STRING) {
      if (err) *err = name + " applies to strings only";
      return false;
    }
    std::string s = in.asString();
    if (name == "lowercase") {
      s = lower(s);
    } else if (name == "uppercase") {
      std::transform(s.begin(), s.end(), s.begin(),
                     [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    } else {
      s = trimmed(s);
    }
    *out = core::Value(s);
    return true;
  }
  if (err) *err = "unknown transform \"" + name + "\"";
  return false;
}

const std::vector<std::string>& knownTransportKinds() {
  static const std::vector<std::string> kinds = {"http",  "form",        "sqlite",
                                                 "file",  "computation", "local"};
  return kinds;
}

std::string toJsonString(const AdapterDefinition& def, bool pretty) {
  nlohmann::json j;
  j["id"] = def.id;
  j["requirementId"] = def.requirementId;
  j["requirementName"] = def.requirementName;
  j["targetModule"] = def.targetModule;
  j["targetCapabilityId"] = def.targetCapabilityId;
  j["targetCapabilityName"] = def.targetCapabilityName;
  j["transportKind"] = def.transportKind;
  j["baseUrl"] = def.baseUrl;
  j["endpoint"] = def.endpoint;
  j["method"] = def.method;
  j["sqlitePath"] = def.sqlitePath;
  j["table"] = def.table;
  j["operation"] = def.operation;
  j["filePath"] = def.filePath;
  j["fileOperation"] = def.fileOperation;
  j["fileFormat"] = def.fileFormat;
  j["computations"] = nlohmann::json::array();
  for (const auto& c : def.computations) {
    j["computations"].push_back({{"output", c.first}, {"expression", c.second}});
  }
  j["handler"] = def.handler;
  j["inputMap"] = nlohmann::json::array();
  for (const auto& m : def.inputMap) {
    nlohmann::json entry = {{"from", m.from}, {"to", m.to}, {"transform", m.transform}};
    // Only emitted when the requirement declares the input optional, so stored adapter
    // artifacts that predate the flag round trip unchanged.
    if (!m.required) entry["required"] = false;
    j["inputMap"].push_back(std::move(entry));
  }
  j["outputMap"] = nlohmann::json::array();
  for (const auto& m : def.outputMap) {
    j["outputMap"].push_back({{"from", m.from}, {"to", m.to}, {"transform", m.transform}});
  }
  j["confidence"] = def.confidence;
  j["explanation"] = def.explanation;
  return pretty ? j.dump(2) : j.dump();
}

namespace {

bool readString(const nlohmann::json& j, const char* key, std::string* out, std::string* err,
                bool required) {
  const auto it = j.find(key);
  if (it == j.end() || it->is_null()) {
    if (required) {
      if (err) *err = std::string("missing required field \"") + key + "\"";
      return false;
    }
    return true;
  }
  if (!it->is_string()) {
    if (err) *err = std::string("field \"") + key + "\" must be a string";
    return false;
  }
  *out = it->get<std::string>();
  return true;
}

bool readMappings(const nlohmann::json& j, const char* key, std::vector<FieldMapping>* out,
                  std::string* err) {
  const auto it = j.find(key);
  if (it == j.end()) return true;
  if (!it->is_array()) {
    if (err) *err = std::string("field \"") + key + "\" must be an array";
    return false;
  }
  for (const auto& item : *it) {
    if (!item.is_object()) {
      if (err) *err = std::string("field \"") + key + "\" entries must be objects";
      return false;
    }
    FieldMapping m;
    if (!readString(item, "from", &m.from, err, true)) return false;
    if (!readString(item, "to", &m.to, err, true)) return false;
    if (!readString(item, "transform", &m.transform, err, false)) return false;
    if (m.transform.empty()) m.transform = "identity";
    if (!isKnownTransform(m.transform)) {
      if (err) *err = "unknown transform \"" + m.transform + "\"";
      return false;
    }
    if (item.contains("required")) {
      if (!item["required"].is_boolean()) {
        if (err) *err = std::string("field \"") + key + "\" entry \"required\" must be a boolean";
        return false;
      }
      m.required = item["required"].get<bool>();
    }
    out->push_back(std::move(m));
  }
  return true;
}

}  // namespace

bool parseAdapter(const std::string& json, AdapterDefinition* out, std::string* err) {
  nlohmann::json j;
  try {
    j = nlohmann::json::parse(json);
  } catch (const nlohmann::json::exception& e) {
    if (err) *err = std::string("invalid JSON: ") + e.what();
    return false;
  }
  if (!j.is_object()) {
    if (err) *err = "adapter document must be a JSON object";
    return false;
  }
  AdapterDefinition def;
  if (!readString(j, "id", &def.id, err, true)) return false;
  if (def.id.empty()) {
    if (err) *err = "field \"id\" must not be empty";
    return false;
  }
  if (!readString(j, "requirementId", &def.requirementId, err, false)) return false;
  if (!readString(j, "requirementName", &def.requirementName, err, false)) return false;
  if (!readString(j, "targetModule", &def.targetModule, err, false)) return false;
  if (!readString(j, "targetCapabilityId", &def.targetCapabilityId, err, true)) return false;
  if (def.targetCapabilityId.empty()) {
    if (err) *err = "field \"targetCapabilityId\" must not be empty";
    return false;
  }
  if (!readString(j, "targetCapabilityName", &def.targetCapabilityName, err, false)) return false;
  if (!readString(j, "transportKind", &def.transportKind, err, true)) return false;
  const auto& kinds = knownTransportKinds();
  if (std::find(kinds.begin(), kinds.end(), def.transportKind) == kinds.end()) {
    if (err) *err = "unknown transport kind \"" + def.transportKind + "\"";
    return false;
  }
  if (!readString(j, "baseUrl", &def.baseUrl, err, false)) return false;
  if (!readString(j, "endpoint", &def.endpoint, err, false)) return false;
  def.method = "POST";
  if (!readString(j, "method", &def.method, err, false)) return false;
  if (!readString(j, "sqlitePath", &def.sqlitePath, err, false)) return false;
  if (!readString(j, "table", &def.table, err, false)) return false;
  if (!readString(j, "operation", &def.operation, err, false)) return false;
  if (!readString(j, "filePath", &def.filePath, err, false)) return false;
  if (!readString(j, "fileOperation", &def.fileOperation, err, false)) return false;
  if (def.fileOperation.empty()) def.fileOperation = "write";
  if (!readString(j, "fileFormat", &def.fileFormat, err, false)) return false;
  if (def.fileFormat.empty()) def.fileFormat = "json";
  if (!readString(j, "handler", &def.handler, err, false)) return false;
  const auto compIt = j.find("computations");
  if (compIt != j.end()) {
    if (!compIt->is_array()) {
      if (err) *err = "field \"computations\" must be an array";
      return false;
    }
    for (const auto& item : *compIt) {
      if (!item.is_object()) {
        if (err) *err = "field \"computations\" entries must be objects";
        return false;
      }
      std::string name;
      std::string expression;
      if (!readString(item, "output", &name, err, true)) return false;
      if (!readString(item, "expression", &expression, err, true)) return false;
      def.computations.emplace_back(name, expression);
    }
  }
  if (!readMappings(j, "inputMap", &def.inputMap, err)) return false;
  if (!readMappings(j, "outputMap", &def.outputMap, err)) return false;
  const auto confIt = j.find("confidence");
  if (confIt != j.end()) {
    if (!confIt->is_number()) {
      if (err) *err = "field \"confidence\" must be a number";
      return false;
    }
    def.confidence = confIt->get<double>();
  }
  const auto expIt = j.find("explanation");
  if (expIt != j.end()) {
    if (!expIt->is_array()) {
      if (err) *err = "field \"explanation\" must be an array";
      return false;
    }
    for (const auto& item : *expIt) {
      if (!item.is_string()) {
        if (err) *err = "field \"explanation\" entries must be strings";
        return false;
      }
      def.explanation.push_back(item.get<std::string>());
    }
  }
  *out = std::move(def);
  return true;
}

}  // namespace adapter
}  // namespace careweave
