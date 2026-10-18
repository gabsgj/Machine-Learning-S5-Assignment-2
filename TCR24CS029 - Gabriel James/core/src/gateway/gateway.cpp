// Gateway core: discovery, registry, resolution, execution, workflows and the audit trail.
// The HTTP server lives in server.cpp and only routes requests into these methods.
#include "careweave/gateway/gateway.hpp"

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <thread>

#include <sqlite3.h>

#include "careweave/adapter/adapter.hpp"
#include "careweave/adapter/runner.hpp"
#include "careweave/adapter/synthesizer.hpp"
#include "careweave/adapter/transport.hpp"
#include "careweave/compat/compat_engine.hpp"
#include "careweave/core/value_json.hpp"
#include "careweave/spec/spec_parser.hpp"
#include "httplib.h"

namespace careweave {
namespace gateway {

namespace fs = std::filesystem;
using nlohmann::json;

namespace {

constexpr double kAmbiguityMargin = 0.05;  // the mapper default, reported in resolutions

long long nowMillis() {
  return std::chrono::duration_cast<std::chrono::milliseconds>(
             std::chrono::system_clock::now().time_since_epoch())
      .count();
}

std::string jsonDump(const json& document) { return document.dump(2) + "\n"; }

}  // namespace

// ---- renders ----

std::string CallOutcome::render() const {
  json document;
  document["ok"] = ok;
  document["module_id"] = moduleId;
  document["capability_id"] = capabilityId;
  document["adapter_id"] = adapterId;
  document["attempts"] = attempts;
  document["status"] = status;
  document["fallback_used"] = fallbackUsed;
  document["module_called"] = moduleCalled;
  if (!error.empty()) document["error"] = error;
  json outputsJson = json::object();
  for (const auto& entry : outputs) outputsJson[entry.first] = core::valueToJson(entry.second);
  document["outputs"] = outputsJson;
  json stateJson = json::object();
  for (const auto& entry : state.all()) stateJson[entry.first] = core::valueToJson(entry.second);
  document["state"] = stateJson;
  document["trace"] = trace;
  return jsonDump(document);
}

std::string WorkflowResult::render() const {
  json document;
  document["ok"] = ok;
  document["workflow_id"] = workflowId;
  if (!error.empty()) document["error"] = error;
  json stepsJson = json::array();
  for (const WorkflowStepResult& step : steps) {
    json entry;
    entry["name"] = step.name;
    entry["module_id"] = step.moduleId;
    entry["capability_id"] = step.capabilityId;
    entry["verdict"] = step.verdict;
    if (!step.verdictDetail.empty()) entry["verdict_detail"] = step.verdictDetail;
    entry["fallback_used"] = step.fallbackUsed;
    entry["attempts"] = step.attempts;
    entry["call"] = json::parse(step.call.render());
    stepsJson.push_back(std::move(entry));
  }
  document["steps"] = stepsJson;
  return jsonDump(document);
}

// ---- workflow definition parsing ----

bool parseWorkflowDefinition(const json& document, WorkflowDefinition* out, std::string* error) {
  if (!document.is_object()) {
    *error = "the workflow definition must be a JSON object";
    return false;
  }
  out->id = document.value("workflow_id", std::string());
  if (out->id.empty()) {
    *error = "the workflow definition needs a workflow_id";
    return false;
  }
  if (!document.contains("steps") || !document["steps"].is_array() ||
      document["steps"].empty()) {
    *error = "the workflow " + out->id + " needs a non empty steps array";
    return false;
  }
  std::set<std::string> names;
  for (const json& stepDocument : document["steps"]) {
    WorkflowStepSpec step;
    step.name = stepDocument.value("name", std::string());
    if (step.name.empty()) {
      *error = "every workflow step needs a name";
      return false;
    }
    if (!names.insert(step.name).second) {
      *error = "the workflow step name " + step.name + " is used twice";
      return false;
    }
    step.requirementPath = stepDocument.value("requirement", std::string());
    step.moduleId = stepDocument.value("module", std::string());
    step.capabilityId = stepDocument.value("capability", std::string());
    if (step.requirementPath.empty() &&
        (step.moduleId.empty() || step.capabilityId.empty())) {
      *error = "step " + step.name +
               " needs either a requirement sheet or a module and capability binding";
      return false;
    }
    if (stepDocument.contains("inputs")) {
      for (auto it = stepDocument["inputs"].begin(); it != stepDocument["inputs"].end(); ++it) {
        core::Value value;
        std::string inputError;
        if (!core::jsonToValue(it.value(), &value, &inputError)) {
          *error = "step " + step.name + " input " + it.key() + ": " + inputError;
          return false;
        }
        step.inputs[it.key()] = value;
      }
    }
    if (stepDocument.contains("bind")) {
      for (auto it = stepDocument["bind"].begin(); it != stepDocument["bind"].end(); ++it) {
        step.bind[it.key()] = it.value().get<std::string>();
      }
    }
    if (stepDocument.contains("preferred_modules")) {
      if (!stepDocument["preferred_modules"].is_array()) {
        *error = "step " + step.name + " preferred_modules must be an array of module ids";
        return false;
      }
      for (const json& entry : stepDocument["preferred_modules"]) {
        if (!entry.is_string() || entry.get<std::string>().empty()) {
          *error = "step " + step.name + " preferred_modules must be an array of module ids";
          return false;
        }
        step.preferredModules.push_back(entry.get<std::string>());
      }
    }
    if (stepDocument.contains("allow_modules")) {
      if (!stepDocument["allow_modules"].is_array() || stepDocument["allow_modules"].empty()) {
        *error = "step " + step.name + " allow_modules must be a non empty array of module ids";
        return false;
      }
      for (const json& entry : stepDocument["allow_modules"]) {
        if (!entry.is_string() || entry.get<std::string>().empty()) {
          *error = "step " + step.name + " allow_modules must be a non empty array of module ids";
          return false;
        }
        step.allowModules.push_back(entry.get<std::string>());
      }
    }
    out->steps.push_back(std::move(step));
  }
  return true;
}

json workflowDefinitionToJson(const WorkflowDefinition& definition) {
  json document;
  document["workflow_id"] = definition.id;
  json steps = json::array();
  for (const WorkflowStepSpec& step : definition.steps) {
    json entry;
    entry["name"] = step.name;
    if (!step.requirementPath.empty()) entry["requirement"] = step.requirementPath;
    if (!step.moduleId.empty()) entry["module"] = step.moduleId;
    if (!step.capabilityId.empty()) entry["capability"] = step.capabilityId;
    json inputs = json::object();
    for (const auto& binding : step.inputs)
      inputs[binding.first] = core::valueToJson(binding.second);
    entry["inputs"] = inputs;
    if (!step.bind.empty()) {
      json bind = json::object();
      for (const auto& binding : step.bind) bind[binding.first] = binding.second;
      entry["bind"] = bind;
    }
    if (!step.preferredModules.empty()) entry["preferred_modules"] = step.preferredModules;
    if (!step.allowModules.empty()) entry["allow_modules"] = step.allowModules;
    steps.push_back(std::move(entry));
  }
  document["steps"] = steps;
  return document;
}

// ---- default targets ----

std::vector<DiscoveryTarget> defaultTargets(const std::string& rootDir,
                                            const std::string& modulesDir) {
  const std::string modules[7] = {
      "patient-registry",  "appointment-queue",  "opd-ehr",           "pharmacy-inventory",
      "pos-billing",       "legacy-lab-service", "patient-registry-alt"};
  std::vector<DiscoveryTarget> targets;
  int port = 5001;
  for (const std::string& moduleId : modules) {
    DiscoveryTarget target;
    target.moduleId = moduleId;
    target.port = port++;
    target.fallbackSpecPath = (fs::path(modulesDir) / moduleId / "spec.json").string();
    targets.push_back(std::move(target));
  }
  (void)rootDir;
  return targets;
}

// ---- audit store ----

struct Gateway::AuditStore {
  sqlite3* db = nullptr;
  ~AuditStore() {
    if (db != nullptr) sqlite3_close(db);
  }
};

// ---- gateway ----

Gateway::Gateway(GatewayConfig config) : config_(std::move(config)) {
  startedAt_ = std::chrono::steady_clock::now();
  if (config_.targets.empty()) {
    config_.targets = defaultTargets(config_.rootDir, config_.modulesDir);
  }
  openAudit();
}

Gateway::~Gateway() = default;

void Gateway::openAudit() {
  if (config_.auditDbPath.empty()) return;
  const fs::path path(config_.auditDbPath);
  if (path.has_parent_path()) {
    std::error_code error;
    fs::create_directories(path.parent_path(), error);
  }
  audit_ = std::make_unique<AuditStore>();
  if (sqlite3_open(config_.auditDbPath.c_str(), &audit_->db) != SQLITE_OK) {
    audit_.reset();
    return;
  }
  const char* schema =
      "CREATE TABLE IF NOT EXISTS gateway_events ("
      "seq INTEGER PRIMARY KEY AUTOINCREMENT, ts_ms INTEGER, kind TEXT, operation TEXT,"
      "module TEXT, capability TEXT, ok INTEGER, status INTEGER, attempts INTEGER,"
      "fallback INTEGER, latency_ms INTEGER, message TEXT);";
  char* error = nullptr;
  sqlite3_exec(audit_->db, schema, nullptr, nullptr, &error);
  if (error != nullptr) sqlite3_free(error);
}

ModuleRecord* Gateway::findModule(const std::string& moduleId) {
  for (ModuleRecord& record : modules_) {
    if (record.model.moduleId == moduleId) return &record;
  }
  return nullptr;
}

const ModuleRecord* Gateway::module(const std::string& moduleId) const {
  for (const ModuleRecord& record : modules_) {
    if (record.model.moduleId == moduleId) return &record;
  }
  return nullptr;
}

const core::CapabilitySpec* Gateway::capability(const std::string& moduleId,
                                                const std::string& capabilityId) const {
  const ModuleRecord* record = module(moduleId);
  if (record == nullptr) return nullptr;
  for (const core::CapabilitySpec& capability : record->model.capabilities) {
    if (capability.id == capabilityId) return &capability;
  }
  return nullptr;
}

std::string Gateway::moduleUrl(const ModuleRecord& record) const {
  if (!record.baseUrl.empty()) return record.baseUrl;
  return "http://127.0.0.1:" + std::to_string(record.model.port);
}

void Gateway::discover() {
  modules_.clear();
  for (const DiscoveryTarget& target : config_.targets) {
    ModuleRecord record;
    record.baseUrl = "http://127.0.0.1:" + std::to_string(target.port);

    // Live /spec first.
    httplib::Client client("127.0.0.1", target.port);
    client.set_connection_timeout(0, static_cast<int>(config_.requestTimeoutMs) * 1000);
    client.set_read_timeout(0, static_cast<int>(config_.requestTimeoutMs) * 1000);
    if (auto response = client.Get("/spec")) {
      if (response->status == 200) {
        try {
          const json document = json::parse(response->body);
          spec::SpecParseResult parsed =
              spec::parseSpecDocument(document, "live:" + target.moduleId);
          if (parsed.ok) {
            record.model = parsed.model;
            record.specSource = "live GET /spec";
            record.available = true;
          } else {
            record.healthMessage = "live /spec did not parse: " + parsed.renderIssues();
          }
        } catch (const std::exception& error) {
          record.healthMessage = "live /spec is not JSON: " + std::string(error.what());
        }
      } else {
        record.healthMessage = "live /spec answered HTTP " + std::to_string(response->status);
      }
    } else {
      record.healthMessage = "live /spec unreachable";
    }

    // Fallback file.
    if (!record.available && !target.fallbackSpecPath.empty() &&
        fs::exists(target.fallbackSpecPath)) {
      spec::SpecParseResult parsed = spec::loadSpecFile(target.fallbackSpecPath);
      if (parsed.ok) {
        record.model = parsed.model;
        record.specSource = "file " + target.fallbackSpecPath;
        record.available = true;
      } else {
        record.healthMessage += "; fallback " + target.fallbackSpecPath +
                                " did not parse: " + parsed.renderIssues();
      }
    }
    if (!record.available) {
      // Keep the expected id so the management API can show the missing module.
      record.model.moduleId = target.moduleId;
      record.model.port = target.port;
      modules_.push_back(std::move(record));
      continue;
    }

    // Health probe.
    if (auto health = client.Get("/health")) {
      record.healthy = health->status == 200;
      record.healthMessage = record.healthy ? "health ok"
                                            : "health HTTP " + std::to_string(health->status);
    } else if (record.specSource.rfind("file", 0) == 0) {
      record.healthy = false;
      record.healthMessage = "not running; specification loaded from " + record.specSource;
    }
    modules_.push_back(std::move(record));
  }
}

std::vector<Candidate> Gateway::candidates() const {
  std::vector<Candidate> result;
  for (const ModuleRecord& record : modules_) {
    if (!record.available) continue;
    for (const core::CapabilitySpec& capabilitySpec : record.model.capabilities) {
      Candidate candidate;
      candidate.moduleId = record.model.moduleId;
      candidate.capabilityId = capabilitySpec.id;
      candidate.capabilityName = capabilitySpec.name;
      candidate.capabilityType = core::capabilityTypeToString(capabilitySpec.type);
      candidate.endpoint = capabilitySpec.mechanism.endpoint;
      result.push_back(std::move(candidate));
    }
  }
  return result;
}

std::vector<Candidate> Gateway::resolve(const core::CapabilitySpec& requirement,
                                        const std::vector<std::string>& preferredModules,
                                        const std::vector<std::string>& allowModules) const {
  const mapper::Mapper mapperTool;
  std::vector<std::pair<Candidate, double>> scored;
  for (Candidate candidate : candidates()) {
    // The allow list is a hard filter applied before scoring, so a module outside it is never
    // ranked, never promoted and never called as a fallback.
    if (!allowModules.empty() &&
        std::find(allowModules.begin(), allowModules.end(), candidate.moduleId) ==
            allowModules.end()) {
      continue;
    }
    const core::CapabilitySpec* provider = capability(candidate.moduleId, candidate.capabilityId);
    if (provider == nullptr) continue;
    const mapper::MatchResult match = mapperTool.score(requirement, *provider);
    scored.emplace_back(std::move(candidate), match.total);
  }
  std::stable_sort(scored.begin(), scored.end(),
                   [](const std::pair<Candidate, double>& a,
                      const std::pair<Candidate, double>& b) { return a.second > b.second; });
  if (scored.empty()) return {};

  const double top = scored.front().second;
  const double runnerUp = scored.size() > 1 ? scored[1].second : 0.0;
  const double margin = top - runnerUp;
  const bool ambiguous = scored.size() > 1 && margin < kAmbiguityMargin;

  // A preferred module inside the ambiguity margin is promoted to the front, so the alias
  // module can be swapped in deterministically while the ambiguity stays reported. Only a
  // callable candidate is promoted: a form or database sheet that merely resembles the
  // requirement must not shadow the module's live API.
  if (ambiguous && !preferredModules.empty()) {
    for (size_t i = 1; i < scored.size(); ++i) {
      if (top - scored[i].second >= kAmbiguityMargin) break;
      const bool preferred =
          std::find(preferredModules.begin(), preferredModules.end(),
                    scored[i].first.moduleId) != preferredModules.end();
      const bool callable = !scored[i].first.endpoint.empty();
      if (preferred && callable) {
        std::rotate(scored.begin(), scored.begin() + static_cast<long>(i), scored.begin() + static_cast<long>(i) + 1);
        break;
      }
    }
  }

  std::vector<Candidate> ranked;
  ranked.reserve(scored.size());
  for (auto& entry : scored) {
    entry.first.total = entry.second;
    entry.first.margin = margin;
    // A candidate is ambiguous when the resolution is ambiguous and this candidate sits within
    // the ambiguity margin of the top: those are the rows that could plausibly be the answer.
    entry.first.ambiguous = ambiguous && (top - entry.second) < kAmbiguityMargin;
    ranked.push_back(std::move(entry.first));
  }
  return ranked;
}

bool Gateway::moduleAllows(const ModuleRecord& record, std::string* why) const {
  if (!record.circuitOpen) return true;
  const long long openFor = std::chrono::duration_cast<std::chrono::milliseconds>(
                                std::chrono::steady_clock::now() - record.circuitOpenedAt)
                                .count();
  if (openFor >= config_.circuitCooldownMs) {
    *why = "half open probe allowed";
    return true;
  }
  *why = "circuit open for " + record.model.moduleId + " (" +
         std::to_string(config_.circuitCooldownMs - openFor) + " ms of cooldown left)";
  return false;
}

void Gateway::recordModuleResult(const std::string& moduleId, bool ok) {
  ModuleRecord* record = findModule(moduleId);
  if (record == nullptr) return;
  if (ok) {
    record->consecutiveFailures = 0;
    record->circuitOpen = false;
    return;
  }
  record->consecutiveFailures += 1;
  if (record->circuitOpen) {
    record->circuitOpenedAt = std::chrono::steady_clock::now();
    return;
  }
  if (static_cast<size_t>(record->consecutiveFailures) >= config_.circuitThreshold) {
    record->circuitOpen = true;
    record->circuitOpenedAt = std::chrono::steady_clock::now();
  }
}

void Gateway::audit(const std::string& kind, const std::string& operation,
                    const std::string& moduleId, const std::string& capabilityId, bool ok,
                    int status, int attempts, bool fallback, long long latencyMs,
                    const std::string& message) {
  if (!audit_ || audit_->db == nullptr) return;
  sqlite3_stmt* statement = nullptr;
  const char* sql =
      "INSERT INTO gateway_events (ts_ms, kind, operation, module, capability, ok, status,"
      " attempts, fallback, latency_ms, message) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);";
  if (sqlite3_prepare_v2(audit_->db, sql, -1, &statement, nullptr) != SQLITE_OK) return;
  sqlite3_bind_int64(statement, 1, nowMillis());
  sqlite3_bind_text(statement, 2, kind.c_str(), -1, SQLITE_TRANSIENT);
  sqlite3_bind_text(statement, 3, operation.c_str(), -1, SQLITE_TRANSIENT);
  sqlite3_bind_text(statement, 4, moduleId.c_str(), -1, SQLITE_TRANSIENT);
  sqlite3_bind_text(statement, 5, capabilityId.c_str(), -1, SQLITE_TRANSIENT);
  sqlite3_bind_int(statement, 6, ok ? 1 : 0);
  sqlite3_bind_int(statement, 7, status);
  sqlite3_bind_int(statement, 8, attempts);
  sqlite3_bind_int(statement, 9, fallback ? 1 : 0);
  sqlite3_bind_int64(statement, 10, latencyMs);
  sqlite3_bind_text(statement, 11, message.c_str(), -1, SQLITE_TRANSIENT);
  sqlite3_step(statement);
  sqlite3_finalize(statement);
  ++auditSequence_;
}

size_t Gateway::auditCount() const {
  if (!audit_ || audit_->db == nullptr) return 0;
  sqlite3_stmt* statement = nullptr;
  if (sqlite3_prepare_v2(audit_->db, "SELECT COUNT(*) FROM gateway_events;", -1, &statement,
                         nullptr) != SQLITE_OK) {
    return 0;
  }
  size_t count = 0;
  if (sqlite3_step(statement) == SQLITE_ROW) {
    count = static_cast<size_t>(sqlite3_column_int64(statement, 0));
  }
  sqlite3_finalize(statement);
  return count;
}

std::string Gateway::auditJson(size_t limit) const {
  json rows = json::array();
  if (audit_ && audit_->db != nullptr) {
    sqlite3_stmt* statement = nullptr;
    const char* sql =
        "SELECT seq, ts_ms, kind, operation, module, capability, ok, status, attempts, fallback,"
        " latency_ms, message FROM gateway_events ORDER BY seq DESC LIMIT ?;";
    if (sqlite3_prepare_v2(audit_->db, sql, -1, &statement, nullptr) == SQLITE_OK) {
      sqlite3_bind_int64(statement, 1, static_cast<sqlite3_int64>(limit));
      while (sqlite3_step(statement) == SQLITE_ROW) {
        json row;
        row["seq"] = sqlite3_column_int64(statement, 0);
        row["ts_ms"] = sqlite3_column_int64(statement, 1);
        row["kind"] = reinterpret_cast<const char*>(sqlite3_column_text(statement, 2));
        row["operation"] = reinterpret_cast<const char*>(sqlite3_column_text(statement, 3));
        row["module"] = reinterpret_cast<const char*>(sqlite3_column_text(statement, 4));
        row["capability"] = reinterpret_cast<const char*>(sqlite3_column_text(statement, 5));
        row["ok"] = sqlite3_column_int(statement, 6) != 0;
        row["status"] = sqlite3_column_int(statement, 7);
        row["attempts"] = sqlite3_column_int(statement, 8);
        row["fallback"] = sqlite3_column_int(statement, 9) != 0;
        row["latency_ms"] = sqlite3_column_int64(statement, 10);
        row["message"] = reinterpret_cast<const char*>(sqlite3_column_text(statement, 11));
        rows.push_back(std::move(row));
      }
      sqlite3_finalize(statement);
    }
  }
  return jsonDump(rows);
}

CallOutcome Gateway::callCandidate(const Candidate& candidate,
                                   const core::CapabilitySpec& requirement,
                                   const std::map<std::string, core::Value>& inputs,
                                   bool fallback) {
  CallOutcome outcome;
  outcome.moduleId = candidate.moduleId;
  outcome.capabilityId = candidate.capabilityId;
  outcome.fallbackUsed = fallback;

  ModuleRecord* record = findModule(candidate.moduleId);
  const core::CapabilitySpec* provider = capability(candidate.moduleId, candidate.capabilityId);
  if (record == nullptr || provider == nullptr) {
    outcome.error = "unknown module or capability " + candidate.moduleId + "/" +
                    candidate.capabilityId;
    audit("call", candidate.capabilityId, candidate.moduleId, candidate.capabilityId, false, 0, 0,
          fallback, 0, outcome.error);
    return outcome;
  }
  if (provider->mechanism.endpoint.empty()) {
    outcome.error = "capability " + candidate.capabilityId +
                    " declares no HTTP endpoint and cannot be called live";
    audit("call", candidate.capabilityId, candidate.moduleId, candidate.capabilityId, false, 0, 0,
          fallback, 0, outcome.error);
    return outcome;
  }

  // Synthesize the adapter for the requirement against this provider, then force the live HTTP
  // coordinates of the running module (every module capability answers on its declared route).
  const mapper::Mapper mapperTool;
  const mapper::MatchResult match = mapperTool.score(requirement, *provider);
  adapter::AdapterSynthesizer synthesizer;
  adapter::SynthesisRequest synthesisRequest;
  synthesisRequest.requirement = requirement;
  synthesisRequest.match = match;
  synthesisRequest.candidate = *provider;
  synthesisRequest.targetModule = candidate.moduleId;
  synthesisRequest.baseUrl = moduleUrl(*record);
  adapter::SynthesisResult synthesis = synthesizer.synthesize(synthesisRequest);
  if (!synthesis.ok) {
    outcome.error = "adapter synthesis failed: " + synthesis.render();
    audit("call", candidate.capabilityId, candidate.moduleId, candidate.capabilityId, false, 0, 0,
          fallback, 0, outcome.error);
    return outcome;
  }
  adapter::AdapterDefinition definition = synthesis.adapter;
  definition.baseUrl = moduleUrl(*record);
  definition.endpoint = provider->mechanism.endpoint;
  if (!provider->mechanism.method.empty()) definition.method = provider->mechanism.method;
  definition.transportKind = "http";
  definition.id = "adapter-live-" + candidate.moduleId + "-" + candidate.capabilityId;
  outcome.adapterId = definition.id;

  const auto started = std::chrono::steady_clock::now();
  adapter::HttpTransport transport(static_cast<double>(config_.requestTimeoutMs) / 1000.0);
  adapter::AdapterRunner runner(transport);
  for (size_t attempt = 1; attempt <= config_.maxAttempts; ++attempt) {
    outcome.attempts = static_cast<int>(attempt);
    std::string why;
    if (!moduleAllows(*record, &why)) {
      outcome.trace.push_back("attempt " + std::to_string(attempt) + ": " + why);
      outcome.error = why;
      break;
    }
    adapter::AdapterResult result = runner.run(definition, inputs);
    outcome.status = result.status;
    if (result.transportAttempted) outcome.moduleCalled = true;
    for (const std::string& line : result.trace) {
      outcome.trace.push_back("attempt " + std::to_string(attempt) + ": " + line);
    }
    if (result.ok) {
      outcome.ok = true;
      outcome.outputs = result.outputs;
      recordModuleResult(candidate.moduleId, true);
      // Refresh the module state snapshot for the workflows and the dashboard.
      httplib::Client client("127.0.0.1", record->model.port);
      client.set_read_timeout(0, static_cast<int>(config_.requestTimeoutMs) * 1000);
      if (auto stateResponse = client.Get("/state")) {
        if (stateResponse->status == 200) {
          try {
            const json document = json::parse(stateResponse->body);
            if (document.contains("state") && document["state"].is_object()) {
              std::map<std::string, core::Value> values;
              for (auto it = document["state"].begin(); it != document["state"].end(); ++it) {
                core::Value value;
                std::string stateError;
                if (core::jsonToValue(it.value(), &value, &stateError)) {
                  values[it.key()] = value;
                }
              }
              outcome.state = core::AppState::fromMap(values);
            }
          } catch (const std::exception&) {
            // The state snapshot is best effort; the call itself already succeeded.
          }
        }
      }
      const long long latency = std::chrono::duration_cast<std::chrono::milliseconds>(
                                    std::chrono::steady_clock::now() - started)
                                    .count();
      audit("call", candidate.capabilityId, candidate.moduleId, candidate.capabilityId, true,
            result.status, outcome.attempts, outcome.fallbackUsed, latency, "ok");
      return outcome;
    }
    outcome.error = result.error.empty() ? "call failed" : result.error;
    if (!result.transportAttempted) {
      // A local adapter failure (an unbound or unmappable input): the module was never asked,
      // so it is not retried and does not count against the circuit breaker.
      outcome.trace.push_back("attempt " + std::to_string(attempt) +
                              ": local adapter failure, the module was not called");
      break;
    }
    recordModuleResult(candidate.moduleId, false);
    if (attempt < config_.maxAttempts && config_.retryDelayMs > 0) {
      std::this_thread::sleep_for(std::chrono::milliseconds(config_.retryDelayMs));
    }
  }

  const long long latency = std::chrono::duration_cast<std::chrono::milliseconds>(
                                std::chrono::steady_clock::now() - started)
                                .count();
  audit("call", candidate.capabilityId, candidate.moduleId, candidate.capabilityId, false,
        outcome.status, outcome.attempts, outcome.fallbackUsed, latency, outcome.error);
  return outcome;
}

CallOutcome Gateway::callDirect(const std::string& moduleId, const std::string& capabilityId,
                                const std::map<std::string, core::Value>& inputs) {
  const core::CapabilitySpec* provider = capability(moduleId, capabilityId);
  if (provider == nullptr) {
    CallOutcome outcome;
    outcome.moduleId = moduleId;
    outcome.capabilityId = capabilityId;
    outcome.error = "unknown capability " + moduleId + "/" + capabilityId;
    return outcome;
  }
  Candidate candidate;
  candidate.moduleId = moduleId;
  candidate.capabilityId = capabilityId;
  candidate.capabilityName = provider->name;
  candidate.capabilityType = core::capabilityTypeToString(provider->type);
  candidate.endpoint = provider->mechanism.endpoint;
  return callCandidate(candidate, *provider, inputs);
}

CallOutcome Gateway::callRequirement(const core::CapabilitySpec& requirement,
                                     const std::map<std::string, core::Value>& inputs,
                                     const std::vector<std::string>& preferredModules,
                                     const std::vector<std::string>& allowModules) {
  const std::vector<Candidate> ranked = resolve(requirement, preferredModules, allowModules);
  std::vector<std::string> attemptLog;
  std::set<std::string> triedModules;
  CallOutcome firstFailure;
  bool anyFailed = false;
  for (const Candidate& candidate : ranked) {
    if (triedModules.count(candidate.moduleId) != 0) continue;  // one try per module
    if (candidate.endpoint.empty()) {
      // A candidate without a declared HTTP endpoint (a form, a database sheet, a
      // computation) is reported but never consumes the module's single try: the module's
      // live API later in the ranking stays reachable.
      CallOutcome skipped;
      skipped.moduleId = candidate.moduleId;
      skipped.capabilityId = candidate.capabilityId;
      skipped.error = "capability " + candidate.capabilityId +
                      " declares no HTTP endpoint and cannot be called live";
      attemptLog.push_back("module " + candidate.moduleId + " (" + candidate.capabilityId +
                           "): skipped: " + skipped.error);
      anyFailed = true;
      if (firstFailure.moduleId.empty()) firstFailure = std::move(skipped);
      continue;
    }
    triedModules.insert(candidate.moduleId);
    CallOutcome outcome = callCandidate(candidate, requirement, inputs, anyFailed);
    if (outcome.ok) {
      // Prepend the failed attempts so the trace reads as the fallback story it was.
      std::vector<std::string> trace = attemptLog;
      trace.insert(trace.end(), outcome.trace.begin(), outcome.trace.end());
      outcome.trace = std::move(trace);
      return outcome;
    }
    anyFailed = true;
    if (firstFailure.moduleId.empty()) firstFailure = outcome;
    attemptLog.push_back("module " + candidate.moduleId + " (" + candidate.capabilityId +
                         "): failed: " + outcome.error);
  }
  if (firstFailure.moduleId.empty()) {
    CallOutcome outcome;
    outcome.error = ranked.empty() ? "no candidate matched the requirement"
                                   : "every candidate module was skipped or failed";
    return outcome;
  }
  // Everything failed: report the best ranked candidate's outcome, because its reason matters
  // most (a local failure there is the request's own problem, not a module's), and append the
  // remaining attempts to the trace so the whole fallback story stays visible.
  firstFailure.fallbackUsed = true;
  std::vector<std::string> trace = firstFailure.trace;
  trace.insert(trace.end(), attemptLog.begin(), attemptLog.end());
  firstFailure.trace = std::move(trace);
  return firstFailure;
}

std::string Gateway::adapterJson(const std::string& moduleId, const std::string& capabilityId,
                                 const core::CapabilitySpec& requirement,
                                 std::string* error) const {
  const ModuleRecord* record = nullptr;
  for (const ModuleRecord& entry : modules_) {
    if (entry.model.moduleId == moduleId) {
      record = &entry;
      break;
    }
  }
  const core::CapabilitySpec* provider = capability(moduleId, capabilityId);
  json document;
  document["module_id"] = moduleId;
  document["capability_id"] = capabilityId;
  if (record == nullptr || provider == nullptr) {
    document["ok"] = false;
    document["error"] = "unknown module or capability " + moduleId + "/" + capabilityId;
    if (error != nullptr) *error = document["error"].get<std::string>();
    return document.dump(2) + "\n";
  }

  const mapper::Mapper mapperTool;
  const mapper::MatchResult match = mapperTool.score(requirement, *provider);
  adapter::SynthesisRequest synthesisRequest;
  synthesisRequest.requirement = requirement;
  synthesisRequest.match = match;
  synthesisRequest.candidate = *provider;
  synthesisRequest.targetModule = moduleId;
  synthesisRequest.baseUrl = moduleUrl(*record);
  const adapter::AdapterSynthesizer synthesizer;
  const adapter::SynthesisResult synthesis = synthesizer.synthesize(synthesisRequest);

  document["ok"] = synthesis.ok;
  document["requirement_id"] = requirement.id;
  document["requirement_name"] = requirement.name;
  document["module_available"] = record->available;
  document["score"] = match.total;
  document["score_parts"] = {{"name", match.nameSimilarity},
                             {"fields", match.fieldSimilarity},
                             {"conditions", match.conditionSimilarity},
                             {"kind_matches", match.kindMatches}};
  if (synthesis.ok) {
    const json definition =
        json::parse(adapter::toJsonString(synthesis.adapter), nullptr, false);
    document["adapter"] = definition.is_discarded() ? json::object() : definition;
  } else {
    document["errors"] = synthesis.errors;
    document["message"] = synthesis.render();
    if (error != nullptr) *error = synthesis.render();
  }
  return document.dump(2) + "\n";
}

WorkflowResult Gateway::runWorkflow(const WorkflowDefinition& definition) {
  WorkflowResult result;
  result.workflowId = definition.id;

  // One compatibility model over the union of the participating modules' initial states; state
  // variable names are module namespaced, so cross module steps stay uncoupled while same module
  // steps are checked against their real state transitions.
  core::ApplicationModel workflowModel;
  workflowModel.moduleId = "workflow-" + definition.id;
  for (const ModuleRecord& record : modules_) {
    if (!record.available) continue;
    for (const auto& binding : record.model.initialState) {
      workflowModel.initialState.insert(binding);
    }
  }

  const core::CapabilitySpec* previousProvider = nullptr;
  std::map<std::string, std::map<std::string, core::Value>> outputsByStep;
  const auto workflowStarted = std::chrono::steady_clock::now();

  for (const WorkflowStepSpec& step : definition.steps) {
    WorkflowStepResult stepResult;
    stepResult.name = step.name;

    // Resolve inputs: literals plus bindings from earlier steps.
    std::map<std::string, core::Value> inputs = step.inputs;
    for (const auto& binding : step.bind) {
      const std::string& expression = binding.second;
      const size_t dot = expression.find('.');
      if (dot == std::string::npos) {
        result.error = "step " + step.name + ": binding " + binding.first + " = " + expression +
                       " is not of the form step.output";
        result.steps.push_back(std::move(stepResult));
        return result;
      }
      const std::string& sourceStep = expression.substr(0, dot);
      const std::string& sourceOutput = expression.substr(dot + 1);
      const auto stepIt = outputsByStep.find(sourceStep);
      if (stepIt == outputsByStep.end()) {
        result.error = "step " + step.name + ": binding references unknown step " + sourceStep;
        result.steps.push_back(std::move(stepResult));
        return result;
      }
      const auto outputIt = stepIt->second.find(sourceOutput);
      if (outputIt == stepIt->second.end()) {
        result.error = "step " + step.name + ": step " + sourceStep + " produced no output " +
                       sourceOutput;
        result.steps.push_back(std::move(stepResult));
        return result;
      }
      inputs[binding.first] = outputIt->second;
    }

    CallOutcome outcome;
    if (!step.requirementPath.empty()) {
      spec::SpecParseResult parsed =
          spec::loadSpecFile((fs::path(config_.rootDir) / step.requirementPath).string());
      if (!parsed.ok || parsed.model.capabilities.empty()) {
        result.error = "step " + step.name + ": requirement " + step.requirementPath +
                       " did not parse: " + parsed.renderIssues();
        result.steps.push_back(std::move(stepResult));
        return result;
      }
      outcome = callRequirement(parsed.model.capabilities.front(), inputs, step.preferredModules,
                                step.allowModules);
    } else if (!step.allowModules.empty() &&
               std::find(step.allowModules.begin(), step.allowModules.end(), step.moduleId) ==
                   step.allowModules.end()) {
      // A direct binding outside the step's own allow list is refused before any call.
      outcome.moduleId = step.moduleId;
      outcome.capabilityId = step.capabilityId;
      outcome.error =
          "the step binds module " + step.moduleId + " which is outside its allow list";
    } else {
      outcome = callDirect(step.moduleId, step.capabilityId, inputs);
    }
    stepResult.call = outcome;
    stepResult.moduleId = outcome.moduleId;
    stepResult.capabilityId = outcome.capabilityId;
    stepResult.fallbackUsed = outcome.fallbackUsed;
    stepResult.attempts = outcome.trace;

    const core::CapabilitySpec* provider = capability(outcome.moduleId, outcome.capabilityId);
    if (!outcome.ok) {
      stepResult.verdict = "call failed";
      result.steps.push_back(std::move(stepResult));
      result.error = "step " + step.name + " failed: " + outcome.error;
      audit("workflow", definition.id, outcome.moduleId, outcome.capabilityId, false, outcome.status,
            outcome.attempts, outcome.fallbackUsed,
            std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::steady_clock::now() - workflowStarted)
                .count(),
            "step " + step.name + " failed: " + outcome.error);
      return result;
    }
    if (previousProvider != nullptr && provider != nullptr) {
      compat::CompatEngine engine(workflowModel);
      const compat::CompatibilityReport report = engine.check(*previousProvider, *provider);
      stepResult.verdict = compat::verdictToString(report.verdict);
      stepResult.verdictDetail = report.render();
      if (report.verdict == compat::Verdict::INCOMPATIBLE) {
        result.steps.push_back(std::move(stepResult));
        result.error = "step " + step.name + " is incompatible with the previous step";
        audit("workflow", definition.id, outcome.moduleId, outcome.capabilityId, false, 0,
              outcome.attempts, outcome.fallbackUsed,
              std::chrono::duration_cast<std::chrono::milliseconds>(
                  std::chrono::steady_clock::now() - workflowStarted)
                  .count(),
              result.error);
        return result;
      }
    } else {
      stepResult.verdict = "first step";
    }
    previousProvider = provider;
    outputsByStep[step.name] = outcome.outputs;
    result.steps.push_back(std::move(stepResult));
  }

  result.ok = true;
  const bool anyFallback =
      std::any_of(result.steps.begin(), result.steps.end(),
                  [](const WorkflowStepResult& step) { return step.fallbackUsed; });
  audit("workflow", definition.id, "", "", true, 0, static_cast<int>(result.steps.size()),
        anyFallback,
        std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() -
                                                              workflowStarted)
            .count(),
        "workflow completed with " + std::to_string(result.steps.size()) + " steps");
  return result;
}

// ---- management JSON ----

std::string Gateway::healthJson() const {
  size_t healthy = 0;
  json modules = json::array();
  for (const ModuleRecord& record : modules_) {
    if (record.available && record.healthy) ++healthy;
    modules.push_back({{"module_id", record.model.moduleId},
                       {"available", record.available},
                       {"healthy", record.healthy},
                       {"circuit_open", record.circuitOpen},
                       {"message", record.healthMessage}});
  }
  json document;
  document["status"] = "ok";
  document["uptime_s"] = std::chrono::duration_cast<std::chrono::seconds>(
                             std::chrono::steady_clock::now() - startedAt_)
                             .count();
  document["modules_total"] = modules_.size();
  document["modules_healthy"] = healthy;
  document["audit_events"] = auditCount();
  document["modules"] = modules;
  return jsonDump(document);
}

std::string Gateway::modulesJson() const {
  json modules = json::array();
  for (const ModuleRecord& record : modules_) {
    json entry;
    entry["module_id"] = record.model.moduleId;
    entry["available"] = record.available;
    entry["healthy"] = record.healthy;
    entry["health_message"] = record.healthMessage;
    entry["spec_source"] = record.specSource;
    entry["port"] = record.model.port;
    entry["base_url"] = moduleUrl(record);
    entry["domain"] = record.model.domain;
    entry["description"] = record.model.description;
    entry["capabilities"] = record.model.capabilities.size();
    entry["circuit_open"] = record.circuitOpen;
    entry["consecutive_failures"] = record.consecutiveFailures;
    modules.push_back(std::move(entry));
  }
  return jsonDump(modules);
}

std::string Gateway::registryJson() const {
  json rows = json::array();
  for (const Candidate& candidate : candidates()) {
    rows.push_back({{"module_id", candidate.moduleId},
                    {"capability_id", candidate.capabilityId},
                    {"capability_name", candidate.capabilityName},
                    {"capability_type", candidate.capabilityType},
                    {"endpoint", candidate.endpoint}});
  }
  return jsonDump(rows);
}

std::string Gateway::operationsJson() const {
  json byModule = json::object();
  for (const ModuleRecord& record : modules_) {
    if (!record.available) continue;
    json operations = json::array();
    for (const core::CapabilitySpec& capabilitySpec : record.model.capabilities) {
      operations.push_back({{"name", capabilitySpec.name},
                            {"capability_id", capabilitySpec.id},
                            {"type", core::capabilityTypeToString(capabilitySpec.type)},
                            {"endpoint", capabilitySpec.mechanism.endpoint}});
    }
    byModule[record.model.moduleId] = operations;
  }
  json document;
  document["areas"] = {{"patients", "patient-registry"},
                       {"queue", "appointment-queue"},
                       {"consultations", "opd-ehr"},
                       {"dispense", "pharmacy-inventory"},
                       {"billing", "pos-billing"},
                       {"labs", "legacy-lab-service"},
                       {"patients_alternate", "patient-registry-alt"}};
  document["operations"] = byModule;
  return jsonDump(document);
}

}  // namespace gateway
}  // namespace careweave
