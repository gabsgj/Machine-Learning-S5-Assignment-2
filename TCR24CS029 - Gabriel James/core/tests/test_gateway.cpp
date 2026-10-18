// Gateway tests.
//
// The gateway is tested against real HTTP: every fake module below is a real httplib server on
// an ephemeral port that serves its own specification at GET /spec (serialized by the real
// specToJson), answers /health and /state, and executes every declared capability route with a
// scriptable failure counter. The tests then cover discovery (live and file fallback),
// execution with retries, circuit breaking with cooldown and half open recovery, cross module
// fallback, workflow binding plus the compatibility guard, the audit trail, resolution with the
// ambiguity margin, module preference and the hard allow list, and the management JSON
// documents.
#include <atomic>
#include <chrono>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <thread>
#include <utility>
#include <vector>

#include "careweave/core/value_json.hpp"
#include "careweave/gateway/gateway.hpp"
#include "careweave/spec/spec_parser.hpp"
#include "careweave/test/framework.hpp"
#include "httplib.h"
#include "nlohmann/json.hpp"

namespace fs = std::filesystem;
namespace cw = careweave::gateway;
using careweave::core::ApplicationModel;
using careweave::core::CapabilitySpec;
using careweave::core::CapabilityType;
using careweave::core::Condition;
using careweave::core::ConditionOp;
using careweave::core::Effect;
using careweave::core::EffectOp;
using careweave::core::InputSpec;
using careweave::core::OutputSpec;
using careweave::core::StateVariableSchema;
using careweave::core::Value;

namespace {

// ---- fixtures ----

fs::path tempDir() {
  const fs::path dir = fs::temp_directory_path() / "careweave_gateway_tests";
  std::error_code error;
  fs::create_directories(dir, error);
  return dir;
}

StateVariableSchema boolVariable(const std::string& name) {
  StateVariableSchema variable;
  variable.name = name;
  variable.type = "boolean";
  variable.domainValues = {"false", "true"};
  return variable;
}

InputSpec inputSpec(const std::string& name, bool required = true) {
  InputSpec spec;
  spec.name = name;
  spec.type = "string";
  spec.required = required;
  return spec;
}

OutputSpec outputSpec(const std::string& name) {
  OutputSpec spec;
  spec.name = name;
  spec.type = "string";
  return spec;
}

Condition condition(const std::string& variable, Value value) {
  Condition conditionSpec;
  conditionSpec.variable = variable;
  conditionSpec.op = ConditionOp::EQ;
  conditionSpec.value = std::move(value);
  return conditionSpec;
}

Effect effect(const std::string& variable, Value value) {
  Effect effectSpec;
  effectSpec.variable = variable;
  effectSpec.op = EffectOp::SET;
  effectSpec.value = std::move(value);
  return effectSpec;
}

CapabilitySpec capabilitySpec(const std::string& id, const std::string& name,
                              std::vector<InputSpec> inputs, std::vector<OutputSpec> outputs,
                              std::vector<Condition> preconditions = {},
                              std::vector<Effect> effects = {}) {
  CapabilitySpec spec;
  spec.id = id;
  spec.name = name;
  spec.description = "gateway test capability";
  spec.type = CapabilityType::API;
  spec.inputs = std::move(inputs);
  spec.outputs = std::move(outputs);
  spec.preconditions = std::move(preconditions);
  spec.effects = std::move(effects);
  spec.mechanism.kind = CapabilityType::API;
  spec.mechanism.method = "POST";
  spec.mechanism.endpoint = "/api/" + name;
  return spec;
}

ApplicationModel baseModel(const std::string& moduleId) {
  ApplicationModel model;
  model.moduleId = moduleId;
  model.version = "1.0.0";
  model.domain = "generic";
  model.description = "gateway test module";
  return model;
}

// Model with one echo capability and one state variable.
ApplicationModel echoModel(const std::string& moduleId) {
  ApplicationModel model = baseModel(moduleId);
  model.stateSchema = {boolVariable("Flag.up")};
  model.initialState["Flag.up"] = Value(false);
  model.goal = {condition("Flag.up", Value(true))};
  model.capabilities = {
      capabilitySpec("A-Echo", "echo", {inputSpec("value")}, {outputSpec("echoed")})};
  return model;
}

// Model for the workflow tests: a registration that unlocks an admission, and a pair whose
// second half contradicts the first.
ApplicationModel workflowModel(const std::string& moduleId) {
  ApplicationModel model = baseModel(moduleId);
  model.stateSchema = {boolVariable("Patient.registered"), boolVariable("Flag.up"),
                       boolVariable("Flag.closed")};
  model.initialState["Patient.registered"] = Value(false);
  model.initialState["Flag.up"] = Value(false);
  model.initialState["Flag.closed"] = Value(false);
  model.goal = {condition("Patient.registered", Value(true))};
  model.capabilities = {
      capabilitySpec("A-Register", "register", {inputSpec("full_name")},
                     {outputSpec("patient_id")}, {},
                     {effect("Patient.registered", Value(true))}),
      capabilitySpec("A-Admit", "admit", {inputSpec("patient_id")}, {outputSpec("bed")},
                     {condition("Patient.registered", Value(true))}, {}),
      capabilitySpec("A-Open", "open", {}, {outputSpec("opened")}, {},
                     {effect("Flag.up", Value(true))}),
      capabilitySpec("A-Close", "close_pair", {}, {outputSpec("closed")},
                     {condition("Flag.up", Value(false))},
                     {effect("Flag.closed", Value(true))}),
  };
  return model;
}

// A real module over HTTP: real /spec, /health, /state and capability routes.
struct FakeModule {
  careweave::core::ApplicationModel model;
  httplib::Server server;
  std::thread thread;
  int port = 0;
  std::shared_ptr<std::atomic<int>> remainingFailures{new std::atomic<int>(0)};
  std::shared_ptr<std::atomic<int>> callCount{new std::atomic<int>(0)};
  std::map<std::string, std::map<std::string, Value>> scripted;

  ~FakeModule() {
    server.stop();
    if (thread.joinable()) thread.join();
  }

  void scriptOutput(const std::string& capabilityName, const std::string& outputName,
                    Value value) {
    scripted[capabilityName][outputName] = std::move(value);
  }

  void start() {
    port = server.bind_to_any_port("127.0.0.1");
    model.port = port;
    model.baseUrl = "http://127.0.0.1:" + std::to_string(port);
    const std::string specBody = careweave::spec::specToJson(model).dump();
    server.Get("/spec", [specBody](const httplib::Request&, httplib::Response& response) {
      response.set_content(specBody, "application/json");
    });
    server.Get("/health", [](const httplib::Request&, httplib::Response& response) {
      response.set_content(R"({"status":"ok"})", "application/json");
    });
    std::string stateBody;
    {
      nlohmann::json state = nlohmann::json::object();
      for (const auto& entry : model.initialState) {
        state[entry.first] = careweave::core::valueToJson(entry.second);
      }
      stateBody = nlohmann::json{{"state", state}}.dump();
    }
    server.Get("/state", [stateBody](const httplib::Request&, httplib::Response& response) {
      response.set_content(stateBody, "application/json");
    });
    for (const CapabilitySpec& capability : model.capabilities) {
      const std::string endpoint = capability.mechanism.endpoint;
      if (endpoint.empty()) continue;  // a sheet without a live route stays spec only
      const std::string name = capability.name;
      nlohmann::json outputBody = nlohmann::json::object();
      for (const OutputSpec& output : capability.outputs) {
        Value value(output.name + "_value");
        const auto scriptedCapability = scripted.find(name);
        if (scriptedCapability != scripted.end()) {
          const auto override = scriptedCapability->second.find(output.name);
          if (override != scriptedCapability->second.end()) value = override->second;
        }
        outputBody[output.name] = careweave::core::valueToJson(value);
      }
      const std::string outputsDump = outputBody.dump();
      const std::shared_ptr<std::atomic<int>> failures = remainingFailures;
      const std::shared_ptr<std::atomic<int>> calls = callCount;
      server.Post(endpoint,
                  [name, outputsDump, failures, calls](const httplib::Request&,
                                                       httplib::Response& response) {
                    calls->fetch_add(1, std::memory_order_relaxed);
                    if (failures->load(std::memory_order_relaxed) > 0) {
                      failures->fetch_sub(1, std::memory_order_relaxed);
                      response.status = 500;
                      response.set_content(
                          nlohmann::json{{"status", "error"}, {"error", "scripted failure"}}
                              .dump(),
                          "application/json");
                      return;
                    }
                    response.set_content(
                        nlohmann::json{{"status", "ok"},
                                       {"capability", name},
                                       {"outputs", nlohmann::json::parse(outputsDump)}}
                            .dump(),
                        "application/json");
                  });
    }
    thread = std::thread([this] { server.listen_after_bind(); });
    while (!server.is_running()) {
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
  }
};

cw::GatewayConfig testConfig() {
  cw::GatewayConfig config;
  config.rootDir = tempDir().string();
  config.modulesDir = (tempDir() / "modules").string();
  config.dashboardDir = (tempDir() / "dashboard").string();
  config.maxAttempts = 1;
  config.circuitThreshold = 3;
  config.circuitCooldownMs = 60000;
  config.retryDelayMs = 0;
  config.requestTimeoutMs = 2000;
  return config;
}

void addTarget(cw::GatewayConfig* config, const std::string& moduleId, int port,
               const std::string& fallbackSpecPath = "") {
  cw::DiscoveryTarget target;
  target.moduleId = moduleId;
  target.port = port;
  target.fallbackSpecPath = fallbackSpecPath;
  config->targets.push_back(target);
}

int closedPort() {
  httplib::Server probe;
  return probe.bind_to_any_port("127.0.0.1");
}

bool contains(const std::string& text, const std::string& needle) {
  return text.find(needle) != std::string::npos;
}

bool anyLineContains(const std::vector<std::string>& lines, const std::string& needle) {
  for (const std::string& line : lines) {
    if (contains(line, needle)) return true;
  }
  return false;
}

}  // namespace

CW_TEST_CASE(discovery_reads_live_specs_and_falls_back_to_files) {
  FakeModule liveA;
  liveA.model = echoModel("fake-a");
  liveA.start();
  FakeModule liveB;
  liveB.model = echoModel("fake-b");
  liveB.start();

  // A module that is not running: its specification has to come from the fallback file.
  ApplicationModel fileModel = echoModel("fake-file");
  const fs::path specPath = tempDir() / "fake_file_spec.json";
  std::string writeError;
  CW_CHECK(careweave::spec::writeSpecJson(fileModel, specPath.string(), &writeError));

  cw::GatewayConfig config = testConfig();
  addTarget(&config, "fake-a", liveA.port);
  addTarget(&config, "fake-b", liveB.port);
  addTarget(&config, "fake-file", closedPort(), specPath.string());
  cw::Gateway gateway(config);

  gateway.discover();
  CW_CHECK(gateway.modules().size() == 3);

  const cw::ModuleRecord* live = gateway.module("fake-a");
  CW_CHECK(live != nullptr);
  if (live == nullptr) return;
  CW_CHECK(live->available);
  CW_CHECK(live->healthy);
  CW_CHECK(contains(live->specSource, "live"));

  const cw::ModuleRecord* file = gateway.module("fake-file");
  CW_CHECK(file != nullptr);
  if (file == nullptr) return;
  CW_CHECK(file->available);
  CW_CHECK(!file->healthy);
  CW_CHECK(contains(file->specSource, "file"));
  CW_CHECK(contains(file->healthMessage, "not running"));

  CW_CHECK(gateway.candidates().size() == 3);
}

CW_TEST_CASE(direct_call_executes_and_returns_named_outputs) {
  FakeModule module;
  module.model = echoModel("fake-a");
  module.scriptOutput("echo", "echoed", Value("hello-echo"));
  module.start();

  cw::GatewayConfig config = testConfig();
  addTarget(&config, "fake-a", module.port);
  cw::Gateway gateway(config);
  gateway.discover();

  const cw::CallOutcome outcome =
      gateway.callDirect("fake-a", "A-Echo", {{"value", Value("hello")}});
  CW_CHECK(outcome.ok);
  CW_CHECK(outcome.attempts == 1);
  CW_CHECK(outcome.status == 200);
  CW_CHECK(outcome.moduleId == "fake-a");
  CW_CHECK(outcome.capabilityId == "A-Echo");
  CW_CHECK(contains(outcome.adapterId, "adapter-live-fake-a-A-Echo"));
  CW_CHECK(outcome.outputs.count("echoed") == 1);
  if (outcome.outputs.count("echoed") == 1) {
    CW_CHECK(outcome.outputs.at("echoed").asString() == "hello-echo");
  }
  CW_CHECK(outcome.state.has("Flag.up"));
  CW_CHECK(!outcome.state.get("Flag.up").asBool());

  const nlohmann::json rendered = nlohmann::json::parse(outcome.render(), nullptr, false);
  CW_CHECK(!rendered.is_discarded());
  if (!rendered.is_discarded()) {
    CW_CHECK(rendered["ok"].get<bool>());
    CW_CHECK(rendered["outputs"]["echoed"].get<std::string>() == "hello-echo");
  }
}

CW_TEST_CASE(retries_recover_a_transient_failure) {
  FakeModule module;
  module.model = echoModel("fake-a");
  module.remainingFailures->store(1);
  module.start();

  cw::GatewayConfig config = testConfig();
  config.maxAttempts = 2;
  addTarget(&config, "fake-a", module.port);
  cw::Gateway gateway(config);
  gateway.discover();

  const cw::CallOutcome outcome =
      gateway.callDirect("fake-a", "A-Echo", {{"value", Value("x")}});
  CW_CHECK(outcome.ok);
  CW_CHECK(outcome.attempts == 2);
  CW_CHECK(module.callCount->load() == 2);
  CW_CHECK(gateway.module("fake-a") != nullptr && !gateway.module("fake-a")->circuitOpen);
}

CW_TEST_CASE(circuit_breaker_opens_and_recovers_after_cooldown) {
  FakeModule module;
  module.model = echoModel("fake-a");
  module.remainingFailures->store(1000);
  module.start();

  cw::GatewayConfig config = testConfig();
  config.circuitThreshold = 1;
  addTarget(&config, "fake-a", module.port);
  cw::Gateway gateway(config);
  gateway.discover();

  const cw::CallOutcome first =
      gateway.callDirect("fake-a", "A-Echo", {{"value", Value("x")}});
  CW_CHECK(!first.ok);
  CW_CHECK(gateway.module("fake-a")->circuitOpen);
  CW_CHECK(gateway.module("fake-a")->consecutiveFailures == 1);
  const int callsAfterFirst = module.callCount->load();

  // While the circuit is open and the cooldown has not elapsed the call is refused locally.
  const cw::CallOutcome second =
      gateway.callDirect("fake-a", "A-Echo", {{"value", Value("x")}});
  CW_CHECK(!second.ok);
  CW_CHECK(contains(second.error, "circuit open"));
  CW_CHECK(anyLineContains(second.trace, "circuit open"));
  CW_CHECK(module.callCount->load() == callsAfterFirst);

  // Half open recovery: with no cooldown the next attempt is allowed through, and a success
  // closes the circuit again.
  FakeModule recovered;
  recovered.model = echoModel("fake-a");
  recovered.remainingFailures->store(1);
  recovered.start();
  cw::GatewayConfig recoveryConfig = testConfig();
  recoveryConfig.circuitThreshold = 1;
  recoveryConfig.circuitCooldownMs = 0;
  addTarget(&recoveryConfig, "fake-a", recovered.port);
  cw::Gateway recoveryGateway(recoveryConfig);
  recoveryGateway.discover();

  const cw::CallOutcome failed =
      recoveryGateway.callDirect("fake-a", "A-Echo", {{"value", Value("x")}});
  CW_CHECK(!failed.ok);
  CW_CHECK(recoveryGateway.module("fake-a")->circuitOpen);

  const cw::CallOutcome probed =
      recoveryGateway.callDirect("fake-a", "A-Echo", {{"value", Value("x")}});
  CW_CHECK(probed.ok);
  CW_CHECK(!recoveryGateway.module("fake-a")->circuitOpen);
  CW_CHECK(recoveryGateway.module("fake-a")->consecutiveFailures == 0);
}

CW_TEST_CASE(fallback_tries_the_next_module) {
  FakeModule first;
  first.model = echoModel("fake-a");
  first.remainingFailures->store(1000);
  first.start();
  FakeModule second;
  second.model = echoModel("fake-b");
  second.start();

  cw::GatewayConfig config = testConfig();
  addTarget(&config, "fake-a", first.port);
  addTarget(&config, "fake-b", second.port);
  cw::Gateway gateway(config);
  gateway.discover();

  const CapabilitySpec requirement =
      capabilitySpec("REQ-Echo", "echo", {inputSpec("value")}, {outputSpec("echoed")});
  const cw::CallOutcome outcome = gateway.callRequirement(requirement, {{"value", Value("x")}});
  CW_CHECK(outcome.ok);
  CW_CHECK(outcome.moduleId == "fake-b");
  CW_CHECK(outcome.fallbackUsed);
  CW_CHECK(second.callCount->load() == 1);
  CW_CHECK(anyLineContains(outcome.trace, "module fake-a"));
  CW_CHECK(anyLineContains(outcome.trace, "failed"));
}

CW_TEST_CASE(workflow_binds_step_outputs_and_guards_compatibility) {
  FakeModule module;
  module.model = workflowModel("fake-a");
  module.scriptOutput("register", "patient_id", Value("P-42"));
  module.start();

  cw::GatewayConfig config = testConfig();
  addTarget(&config, "fake-a", module.port);
  cw::Gateway gateway(config);
  gateway.discover();

  cw::WorkflowDefinition definition;
  definition.id = "clinic-test";
  cw::WorkflowStepSpec registerStep;
  registerStep.name = "register";
  registerStep.moduleId = "fake-a";
  registerStep.capabilityId = "A-Register";
  registerStep.inputs["full_name"] = Value("Ada Lovelace");
  cw::WorkflowStepSpec admitStep;
  admitStep.name = "admit";
  admitStep.moduleId = "fake-a";
  admitStep.capabilityId = "A-Admit";
  admitStep.bind["patient_id"] = "register.patient_id";
  definition.steps = {registerStep, admitStep};

  const cw::WorkflowResult result = gateway.runWorkflow(definition);
  CW_CHECK(result.ok);
  CW_CHECK(result.steps.size() == 2);
  if (result.steps.size() != 2) return;
  CW_CHECK(result.steps[0].verdict == "first step");
  CW_CHECK(result.steps[0].call.ok);
  CW_CHECK(result.steps[0].call.outputs.count("patient_id") == 1);
  if (result.steps[0].call.outputs.count("patient_id") == 1) {
    CW_CHECK(result.steps[0].call.outputs.at("patient_id").asString() == "P-42");
  }
  CW_CHECK(result.steps[1].verdict == "compatible");
  CW_CHECK(result.steps[1].call.ok);
  CW_CHECK(result.steps[1].call.outputs.count("bed") == 1);

  const nlohmann::json rendered = nlohmann::json::parse(result.render(), nullptr, false);
  CW_CHECK(!rendered.is_discarded());
  if (!rendered.is_discarded() && rendered["steps"].size() == 2) {
    CW_CHECK(rendered["steps"][1]["verdict"].get<std::string>() == "compatible");
  }

  // A pair the engine rejects: the second step requires the opposite of what the first wrote.
  cw::WorkflowDefinition unsafe;
  unsafe.id = "safety-test";
  cw::WorkflowStepSpec openStep;
  openStep.name = "open";
  openStep.moduleId = "fake-a";
  openStep.capabilityId = "A-Open";
  cw::WorkflowStepSpec closeStep;
  closeStep.name = "close";
  closeStep.moduleId = "fake-a";
  closeStep.capabilityId = "A-Close";
  unsafe.steps = {openStep, closeStep};

  const cw::WorkflowResult rejected = gateway.runWorkflow(unsafe);
  CW_CHECK(!rejected.ok);
  CW_CHECK(contains(rejected.error, "incompatible"));
  CW_CHECK(rejected.steps.size() == 2);
  if (rejected.steps.size() == 2) {
    CW_CHECK(rejected.steps[1].verdict == "incompatible");
  }
}

CW_TEST_CASE(local_adapter_failures_do_not_trip_the_circuit) {
  // A call that fails during local adapter validation never reaches the module: it is not
  // retried, it does not count against the circuit breaker, and the module stays usable.
  FakeModule module;
  module.model = echoModel("fake-a");
  module.start();

  cw::GatewayConfig config = testConfig();
  config.maxAttempts = 2;
  config.circuitThreshold = 1;
  addTarget(&config, "fake-a", module.port);
  cw::Gateway gateway(config);
  gateway.discover();

  const cw::CallOutcome local = gateway.callDirect("fake-a", "A-Echo", {});
  CW_CHECK(!local.ok);
  CW_CHECK(contains(local.error, "missing requirement input"));
  CW_CHECK(local.attempts == 1);
  CW_CHECK(!local.moduleCalled);
  CW_CHECK(anyLineContains(local.trace, "local adapter failure"));
  CW_CHECK(module.callCount->load() == 0);
  CW_CHECK(gateway.module("fake-a") != nullptr && !gateway.module("fake-a")->circuitOpen);
  CW_CHECK(gateway.module("fake-a")->consecutiveFailures == 0);

  // The same module still answers a well formed call.
  const cw::CallOutcome ok = gateway.callDirect("fake-a", "A-Echo", {{"value", Value("x")}});
  CW_CHECK(ok.ok);
  CW_CHECK(ok.moduleCalled);
  CW_CHECK(module.callCount->load() == 1);
}

CW_TEST_CASE(audit_trail_records_calls_and_workflows) {
  FakeModule module;
  module.model = echoModel("fake-a");
  module.start();

  const fs::path auditPath = tempDir() / "gateway_audit_test.db";
  std::error_code removeError;
  fs::remove(auditPath, removeError);

  cw::GatewayConfig config = testConfig();
  config.auditDbPath = auditPath.string();
  addTarget(&config, "fake-a", module.port);
  cw::Gateway gateway(config);
  gateway.discover();
  CW_CHECK(gateway.auditCount() == 0);

  const cw::CallOutcome ok = gateway.callDirect("fake-a", "A-Echo", {{"value", Value("x")}});
  CW_CHECK(ok.ok);

  module.remainingFailures->store(1);
  const cw::CallOutcome failed =
      gateway.callDirect("fake-a", "A-Echo", {{"value", Value("x")}});
  CW_CHECK(!failed.ok);
  CW_CHECK(gateway.auditCount() == 2);

  cw::WorkflowDefinition definition;
  definition.id = "audit-test";
  cw::WorkflowStepSpec step;
  step.name = "echo";
  step.moduleId = "fake-a";
  step.capabilityId = "A-Echo";
  step.inputs["value"] = Value("x");
  definition.steps = {step};
  const cw::WorkflowResult result = gateway.runWorkflow(definition);
  CW_CHECK(result.ok);
  // The workflow adds the audit row of its step call plus the workflow summary row.
  CW_CHECK(gateway.auditCount() == 4);

  const nlohmann::json rows = nlohmann::json::parse(gateway.auditJson(10), nullptr, false);
  CW_CHECK(!rows.is_discarded());
  CW_CHECK(rows.size() == 4);
  if (!rows.is_discarded() && rows.size() == 4) {
    CW_CHECK(rows[0]["kind"].get<std::string>() == "workflow");
    CW_CHECK(rows[0]["ok"].get<bool>());
    CW_CHECK(rows[1]["kind"].get<std::string>() == "call");
    CW_CHECK(rows[1]["ok"].get<bool>());
    CW_CHECK(!rows[2]["ok"].get<bool>());
    CW_CHECK(rows[2]["module"].get<std::string>() == "fake-a");
    CW_CHECK(rows[3]["ok"].get<bool>());
  }
}

CW_TEST_CASE(resolution_reports_ambiguity_and_honours_preference) {
  FakeModule first;
  first.model = echoModel("fake-a");
  first.model.capabilities.push_back(capabilitySpec("A-Alpha", "alpha_tool",
                                                    {inputSpec("alpha_value")},
                                                    {outputSpec("alpha_result")}));
  first.start();
  FakeModule second;
  second.model = echoModel("fake-b");
  second.model.capabilities.push_back(capabilitySpec("B-Beta", "beta_tool",
                                                     {inputSpec("beta_value")},
                                                     {outputSpec("beta_result")}));
  second.start();

  cw::GatewayConfig config = testConfig();
  addTarget(&config, "fake-a", first.port);
  addTarget(&config, "fake-b", second.port);
  cw::Gateway gateway(config);
  gateway.discover();

  const CapabilitySpec echoRequirement =
      capabilitySpec("REQ-Echo", "echo", {inputSpec("value")}, {outputSpec("echoed")});
  const std::vector<cw::Candidate> ranked = gateway.resolve(echoRequirement);
  CW_CHECK(ranked.size() == 4);
  if (ranked.size() != 4) return;
  CW_CHECK(ranked[0].total > 0.0);
  CW_CHECK(ranked[0].ambiguous);
  CW_CHECK(ranked[0].moduleId == "fake-a");

  const std::vector<cw::Candidate> preferred = gateway.resolve(echoRequirement, {"fake-b"});
  CW_CHECK(!preferred.empty());
  if (!preferred.empty()) {
    CW_CHECK(preferred[0].moduleId == "fake-b");
    CW_CHECK(preferred[0].ambiguous);
  }

  const CapabilitySpec alphaRequirement = capabilitySpec(
      "REQ-Alpha", "alpha_tool", {inputSpec("alpha_value")}, {outputSpec("alpha_result")});
  const std::vector<cw::Candidate> alpha = gateway.resolve(alphaRequirement);
  CW_CHECK(!alpha.empty());
  if (!alpha.empty()) {
    CW_CHECK(!alpha[0].ambiguous);
    CW_CHECK(alpha[0].capabilityName == "alpha_tool");
    CW_CHECK(alpha[0].moduleId == "fake-a");
  }
}

CW_TEST_CASE(live_calls_promote_and_skip_sheets_without_endpoints) {
  // A form sheet that mirrors a live API must never shadow that API: the resolver promotes
  // only callable candidates, and a call that meets a sheet skips it without consuming its
  // module's single try. fake-sheet holds one such sheet, fake-alt holds a sheet and the API
  // that answers it, and fake-canonical is the lower scoring fallback.
  const CapabilitySpec requirement =
      capabilitySpec("REQ-Pat_reg", "pat_reg", {inputSpec("pat_no"), inputSpec("pat_name")},
                     {outputSpec("pat_reg")});
  const auto formSheet = [](const std::string& id) {
    CapabilitySpec form = capabilitySpec(id, "pat_reg",
                                         {inputSpec("pat_no"), inputSpec("pat_name")},
                                         {outputSpec("pat_reg")});
    form.type = CapabilityType::GUI;
    form.mechanism.kind = CapabilityType::GUI;
    form.mechanism.endpoint.clear();
    return form;
  };

  FakeModule sheet;
  sheet.model = echoModel("fake-sheet");
  sheet.model.capabilities = {formSheet("S-Form")};
  sheet.start();

  FakeModule alt;
  alt.model = echoModel("fake-alt");
  alt.model.capabilities = {
      formSheet("ALT-Form"),
      capabilitySpec("ALT-Register", "pat_reg", {inputSpec("pat_no"), inputSpec("pat_name")},
                     {outputSpec("pat_reg")}),
  };
  alt.start();

  FakeModule canonical;
  canonical.model = echoModel("fake-canonical");
  canonical.model.capabilities = {capabilitySpec("CAN-Register", "register_patient",
                                                 {inputSpec("mrn"), inputSpec("full_name")},
                                                 {outputSpec("patient_id")})};
  canonical.start();

  cw::GatewayConfig config = testConfig();
  addTarget(&config, "fake-sheet", sheet.port);
  addTarget(&config, "fake-alt", alt.port);
  addTarget(&config, "fake-canonical", canonical.port);
  cw::Gateway gateway(config);
  gateway.discover();

  // The exact mirrors tie at the top, so the resolution is ambiguous and the sheet leads.
  const std::vector<cw::Candidate> ranked = gateway.resolve(requirement);
  CW_CHECK(ranked.size() == 4);
  if (ranked.size() == 4) {
    CW_CHECK(ranked[0].capabilityId == "S-Form");
    CW_CHECK(ranked[0].ambiguous);
    CW_CHECK(ranked[1].capabilityId == "ALT-Form");
    CW_CHECK(ranked[2].capabilityId == "ALT-Register");
  }

  // With the alt module preferred, its callable candidate is promoted over the sheet while
  // the ambiguity stays reported.
  const std::vector<cw::Candidate> preferred = gateway.resolve(requirement, {"fake-alt"});
  CW_CHECK(preferred.size() == 4);
  if (preferred.size() == 4) {
    CW_CHECK(preferred[0].moduleId == "fake-alt");
    CW_CHECK(preferred[0].capabilityId == "ALT-Register");
    CW_CHECK(preferred[0].ambiguous);
  }

  // A call for the alt module lands on its API, never on the sheet.
  const cw::CallOutcome preferredCall =
      gateway.callRequirement(requirement, {{"pat_no", Value("L-1")}, {"pat_name", Value("Ada")}},
                              {"fake-alt"});
  CW_CHECK(preferredCall.ok);
  CW_CHECK(preferredCall.moduleId == "fake-alt");
  CW_CHECK(preferredCall.capabilityId == "ALT-Register");
  CW_CHECK(alt.callCount->load() == 1);
  CW_CHECK(canonical.callCount->load() == 0);

  // Without a preference the sheets are skipped, not tried: the call still reaches the alt
  // module's API instead of burning its single try and falling through to the canonical one.
  const cw::CallOutcome plainCall = gateway.callRequirement(
      requirement, {{"pat_no", Value("L-2")}, {"pat_name", Value("Bo")}});
  CW_CHECK(plainCall.ok);
  CW_CHECK(plainCall.moduleId == "fake-alt");
  CW_CHECK(plainCall.capabilityId == "ALT-Register");
  CW_CHECK(anyLineContains(plainCall.trace, "skipped"));
  CW_CHECK(!anyLineContains(plainCall.trace, "): failed:"));
  CW_CHECK(canonical.callCount->load() == 0);
}

CW_TEST_CASE(management_documents_render) {
  FakeModule module;
  module.model = echoModel("fake-a");
  module.start();

  cw::GatewayConfig config = testConfig();
  addTarget(&config, "fake-a", module.port);
  cw::Gateway gateway(config);
  gateway.discover();

  const nlohmann::json modules = nlohmann::json::parse(gateway.modulesJson(), nullptr, false);
  CW_CHECK(!modules.is_discarded());
  CW_CHECK(modules.size() == 1);
  if (!modules.is_discarded() && modules.size() == 1) {
    CW_CHECK(modules[0]["module_id"].get<std::string>() == "fake-a");
    CW_CHECK(modules[0]["available"].get<bool>());
    CW_CHECK(modules[0]["capabilities"].get<size_t>() == 1);
  }

  const nlohmann::json registry = nlohmann::json::parse(gateway.registryJson(), nullptr, false);
  CW_CHECK(registry.size() == 1);
  if (registry.size() == 1) {
    CW_CHECK(registry[0]["capability_id"].get<std::string>() == "A-Echo");
  }

  const nlohmann::json health = nlohmann::json::parse(gateway.healthJson(), nullptr, false);
  CW_CHECK(health["status"].get<std::string>() == "ok");
  CW_CHECK(health["modules_total"].get<size_t>() == 1);
  CW_CHECK(health["modules_healthy"].get<size_t>() == 1);

  const nlohmann::json operations =
      nlohmann::json::parse(gateway.operationsJson(), nullptr, false);
  CW_CHECK(operations["areas"]["patients"].get<std::string>() == "patient-registry");
  CW_CHECK(operations["operations"].contains("fake-a"));
}

CW_TEST_CASE(workflow_definitions_round_trip_and_reject_malformed_documents) {
  const nlohmann::json valid = nlohmann::json::parse(R"({
    "workflow_id": "round-trip",
    "steps": [
      {"name": "one", "module": "fake-a", "capability": "A-Echo",
       "inputs": {"value": "x"}, "bind": {"echoed": "one.echoed"},
       "preferred_modules": ["fake-a"], "allow_modules": ["fake-a", "fake-b"]}
    ]
  })",
                                                     nullptr, false);
  cw::WorkflowDefinition definition;
  std::string error;
  CW_CHECK(cw::parseWorkflowDefinition(valid, &definition, &error));
  CW_CHECK(definition.id == "round-trip");
  CW_CHECK(definition.steps.size() == 1);
  if (definition.steps.size() == 1) {
    CW_CHECK(definition.steps[0].bind.at("echoed") == "one.echoed");
    CW_CHECK(definition.steps[0].preferredModules.size() == 1);
    CW_CHECK(definition.steps[0].allowModules.size() == 2);
  }

  const nlohmann::json rebuilt = cw::workflowDefinitionToJson(definition);
  CW_CHECK(rebuilt["steps"][0].contains("allow_modules"));
  cw::WorkflowDefinition reparsed;
  CW_CHECK(cw::parseWorkflowDefinition(rebuilt, &reparsed, &error));
  CW_CHECK(reparsed.id == definition.id);
  CW_CHECK(reparsed.steps.size() == definition.steps.size());
  if (reparsed.steps.size() == definition.steps.size() && !reparsed.steps.empty()) {
    CW_CHECK(reparsed.steps[0].capabilityId == definition.steps[0].capabilityId);
    CW_CHECK(reparsed.steps[0].allowModules == definition.steps[0].allowModules);
  }

  const nlohmann::json missingSteps = nlohmann::json::parse(R"({"workflow_id": "no-steps"})",
                                                            nullptr, false);
  CW_CHECK(!cw::parseWorkflowDefinition(missingSteps, &definition, &error));
  CW_CHECK(contains(error, "steps"));

  const nlohmann::json noTarget = nlohmann::json::parse(
      R"({"workflow_id": "unbound", "steps": [{"name": "one"}]})", nullptr, false);
  CW_CHECK(!cw::parseWorkflowDefinition(noTarget, &definition, &error));
  CW_CHECK(contains(error, "requirement sheet"));

  const nlohmann::json badInput = nlohmann::json::parse(
      R"({"workflow_id": "bad-input", "steps": [{"name": "one", "module": "m",
          "capability": "c", "inputs": {"x": {"nested": true}}}]})",
      nullptr, false);
  CW_CHECK(!cw::parseWorkflowDefinition(badInput, &definition, &error));
  CW_CHECK(contains(error, "input"));

  // The two module lists on a step are validated, so a typo cannot silently widen a call.
  const nlohmann::json allowNotArray = nlohmann::json::parse(
      R"({"workflow_id": "bad-allow", "steps": [{"name": "one", "module": "m",
          "capability": "c", "allow_modules": "m"}]})",
      nullptr, false);
  CW_CHECK(!cw::parseWorkflowDefinition(allowNotArray, &definition, &error));
  CW_CHECK(contains(error, "allow_modules"));

  const nlohmann::json allowEmpty = nlohmann::json::parse(
      R"({"workflow_id": "empty-allow", "steps": [{"name": "one", "module": "m",
          "capability": "c", "allow_modules": []}]})",
      nullptr, false);
  CW_CHECK(!cw::parseWorkflowDefinition(allowEmpty, &definition, &error));
  CW_CHECK(contains(error, "allow_modules"));

  const nlohmann::json allowBadEntry = nlohmann::json::parse(
      R"({"workflow_id": "bad-allow-entry", "steps": [{"name": "one", "module": "m",
          "capability": "c", "allow_modules": ["m", 5]}]})",
      nullptr, false);
  CW_CHECK(!cw::parseWorkflowDefinition(allowBadEntry, &definition, &error));
  CW_CHECK(contains(error, "allow_modules"));

  const nlohmann::json preferredNotArray = nlohmann::json::parse(
      R"({"workflow_id": "bad-preferred", "steps": [{"name": "one", "module": "m",
          "capability": "c", "preferred_modules": 5}]})",
      nullptr, false);
  CW_CHECK(!cw::parseWorkflowDefinition(preferredNotArray, &definition, &error));
  CW_CHECK(contains(error, "preferred_modules"));
}

CW_TEST_CASE(resolution_and_calls_respect_a_hard_allow_list) {
  FakeModule first;
  first.model = echoModel("fake-a");
  first.model.capabilities.push_back(capabilitySpec("A-Alpha", "alpha_tool",
                                                    {inputSpec("alpha_value")},
                                                    {outputSpec("alpha_result")}));
  first.start();
  FakeModule second;
  second.model = echoModel("fake-b");
  second.model.capabilities.push_back(capabilitySpec("B-Beta", "beta_tool",
                                                     {inputSpec("beta_value")},
                                                     {outputSpec("beta_result")}));
  second.start();

  cw::GatewayConfig config = testConfig();
  addTarget(&config, "fake-a", first.port);
  addTarget(&config, "fake-b", second.port);
  cw::Gateway gateway(config);
  gateway.discover();

  const CapabilitySpec echoRequirement =
      capabilitySpec("REQ-Echo", "echo", {inputSpec("value")}, {outputSpec("echoed")});

  // Without a filter both modules rank; the allow list keeps only the listed modules, and a
  // preference outside the list cannot pull its module back in.
  CW_CHECK(gateway.resolve(echoRequirement).size() == 4);
  const std::vector<cw::Candidate> allowed =
      gateway.resolve(echoRequirement, {"fake-b"}, {"fake-a"});
  CW_CHECK(allowed.size() == 2);
  if (allowed.size() == 2) {
    CW_CHECK(allowed[0].moduleId == "fake-a");
    CW_CHECK(allowed[1].moduleId == "fake-a");
  }
  const std::vector<cw::Candidate> other =
      gateway.resolve(echoRequirement, {"fake-a"}, {"fake-b"});
  CW_CHECK(other.size() == 2);
  if (other.size() == 2) {
    CW_CHECK(other[0].moduleId == "fake-b");
  }
  // An allow list that names nothing in the registry ranks nothing.
  CW_CHECK(gateway.resolve(echoRequirement, {}, {"ghost"}).empty());

  // A call runs inside the list.
  std::map<std::string, Value> inputs;
  inputs["value"] = Value("allowed");
  const cw::CallOutcome called = gateway.callRequirement(echoRequirement, inputs, {}, {"fake-b"});
  CW_CHECK_MSG(called.ok, called.error);
  CW_CHECK(called.moduleId == "fake-b");

  // A call whose allow list matches nothing fails before any module is touched.
  const cw::CallOutcome denied = gateway.callRequirement(echoRequirement, inputs, {}, {"ghost"});
  CW_CHECK(!denied.ok);
  CW_CHECK(contains(denied.error, "no candidate matched"));
  CW_CHECK(!denied.moduleCalled);
  CW_CHECK(second.callCount->load() == 1);

  // Cross module fallback stays inside the list too: the first allowed module fails once and
  // the second allowed module answers.
  first.remainingFailures->store(1);
  const cw::CallOutcome fellBack =
      gateway.callRequirement(echoRequirement, inputs, {}, {"fake-a", "fake-b"});
  CW_CHECK_MSG(fellBack.ok, fellBack.error);
  CW_CHECK(fellBack.moduleId == "fake-b");
  CW_CHECK(fellBack.fallbackUsed);
  CW_CHECK(first.callCount->load() == 1);
  CW_CHECK(second.callCount->load() == 2);
}

CW_TEST_CASE(workflow_steps_bind_within_their_allow_lists) {
  FakeModule first;
  first.model = echoModel("fake-a");
  first.start();
  FakeModule second;
  second.model = echoModel("fake-b");
  second.start();

  cw::GatewayConfig config = testConfig();
  addTarget(&config, "fake-a", first.port);
  addTarget(&config, "fake-b", second.port);
  cw::Gateway gateway(config);
  gateway.discover();

  // A direct step outside its own allow list is refused before any call.
  cw::WorkflowDefinition outside;
  outside.id = "allow-outside";
  cw::WorkflowStepSpec blocked;
  blocked.name = "register";
  blocked.moduleId = "fake-a";
  blocked.capabilityId = "A-Echo";
  blocked.allowModules = {"fake-b"};
  outside.steps.push_back(blocked);
  const cw::WorkflowResult refused = gateway.runWorkflow(outside);
  CW_CHECK(!refused.ok);
  CW_CHECK(contains(refused.error, "outside its allow list"));
  CW_CHECK(first.callCount->load() == 0);

  // The same binding inside its allow list runs.
  cw::WorkflowDefinition inside;
  inside.id = "allow-inside";
  cw::WorkflowStepSpec allowed;
  allowed.name = "register";
  allowed.moduleId = "fake-a";
  allowed.capabilityId = "A-Echo";
  allowed.inputs["value"] = Value("workflow");
  allowed.allowModules = {"fake-a", "fake-b"};
  inside.steps.push_back(allowed);
  const cw::WorkflowResult ran = gateway.runWorkflow(inside);
  CW_CHECK_MSG(ran.ok, ran.error);
  CW_CHECK(first.callCount->load() == 1);

  // A mapped step resolves inside its list, and the preference inside the list still wins.
  // The fixture mirrors the echo capability in the same vocabulary as the fake modules.
  {
    std::ofstream fixture(tempDir() / "workflow_allow_requirement.yaml",
                          std::ios::binary | std::ios::trunc);
    fixture << R"(spec_version: "1.0"
module:
  module_id: requirement-echo
  version: "1.0"
  domain: generic
capabilities:
  - id: REQ-Echo
    name: echo
    type: API
    description: Requirement fixture for the workflow allow list test.
    inputs:
      - name: value
        type: string
        required: true
    outputs:
      - name: echoed
        type: string
    preconditions: []
    effects: []
    constraints: []
    resources: []
    quality:
      time_ms: 10
      money: 0
      resource: 0.01
      risk: 0.01
      energy: 0.001
    reliability: 0.9
    availability:
      always: true
    mechanism:
      kind: API
      method: POST
      endpoint: /api/echo
)";
  }
  cw::WorkflowDefinition mapped;
  mapped.id = "allow-mapped";
  cw::WorkflowStepSpec step;
  step.name = "register";
  step.requirementPath = "workflow_allow_requirement.yaml";
  step.inputs["value"] = Value("mapped");
  step.allowModules = {"fake-b"};
  mapped.steps.push_back(step);
  const cw::WorkflowResult mappedResult = gateway.runWorkflow(mapped);
  CW_CHECK_MSG(mappedResult.ok, mappedResult.error);
  if (!mappedResult.steps.empty()) {
    CW_CHECK(mappedResult.steps[0].moduleId == "fake-b");
  }
  CW_CHECK(second.callCount->load() == 1);

  cw::WorkflowDefinition promoted;
  promoted.id = "allow-mapped-preferred";
  cw::WorkflowStepSpec preferredStep;
  preferredStep.name = "register";
  preferredStep.requirementPath = "workflow_allow_requirement.yaml";
  preferredStep.inputs["value"] = Value("mapped");
  preferredStep.preferredModules = {"fake-b"};
  preferredStep.allowModules = {"fake-a", "fake-b"};
  promoted.steps.push_back(preferredStep);
  const cw::WorkflowResult promotedResult = gateway.runWorkflow(promoted);
  CW_CHECK_MSG(promotedResult.ok, promotedResult.error);
  if (!promotedResult.steps.empty()) {
    CW_CHECK(promotedResult.steps[0].moduleId == "fake-b");
  }

  // A mapped step whose list matches nothing fails with the resolver's reason.
  cw::WorkflowDefinition denied;
  denied.id = "allow-mapped-denied";
  cw::WorkflowStepSpec deniedStep;
  deniedStep.name = "register";
  deniedStep.requirementPath = "workflow_allow_requirement.yaml";
  deniedStep.allowModules = {"ghost"};
  denied.steps.push_back(deniedStep);
  const cw::WorkflowResult deniedResult = gateway.runWorkflow(denied);
  CW_CHECK(!deniedResult.ok);
  CW_CHECK(contains(deniedResult.error, "no candidate matched"));
}

int main() { return careweave::testing::runAll("test_gateway"); }
