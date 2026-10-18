#include "careweave/adapter/synthesizer.hpp"

#include <algorithm>
#include <set>
#include <sstream>

#include "careweave/adapter/expression.hpp"

namespace careweave {
namespace adapter {

namespace {

std::string normalizeType(const std::string& type) {
  return core::valueTypeToString(core::valueTypeFromString(type));
}

std::string sanitizeIdPart(const std::string& name) {
  std::string out;
  for (char c : name) {
    out += (c == ' ' || c == '/') ? '-' : c;
  }
  return out;
}

const core::InputSpec* findInput(const std::vector<core::InputSpec>& list, const std::string& name) {
  for (const auto& item : list) {
    if (item.name == name) return &item;
  }
  return nullptr;
}

const core::OutputSpec* findOutput(const std::vector<core::OutputSpec>& list,
                                   const std::string& name) {
  for (const auto& item : list) {
    if (item.name == name) return &item;
  }
  return nullptr;
}

}  // namespace

std::string chooseTransform(const std::string& from, const std::string& to) {
  const std::string a = normalizeType(from);
  const std::string b = normalizeType(to);
  if (a == b) return "identity";
  // Lists carry many values, so they neither feed a scalar field nor accept one; converting
  // through the rendered form would silently change the payload shape.
  if (a == "list" || b == "list") return std::string();
  if (b == "boolean") return "to_bool";
  if (b == "integer") return "to_int";
  if (b == "real") return "to_real";
  if (b == "string" || b == "enum") return "to_string";
  return std::string();
}

SynthesisResult AdapterSynthesizer::synthesize(const SynthesisRequest& request) const {
  SynthesisResult result;
  const core::CapabilitySpec& req = request.requirement;
  const core::CapabilitySpec& cand = request.candidate;
  const mapper::MatchResult& match = request.match;

  if (req.name.empty() || cand.id.empty() || cand.name.empty()) {
    result.errors.push_back("requirement and candidate must both be fully identified");
    return result;
  }
  if (!match.candidateId.empty() && match.candidateId != cand.id) {
    result.errors.push_back("the match describes candidate \"" + match.candidateId +
                            "\" but the candidate given is \"" + cand.id + "\"");
    return result;
  }

  AdapterDefinition def;
  def.id = "adapter-" + sanitizeIdPart(req.name) + "-to-" + sanitizeIdPart(cand.name);
  def.requirementId = req.id;
  def.requirementName = req.name;
  def.targetModule = request.targetModule;
  def.targetCapabilityId = cand.id;
  def.targetCapabilityName = cand.name;
  def.confidence = match.total;
  def.explanation = match.explanation;

  // ---- Inputs ----
  std::set<std::string> mappedRequirementInputs;
  std::set<std::string> mappedProviderInputs;
  for (const auto& field : match.inputs) {
    const core::InputSpec* reqInput = findInput(req.inputs, field.required);
    if (reqInput == nullptr) {
      result.errors.push_back("the match binds requirement input \"" + field.required +
                              "\" which the requirement does not declare");
      continue;
    }
    if (!field.assigned) {
      if (reqInput->required) {
        result.errors.push_back("requirement input \"" + field.required +
                                "\" was not assigned to any provider input");
      } else {
        def.explanation.push_back("optional requirement input \"" + field.required +
                                  "\" has no provider counterpart");
      }
      continue;
    }
    const core::InputSpec* candInput = findInput(cand.inputs, field.provided);
    if (candInput == nullptr) {
      result.errors.push_back("the match binds provider input \"" + field.provided +
                              "\" which the candidate does not declare");
      continue;
    }
    const std::string transform = chooseTransform(reqInput->type, candInput->type);
    if (transform.empty()) {
      result.errors.push_back("cannot convert requirement input \"" + field.required + "\" of type " +
                              reqInput->type + " to provider type " + candInput->type);
      continue;
    }
    def.inputMap.push_back(FieldMapping{field.required, field.provided, transform,
                                        reqInput->required});
    mappedRequirementInputs.insert(field.required);
    mappedProviderInputs.insert(field.provided);
  }
  for (const auto& reqInput : req.inputs) {
    if (reqInput.required && mappedRequirementInputs.count(reqInput.name) == 0) {
      // Already reported above when the match listed the field; report the remaining case
      // where the match omitted the requirement input entirely.
      const bool reported =
          std::any_of(match.inputs.begin(), match.inputs.end(),
                      [&](const mapper::FieldMatch& f) { return f.required == reqInput.name; });
      if (!reported) {
        result.errors.push_back("requirement input \"" + reqInput.name +
                                "\" has no entry in the match");
      }
    }
  }
  for (const auto& candInput : cand.inputs) {
    if (candInput.required && mappedProviderInputs.count(candInput.name) == 0) {
      result.errors.push_back("provider input \"" + candInput.name +
                              "\" is required but nothing binds it");
    }
  }

  // ---- Outputs ----
  std::set<std::string> mappedRequirementOutputs;
  for (const auto& field : match.outputs) {
    const core::OutputSpec* reqOutput = findOutput(req.outputs, field.required);
    if (reqOutput == nullptr) {
      result.errors.push_back("the match names requirement output \"" + field.required +
                              "\" which the requirement does not declare");
      continue;
    }
    if (!field.assigned) {
      result.errors.push_back("requirement output \"" + field.required +
                              "\" is not provided by the candidate");
      continue;
    }
    const core::OutputSpec* candOutput = findOutput(cand.outputs, field.provided);
    if (candOutput == nullptr) {
      result.errors.push_back("the match binds provider output \"" + field.provided +
                              "\" which the candidate does not declare");
      continue;
    }
    const std::string transform = chooseTransform(candOutput->type, reqOutput->type);
    if (transform.empty()) {
      result.errors.push_back("cannot convert provider output \"" + field.provided +
                              "\" of type " + candOutput->type + " to requirement type " +
                              reqOutput->type);
      continue;
    }
    def.outputMap.push_back({field.provided, field.required, transform});
    mappedRequirementOutputs.insert(field.required);
  }
  for (const auto& reqOutput : req.outputs) {
    if (mappedRequirementOutputs.count(reqOutput.name) == 0) {
      const bool reported =
          std::any_of(match.outputs.begin(), match.outputs.end(),
                      [&](const mapper::FieldMatch& f) { return f.required == reqOutput.name; });
      if (!reported) {
        result.errors.push_back("requirement output \"" + reqOutput.name +
                                "\" has no entry in the match");
      }
    }
  }

  // ---- Transport ----
  const core::ExecutionMechanism& mech = cand.mechanism;
  const std::string& baseUrl = request.baseUrl;
  switch (cand.type) {
    case core::CapabilityType::API: {
      def.transportKind = "http";
      def.baseUrl = baseUrl;
      def.endpoint = mech.endpoint;
      def.method = mech.method.empty() ? "POST" : mech.method;
      if (baseUrl.empty()) result.errors.push_back("API candidate needs a module base URL");
      if (def.endpoint.empty()) result.errors.push_back("API mechanism declares no endpoint");
      break;
    }
    case core::CapabilityType::SERVICE: {
      if (!baseUrl.empty()) {
        def.transportKind = "http";
        def.baseUrl = baseUrl;
        def.endpoint = mech.endpoint.empty() ? "/invoke/" + cand.id : mech.endpoint;
        def.method = mech.method.empty() ? "POST" : mech.method;
      } else {
        def.transportKind = "local";
        def.handler = !mech.service.empty() ? mech.service : mech.function;
        if (def.handler.empty()) {
          result.errors.push_back("offline SERVICE candidate declares no service or function name");
        }
      }
      break;
    }
    case core::CapabilityType::GUI: {
      def.transportKind = "form";
      def.baseUrl = baseUrl;
      def.endpoint = !mech.page.empty()          ? mech.page
                     : !mech.action.empty()      ? mech.action
                     : !mech.endpoint.empty()    ? mech.endpoint
                     : !mech.component.empty()   ? "/" + mech.component
                                                 : std::string();
      def.method = "POST";
      if (baseUrl.empty()) result.errors.push_back("GUI candidate needs a module base URL");
      if (def.endpoint.empty()) {
        result.errors.push_back("GUI mechanism declares no page, action or component");
      }
      break;
    }
    case core::CapabilityType::DATABASE: {
      def.transportKind = "sqlite";
      def.sqlitePath = request.databasePath;
      def.table = mech.table;
      if (request.databasePath.empty()) {
        result.errors.push_back("DATABASE candidate needs a database path");
      }
      if (mech.table.empty()) result.errors.push_back("DATABASE mechanism declares no table");
      if (mech.operation.empty() || mech.operation == "insert" || mech.operation == "create") {
        def.operation = "insert";
      } else if (mech.operation == "update" || mech.operation == "set") {
        def.operation = "update";
      } else if (mech.operation == "select" || mech.operation == "query" ||
                 mech.operation == "select_one" || mech.operation == "read") {
        def.operation = "select_one";
      } else {
        result.errors.push_back("DATABASE mechanism declares unknown operation \"" +
                                mech.operation + "\"");
      }
      break;
    }
    case core::CapabilityType::FILE: {
      def.transportKind = "file";
      def.filePath = mech.path;
      def.fileOperation = request.fileOperation.empty() ? "write" : request.fileOperation;
      def.fileFormat = mech.format.empty() ? "json" : mech.format;
      if (mech.path.empty()) result.errors.push_back("FILE mechanism declares no path");
      if (def.fileOperation != "read" && def.fileOperation != "write") {
        result.errors.push_back("FILE operation \"" + def.fileOperation +
                                "\" must be read or write");
      }
      if (def.fileFormat != "json") {
        result.errors.push_back("FILE format \"" + def.fileFormat + "\" is not supported");
      }
      break;
    }
    case core::CapabilityType::COMPUTATION: {
      def.transportKind = "computation";
      if (mech.expression.empty()) {
        result.errors.push_back("COMPUTATION mechanism declares no expression");
        break;
      }
      std::vector<std::string> variableNames;
      for (const auto& m : def.inputMap) variableNames.push_back(m.to);
      std::istringstream entries(mech.expression);
      std::string entry;
      while (std::getline(entries, entry, ';')) {
        const size_t eq = entry.find('=');
        if (eq == std::string::npos) {
          result.errors.push_back("computation entry \"" + entry +
                                  "\" must have the form name = expression");
          continue;
        }
        std::string name = entry.substr(0, eq);
        std::string expr = entry.substr(eq + 1);
        name.erase(0, name.find_first_not_of(" \t"));
        name.erase(name.find_last_not_of(" \t") + 1);
        expr.erase(0, expr.find_first_not_of(" \t"));
        expr.erase(expr.find_last_not_of(" \t") + 1);
        if (name.empty() || expr.empty()) {
          result.errors.push_back("computation entry \"" + entry + "\" is incomplete");
          continue;
        }
        std::string err;
        if (!checkExpression(expr, variableNames, &err)) {
          result.errors.push_back("computation \"" + name + "\": " + err);
          continue;
        }
        def.computations.emplace_back(name, expr);
        variableNames.push_back(name);
      }
      break;
    }
    case core::CapabilityType::FUNCTION: {
      def.transportKind = "local";
      def.handler = !mech.function.empty() ? mech.function : mech.modulePath;
      if (def.handler.empty()) result.errors.push_back("FUNCTION mechanism declares no function");
      break;
    }
    case core::CapabilityType::EVENT: {
      def.transportKind = "local";
      def.handler = !mech.handler.empty() ? mech.handler : mech.trigger;
      if (def.handler.empty()) result.errors.push_back("EVENT mechanism declares no handler");
      break;
    }
    case core::CapabilityType::MESSAGE: {
      def.transportKind = "local";
      def.handler = !mech.topic.empty() ? mech.topic : mech.queue;
      if (def.handler.empty()) result.errors.push_back("MESSAGE mechanism declares no topic");
      break;
    }
  }

  def.explanation.push_back("transport " + def.transportKind + " chosen for capability type " +
                            core::capabilityTypeToString(cand.type));
  def.explanation.push_back("confidence " + std::to_string(def.confidence) + " from the mapper");

  result.adapter = std::move(def);
  result.ok = result.errors.empty();
  return result;
}

std::string SynthesisResult::render() const {
  std::ostringstream os;
  os << (ok ? "adapter synthesis ok\n" : "adapter synthesis failed\n");
  if (!ok) {
    for (const auto& error : errors) os << "  error: " << error << "\n";
  }
  os << adapter.render();
  return os.str();
}

}  // namespace adapter
}  // namespace careweave
