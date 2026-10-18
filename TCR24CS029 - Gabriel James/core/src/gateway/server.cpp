// Gateway HTTP server: the management API, the canonical hospital API, the workflow endpoint
// and the dashboard. The server is a thin shell over the library methods of gateway.cpp: it
// parses requests, calls them and renders their results as JSON. One worker thread serves
// requests so the registry, the circuit state and the audit trail stay deterministic.
#include "careweave/gateway/gateway.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "careweave/bundle/bundler.hpp"
#include "careweave/core/value_json.hpp"
#include "careweave/embedding/encoders.hpp"
#include "careweave/embedding/vector.hpp"
#include "careweave/planner/planner.hpp"
#include "careweave/spec/spec_parser.hpp"
#include "httplib.h"

namespace careweave {
namespace gateway {

namespace fs = std::filesystem;
using nlohmann::json;

namespace {

void sendJson(httplib::Response& response, const std::string& body, int status = 200) {
  response.status = status;
  response.set_content(body, "application/json");
}

std::string errorBody(const std::string& message) {
  return json{{"status", "error"}, {"error", message}}.dump(2) + "\n";
}

bool parseBody(const httplib::Request& request, json* document, std::string* error) {
  if (request.body.empty()) {
    *error = "the request body must be a JSON object";
    return false;
  }
  *document = json::parse(request.body, nullptr, false);
  if (document->is_discarded() || !document->is_object()) {
    *error = "the request body must be a JSON object";
    return false;
  }
  return true;
}

bool parseInputs(const json& document, std::map<std::string, core::Value>* inputs,
                 std::string* error) {
  if (!document.is_object()) {
    *error = "inputs must be a JSON object";
    return false;
  }
  for (auto it = document.begin(); it != document.end(); ++it) {
    core::Value value;
    std::string valueError;
    if (!core::jsonToValue(it.value(), &value, &valueError)) {
      *error = "input " + it.key() + ": " + valueError;
      return false;
    }
    (*inputs)[it.key()] = value;
  }
  return true;
}

std::vector<std::string> parsePreferred(const json& document) {
  std::vector<std::string> preferred;
  if (document.contains("preferred_modules") && document["preferred_modules"].is_array()) {
    for (const json& entry : document["preferred_modules"]) {
      if (entry.is_string()) preferred.push_back(entry.get<std::string>());
    }
  }
  return preferred;
}

// Shared reader for the id and name lists of the resolve, call, workflow and bundle bodies. The
// key is optional; when present it must be a non empty array of non empty strings, so a caller
// that computed an empty set gets a clear error instead of a silently widened or broken request.
bool parseStringList(const json& document, const char* key, const char* description,
                     std::vector<std::string>* out, std::string* error) {
  if (!document.contains(key)) return true;
  const json& value = document[key];
  if (!value.is_array() || value.empty()) {
    *error = std::string(key) + " must be a non empty array of " + description;
    return false;
  }
  for (const json& entry : value) {
    if (!entry.is_string() || entry.get<std::string>().empty()) {
      *error = std::string(key) + " must be a non empty array of " + description;
      return false;
    }
    out->push_back(entry.get<std::string>());
  }
  return true;
}

std::string candidatesJson(const std::vector<Candidate>& candidates) {
  json rows = json::array();
  for (const Candidate& candidate : candidates) {
    rows.push_back({{"module_id", candidate.moduleId},
                    {"capability_id", candidate.capabilityId},
                    {"capability_name", candidate.capabilityName},
                    {"capability_type", candidate.capabilityType},
                    {"endpoint", candidate.endpoint},
                    {"total", candidate.total},
                    {"margin", candidate.margin},
                    {"ambiguous", candidate.ambiguous}});
  }
  return rows.dump(2) + "\n";
}

// Resolves a repository relative path and refuses anything that leaves the tree, so the
// dashboard endpoints read sheets and place bundles without path surprises.
bool resolveInsideRoot(const std::string& rootDir, const std::string& relative, fs::path* out,
                       std::string* error) {
  if (relative.empty()) {
    *error = "a relative path is required";
    return false;
  }
  const fs::path candidate(relative);
  if (candidate.is_absolute()) {
    *error = "paths are relative to the repository root";
    return false;
  }
  std::error_code ec;
  const fs::path root = fs::weakly_canonical(fs::path(rootDir), ec);
  if (ec) {
    *error = "cannot resolve the repository root";
    return false;
  }
  const fs::path joined = fs::weakly_canonical(root / candidate, ec);
  if (ec) {
    *error = "cannot resolve " + relative;
    return false;
  }
  const std::string rootText = root.string();
  const std::string joinedText = joined.string();
  if (joinedText != rootText && joinedText.rfind(rootText + "/", 0) != 0) {
    *error = "paths stay inside the repository root";
    return false;
  }
  *out = joined;
  return true;
}

bool loadSheetModel(const std::string& rootDir, const std::string& relative,
                    spec::SpecParseResult* parsed, std::string* error, int* status) {
  fs::path path;
  if (!resolveInsideRoot(rootDir, relative, &path, error)) {
    *status = 400;
    return false;
  }
  std::error_code ec;
  if (!fs::is_regular_file(path, ec)) {
    *error = "no sheet at " + relative;
    *status = 404;
    return false;
  }
  spec::SpecParseOptions options;
  options.requireSchema = true;
  *parsed = spec::loadSpecFile(path.string(), options);
  if (!parsed->ok) {
    *error = "the sheet did not parse: " + parsed->renderIssues();
    *status = 422;
    return false;
  }
  return true;
}

// Every sheet the dashboard can offer: the application sheets, the requirement sheets and the
// workflow definitions, with just enough metadata to list them.
json sheetRows(const std::string& rootDir) {
  const fs::path root(rootDir);
  std::vector<fs::path> files;
  for (const char* relative : {"specs/app", "specs/workflows"}) {
    const fs::path dir = root / relative;
    std::error_code ec;
    if (!fs::is_directory(dir, ec)) continue;
    for (const fs::directory_entry& entry : fs::recursive_directory_iterator(dir, ec)) {
      if (ec) break;
      const fs::path& path = entry.path();
      const std::string extension = path.extension().string();
      if (extension != ".yaml" && extension != ".yml" && extension != ".json") continue;
      files.push_back(path);
    }
  }
  std::sort(files.begin(), files.end());

  json rows = json::array();
  for (const fs::path& path : files) {
    const std::string relative = fs::relative(path, root).generic_string();
    json row = {{"path", relative}};
    if (path.extension() == ".json") {
      std::ifstream file(path);
      std::stringstream buffer;
      buffer << file.rdbuf();
      const json document = json::parse(buffer.str(), nullptr, false);
      if (document.is_discarded()) continue;
      row["kind"] = "workflow";
      // Workflow sheets name their id "workflow_id"; older drafts used "id".
      row["id"] = document.contains("workflow_id") ? document.value("workflow_id", std::string())
                                                   : document.value("id", std::string());
      row["capabilities"] = 0;
      row["steps"] = document.contains("steps") && document["steps"].is_array()
                         ? document["steps"].size()
                         : 0;
      row["capability_id"] = "";
      row["capability_name"] = "";
    } else {
      spec::SpecParseOptions options;
      options.requireSchema = true;
      const spec::SpecParseResult parsed = spec::loadSpecFile(path.string(), options);
      if (!parsed.ok) continue;
      row["kind"] = relative.find("/requirements/") != std::string::npos ? "requirement"
                                                                         : "application";
      row["id"] = parsed.model.moduleId;
      row["capabilities"] = parsed.model.capabilities.size();
      row["steps"] = 0;
      row["capability_id"] =
          parsed.model.capabilities.empty() ? "" : parsed.model.capabilities.front().id;
      row["capability_name"] =
          parsed.model.capabilities.empty() ? "" : parsed.model.capabilities.front().name;
    }
    rows.push_back(row);
  }
  return rows;
}

bool readJsonFile(const fs::path& path, json* out) {
  std::ifstream file(path);
  if (!file) return false;
  std::stringstream buffer;
  buffer << file.rdbuf();
  *out = json::parse(buffer.str(), nullptr, false);
  return !out->is_discarded();
}

}  // namespace

void Gateway::listen() {
  httplib::Server server;
  server.new_task_queue = [] { return new httplib::ThreadPool(1); };

  const fs::path dashboardPath(config_.dashboardDir);
  const bool dashboardReady =
      !config_.dashboardDir.empty() && fs::is_directory(dashboardPath) &&
      fs::exists(dashboardPath / "index.html");
  if (dashboardReady) {
    server.set_mount_point("/", dashboardPath.string());
  } else {
    server.Get("/", [dashboardPath](const httplib::Request&, httplib::Response& response) {
      sendJson(response,
               errorBody("the dashboard has not been built; expected " +
                         (dashboardPath / "index.html").string()),
               503);
    });
  }

  server.Get("/health", [this](const httplib::Request&, httplib::Response& response) {
    sendJson(response, healthJson());
  });

  server.Get("/api/modules", [this](const httplib::Request&, httplib::Response& response) {
    sendJson(response, modulesJson());
  });

  server.Post("/api/discover", [this](const httplib::Request&, httplib::Response& response) {
    discover();
    sendJson(response, modulesJson());
  });

  server.Get("/api/registry", [this](const httplib::Request&, httplib::Response& response) {
    sendJson(response, registryJson());
  });

  server.Get("/api/audit", [this](const httplib::Request& request, httplib::Response& response) {
    size_t limit = 50;
    if (request.has_param("limit")) {
      try {
        limit = static_cast<size_t>(std::stoul(request.get_param_value("limit")));
      } catch (const std::exception&) {
        limit = 50;
      }
    }
    sendJson(response, auditJson(limit));
  });

  server.Get("/api/hospital/operations",
             [this](const httplib::Request&, httplib::Response& response) {
               sendJson(response, operationsJson());
             });

  // Canonical hospital API: one endpoint per registry capability name (patients, queue,
  // consultations, dispense, billing, labs), executed through the same machinery as everything
  // else. `?module=<id>` disambiguates when several modules declare the same name.
  server.Post(R"(/api/hospital/([A-Za-z0-9_]+))",
              [this](const httplib::Request& request, httplib::Response& response) {
                const std::string operation = request.matches[1].str();
                const std::string moduleFilter =
                    request.has_param("module") ? request.get_param_value("module") : "";
                const std::vector<Candidate> registry = candidates();
                const Candidate* selected = nullptr;
                for (const Candidate& candidate : registry) {
                  if (!moduleFilter.empty() && candidate.moduleId != moduleFilter) continue;
                  if (candidate.capabilityName == operation ||
                      candidate.capabilityId == operation) {
                    selected = &candidate;
                    break;
                  }
                }
                if (selected == nullptr) {
                  sendJson(response,
                           errorBody("no registry capability is named " + operation), 404);
                  return;
                }
                std::map<std::string, core::Value> inputs;
                if (!request.body.empty()) {
                  json document;
                  std::string bodyError;
                  if (!parseBody(request, &document, &bodyError)) {
                    sendJson(response, errorBody(bodyError), 400);
                    return;
                  }
                  if (!parseInputs(document, &inputs, &bodyError)) {
                    sendJson(response, errorBody(bodyError), 400);
                    return;
                  }
                }
                const CallOutcome outcome =
                    callDirect(selected->moduleId, selected->capabilityId, inputs);
                sendJson(response, outcome.render(),
                         outcome.ok ? 200 : (outcome.moduleCalled ? 502 : 422));
              });

  server.Post("/api/resolve", [this](const httplib::Request& request,
                                     httplib::Response& response) {
    json document;
    std::string bodyError;
    if (!parseBody(request, &document, &bodyError)) {
      sendJson(response, errorBody(bodyError), 400);
      return;
    }
    const std::string requirementPath = document.value("requirement", std::string());
    if (requirementPath.empty()) {
      sendJson(response, errorBody("the resolve call needs a requirement sheet path"), 400);
      return;
    }
    std::vector<std::string> allowModules;
    if (!parseStringList(document, "allow_modules", "module ids", &allowModules, &bodyError)) {
      sendJson(response, errorBody(bodyError), 400);
      return;
    }
    const spec::SpecParseResult parsed =
        spec::loadSpecFile((fs::path(config_.rootDir) / requirementPath).string());
    if (!parsed.ok || parsed.model.capabilities.empty()) {
      sendJson(response,
               errorBody("the requirement did not parse: " + parsed.renderIssues()), 422);
      return;
    }
    sendJson(response, candidatesJson(resolve(parsed.model.capabilities.front(),
                                              parsePreferred(document), allowModules)));
  });

  server.Post("/api/call", [this](const httplib::Request& request, httplib::Response& response) {
    json document;
    std::string bodyError;
    if (!parseBody(request, &document, &bodyError)) {
      sendJson(response, errorBody(bodyError), 400);
      return;
    }
    const std::string requirementPath = document.value("requirement", std::string());
    if (requirementPath.empty()) {
      sendJson(response, errorBody("the call needs a requirement sheet path"), 400);
      return;
    }
    std::vector<std::string> allowModules;
    if (!parseStringList(document, "allow_modules", "module ids", &allowModules, &bodyError)) {
      sendJson(response, errorBody(bodyError), 400);
      return;
    }
    const spec::SpecParseResult parsed =
        spec::loadSpecFile((fs::path(config_.rootDir) / requirementPath).string());
    if (!parsed.ok || parsed.model.capabilities.empty()) {
      sendJson(response,
               errorBody("the requirement did not parse: " + parsed.renderIssues()), 422);
      return;
    }
    std::map<std::string, core::Value> inputs;
    if (document.contains("inputs") && !parseInputs(document["inputs"], &inputs, &bodyError)) {
      sendJson(response, errorBody(bodyError), 400);
      return;
    }
    const CallOutcome outcome = callRequirement(parsed.model.capabilities.front(), inputs,
                                                parsePreferred(document), allowModules);
    sendJson(response, outcome.render(), outcome.ok ? 200 : (outcome.moduleCalled ? 502 : 422));
  });

  server.Post("/api/workflow", [this](const httplib::Request& request,
                                      httplib::Response& response) {
    json document;
    std::string bodyError;
    if (!parseBody(request, &document, &bodyError)) {
      sendJson(response, errorBody(bodyError), 400);
      return;
    }
    WorkflowDefinition definition;
    std::string definitionError;
    const std::string workflowPath = document.value("workflow", std::string());
    if (!workflowPath.empty()) {
      const fs::path path = fs::path(config_.rootDir) / workflowPath;
      std::ifstream file(path);
      if (!file) {
        sendJson(response, errorBody("workflow file not found: " + path.string()), 404);
        return;
      }
      std::stringstream buffer;
      buffer << file.rdbuf();
      json workflowDocument = json::parse(buffer.str(), nullptr, false);
      if (workflowDocument.is_discarded()) {
        sendJson(response, errorBody("workflow file is not JSON: " + path.string()), 422);
        return;
      }
      if (!parseWorkflowDefinition(workflowDocument, &definition, &definitionError)) {
        sendJson(response, errorBody(definitionError), 422);
        return;
      }
    } else if (document.contains("definition")) {
      if (!parseWorkflowDefinition(document["definition"], &definition, &definitionError)) {
        sendJson(response, errorBody(definitionError), 422);
        return;
      }
    } else {
      sendJson(response,
               errorBody("provide a workflow file path or an inline definition"), 400);
      return;
    }
    const WorkflowResult result = runWorkflow(definition);
    sendJson(response, result.render(), result.ok ? 200 : 422);
  });

  // ---- dashboard support: sheets, embeddings, adapters, plans, bundles, experiment results ----
  // These endpoints exist for the dashboard panels; each one is a thin shell over the same
  // library methods the CLI and the tests use, so the two front ends cannot drift apart.

  server.Get("/api/sheets", [this](const httplib::Request&, httplib::Response& response) {
    sendJson(response, sheetRows(config_.rootDir).dump(2) + "\n");
  });

  server.Get("/api/sheet", [this](const httplib::Request& request, httplib::Response& response) {
    const std::string relative = request.get_param_value("path");
    fs::path path;
    std::string pathError;
    if (!resolveInsideRoot(config_.rootDir, relative, &path, &pathError)) {
      sendJson(response, errorBody(pathError), 400);
      return;
    }
    std::error_code ec;
    if (!fs::is_regular_file(path, ec)) {
      sendJson(response, errorBody("no sheet at " + relative), 404);
      return;
    }
    if (path.extension() == ".json") {
      json document;
      if (!readJsonFile(path, &document)) {
        sendJson(response, errorBody("the document is not JSON: " + relative), 422);
        return;
      }
      sendJson(response, json{{"path", relative}, {"kind", "workflow"}, {"definition", document}}
                                .dump(2) + "\n");
      return;
    }
    spec::SpecParseOptions options;
    options.requireSchema = true;
    const spec::SpecParseResult parsed = spec::loadSpecFile(path.string(), options);
    if (!parsed.ok) {
      sendJson(response, errorBody("the sheet did not parse: " + parsed.renderIssues()), 422);
      return;
    }
    const std::string kind =
        relative.find("/requirements/") != std::string::npos ? "requirement" : "application";
    sendJson(response, json{{"path", relative},
                            {"kind", kind},
                            {"model", spec::specToJson(parsed.model)}}
                              .dump(2) + "\n");
  });

  server.Post("/api/embed", [this](const httplib::Request& request, httplib::Response& response) {
    json document;
    std::string bodyError;
    if (!parseBody(request, &document, &bodyError)) {
      sendJson(response, errorBody(bodyError), 400);
      return;
    }
    spec::SpecParseResult parsed;
    std::string loadError;
    int loadStatus = 422;
    if (!loadSheetModel(config_.rootDir, document.value("sheet", std::string()), &parsed,
                        &loadError, &loadStatus)) {
      sendJson(response, errorBody(loadError), loadStatus);
      return;
    }
    const std::string onlyId = document.value("capability", std::string());
    const embedding::Encoder encoder;
    json rows = json::array();
    for (const core::CapabilitySpec& capability : parsed.model.capabilities) {
      if (!onlyId.empty() && capability.id != onlyId) continue;
      const embedding::EncodedCapability encoded = encoder.encodeCapabilityDetailed(capability);
      json blocks = json::object();
      for (const auto& block : encoded.blocks) {
        blocks[block.first] = {{"size", block.second.size()},
                               {"norm", embedding::VectorMath::norm(block.second)}};
      }
      rows.push_back({{"id", encoded.id},
                      {"name", encoded.name},
                      {"dimensions", encoded.vector.size()},
                      {"blocks", blocks}});
    }
    if (rows.empty()) {
      sendJson(response, errorBody("no capability matches \"" + onlyId + "\""), 404);
      return;
    }
    sendJson(response,
             json{{"sheet", document.value("sheet", std::string())}, {"capabilities", rows}}
                     .dump(2) + "\n");
  });

  server.Post("/api/embed/compare", [this](const httplib::Request& request,
                                           httplib::Response& response) {
    json document;
    std::string bodyError;
    if (!parseBody(request, &document, &bodyError)) {
      sendJson(response, errorBody(bodyError), 400);
      return;
    }
    spec::SpecParseResult parsed;
    std::string loadError;
    int loadStatus = 422;
    if (!loadSheetModel(config_.rootDir, document.value("sheet", std::string()), &parsed,
                        &loadError, &loadStatus)) {
      sendJson(response, errorBody(loadError), loadStatus);
      return;
    }
    const std::string leftId = document.value("left", std::string());
    const std::string rightId = document.value("right", std::string());
    const embedding::Encoder encoder;
    std::map<std::string, embedding::EncodedCapability> encoded;
    for (const core::CapabilitySpec& capability : parsed.model.capabilities) {
      encoded.emplace(capability.id, encoder.encodeCapabilityDetailed(capability));
    }
    const auto left = encoded.find(leftId);
    const auto right = encoded.find(rightId);
    if (left == encoded.end() || right == encoded.end()) {
      sendJson(response, errorBody("both capabilities must exist in the sheet"), 404);
      return;
    }
    json blocks = json::object();
    for (const auto& block : left->second.blocks) {
      const auto other = right->second.blocks.find(block.first);
      if (other == right->second.blocks.end()) continue;
      blocks[block.first] = embedding::VectorMath::cosine(block.second, other->second);
    }
    const json result = {
        {"sheet", document.value("sheet", std::string())},
        {"left", leftId},
        {"right", rightId},
        {"total", embedding::VectorMath::cosine(left->second.vector, right->second.vector)},
        {"functional",
         embedding::VectorMath::cosine(left->second.functionalView(), right->second.functionalView())},
        {"implementation", embedding::VectorMath::cosine(left->second.implementationView(),
                                                          right->second.implementationView())},
        {"blocks", blocks}};
    sendJson(response, result.dump(2) + "\n");
  });

  server.Post("/api/adapter", [this](const httplib::Request& request,
                                     httplib::Response& response) {
    json document;
    std::string bodyError;
    if (!parseBody(request, &document, &bodyError)) {
      sendJson(response, errorBody(bodyError), 400);
      return;
    }
    const std::string requirementPath = document.value("requirement", std::string());
    const std::string moduleId = document.value("module", std::string());
    const std::string capabilityId = document.value("capability", std::string());
    if (requirementPath.empty() || moduleId.empty() || capabilityId.empty()) {
      sendJson(response,
               errorBody("the adapter call needs requirement, module and capability"), 400);
      return;
    }
    spec::SpecParseResult parsed;
    std::string loadError;
    int loadStatus = 422;
    if (!loadSheetModel(config_.rootDir, requirementPath, &parsed, &loadError, &loadStatus)) {
      sendJson(response, errorBody(loadError), loadStatus);
      return;
    }
    if (parsed.model.capabilities.empty()) {
      sendJson(response, errorBody("the requirement sheet declares no capability"), 422);
      return;
    }
    std::string synthesisError;
    const std::string body = adapterJson(moduleId, capabilityId,
                                         parsed.model.capabilities.front(), &synthesisError);
    const json result = json::parse(body, nullptr, false);
    const bool ok = !result.is_discarded() && result.value("ok", false);
    sendJson(response, body, ok ? 200 : 422);
  });

  server.Post("/api/plan", [this](const httplib::Request& request, httplib::Response& response) {
    json document;
    std::string bodyError;
    if (!parseBody(request, &document, &bodyError)) {
      sendJson(response, errorBody(bodyError), 400);
      return;
    }
    spec::SpecParseResult parsed;
    std::string loadError;
    int loadStatus = 422;
    if (!loadSheetModel(config_.rootDir, document.value("sheet", std::string()), &parsed,
                        &loadError, &loadStatus)) {
      sendJson(response, errorBody(loadError), loadStatus);
      return;
    }
    std::vector<core::Condition> goal;
    if (document.contains("goals") && document["goals"].is_object() &&
        !document["goals"].empty()) {
      for (auto it = document["goals"].begin(); it != document["goals"].end(); ++it) {
        core::Condition condition;
        condition.variable = it.key();
        condition.op = core::ConditionOp::EQ;
        std::string valueError;
        if (!core::jsonToValue(it.value(), &condition.value, &valueError)) {
          sendJson(response, errorBody("goal " + it.key() + ": " + valueError), 400);
          return;
        }
        goal.push_back(std::move(condition));
      }
    } else {
      goal = parsed.model.goal;
    }
    if (goal.empty()) {
      sendJson(response,
               errorBody("no goal was given and the sheet declares none; pass a goals object"),
               422);
      return;
    }
    planner::PlanOptions options;
    const std::string strategy = document.value("strategy", "fewest-steps");
    if (strategy == "fewest-steps") {
      options.strategy = planner::PlanStrategy::FewestSteps;
    } else if (strategy == "least-time") {
      options.strategy = planner::PlanStrategy::LeastTime;
    } else if (strategy == "least-money") {
      options.strategy = planner::PlanStrategy::LeastMoney;
    } else if (strategy == "most-reliable") {
      options.strategy = planner::PlanStrategy::MostReliable;
    } else {
      sendJson(response, errorBody("unknown plan strategy \"" + strategy + "\""), 400);
      return;
    }
    if (document.contains("max_depth") && document["max_depth"].is_number_integer()) {
      const long long depth = document["max_depth"].get<long long>();
      if (depth < 1 || depth > 20) {
        sendJson(response, errorBody("max_depth must be between 1 and 20"), 400);
        return;
      }
      options.maxDepth = static_cast<size_t>(depth);
    }
    const bool backward = document.value("backward", false);
    const planner::Planner plannerTool(parsed.model);
    const planner::PlanResult result =
        backward ? plannerTool.planBackward(goal, options) : plannerTool.planForward(goal, options);

    json output;
    output["found"] = result.found;
    output["validated"] = result.validated;
    if (!result.reason.empty()) output["reason"] = result.reason;
    output["steps"] = json::array();
    for (const planner::PlanStep& step : result.steps) {
      output["steps"].push_back({{"capability_id", step.capabilityId},
                                 {"capability_name", step.capabilityName},
                                 {"consumed_preconditions", step.consumedPreconditions},
                                 {"established", step.established}});
    }
    output["total_time_ms"] = result.totalTimeMs;
    output["total_money"] = result.totalMoney;
    output["total_risk"] = result.totalRisk;
    output["total_reliability"] = result.totalReliability;
    output["expanded_states"] = result.expandedStates;
    output["explored_states"] = result.exploredStates;
    output["depth"] = result.depth;
    output["explanation"] = result.explanation;
    output["note"] =
        "the planner is background machinery, outside the Assignment 2 evaluation scope";
    sendJson(response, output.dump(2) + "\n", result.found && result.validated ? 200 : 422);
  });

  server.Post("/api/bundle", [this](const httplib::Request& request, httplib::Response& response) {
    json document = json::object();
    std::string bodyError;
    if (!request.body.empty()) {
      if (!parseBody(request, &document, &bodyError)) {
        sendJson(response, errorBody(bodyError), 400);
        return;
      }
    }
    bundle::BundleOptions options;
    options.rootDir = config_.rootDir;
    if (!parseStringList(document, "modules", "module ids", &options.selectedModules,
                         &bodyError) ||
        !parseStringList(document, "workflows", "workflow names", &options.selectedWorkflows,
                         &bodyError)) {
      sendJson(response, errorBody(bodyError), 400);
      return;
    }
    if (document.contains("no_workflows")) {
      if (!document["no_workflows"].is_boolean()) {
        sendJson(response, errorBody("no_workflows must be a boolean"), 400);
        return;
      }
      if (document["no_workflows"].get<bool>() && !options.selectedWorkflows.empty()) {
        sendJson(response, errorBody("give either workflows or no_workflows, not both"), 400);
        return;
      }
      options.includeWorkflows = !document["no_workflows"].get<bool>();
    }
    std::string displayPath = "dist/careweave-mini";
    fs::path outDir = fs::path(config_.rootDir) / displayPath;
    if (document.contains("out")) {
      const std::string relative = document.value("out", std::string());
      std::string pathError;
      if (!resolveInsideRoot(config_.rootDir, relative, &outDir, &pathError)) {
        sendJson(response, errorBody(pathError), 400);
        return;
      }
      displayPath = relative;
    }
    options.outDir = outDir.string();
    options.displayPath = displayPath;
    options.includeDashboard = !document.value("no_dashboard", false);
    const bundle::BundleResult result = bundle::createBundle(options);
    sendJson(response, result.render(), result.ok ? 200 : 500);
  });

  server.Get("/api/experiments", [this](const httplib::Request&, httplib::Response& response) {
    const fs::path outDir = fs::path(config_.rootDir) / "experiments" / "out";
    json result = json::object();
    json evaluation;
    if (readJsonFile(outDir / "evaluation.json", &evaluation)) result["evaluation"] = evaluation;
    json experiments = json::object();
    for (const char* name :
         {"exp1_compatibility", "exp2_composition", "exp3_alternative_implementations",
          "exp4_irrelevant_capabilities", "exp5_operational_attributes"}) {
      json document;
      if (readJsonFile(outDir / (std::string(name) + ".json"), &document)) {
        experiments[name] = document;
      }
    }
    result["experiments"] = experiments;
    if (!result.contains("evaluation") && experiments.empty()) {
      sendJson(response, errorBody("no experiment results are in experiments/out yet"), 404);
      return;
    }
    sendJson(response, result.dump(2) + "\n");
  });

  server.set_error_handler([](const httplib::Request& request, httplib::Response& response) {
    if (response.body.empty()) {
      response.set_content(
          errorBody("no route for " + request.method + " " + request.path), "application/json");
    }
  });

  std::cout << "careweave gateway on http://" << config_.host << ":" << config_.port
            << " (dashboard " << (dashboardReady ? "ready" : "not built yet") << ")\n";
  std::cout.flush();
  server.listen(config_.host.c_str(), config_.port);
}

}  // namespace gateway
}  // namespace careweave
