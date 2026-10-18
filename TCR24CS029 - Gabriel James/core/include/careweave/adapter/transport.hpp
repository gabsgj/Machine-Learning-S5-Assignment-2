#pragma once
// Adapter transports.
//
// A transport performs the actual call of one provider capability and returns its outputs in
// the provider vocabulary. The base contract is deliberately small so every capability type
// from the specification has an honest implementation:
//
//   API, SERVICE   http         JSON over HTTP (cpp-httplib), the live module convention
//   GUI            form         HTML form encoded POST to the page action
//   DATABASE       sqlite       parameterized insert, update or select_one through the
//                               vendored SQLite C API, WAL mode
//   FILE           file         reads or writes a JSON document
//   COMPUTATION    computation  evaluates the adapter's arithmetic expressions over the inputs
//   FUNCTION       local        calls a handler registered in the process
//   EVENT, MESSAGE local        calls a handler registered in the process, so a workflow can
//                               run without a broker and the same adapter drives a broker in
//                               production by registering a publishing handler under the name
//
// Every transport returns the raw provider outputs; the runner renames them back afterwards.
#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "careweave/adapter/adapter.hpp"
#include "careweave/core/types.hpp"

namespace careweave {
namespace adapter {

struct TransportResult {
  bool ok = false;
  std::map<std::string, core::Value> outputs;
  std::string error;
  int status = 0;
  std::vector<std::string> trace;
};

class Transport {
 public:
  virtual ~Transport() = default;
  virtual TransportResult invoke(const AdapterDefinition& def,
                                 const std::map<std::string, core::Value>& payload) = 0;
  virtual std::string kind() const = 0;
};

// JSON over HTTP. Request: POST of the payload object to baseUrl + endpoint. Response
// convention: {"status":"ok","outputs":{...}} on success, {"status":"error","error":"..."} on
// failure. A body that is a bare JSON object without a status field is treated as the outputs,
// so a minimal endpoint remains callable; a non JSON body is an error.
class HttpTransport : public Transport {
 public:
  explicit HttpTransport(double timeoutSeconds = 15.0) : timeoutSeconds_(timeoutSeconds) {}
  TransportResult invoke(const AdapterDefinition& def,
                         const std::map<std::string, core::Value>& payload) override;
  std::string kind() const override { return "http"; }

 private:
  double timeoutSeconds_;
};

// HTML form encoded POST (GUI capabilities). Same response convention as HTTP.
class FormTransport : public Transport {
 public:
  explicit FormTransport(double timeoutSeconds = 15.0) : timeoutSeconds_(timeoutSeconds) {}
  TransportResult invoke(const AdapterDefinition& def,
                         const std::map<std::string, core::Value>& payload) override;
  std::string kind() const override { return "form"; }

 private:
  double timeoutSeconds_;
};

// Direct SQLite access through the vendored amalgamation. Operations:
//   insert      INSERT INTO table (columns) VALUES (?...), outputs row_id and rows_changed
//   update      UPDATE table SET non key columns WHERE key = ?, key is an input ending in _id
//   select_one  SELECT * WHERE every input matches, outputs the first row's columns
// The connection uses WAL mode and a busy timeout so it cooperates with the Flask writers.
class SqliteTransport : public Transport {
 public:
  TransportResult invoke(const AdapterDefinition& def,
                         const std::map<std::string, core::Value>& payload) override;
  std::string kind() const override { return "sqlite"; }
};

// Reads or writes one JSON document. write emits the payload object to filePath and outputs
// path and bytes; read loads the document and returns its top level entries as outputs.
class FileTransport : public Transport {
 public:
  TransportResult invoke(const AdapterDefinition& def,
                         const std::map<std::string, core::Value>& payload) override;
  std::string kind() const override { return "file"; }
};

// Evaluates the adapter's computations over the payload, left to right.
class ComputationTransport : public Transport {
 public:
  TransportResult invoke(const AdapterDefinition& def,
                         const std::map<std::string, core::Value>& payload) override;
  std::string kind() const override { return "computation"; }
};

using LocalHandler =
    std::function<TransportResult(const std::map<std::string, core::Value>& inputs)>;

class HandlerRegistry {
 public:
  void add(const std::string& name, LocalHandler handler);
  bool has(const std::string& name) const;
  // Returns an empty function when the name is unknown.
  LocalHandler get(const std::string& name) const;
  std::vector<std::string> namesSorted() const;

 private:
  std::map<std::string, LocalHandler> handlers_;
};

// Dispatches to a handler registered under def.handler.
class LocalTransport : public Transport {
 public:
  explicit LocalTransport(HandlerRegistry& registry) : registry_(registry) {}
  TransportResult invoke(const AdapterDefinition& def,
                         const std::map<std::string, core::Value>& payload) override;
  std::string kind() const override { return "local"; }

 private:
  HandlerRegistry& registry_;
};

// Builds the transport named by kind. `registry` may be null when no local transport is
// requested. Returns null for an unknown kind.
std::unique_ptr<Transport> makeTransport(const std::string& kind, HandlerRegistry* registry,
                                         double timeoutSeconds = 15.0);

}  // namespace adapter
}  // namespace careweave
