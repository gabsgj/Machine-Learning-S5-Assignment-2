#pragma once
// Gateway: the running system around the specification tooling.
//
// The gateway discovers the live Flask modules (GET /spec on their ports, falling back to their
// spec files when a module is down), keeps a registry of every declared capability, resolves
// requirements against that registry with the mapper, synthesizes adapters for the chosen
// provider, executes calls over HTTP with retries and per module circuit breaking, records every
// attempt in a SQLite audit trail, runs multi step workflows with the compatibility engine
// guarding each adjacent pair, and serves the dashboard plus a management API.
//
// The canonical hospital API is the direct layer over the same machinery: POST
// /api/hospital/<capability-name> binds a canonical operation name to the registry capability of
// that name and executes it, so the clinical areas (patients, queue, consultations, dispense,
// billing, labs) are all reachable under one prefix.
//
// Everything the gateway does is also exposed as a library API (used by the tests, the CLI run
// and bundle commands and the dashboard endpoints); the HTTP server is a thin shell over it.
#include <chrono>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "careweave/adapter/adapter.hpp"
#include "careweave/core/types.hpp"
#include "careweave/mapper/mapper.hpp"
#include "nlohmann/json.hpp"

namespace careweave {
namespace gateway {

// ---- discovery and registry ----

struct DiscoveryTarget {
  std::string moduleId;          // expected module id, also names the fallback
  int port = 0;                  // live port to probe
  std::string fallbackSpecPath;  // used when GET /spec does not answer
};

struct ModuleRecord {
  core::ApplicationModel model;
  std::string baseUrl;
  std::string specSource;        // "live GET /spec" or the fallback path
  bool available = false;        // a specification was obtained (live or from the file)
  bool healthy = false;          // the last health probe answered
  std::string healthMessage;
  int consecutiveFailures = 0;
  bool circuitOpen = false;
  std::chrono::steady_clock::time_point circuitOpenedAt{};
};

// One capability bound to its module, as the registry and the resolvers see it.
struct Candidate {
  std::string moduleId;
  std::string capabilityId;
  std::string capabilityName;
  std::string capabilityType;
  std::string endpoint;
  double total = 0.0;
  double margin = 0.0;     // best total minus runner up in the resolution that produced it
  bool ambiguous = false;  // the resolution landed inside the ambiguity margin
};

struct CallOutcome {
  bool ok = false;
  std::string moduleId;
  std::string capabilityId;
  std::string adapterId;
  int attempts = 0;
  int status = 0;
  bool fallbackUsed = false;
  // True when a transport attempt actually reached the module. A call that fails during local
  // adapter validation (an unbound input, a transform that cannot convert) never called the
  // module: it is not retried and it does not count against the circuit breaker.
  bool moduleCalled = false;
  std::string error;
  std::map<std::string, core::Value> outputs;
  core::AppState state;
  std::vector<std::string> trace;
  std::string render() const;
};

// ---- workflows ----

struct WorkflowStepSpec {
  std::string name;
  std::string requirementPath;  // relative to the repository root, or empty
  std::string moduleId;         // direct binding when requirementPath is empty
  std::string capabilityId;
  std::map<std::string, core::Value> inputs;
  // input name -> "step.output" of an earlier step, resolved before execution.
  std::map<std::string, std::string> bind;
  std::vector<std::string> preferredModules;  // mapping preference order
  // Hard per step filter: when not empty, only these module ids may serve the step. A mapped
  // step resolves inside the list; a direct step that binds a module outside it fails.
  std::vector<std::string> allowModules;
};

struct WorkflowDefinition {
  std::string id;
  std::vector<WorkflowStepSpec> steps;
};

bool parseWorkflowDefinition(const nlohmann::json& document, WorkflowDefinition* out,
                             std::string* error);
nlohmann::json workflowDefinitionToJson(const WorkflowDefinition& definition);

struct WorkflowStepResult {
  std::string name;
  std::string moduleId;
  std::string capabilityId;
  std::string verdict;        // "first step", "compatible", "uncertain", "incompatible"
  std::string verdictDetail;
  bool fallbackUsed = false;
  std::vector<std::string> attempts;
  CallOutcome call;
};

struct WorkflowResult {
  bool ok = false;
  std::string workflowId;
  std::string error;
  std::vector<WorkflowStepResult> steps;
  std::string render() const;
};

// ---- configuration ----

struct GatewayConfig {
  std::string rootDir;       // the repository root (module specs and requirement sheets)
  std::string modulesDir;    // modules/, used to build the default targets
  std::vector<DiscoveryTarget> targets;
  size_t maxAttempts = 2;        // per candidate call, including the first
  size_t circuitThreshold = 3;   // consecutive failures that open a module circuit
  long long circuitCooldownMs = 10000;
  long long retryDelayMs = 50;
  int requestTimeoutMs = 2500;
  std::string auditDbPath;       // empty disables the audit trail
  std::string dashboardDir;      // static dashboard served at /
  std::string host = "127.0.0.1";
  int port = 5100;
};

// The seven shipped modules on ports 5001 to 5007 with their spec files as fallbacks.
std::vector<DiscoveryTarget> defaultTargets(const std::string& rootDir,
                                            const std::string& modulesDir);

// ---- the gateway ----

class Gateway {
 public:
  explicit Gateway(GatewayConfig config);
  ~Gateway();
  Gateway(const Gateway&) = delete;
  Gateway& operator=(const Gateway&) = delete;

  // Discovery: for every target, try the live /spec (and /health), then the fallback file.
  void discover();
  const std::vector<ModuleRecord>& modules() const { return modules_; }
  std::vector<Candidate> candidates() const;
  const ModuleRecord* module(const std::string& moduleId) const;
  const core::CapabilitySpec* capability(const std::string& moduleId,
                                         const std::string& capabilityId) const;

  // Resolution: score the requirement against every registry capability; when the best two are
  // inside the ambiguity margin the result records that, and a preferred module inside the
  // margin is promoted to the front so a swap in remains deterministic. A non empty allow list
  // is a hard filter: only candidates of those modules are scored, and a preferred module
  // outside the list is never promoted.
  std::vector<Candidate> resolve(const core::CapabilitySpec& requirement,
                                 const std::vector<std::string>& preferredModules = {},
                                 const std::vector<std::string>& allowModules = {}) const;

  // Execution of one chosen candidate: synthesize the adapter for the requirement, force the
  // live HTTP coordinates of the module, run with retries and the circuit breaker, audit.
  // `fallback` records in the audit row that this attempt follows an earlier module failure.
  CallOutcome callCandidate(const Candidate& candidate, const core::CapabilitySpec& requirement,
                            const std::map<std::string, core::Value>& inputs,
                            bool fallback = false);

  // Direct call by capability id: the requirement is the capability itself.
  CallOutcome callDirect(const std::string& moduleId, const std::string& capabilityId,
                         const std::map<std::string, core::Value>& inputs);

  // Resolve then execute, falling back over the ranked candidates (different modules first)
  // while their circuits allow it. The allow list restricts both the ranking and the fallbacks.
  CallOutcome callRequirement(const core::CapabilitySpec& requirement,
                              const std::map<std::string, core::Value>& inputs,
                              const std::vector<std::string>& preferredModules = {},
                              const std::vector<std::string>& allowModules = {});

  // Adapter preview for the dashboard: the same synthesis the live call path performs for one
  // requirement and one registry capability, rendered as JSON. `error` receives the reason when
  // no definition can be produced.
  std::string adapterJson(const std::string& moduleId, const std::string& capabilityId,
                          const core::CapabilitySpec& requirement, std::string* error) const;

  // Multi step workflow: mapping or direct steps, bound inputs, compatibility guard.
  WorkflowResult runWorkflow(const WorkflowDefinition& definition);

  // Audit trail.
  size_t auditCount() const;
  std::string auditJson(size_t limit) const;

  // Management JSON documents.
  std::string healthJson() const;
  std::string modulesJson() const;
  std::string registryJson() const;
  std::string operationsJson() const;

  // HTTP server: management API, canonical hospital API, workflow endpoint and dashboard.
  void listen();

  GatewayConfig& config() { return config_; }

 private:
  ModuleRecord* findModule(const std::string& moduleId);
  bool moduleAllows(const ModuleRecord& record, std::string* why) const;
  void recordModuleResult(const std::string& moduleId, bool ok);
  void audit(const std::string& kind, const std::string& operation,
             const std::string& moduleId, const std::string& capabilityId, bool ok,
             int status, int attempts, bool fallback, long long latencyMs,
             const std::string& message);
  void openAudit();
  std::string moduleUrl(const ModuleRecord& record) const;

  GatewayConfig config_;
  std::vector<ModuleRecord> modules_;
  size_t auditSequence_ = 0;
  struct AuditStore;
  std::unique_ptr<AuditStore> audit_;
  std::chrono::steady_clock::time_point startedAt_{};
};

}  // namespace gateway
}  // namespace careweave
