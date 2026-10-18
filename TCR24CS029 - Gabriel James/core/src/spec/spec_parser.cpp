#include "careweave/spec/spec_parser.hpp"

#include <algorithm>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <set>
#include <sstream>

#include "careweave/spec/yaml_lite.hpp"

namespace careweave {
namespace spec {

using json = nlohmann::json;

namespace {

std::string readFileText(const std::string& path, bool* ok) {
  std::ifstream in(path, std::ios::binary);
  if (!in) {
    if (ok) *ok = false;
    return {};
  }
  std::ostringstream buf;
  buf << in.rdbuf();
  if (ok) *ok = true;
  return buf.str();
}

bool endsWith(const std::string& s, const std::string& suffix) {
  return s.size() >= suffix.size() && s.compare(s.size() - suffix.size(), suffix.size(), suffix) == 0;
}

void addIssue(std::vector<ValidationIssue>* issues, const std::string& path,
              const std::string& message, const std::string& schemaPath = "") {
  ValidationIssue issue;
  issue.path = path;
  issue.message = message;
  issue.schemaPath = schemaPath;
  issues->push_back(std::move(issue));
}

std::vector<std::string> stringList(const json& v) {
  std::vector<std::string> out;
  if (v.is_array()) {
    for (const auto& item : v) {
      if (item.is_string()) {
        out.push_back(item.get<std::string>());
      } else if (!item.is_null()) {
        // Boolean, numeric and structured domain entries keep their textual form so a domain
        // like [false, true] or [0, 10000] survives decoding.
        out.push_back(item.dump());
      }
    }
  } else if (v.is_string()) {
    out.push_back(v.get<std::string>());
  }
  return out;
}

core::Value decodeValue(const json& v) {
  if (v.is_boolean()) return core::Value(v.get<bool>());
  if (v.is_number_integer()) return core::Value(v.get<int64_t>());
  if (v.is_number_float()) return core::Value(v.get<double>());
  if (v.is_string()) return core::Value(v.get<std::string>());
  if (v.is_array()) {
    std::vector<std::string> items;
    for (const auto& item : v) {
      if (item.is_string()) items.push_back(item.get<std::string>());
      else if (item.is_boolean()) items.push_back(item.get<bool>() ? "true" : "false");
      else if (item.is_number()) items.push_back(std::to_string(item.get<double>()));
    }
    return core::Value(std::move(items));
  }
  return core::Value(std::string());
}

core::Condition decodeCondition(const json& c) {
  core::Condition cond;
  cond.variable = c.value("variable", std::string());
  cond.op = core::conditionOpFromString(c.value("op", std::string("=")));
  cond.value = decodeValue(c.value("value", json(nullptr)));
  return cond;
}

core::Effect decodeEffect(const json& e) {
  core::Effect eff;
  eff.variable = e.value("variable", std::string());
  eff.op = core::effectOpFromString(e.value("op", std::string("SET")));
  eff.value = decodeValue(e.value("value", json(nullptr)));
  return eff;
}

core::InputSpec decodeInput(const json& i) {
  core::InputSpec in;
  in.name = i.value("name", std::string());
  in.type = i.value("type", std::string("string"));
  const json& domain = i.value("domain", json("any"));
  if (domain.is_string()) {
    in.domain = domain.get<std::string>();
  } else if (domain.is_array()) {
    in.domainValues = stringList(domain);
    in.domain = "enum:" + std::to_string(in.domainValues.size()) + " values";
  }
  in.required = i.value("required", true);
  return in;
}

core::OutputSpec decodeOutput(const json& o) {
  core::OutputSpec out;
  out.name = o.value("name", std::string());
  out.type = o.value("type", std::string("string"));
  const json& domain = o.value("domain", json("any"));
  if (domain.is_string()) {
    out.domain = domain.get<std::string>();
  } else if (domain.is_array()) {
    out.domainValues = stringList(domain);
    out.domain = "enum:" + std::to_string(out.domainValues.size()) + " values";
  }
  return out;
}

core::ExecutionMechanism decodeMechanism(const json& m, core::CapabilityType type) {
  core::ExecutionMechanism mech;
  mech.kind = type;
  if (m.is_object()) {
    if (m.contains("kind") && m["kind"].is_string()) {
      mech.kind = core::capabilityTypeFromString(m["kind"].get<std::string>());
    }
    mech.method = m.value("method", std::string());
    mech.endpoint = m.value("endpoint", std::string());
    mech.operation = m.value("operation", std::string());
    mech.table = m.value("table", std::string());
    mech.action = m.value("action", std::string());
    mech.component = m.value("component", std::string());
    mech.page = m.value("page", std::string());
    mech.trigger = m.value("trigger", std::string());
    mech.handler = m.value("handler", std::string());
    mech.topic = m.value("topic", std::string());
    mech.queue = m.value("queue", std::string());
    mech.function = m.value("function", std::string());
    mech.modulePath = m.value("module_path", std::string());
    mech.path = m.value("path", std::string());
    mech.format = m.value("format", std::string());
    mech.expression = m.value("expression", std::string());
    mech.artifact = m.value("output_artifact", std::string());
    mech.service = m.value("service", std::string());
    mech.baseUrl = m.value("base_url", std::string());
    mech.notes = m.value("notes", std::string());
  }
  return mech;
}

// "08:00" -> 480 minutes after midnight.
int parseClock(const std::string& s) {
  if (s.size() != 5 || s[2] != ':') return -1;
  const int h = std::atoi(s.substr(0, 2).c_str());
  const int m = std::atoi(s.substr(3, 2).c_str());
  if (h < 0 || h > 23 || m < 0 || m > 59) return -1;
  return h * 60 + m;
}

core::OperationalSpec decodeOperational(const json& cap) {
  core::OperationalSpec ops;
  if (cap.contains("quality") && cap["quality"].is_object()) {
    const json& q = cap["quality"];
    ops.cost.timeMs = q.value("time_ms", 0.0);
    ops.cost.money = q.value("money", 0.0);
    ops.cost.resource = q.value("resource", 0.0);
    ops.cost.risk = q.value("risk", 0.0);
    ops.cost.energy = q.value("energy", 0.0);
    for (auto it = q.begin(); it != q.end(); ++it) {
      const std::string key = it.key();
      if (key == "time_ms" || key == "money" || key == "resource" || key == "risk" ||
          key == "energy") {
        continue;
      }
      if (it.value().is_number()) ops.cost.extra[key] = it.value().get<double>();
    }
  }
  ops.reliability = cap.value("reliability", 1.0);
  if (cap.contains("availability")) {
    const json& a = cap["availability"];
    if (a.is_boolean()) {
      ops.available = a.get<bool>();
    } else if (a.is_number()) {
      ops.available = a.get<double>() != 0.0;
    } else if (a.is_object()) {
      ops.available = a.value("always", true);
      if (a.contains("windows") && a["windows"].is_array() && !a["windows"].empty()) {
        ops.windowed = true;
        for (const auto& w : a["windows"]) {
          core::AvailabilityWindow window;
          window.days = stringList(w.value("days", json::array()));
          window.fromMinutes = parseClock(w.value("from", std::string("00:00")));
          window.toMinutes = parseClock(w.value("to", std::string("23:59")));
          ops.windows.push_back(window);
        }
      }
    }
  }
  return ops;
}

core::CapabilitySpec decodeCapability(const json& c) {
  core::CapabilitySpec cap;
  cap.id = c.value("id", std::string());
  cap.name = c.value("name", std::string());
  cap.description = c.value("description", std::string());
  cap.type = core::capabilityTypeFromString(c.value("type", std::string("FUNCTION")));
  for (const auto& i : c.value("inputs", json::array())) cap.inputs.push_back(decodeInput(i));
  for (const auto& o : c.value("outputs", json::array())) cap.outputs.push_back(decodeOutput(o));
  for (const auto& p : c.value("preconditions", json::array())) {
    cap.preconditions.push_back(decodeCondition(p));
  }
  for (const auto& e : c.value("effects", json::array())) cap.effects.push_back(decodeEffect(e));
  for (const auto& k : c.value("constraints", json::array())) {
    cap.constraints.push_back(decodeCondition(k));
  }
  cap.resources = stringList(c.value("resources", json::array()));
  cap.operational = decodeOperational(c);
  cap.mechanism = decodeMechanism(c.value("mechanism", json::object()), cap.type);
  cap.roles = stringList(c.value("roles", json::array()));
  if (c.contains("state_delta_hint") && c["state_delta_hint"].is_object()) {
    for (auto it = c["state_delta_hint"].begin(); it != c["state_delta_hint"].end(); ++it) {
      cap.stateDeltaHint[it.key()] = decodeValue(it.value());
    }
  }
  return cap;
}

core::StateVariableSchema decodeStateVariable(const json& v) {
  core::StateVariableSchema s;
  s.name = v.value("name", std::string());
  s.type = v.value("type", std::string("string"));
  const json& domain = v.value("domain", json(nullptr));
  if (domain.is_array()) {
    s.domainValues = stringList(domain);
    if (s.domainValues.size() == 2) {
      try {
        s.domainMin = std::stod(s.domainValues[0]);
        s.domainMax = std::stod(s.domainValues[1]);
        s.bounded = true;
      } catch (...) {
        s.bounded = false;
      }
    }
    std::ostringstream os;
    os << "[";
    for (size_t i = 0; i < s.domainValues.size(); ++i) {
      if (i) os << ", ";
      os << s.domainValues[i];
    }
    os << "]";
    s.domainText = os.str();
  } else if (domain.is_string()) {
    s.domainText = domain.get<std::string>();
  }
  return s;
}

std::vector<ValidationIssue> semanticChecks(const core::ApplicationModel& m,
                                            bool strictVariables) {
  std::vector<ValidationIssue> issues;
  std::set<std::string> declared;
  for (const auto& v : m.stateSchema) declared.insert(v.name);
  std::set<std::string> declaredResources;
  for (const auto& r : m.resources) declaredResources.insert(r.id);

  if (m.capabilities.empty()) {
    addIssue(&issues, "/capabilities", "the application must declare at least one capability");
  }
  std::set<std::string> ids;
  for (size_t ci = 0; ci < m.capabilities.size(); ++ci) {
    const auto& cap = m.capabilities[ci];
    const std::string base = "/capabilities/" + std::to_string(ci);
    if (cap.id.empty()) addIssue(&issues, base + "/id", "capability id is empty");
    if (cap.name.empty()) addIssue(&issues, base + "/name", "capability name is empty");
    if (!cap.id.empty() && !ids.insert(cap.id).second) {
      addIssue(&issues, base + "/id", "duplicate capability id " + cap.id);
    }
    if (cap.mechanism.kind != cap.type) {
      addIssue(&issues, base + "/mechanism/kind",
               "mechanism kind " + core::capabilityTypeToString(cap.mechanism.kind) +
                   " disagrees with capability type " + core::capabilityTypeToString(cap.type));
    }
    const auto checkConditionVariables = [&](const std::vector<core::Condition>& conds,
                                            const std::string& where) {
      for (size_t i = 0; i < conds.size(); ++i) {
        const std::string& var = conds[i].variable;
        if (var.empty()) {
          addIssue(&issues, base + where + "/" + std::to_string(i), "condition variable is empty");
          continue;
        }
        if (strictVariables && declared.count(var) == 0) {
          addIssue(&issues, base + where + "/" + std::to_string(i),
                   "condition references undeclared state variable \"" + var + "\"");
        }
      }
    };
    checkConditionVariables(cap.preconditions, "/preconditions");
    checkConditionVariables(cap.constraints, "/constraints");
    for (size_t i = 0; i < cap.effects.size(); ++i) {
      const std::string& var = cap.effects[i].variable;
      if (var.empty()) {
        addIssue(&issues, base + "/effects/" + std::to_string(i), "effect variable is empty");
        continue;
      }
      if (strictVariables && declared.count(var) == 0) {
        addIssue(&issues, base + "/effects/" + std::to_string(i),
                 "effect writes undeclared state variable \"" + var + "\"");
      }
    }
    for (size_t i = 0; i < cap.inputs.size(); ++i) {
      if (cap.inputs[i].name.empty()) {
        addIssue(&issues, base + "/inputs/" + std::to_string(i), "input name is empty");
      }
    }
    for (size_t i = 0; i < cap.outputs.size(); ++i) {
      if (cap.outputs[i].name.empty()) {
        addIssue(&issues, base + "/outputs/" + std::to_string(i), "output name is empty");
      }
    }
    if (cap.operational.reliability < 0.0 || cap.operational.reliability > 1.0) {
      addIssue(&issues, base + "/reliability", "reliability must lie in [0,1]");
    }
    for (const std::string& resourceId : cap.resources) {
      if (declaredResources.count(resourceId) == 0) {
        addIssue(&issues, base + "/resources",
                 "capability requires undeclared resource \"" + resourceId + "\"");
      }
    }
  }

  if (strictVariables) {
    for (const auto& kv : m.initialState) {
      if (declared.count(kv.first) == 0) {
        addIssue(&issues, "/initial_state/" + kv.first,
                 "initial state assigns undeclared variable \"" + kv.first + "\"");
      }
    }
  }
  for (size_t i = 0; i < m.goal.size(); ++i) {
    if (strictVariables && declared.count(m.goal[i].variable) == 0) {
      addIssue(&issues, "/goal/" + std::to_string(i),
               "goal references undeclared state variable \"" + m.goal[i].variable + "\"");
    }
  }
  for (size_t i = 0; i < m.resources.size(); ++i) {
    if (m.resources[i].id.empty()) {
      addIssue(&issues, "/resources/" + std::to_string(i), "resource id is empty");
    }
  }
  return issues;
}

// ---- YAML emission ----

bool needsQuotes(const std::string& s) {
  if (s.empty()) return true;
  if (s == "true" || s == "false" || s == "null" || s == "~" || s == "yes" || s == "no") return true;
  char* end = nullptr;
  std::strtod(s.c_str(), &end);
  if (end && *end == '\0') return true;
  for (char c : s) {
    if (c == ':' || c == '#' || c == '\n' || c == '{' || c == '}' || c == '[' || c == ']' ||
        c == ',' || c == '&' || c == '*' || c == '!' || c == '|' || c == '>' || c == '\'' ||
        c == '"' || c == '%' || c == '@' || c == '`') {
      return true;
    }
  }
  if (s.front() == ' ' || s.back() == ' ') return true;
  return false;
}

std::string yamlScalar(const std::string& s) {
  if (!needsQuotes(s)) return s;
  std::string out = "\"";
  for (char c : s) {
    if (c == '"' || c == '\\') out += '\\';
    if (c == '\n') {
      out += "\\n";
      continue;
    }
    out += c;
  }
  out += "\"";
  return out;
}

void emitYamlValue(const json& v, int indent, std::ostringstream& os, bool inSequence);

void emitYamlScalarOrCollection(const json& v, int indent, std::ostringstream& os, bool afterDash) {
  if (v.is_object()) {
    if (v.empty()) {
      os << " {}";
      return;
    }
    bool first = true;
    for (auto it = v.begin(); it != v.end(); ++it) {
      if (!first || !afterDash) {
        os << "\n" << std::string(static_cast<size_t>(indent), ' ');
      } else {
        os << " ";
      }
      first = false;
      os << it.key() << ":";
      emitYamlValue(it.value(), indent + 2, os, false);
    }
    return;
  }
  if (v.is_array()) {
    if (v.empty()) {
      os << " []";
      return;
    }
    bool first = true;
    for (const auto& item : v) {
      if (first && afterDash) {
        os << " -";
      } else {
        os << "\n" << std::string(static_cast<size_t>(indent), ' ') << "-";
      }
      first = false;
      emitYamlScalarOrCollection(item, indent + 2, os, true);
    }
    return;
  }
  os << " ";
  if (v.is_string()) {
    os << yamlScalar(v.get<std::string>());
  } else {
    os << v.dump();
  }
}

void emitYamlValue(const json& v, int indent, std::ostringstream& os, bool inSequence) {
  emitYamlScalarOrCollection(v, indent, os, inSequence);
}

}  // namespace

std::string SpecParseResult::renderIssues() const {
  std::ostringstream os;
  for (const auto& issue : issues) {
    os << origin << issue.path << ": " << issue.message;
    if (!issue.schemaPath.empty() && issue.schemaPath != "#") {
      os << " (schema " << issue.schemaPath << ")";
    }
    os << "\n";
  }
  std::string s = os.str();
  if (!s.empty() && s.back() == '\n') s.pop_back();
  return s;
}

std::string findSchemaFile(const std::string& startPath) {
  // Resolve the path first so the climb is independent of how the caller spelled the path or
  // which directory the process runs in: a relative path is joined with the working directory
  // and the parents are then walked up to the filesystem root.
  std::error_code ec;
  std::filesystem::path resolved = std::filesystem::absolute(startPath, ec);
  if (ec) resolved = std::filesystem::path(startPath);
  std::filesystem::path dir = resolved.parent_path();
  for (int depth = 0; depth < 12 && !dir.empty(); ++depth) {
    const std::filesystem::path candidate = dir / "specs" / "capability.schema.json";
    std::ifstream probe(candidate.string());
    if (probe.good()) return candidate.string();
    const std::filesystem::path parent = dir.parent_path();
    if (parent == dir) break;
    dir = parent;
  }
  return std::string();
}

SpecParseResult loadSpecFile(const std::string& path, const SpecParseOptions& options) {
  SpecParseResult result;
  result.origin = path;
  bool readOk = false;
  const std::string text = readFileText(path, &readOk);
  if (!readOk) {
    addIssue(&result.issues, "/", "cannot read specification file");
    return result;
  }
  json doc;
  std::string error;
  const bool preferYaml = endsWith(path, ".yaml") || endsWith(path, ".yml");
  bool parsed = false;
  if (preferYaml) {
    parsed = parseYaml(text, &doc, &error);
  } else {
    try {
      doc = json::parse(text);
      parsed = true;
    } catch (const json::parse_error& e) {
      error = e.what();
    }
  }
  if (!parsed) {
    addIssue(&result.issues, "/", "cannot parse specification: " + error);
    return result;
  }
  return parseSpecDocument(doc, path, options);
}

SpecParseResult parseSpecDocument(const json& doc, const std::string& origin,
                                 const SpecParseOptions& options) {
  SpecParseResult result;
  result.origin = origin;

  std::string schemaPath = options.schemaPath;
  if (schemaPath.empty()) schemaPath = findSchemaFile(origin);
  if (!schemaPath.empty()) {
    bool ok = false;
    const std::string schemaText = readFileText(schemaPath, &ok);
    if (ok) {
      try {
        const json schema = json::parse(schemaText);
        const ValidationReport report = validateAgainstSchema(doc, schema, schema);
        for (const auto& issue : report.issues) result.issues.push_back(issue);
      } catch (const json::parse_error& e) {
        addIssue(&result.issues, "/", std::string("schema file is not valid JSON: ") + e.what());
      }
    } else {
      addIssue(&result.issues, "/", "cannot read schema file " + schemaPath);
    }
  } else if (options.requireSchema) {
    addIssue(&result.issues, "/", "no capability schema found for " + origin);
  }

  core::ApplicationModel m;
  if (doc.contains("module")) {
    const json& mod = doc["module"];
    m.moduleId = mod.value("module_id", std::string());
    m.version = mod.value("version", std::string());
    m.domain = mod.value("domain", std::string("generic"));
    m.port = mod.value("port", 0);
    m.baseUrl = mod.value("base_url", std::string());
    m.health = mod.value("health", std::string("/health"));
    m.description = mod.value("description", std::string());
    m.language = mod.value("language", std::string());
    m.databaseFile = mod.value("database_file", std::string());
    m.ui = mod.value("ui", std::string());
  }
  if (doc.contains("state_schema") && doc["state_schema"].is_array()) {
    for (const auto& v : doc["state_schema"]) m.stateSchema.push_back(decodeStateVariable(v));
  }
  if (doc.contains("initial_state") && doc["initial_state"].is_object()) {
    for (auto it = doc["initial_state"].begin(); it != doc["initial_state"].end(); ++it) {
      m.initialState[it.key()] = decodeValue(it.value());
    }
  }
  if (doc.contains("resources") && doc["resources"].is_array()) {
    for (const auto& r : doc["resources"]) {
      core::ResourceSpec spec;
      spec.id = r.value("id", std::string());
      spec.kind = r.value("kind", std::string());
      spec.available = r.value("available", true);
      spec.details = r.value("details", std::string());
      m.resources.push_back(spec);
    }
  }
  if (doc.contains("constraints") && doc["constraints"].is_array()) {
    for (const auto& c : doc["constraints"]) {
      core::ConstraintSpec spec;
      spec.id = c.value("id", std::string());
      spec.kind = c.value("kind", std::string());
      spec.expression = c.value("expression", std::string());
      spec.enforcedBy = c.value("enforced_by", std::string());
      m.constraints.push_back(spec);
    }
  }
  if (doc.contains("goal") && doc["goal"].is_array()) {
    for (const auto& g : doc["goal"]) m.goal.push_back(decodeCondition(g));
  }
  if (doc.contains("capabilities") && doc["capabilities"].is_array()) {
    for (const auto& c : doc["capabilities"]) m.capabilities.push_back(decodeCapability(c));
  }

  for (auto& issue : semanticChecks(m, options.strictVariables)) {
    result.issues.push_back(std::move(issue));
  }
  result.model = std::move(m);
  result.ok = result.issues.empty();
  return result;
}

nlohmann::json specToJson(const core::ApplicationModel& m) {
  json doc;
  doc["spec_version"] = "1.0";
  json mod;
  mod["module_id"] = m.moduleId;
  mod["version"] = m.version;
  mod["domain"] = m.domain;
  mod["port"] = m.port;
  mod["base_url"] = m.baseUrl;
  mod["health"] = m.health;
  mod["description"] = m.description;
  mod["language"] = m.language;
  if (!m.databaseFile.empty()) mod["database_file"] = m.databaseFile;
  if (!m.ui.empty()) mod["ui"] = m.ui;
  doc["module"] = mod;

  json schema = json::array();
  for (const auto& v : m.stateSchema) {
    json entry;
    entry["name"] = v.name;
    entry["type"] = v.type;
    if (!v.domainValues.empty()) {
      json dom = json::array();
      for (const auto& d : v.domainValues) {
        // Preserve numeric domain entries as numbers where they parse cleanly.
        char* end = nullptr;
        std::strtod(d.c_str(), &end);
        if (end && *end == '\0' && !d.empty()) dom.push_back(std::stod(d));
        else dom.push_back(d);
      }
      entry["domain"] = dom;
    } else {
      entry["domain"] = v.domainText.empty() ? std::string("unbounded") : v.domainText;
    }
    schema.push_back(entry);
  }
  doc["state_schema"] = schema;

  json init = json::object();
  for (const auto& kv : m.initialState) {
    if (kv.second.type() == core::ValueType::BOOL) init[kv.first] = kv.second.asBool();
    else if (kv.second.type() == core::ValueType::INT) init[kv.first] = kv.second.asInt();
    else if (kv.second.type() == core::ValueType::REAL) init[kv.first] = kv.second.asDouble();
    else if (kv.second.type() == core::ValueType::LIST) init[kv.first] = kv.second.asList();
    else init[kv.first] = kv.second.asString();
  }
  doc["initial_state"] = init;

  json resources = json::array();
  for (const auto& r : m.resources) {
    json entry;
    entry["id"] = r.id;
    entry["kind"] = r.kind;
    entry["available"] = r.available;
    if (!r.details.empty()) entry["details"] = r.details;
    resources.push_back(entry);
  }
  doc["resources"] = resources;

  json constraints = json::array();
  for (const auto& c : m.constraints) {
    json entry;
    entry["id"] = c.id;
    entry["kind"] = c.kind;
    entry["expression"] = c.expression;
    if (!c.enforcedBy.empty()) entry["enforced_by"] = c.enforcedBy;
    constraints.push_back(entry);
  }
  doc["constraints"] = constraints;

  json goal = json::array();
  for (const auto& c : m.goal) {
    json entry;
    entry["variable"] = c.variable;
    entry["op"] = core::conditionOpToString(c.op);
    switch (c.value.type()) {
      case core::ValueType::BOOL: entry["value"] = c.value.asBool(); break;
      case core::ValueType::INT: entry["value"] = c.value.asInt(); break;
      case core::ValueType::REAL: entry["value"] = c.value.asDouble(); break;
      case core::ValueType::LIST: entry["value"] = c.value.asList(); break;
      default: entry["value"] = c.value.asString(); break;
    }
    goal.push_back(entry);
  }
  doc["goal"] = goal;

  json caps = json::array();
  for (const auto& cap : m.capabilities) {
    json c;
    c["id"] = cap.id;
    c["name"] = cap.name;
    c["type"] = core::capabilityTypeToString(cap.type);
    c["description"] = cap.description;
    json inputs = json::array();
    for (const auto& i : cap.inputs) {
      json e;
      e["name"] = i.name;
      e["type"] = i.type;
      if (i.domainValues.empty()) e["domain"] = i.domain;
      else e["domain"] = i.domainValues;
      e["required"] = i.required;
      inputs.push_back(e);
    }
    c["inputs"] = inputs;
    json outputs = json::array();
    for (const auto& o : cap.outputs) {
      json e;
      e["name"] = o.name;
      e["type"] = o.type;
      if (o.domainValues.empty()) e["domain"] = o.domain;
      else e["domain"] = o.domainValues;
      outputs.push_back(e);
    }
    c["outputs"] = outputs;
    const auto condJson = [](const core::Condition& cond) {
      json e;
      e["variable"] = cond.variable;
      e["op"] = core::conditionOpToString(cond.op);
      switch (cond.value.type()) {
        case core::ValueType::BOOL: e["value"] = cond.value.asBool(); break;
        case core::ValueType::INT: e["value"] = cond.value.asInt(); break;
        case core::ValueType::REAL: e["value"] = cond.value.asDouble(); break;
        case core::ValueType::LIST: e["value"] = cond.value.asList(); break;
        default: e["value"] = cond.value.asString(); break;
      }
      return e;
    };
    json pre = json::array();
    for (const auto& p : cap.preconditions) pre.push_back(condJson(p));
    c["preconditions"] = pre;
    json eff = json::array();
    for (const auto& e : cap.effects) {
      json entry;
      entry["variable"] = e.variable;
      entry["op"] = core::effectOpToString(e.op);
      switch (e.value.type()) {
        case core::ValueType::BOOL: entry["value"] = e.value.asBool(); break;
        case core::ValueType::INT: entry["value"] = e.value.asInt(); break;
        case core::ValueType::REAL: entry["value"] = e.value.asDouble(); break;
        case core::ValueType::LIST: entry["value"] = e.value.asList(); break;
        default: entry["value"] = e.value.asString(); break;
      }
      eff.push_back(entry);
    }
    c["effects"] = eff;
    json cons = json::array();
    for (const auto& k : cap.constraints) cons.push_back(condJson(k));
    c["constraints"] = cons;
    c["resources"] = cap.resources;
    json q;
    q["time_ms"] = cap.operational.cost.timeMs;
    q["money"] = cap.operational.cost.money;
    q["resource"] = cap.operational.cost.resource;
    q["risk"] = cap.operational.cost.risk;
    q["energy"] = cap.operational.cost.energy;
    for (const auto& kv : cap.operational.cost.extra) q[kv.first] = kv.second;
    c["quality"] = q;
    c["reliability"] = cap.operational.reliability;
    if (cap.operational.windowed && !cap.operational.windows.empty()) {
      json a;
      a["always"] = cap.operational.available;
      json windows = json::array();
      for (const auto& w : cap.operational.windows) {
        json entry;
        entry["days"] = w.days;
        char from[8], to[8];
        std::snprintf(from, sizeof(from), "%02d:%02d", w.fromMinutes / 60, w.fromMinutes % 60);
        std::snprintf(to, sizeof(to), "%02d:%02d", w.toMinutes / 60, w.toMinutes % 60);
        entry["from"] = from;
        entry["to"] = to;
        windows.push_back(entry);
      }
      a["windows"] = windows;
      c["availability"] = a;
    } else {
      c["availability"] = cap.operational.available;
    }
    json mech;
    mech["kind"] = core::capabilityTypeToString(cap.mechanism.kind);
    const auto putIf = [&mech](const char* key, const std::string& value) {
      if (!value.empty()) mech[key] = value;
    };
    putIf("method", cap.mechanism.method);
    putIf("endpoint", cap.mechanism.endpoint);
    putIf("operation", cap.mechanism.operation);
    putIf("table", cap.mechanism.table);
    putIf("action", cap.mechanism.action);
    putIf("component", cap.mechanism.component);
    putIf("page", cap.mechanism.page);
    putIf("trigger", cap.mechanism.trigger);
    putIf("handler", cap.mechanism.handler);
    putIf("topic", cap.mechanism.topic);
    putIf("queue", cap.mechanism.queue);
    putIf("function", cap.mechanism.function);
    putIf("module_path", cap.mechanism.modulePath);
    putIf("path", cap.mechanism.path);
    putIf("format", cap.mechanism.format);
    putIf("expression", cap.mechanism.expression);
    putIf("output_artifact", cap.mechanism.artifact);
    putIf("service", cap.mechanism.service);
    putIf("base_url", cap.mechanism.baseUrl);
    putIf("notes", cap.mechanism.notes);
    c["mechanism"] = mech;
    if (!cap.roles.empty()) c["roles"] = cap.roles;
    caps.push_back(c);
  }
  doc["capabilities"] = caps;
  return doc;
}

std::string specToYaml(const core::ApplicationModel& model) {
  const json doc = specToJson(model);
  std::ostringstream os;
  os << "# Formal capability specification sheet, YAML rendering.\n";
  os << "# Generated from spec.json by the careweave_cli spec-yaml command; the two files are\n";
  os << "# always equivalent, and the round trip is proved by the command and by the test suite.\n";
  bool first = true;
  for (auto it = doc.begin(); it != doc.end(); ++it) {
    if (!first) os << "\n";
    first = false;
    os << it.key() << ":";
    emitYamlScalarOrCollection(it.value(), 2, os, false);
    os << "\n";
  }
  return os.str();
}

bool writeSpecJson(const core::ApplicationModel& model, const std::string& path, std::string* error) {
  std::ofstream out(path, std::ios::binary);
  if (!out) {
    if (error) *error = "cannot write " + path;
    return false;
  }
  out << specToJson(model).dump(2) << "\n";
  return true;
}

bool writeSpecYaml(const core::ApplicationModel& model, const std::string& path, std::string* error) {
  std::ofstream out(path, std::ios::binary);
  if (!out) {
    if (error) *error = "cannot write " + path;
    return false;
  }
  out << specToYaml(model);
  return true;
}

}  // namespace spec
}  // namespace careweave
