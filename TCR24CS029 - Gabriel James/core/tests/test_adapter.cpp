// Adapter tests: the closed transform registry, synthesis from real mapper output, execution
// over HTTP against a live in-process server, GUI form posting with percent encoding, SQLite
// insertion verified directly against the database file, computation expressions, file
// documents, local handler dispatch, JSON round trips, error propagation and compilation of an
// emitted C++ translation unit.
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include <unistd.h>

#include "careweave/adapter/adapter.hpp"
#include "careweave/adapter/cpp_emitter.hpp"
#include "careweave/adapter/expression.hpp"
#include "careweave/adapter/runner.hpp"
#include "careweave/adapter/synthesizer.hpp"
#include "careweave/adapter/transport.hpp"
#include "careweave/core/value_json.hpp"
#include "careweave/mapper/mapper.hpp"
#include "careweave/test/framework.hpp"
#include "httplib.h"
#include "nlohmann/json.hpp"
#include "sqlite3.h"

using careweave::adapter::AdapterDefinition;
using careweave::adapter::AdapterRunner;
using careweave::adapter::AdapterSynthesizer;
using careweave::adapter::ComputationTransport;
using careweave::adapter::FieldMapping;
using careweave::adapter::FileTransport;
using careweave::adapter::FormTransport;
using careweave::adapter::HandlerRegistry;
using careweave::adapter::HttpTransport;
using careweave::adapter::LocalTransport;
using careweave::adapter::SynthesisRequest;
using careweave::adapter::SynthesisResult;
using careweave::adapter::TransportResult;
using careweave::core::CapabilitySpec;
using careweave::core::CapabilityType;
using careweave::core::Effect;
using careweave::core::EffectOp;
using careweave::core::InputSpec;
using careweave::core::OutputSpec;
using careweave::core::Value;
using careweave::mapper::Mapper;
using careweave::mapper::MatchResult;

namespace {

Effect eff(const std::string& var, EffectOp op, Value v) {
  Effect e;
  e.variable = var;
  e.op = op;
  e.value = std::move(v);
  return e;
}

InputSpec in(const std::string& name, const std::string& type) {
  InputSpec s;
  s.name = name;
  s.type = type;
  return s;
}

OutputSpec out(const std::string& name, const std::string& type) {
  OutputSpec s;
  s.name = name;
  s.type = type;
  return s;
}

// The client requirement written in the alt vocabulary: register a patient, receive the
// registration number.
CapabilitySpec registerRequirement() {
  CapabilitySpec s;
  s.id = "REQ-1";
  s.name = "register_pat";
  s.description = "Register a new patient in the clinic registry";
  s.type = CapabilityType::API;
  s.inputs = {in("pat_no", "string"), in("pat_name", "string")};
  s.outputs = {out("pat_reg", "string")};
  s.effects = {eff("pat_reg.created", EffectOp::SET, Value(true))};
  return s;
}

// The alt module capability. The same vocabulary, so the transform evidence is unambiguous.
CapabilitySpec patRegCapability() {
  CapabilitySpec s;
  s.id = "PA-Register";
  s.name = "Pat_reg";
  s.description = "Create a patient registration record";
  s.type = CapabilityType::API;
  s.inputs = {in("pat_no", "string"), in("pat_name", "string")};
  s.outputs = {out("pat_reg", "string")};
  s.effects = {eff("pat_reg.created", EffectOp::SET, Value(true))};
  return s;
}

// A rival registry with the clinical vocabulary, used to keep the ranking honest.
CapabilitySpec registerPatientMain() {
  CapabilitySpec s;
  s.id = "PR-Register";
  s.name = "RegisterPatient";
  s.description = "Register a patient and assign a medical record number";
  s.type = CapabilityType::API;
  s.inputs = {in("mrn", "string"), in("full_name", "string")};
  s.outputs = {out("patient_id", "string")};
  s.effects = {eff("Patient.registered", EffectOp::SET, Value(true))};
  return s;
}

CapabilitySpec generateInvoice() {
  CapabilitySpec s;
  s.id = "BILL-GenerateInvoice";
  s.name = "GenerateInvoice";
  s.description = "Produce an invoice for a completed visit";
  s.type = CapabilityType::API;
  s.inputs = {in("visit_id", "string")};
  s.outputs = {out("invoice_id", "string")};
  s.effects = {eff("Invoice.exists", EffectOp::SET, Value(true))};
  return s;
}

// Runs the real mapper and returns the synthesis for `cand` alone, asserting the selection.
SynthesisResult synthesizeOne(const CapabilitySpec& req, const CapabilitySpec& cand,
                              const std::string& baseUrl, const std::string& databasePath = "",
                              const std::string& fileOperation = "") {
  const Mapper mapper;
  const std::vector<MatchResult> ranked = mapper.rank(req, {cand});
  const Mapper::Selection selection = mapper.select(ranked);
  CW_CHECK_MSG(selection.bestIndex == 0, "candidate did not pass the mapper threshold");
  SynthesisRequest request;
  request.requirement = req;
  request.match = ranked[0];
  request.candidate = cand;
  request.targetModule = "test-module";
  request.baseUrl = baseUrl;
  request.databasePath = databasePath;
  request.fileOperation = fileOperation;
  const AdapterSynthesizer synthesizer;
  return synthesizer.synthesize(request);
}

bool traceHas(const std::vector<std::string>& trace, const std::string& needle) {
  for (const auto& line : trace) {
    if (line.find(needle) != std::string::npos) return true;
  }
  return false;
}

bool anyContains(const std::vector<std::string>& errors, const std::string& needle) {
  for (const auto& line : errors) {
    if (line.find(needle) != std::string::npos) return true;
  }
  return false;
}

struct TempWorkspace {
  std::filesystem::path dir;
  TempWorkspace() {
    dir = std::filesystem::temp_directory_path() /
          ("careweave_adapter_" + std::to_string(static_cast<long long>(::getpid())));
    std::error_code ec;
    std::filesystem::remove_all(dir, ec);
    std::filesystem::create_directories(dir);
  }
  ~TempWorkspace() {
    std::error_code ec;
    std::filesystem::remove_all(dir, ec);
  }
};

TempWorkspace& workspace() {
  static TempWorkspace w;
  return w;
}

// A real HTTP server on an ephemeral port, speaking the module response convention.
class MockServer {
 public:
  MockServer() {
    server_.Post("/patients/register", [](const httplib::Request& req, httplib::Response& res) {
      const nlohmann::json body = nlohmann::json::parse(req.body, nullptr, false);
      if (body.is_discarded() || !body.contains("pat_no")) {
        res.status = 400;
        res.set_content("{\"status\":\"error\",\"error\":\"pat_no is required\"}",
                        "application/json");
        return;
      }
      const std::string registration = "REG-" + body["pat_no"].get<std::string>();
      nlohmann::json reply = {{"status", "ok"}, {"outputs", {{"pat_reg", registration}}}};
      res.set_content(reply.dump(), "application/json");
    });
    server_.Post("/patients/fail", [](const httplib::Request&, httplib::Response& res) {
      res.status = 409;
      res.set_content("{\"status\":\"error\",\"error\":\"patient already registered\"}",
                      "application/json");
    });
    server_.Post("/ui/patient-form", [](const httplib::Request& req, httplib::Response& res) {
      const std::string patNo = req.get_param_value("pat_no");
      const std::string patName = req.get_param_value("pat_name");
      if (patNo.empty()) {
        res.status = 400;
        res.set_content("{\"status\":\"error\",\"error\":\"pat_no is required\"}",
                        "application/json");
        return;
      }
      nlohmann::json reply = {{"status", "ok"},
                              {"outputs",
                               {{"pat_reg", "FORM-" + patNo}, {"seen_name", patName}}}};
      res.set_content(reply.dump(), "application/json");
    });
    port_ = server_.bind_to_any_port("127.0.0.1");
    thread_ = std::thread([this] { server_.listen_after_bind(); });
    server_.wait_until_ready();
  }
  ~MockServer() {
    server_.stop();
    if (thread_.joinable()) thread_.join();
  }
  std::string url() const { return "http://127.0.0.1:" + std::to_string(port_); }

 private:
  httplib::Server server_;
  int port_ = 0;
  std::thread thread_;
};

}  // namespace

CW_TEST_CASE(transforms_behave_strictly) {
  Value converted;
  std::string err;
  CW_CHECK(careweave::adapter::applyTransform("identity", Value(7), &converted, &err));
  CW_CHECK(converted == Value(7));
  CW_CHECK(careweave::adapter::applyTransform("to_string", Value(42), &converted, &err));
  CW_CHECK(converted.asString() == "42");
  CW_CHECK(careweave::adapter::applyTransform("to_int", Value(std::string("17")), &converted, &err));
  CW_CHECK(converted.asInt() == 17);
  err.clear();
  CW_CHECK(!careweave::adapter::applyTransform("to_int", Value(std::string("17.5")), &converted, &err));
  CW_CHECK(err.find("not an integer") != std::string::npos);
  CW_CHECK(careweave::adapter::applyTransform("to_int", Value(3.9), &converted, &err));
  CW_CHECK(converted.asInt() == 3);
  CW_CHECK(careweave::adapter::applyTransform("to_real", Value(std::string("2.5")), &converted, &err));
  CW_CHECK_NEAR(converted.asDouble(), 2.5, 1e-12);
  CW_CHECK(careweave::adapter::applyTransform("to_bool", Value(std::string(" TRUE ")), &converted, &err));
  CW_CHECK(converted.asBool());
  CW_CHECK(careweave::adapter::applyTransform("to_bool", Value(0), &converted, &err));
  CW_CHECK(!converted.asBool());
  CW_CHECK(!careweave::adapter::applyTransform("to_bool", Value(std::string("maybe")), &converted, &err));
  CW_CHECK(careweave::adapter::applyTransform("lowercase", Value(std::string("Ada")), &converted, &err));
  CW_CHECK(converted.asString() == "ada");
  CW_CHECK(careweave::adapter::applyTransform("uppercase", Value(std::string("Ada")), &converted, &err));
  CW_CHECK(converted.asString() == "ADA");
  CW_CHECK(careweave::adapter::applyTransform("trim", Value(std::string("  Ada Lovelace  ")), &converted, &err));
  CW_CHECK(converted.asString() == "Ada Lovelace");
  CW_CHECK(!careweave::adapter::applyTransform("lowercase", Value(3), &converted, &err));
  CW_CHECK(!careweave::adapter::applyTransform("explode", Value(3), &converted, &err));
  CW_CHECK(careweave::adapter::isKnownTransform("to_int"));
  CW_CHECK(!careweave::adapter::isKnownTransform("explode"));
}

CW_TEST_CASE(choose_transform_follows_the_provider_type) {
  using careweave::adapter::chooseTransform;
  CW_CHECK(chooseTransform("string", "string") == "identity");
  CW_CHECK(chooseTransform("integer", "integer") == "identity");
  CW_CHECK(chooseTransform("string", "integer") == "to_int");
  CW_CHECK(chooseTransform("integer", "string") == "to_string");
  CW_CHECK(chooseTransform("real", "integer") == "to_int");
  CW_CHECK(chooseTransform("bool", "boolean") == "identity");
  CW_CHECK(chooseTransform("categorical", "string") == "to_string");
  CW_CHECK(chooseTransform("string", "list").empty());
  CW_CHECK(chooseTransform("list", "string").empty());
}

CW_TEST_CASE(synthesis_from_real_mapper_output) {
  const CapabilitySpec req = registerRequirement();
  CapabilitySpec cand = patRegCapability();
  cand.mechanism.endpoint = "/patients/register";
  const Mapper mapper;
  const std::vector<CapabilitySpec> candidates = {registerPatientMain(), cand, generateInvoice()};
  const std::vector<MatchResult> ranked = mapper.rank(req, candidates);
  const Mapper::Selection selection = mapper.select(ranked);
  CW_CHECK(selection.bestIndex == 0);
  CW_CHECK(!selection.ambiguous);
  CW_CHECK(ranked[0].candidateId == "PA-Register");

  SynthesisRequest request;
  request.requirement = req;
  request.match = ranked[0];
  request.candidate = cand;
  request.targetModule = "patient-registry-alt";
  request.baseUrl = "http://127.0.0.1:5007";
  const AdapterSynthesizer synthesizer;
  const SynthesisResult synth = synthesizer.synthesize(request);
  CW_CHECK_MSG(synth.ok, synth.render());
  CW_CHECK(synth.errors.empty());
  const AdapterDefinition& adapter = synth.adapter;
  CW_CHECK(adapter.id == "adapter-register_pat-to-Pat_reg");
  CW_CHECK(adapter.transportKind == "http");
  CW_CHECK(adapter.method == "POST");
  CW_CHECK(adapter.baseUrl == "http://127.0.0.1:5007");
  CW_CHECK(adapter.endpoint == "/patients/register");
  CW_CHECK(adapter.targetCapabilityId == "PA-Register");
  CW_CHECK(adapter.targetModule == "patient-registry-alt");
  CW_CHECK(adapter.requirementId == "REQ-1");
  const std::vector<FieldMapping> expectedInputs = {{"pat_no", "pat_no", "identity"},
                                                    {"pat_name", "pat_name", "identity"}};
  CW_CHECK(adapter.inputMap == expectedInputs);
  const std::vector<FieldMapping> expectedOutputs = {{"pat_reg", "pat_reg", "identity"}};
  CW_CHECK(adapter.outputMap == expectedOutputs);
  CW_CHECK_NEAR(adapter.confidence, ranked[0].total, 1e-12);
  CW_CHECK(adapter.confidence > 0.5);
  CW_CHECK(!adapter.explanation.empty());
  const std::string rendered = adapter.render();
  CW_CHECK(rendered.find("http POST http://127.0.0.1:5007/patients/register") != std::string::npos);
  CW_CHECK(rendered.find("pat_no -> pat_no (identity)") != std::string::npos);
}

CW_TEST_CASE(synthesis_refuses_incomplete_bindings) {
  const CapabilitySpec req = registerRequirement();

  // A required provider input that nothing binds.
  CapabilitySpec extra = patRegCapability();
  extra.mechanism.endpoint = "/patients/register";
  extra.inputs.push_back(in("site_code", "string"));
  const SynthesisResult unbound = synthesizeOne(req, extra, "http://127.0.0.1:5007");
  CW_CHECK(!unbound.ok);
  CW_CHECK(anyContains(unbound.errors, "site_code"));

  // An input type that cannot be converted without dropping data.
  CapabilitySpec listy = patRegCapability();
  listy.mechanism.endpoint = "/patients/register";
  listy.inputs[0].type = "list";
  const SynthesisResult incompatible = synthesizeOne(req, listy, "http://127.0.0.1:5007");
  CW_CHECK(!incompatible.ok);
  CW_CHECK(anyContains(incompatible.errors, "cannot convert"));

  // An API candidate without a base URL.
  CapabilitySpec api = patRegCapability();
  api.mechanism.endpoint = "/patients/register";
  const SynthesisResult noUrl = synthesizeOne(req, api, "");
  CW_CHECK(!noUrl.ok);
  CW_CHECK(anyContains(noUrl.errors, "base URL"));
}

CW_TEST_CASE(adapter_json_round_trip) {
  const CapabilitySpec req = registerRequirement();
  CapabilitySpec cand = patRegCapability();
  cand.mechanism.endpoint = "/patients/register";
  const SynthesisResult synth = synthesizeOne(req, cand, "http://127.0.0.1:5007");
  CW_CHECK_MSG(synth.ok, synth.render());
  const AdapterDefinition& adapter = synth.adapter;

  const std::string pretty = careweave::adapter::toJsonString(adapter, true);
  AdapterDefinition reparsed;
  std::string err;
  CW_CHECK_MSG(careweave::adapter::parseAdapter(pretty, &reparsed, &err), err);
  CW_CHECK(reparsed == adapter);

  const std::string compact = careweave::adapter::toJsonString(adapter, false);
  AdapterDefinition reparsedCompact;
  CW_CHECK(careweave::adapter::parseAdapter(compact, &reparsedCompact, &err));
  CW_CHECK(reparsedCompact == adapter);

  // An unknown transform is rejected instead of being carried into a runtime surprise.
  std::string badTransform = pretty;
  const size_t identityPos = badTransform.find("\"identity\"");
  CW_CHECK(identityPos != std::string::npos);
  badTransform.replace(identityPos, 10, "\"teleport\"");
  AdapterDefinition ignored;
  err.clear();
  CW_CHECK(!careweave::adapter::parseAdapter(badTransform, &ignored, &err));
  CW_CHECK(err.find("unknown transform") != std::string::npos);

  // An unknown transport kind is rejected.
  std::string badKind = pretty;
  const size_t kindPos = badKind.find("\"http\"");
  CW_CHECK(kindPos != std::string::npos);
  badKind.replace(kindPos, 6, "\"carrier_pigeon\"");
  err.clear();
  CW_CHECK(!careweave::adapter::parseAdapter(badKind, &ignored, &err));
  CW_CHECK(err.find("unknown transport kind") != std::string::npos);

  // Malformed JSON is rejected with the parse reason.
  err.clear();
  CW_CHECK(!careweave::adapter::parseAdapter("{not json", &ignored, &err));
  CW_CHECK(err.find("invalid JSON") != std::string::npos);
}

CW_TEST_CASE(http_round_trip_against_live_server) {
  MockServer server;
  CapabilitySpec cand = patRegCapability();
  cand.mechanism.endpoint = "/patients/register";
  const SynthesisResult synth = synthesizeOne(registerRequirement(), cand, server.url());
  CW_CHECK_MSG(synth.ok, synth.render());

  HttpTransport transport;
  AdapterRunner runner(transport);
  const careweave::adapter::AdapterResult result =
      runner.run(synth.adapter, {{"pat_no", "P-100"}, {"pat_name", "Ada Lovelace"}});
  CW_CHECK_MSG(result.ok, result.error);
  if (!result.ok) return;
  CW_CHECK(result.outputs.at("pat_reg").asString() == "REG-P-100");
  CW_CHECK(result.status == 200);
  CW_CHECK(traceHas(result.trace, "input pat_no -> pat_no (identity) value=P-100"));
  CW_CHECK(traceHas(result.trace, "http POST " + server.url() + "/patients/register"));
  CW_CHECK(traceHas(result.trace, "output pat_reg -> pat_reg (identity) value=REG-P-100"));

  // Missing inputs and inputs the adapter does not bind are refused before any call.
  const careweave::adapter::AdapterResult missing = runner.run(synth.adapter, {{"pat_no", "P-1"}});
  CW_CHECK(!missing.ok);
  CW_CHECK(missing.error.find("missing requirement input \"pat_name\"") != std::string::npos);
  const careweave::adapter::AdapterResult extra =
      runner.run(synth.adapter, {{"pat_no", "P-1"}, {"pat_name", "Ada"}, {"bogus", "x"}});
  CW_CHECK(!extra.ok);
  CW_CHECK(extra.error.find("not bound by this adapter") != std::string::npos);

  // The provider error propagates with its message and status.
  CapabilitySpec failing = patRegCapability();
  failing.mechanism.endpoint = "/patients/fail";
  const SynthesisResult failSynth = synthesizeOne(registerRequirement(), failing, server.url());
  CW_CHECK(failSynth.ok);
  const careweave::adapter::AdapterResult failed =
      runner.run(failSynth.adapter, {{"pat_no", "P-1"}, {"pat_name", "Ada"}});
  CW_CHECK(!failed.ok);
  CW_CHECK(failed.status == 409);
  CW_CHECK(failed.error == "patient already registered");
}

CW_TEST_CASE(gui_form_round_trip) {
  MockServer server;
  CapabilitySpec req = registerRequirement();
  req.outputs.push_back(out("seen_name", "string"));
  CapabilitySpec cand = patRegCapability();
  cand.type = CapabilityType::GUI;
  cand.mechanism.page = "/ui/patient-form";
  cand.outputs.push_back(out("seen_name", "string"));
  const SynthesisResult synth = synthesizeOne(req, cand, server.url());
  CW_CHECK_MSG(synth.ok, synth.render());
  CW_CHECK(synth.adapter.transportKind == "form");
  CW_CHECK(synth.adapter.endpoint == "/ui/patient-form");

  FormTransport transport;
  AdapterRunner runner(transport);
  const careweave::adapter::AdapterResult result =
      runner.run(synth.adapter, {{"pat_no", "P-1"}, {"pat_name", "Ada Lovelace"}});
  CW_CHECK_MSG(result.ok, result.error);
  if (!result.ok) return;
  CW_CHECK(result.outputs.at("pat_reg").asString() == "FORM-P-1");
  // The space survived percent encoding and decoding on the server side.
  CW_CHECK(result.outputs.at("seen_name").asString() == "Ada Lovelace");
  CW_CHECK(traceHas(result.trace, "form POST " + server.url() + "/ui/patient-form"));
}

CW_TEST_CASE(sqlite_transport_inserts_verifiably) {
  const std::string dbPath = (workspace().dir / "alt_registry.db").string();
  sqlite3* db = nullptr;
  CW_CHECK(sqlite3_open(dbPath.c_str(), &db) == SQLITE_OK);
  CW_CHECK(sqlite3_exec(db, "CREATE TABLE patients (pat_no TEXT NOT NULL, pat_name TEXT NOT NULL);",
                        nullptr, nullptr, nullptr) == SQLITE_OK);
  sqlite3_close(db);

  CapabilitySpec req;
  req.id = "REQ-ROW";
  req.name = "register_row_pat";
  req.description = "Register a patient registration record";
  req.inputs = {in("pat_no", "string"), in("pat_name", "string")};
  req.outputs = {out("row_id", "integer")};
  req.effects = {eff("pat_reg.created", EffectOp::SET, Value(true))};

  CapabilitySpec cand;
  cand.id = "PA-RowWrite";
  cand.name = "Pat_reg";
  cand.description = "Create a patient registration record row";
  cand.type = CapabilityType::DATABASE;
  cand.inputs = {in("pat_no", "string"), in("pat_name", "string")};
  cand.outputs = {out("row_id", "integer")};
  cand.effects = {eff("pat_reg.created", EffectOp::SET, Value(true))};
  cand.mechanism.operation = "insert";
  cand.mechanism.table = "patients";

  const SynthesisResult synth = synthesizeOne(req, cand, "", dbPath);
  CW_CHECK_MSG(synth.ok, synth.render());
  CW_CHECK(synth.adapter.transportKind == "sqlite");
  CW_CHECK(synth.adapter.operation == "insert");

  careweave::adapter::SqliteTransport transport;
  AdapterRunner runner(transport);
  const careweave::adapter::AdapterResult result =
      runner.run(synth.adapter, {{"pat_no", "P-9"}, {"pat_name", "Ada"}});
  CW_CHECK_MSG(result.ok, result.error);
  if (!result.ok) return;
  CW_CHECK(result.outputs.at("row_id").asInt() == 1);
  CW_CHECK(result.providerOutputs.at("rows_changed").asInt() == 1);

  // Direct database verification: the row is really there, with the bound values.
  sqlite3* check = nullptr;
  CW_CHECK(sqlite3_open(dbPath.c_str(), &check) == SQLITE_OK);
  sqlite3_stmt* stmt = nullptr;
  CW_CHECK(sqlite3_prepare_v2(check, "SELECT pat_no, pat_name FROM patients;", -1, &stmt, nullptr) ==
           SQLITE_OK);
  CW_CHECK(sqlite3_step(stmt) == SQLITE_ROW);
  const std::string storedNo(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0)));
  const std::string storedName(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 1)));
  CW_CHECK(storedNo == "P-9");
  CW_CHECK(storedName == "Ada");
  sqlite3_finalize(stmt);
  sqlite3_close(check);
}

CW_TEST_CASE(computation_adapters_evaluate_and_fail_loudly) {
  CapabilitySpec req;
  req.id = "REQ-COMPUTE";
  req.name = "quote_pat_cost";
  req.description = "Compute the cost of a patient visit";
  req.inputs = {in("pat_qty", "integer"), in("pat_price", "real")};
  req.outputs = {out("total", "real")};

  CapabilitySpec cand;
  cand.id = "PA-Cost";
  cand.name = "Pat_cost";
  cand.description = "Compute the cost of a patient visit total";
  cand.type = CapabilityType::COMPUTATION;
  cand.inputs = {in("pat_qty", "integer"), in("pat_price", "real")};
  cand.outputs = {out("total", "real")};
  cand.mechanism.expression = "total = pat_qty * pat_price";

  const SynthesisResult synth = synthesizeOne(req, cand, "");
  CW_CHECK_MSG(synth.ok, synth.render());
  CW_CHECK(synth.adapter.transportKind == "computation");
  CW_CHECK(synth.adapter.computations.size() == 1);

  ComputationTransport transport;
  AdapterRunner runner(transport);
  const careweave::adapter::AdapterResult result =
      runner.run(synth.adapter, {{"pat_qty", 3}, {"pat_price", 2.5}});
  CW_CHECK_MSG(result.ok, result.error);
  if (!result.ok) return;
  CW_CHECK_NEAR(result.outputs.at("total").asDouble(), 7.5, 1e-9);

  // An expression that names a variable the payload cannot supply is refused at synthesis.
  CapabilitySpec badVar = cand;
  badVar.mechanism.expression = "total = missing_var * 2";
  const SynthesisResult badVarSynth = synthesizeOne(req, badVar, "");
  CW_CHECK(!badVarSynth.ok);
  CW_CHECK(anyContains(badVarSynth.errors, "unknown variable"));

  // A malformed expression is refused at synthesis.
  CapabilitySpec malformed = cand;
  malformed.mechanism.expression = "total = pat_qty *";
  const SynthesisResult malformedSynth = synthesizeOne(req, malformed, "");
  CW_CHECK(!malformedSynth.ok);
  CW_CHECK(anyContains(malformedSynth.errors, "unexpected end of expression"));

  // Division by zero is a runtime error, not infinity.
  CapabilitySpec divider = cand;
  divider.mechanism.expression = "total = pat_qty / pat_price";
  const SynthesisResult dividerSynth = synthesizeOne(req, divider, "");
  CW_CHECK(dividerSynth.ok);
  const careweave::adapter::AdapterResult division =
      runner.run(dividerSynth.adapter, {{"pat_qty", 1}, {"pat_price", 0.0}});
  CW_CHECK(!division.ok);
  CW_CHECK(division.error.find("division by zero") != std::string::npos);

  // Direct evaluator checks: precedence, parentheses and functions.
  double value = 0.0;
  std::string err;
  const std::map<std::string, Value> vars = {{"a", Value(3)}, {"b", Value(4)}};
  CW_CHECK(careweave::adapter::evaluateExpression("a + b * 2", vars, &value, &err));
  CW_CHECK_NEAR(value, 11.0, 1e-12);
  CW_CHECK(careweave::adapter::evaluateExpression("(a + b) * 2", vars, &value, &err));
  CW_CHECK_NEAR(value, 14.0, 1e-12);
  CW_CHECK(careweave::adapter::evaluateExpression("min(a, b) + sqrt(b * b)", vars, &value, &err));
  CW_CHECK_NEAR(value, 7.0, 1e-12);
}

CW_TEST_CASE(file_adapters_write_and_read_documents) {
  const std::string filePath = (workspace().dir / "patient_document.json").string();

  CapabilitySpec writeReq;
  writeReq.id = "REQ-WRITE-DOC";
  writeReq.name = "store_pat_doc";
  writeReq.description = "Store a patient document";
  writeReq.inputs = {in("pat_no", "string"), in("pat_name", "string")};
  writeReq.outputs = {out("path", "string"), out("bytes", "integer")};

  CapabilitySpec writeCand;
  writeCand.id = "DOC-Write";
  writeCand.name = "Pat_doc";
  writeCand.description = "Store a patient document as a JSON record";
  writeCand.type = CapabilityType::FILE;
  writeCand.inputs = {in("pat_no", "string"), in("pat_name", "string")};
  writeCand.outputs = {out("path", "string"), out("bytes", "integer")};
  writeCand.mechanism.path = filePath;
  writeCand.mechanism.format = "json";

  const SynthesisResult writeSynth = synthesizeOne(writeReq, writeCand, "");
  CW_CHECK_MSG(writeSynth.ok, writeSynth.render());
  CW_CHECK(writeSynth.adapter.transportKind == "file");
  CW_CHECK(writeSynth.adapter.fileOperation == "write");

  FileTransport transport;
  AdapterRunner runner(transport);
  const careweave::adapter::AdapterResult written =
      runner.run(writeSynth.adapter, {{"pat_no", "P-42"}, {"pat_name", "Ada"}});
  CW_CHECK_MSG(written.ok, written.error);
  if (!written.ok) return;
  CW_CHECK(written.outputs.at("path").asString() == filePath);
  CW_CHECK(written.outputs.at("bytes").asInt() > 0);

  std::ifstream in(filePath, std::ios::binary);
  CW_CHECK(in.is_open());
  std::ostringstream buffer;
  buffer << in.rdbuf();
  const nlohmann::json document = nlohmann::json::parse(buffer.str(), nullptr, false);
  CW_CHECK(!document.is_discarded());
  CW_CHECK(document["pat_no"].get<std::string>() == "P-42");

  // The read variant loads the document back through the adapter pipeline.
  CapabilitySpec readReq;
  readReq.id = "REQ-READ-DOC";
  readReq.name = "load_pat_doc";
  readReq.description = "Load a patient document";
  readReq.outputs = {out("pat_no", "string"), out("pat_name", "string")};

  CapabilitySpec readCand;
  readCand.id = "DOC-Read";
  readCand.name = "Pat_doc";
  readCand.description = "Load a patient document from a JSON record";
  readCand.type = CapabilityType::FILE;
  readCand.outputs = {out("pat_no", "string"), out("pat_name", "string")};
  readCand.mechanism.path = filePath;
  readCand.mechanism.format = "json";

  const SynthesisResult readSynth = synthesizeOne(readReq, readCand, "", "", "read");
  CW_CHECK_MSG(readSynth.ok, readSynth.render());
  CW_CHECK(readSynth.adapter.fileOperation == "read");
  const careweave::adapter::AdapterResult loaded = runner.run(readSynth.adapter, {});
  CW_CHECK_MSG(loaded.ok, loaded.error);
  if (!loaded.ok) return;
  CW_CHECK(loaded.outputs.at("pat_no").asString() == "P-42");
  CW_CHECK(loaded.outputs.at("pat_name").asString() == "Ada");
}

CW_TEST_CASE(local_handlers_dispatch_by_name) {
  CapabilitySpec req;
  req.id = "REQ-EVENT";
  req.name = "pat_registered_evt";
  req.description = "Notify that a patient registration record was created";
  req.outputs = {out("accepted", "boolean")};
  req.effects = {eff("pat_reg.created", EffectOp::SET, Value(true))};

  CapabilitySpec cand;
  cand.id = "EVT-PatRegistered";
  cand.name = "Pat_reg_evt";
  cand.description = "Registration event notification for a patient record";
  cand.type = CapabilityType::EVENT;
  cand.outputs = {out("accepted", "boolean")};
  cand.effects = {eff("pat_reg.created", EffectOp::SET, Value(true))};
  cand.mechanism.handler = "patient.registered";

  const SynthesisResult synth = synthesizeOne(req, cand, "");
  CW_CHECK_MSG(synth.ok, synth.render());
  CW_CHECK(synth.adapter.transportKind == "local");
  CW_CHECK(synth.adapter.handler == "patient.registered");

  HandlerRegistry registry;
  registry.add("patient.registered", [](const std::map<std::string, Value>&) {
    TransportResult r;
    r.ok = true;
    r.outputs["accepted"] = Value(true);
    r.trace.push_back("event fired");
    return r;
  });
  CW_CHECK(registry.has("patient.registered"));
  CW_CHECK(!registry.has("nope"));

  LocalTransport transport(registry);
  AdapterRunner runner(transport);
  const careweave::adapter::AdapterResult result = runner.run(synth.adapter, {});
  CW_CHECK_MSG(result.ok, result.error);
  if (!result.ok) return;
  CW_CHECK(result.outputs.at("accepted").asBool());
  CW_CHECK(traceHas(result.trace, "local handler patient.registered"));

  HandlerRegistry empty;
  LocalTransport bare(empty);
  AdapterRunner bareRunner(bare);
  const careweave::adapter::AdapterResult missing = bareRunner.run(synth.adapter, {});
  CW_CHECK(!missing.ok);
  CW_CHECK(missing.error.find("no local handler registered") != std::string::npos);
}

CW_TEST_CASE(emitted_cpp_compiles_against_the_public_header) {
  CapabilitySpec cand = patRegCapability();
  cand.mechanism.endpoint = "/patients/register";
  const SynthesisResult synth = synthesizeOne(registerRequirement(), cand, "http://127.0.0.1:5007");
  CW_CHECK(synth.ok);
  const std::string code = careweave::adapter::emitAdapterCpp(synth.adapter);
  CW_CHECK(code.find(careweave::adapter::emittedFunctionName(synth.adapter)) != std::string::npos);
  CW_CHECK(code.find(synth.adapter.id) != std::string::npos);
  CW_CHECK(code.find("careweave/adapter/adapter.hpp") != std::string::npos);

  const std::string path = (workspace().dir / "generated_adapter.cpp").string();
  std::ofstream out(path, std::ios::binary | std::ios::trunc);
  out << code;
  out.close();

  const std::string command = "c++ -std=c++17 -fsyntax-only -I \"" +
                              std::string(CAREWEAVE_CORE_DIR) + "/include\" \"" + path + "\"";
  const int status = std::system(command.c_str());
  CW_CHECK_MSG(status == 0, "emitted translation unit failed to compile");
}

CW_TEST_CASE(optional_requirement_inputs_may_be_omitted) {
  // The requirement declares pat_name optional and so does the provider. The synthesized input
  // map carries the optionality, the runner skips the omitted field instead of failing, the
  // JSON round trip keeps the definition identical and emits the flag only when it is false.
  CapabilitySpec requirement = registerRequirement();
  requirement.inputs[1].required = false;  // pat_name
  CapabilitySpec candidate = patRegCapability();
  candidate.inputs[1].required = false;
  candidate.mechanism.endpoint = "/patients/register";
  const SynthesisResult synth = synthesizeOne(requirement, candidate, "http://127.0.0.1:5007");
  CW_CHECK_MSG(synth.ok, synth.render());
  CW_CHECK(synth.adapter.inputMap.size() == 2);
  if (synth.adapter.inputMap.size() == 2) {
    CW_CHECK(synth.adapter.inputMap[0].required);
    CW_CHECK(!synth.adapter.inputMap[1].required);
  }

  MockServer server;
  AdapterDefinition def = synth.adapter;
  def.baseUrl = server.url();
  def.endpoint = "/patients/register";
  def.transportKind = "http";
  HttpTransport transport(5.0);
  AdapterRunner runner(transport);

  const careweave::adapter::AdapterResult omitted =
      runner.run(def, {{"pat_no", Value(std::string("7"))}});
  CW_CHECK_MSG(omitted.ok, omitted.error);
  CW_CHECK(omitted.transportAttempted);
  CW_CHECK(omitted.outputs.count("pat_reg") == 1);
  if (omitted.outputs.count("pat_reg") == 1) {
    CW_CHECK(omitted.outputs.at("pat_reg").asString() == "REG-7");
  }

  const std::string json = careweave::adapter::toJsonString(def);
  CW_CHECK(json.find("\"required\": false") != std::string::npos);
  AdapterDefinition reloaded;
  std::string error;
  CW_CHECK(careweave::adapter::parseAdapter(json, &reloaded, &error));
  CW_CHECK(reloaded == def);

  // A missing required input still stops the run before any transport attempt.
  const careweave::adapter::AdapterResult missing = runner.run(def, {});
  CW_CHECK(!missing.ok);
  CW_CHECK(!missing.transportAttempted);
  CW_CHECK(missing.error.find("missing requirement input") != std::string::npos);
}

int main() { return careweave::testing::runAll("test_adapter"); }
