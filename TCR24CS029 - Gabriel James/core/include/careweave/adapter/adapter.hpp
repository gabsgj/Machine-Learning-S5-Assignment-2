#pragma once
// Adapter definition model.
//
// An adapter binds one client requirement capability template to one concrete provider
// capability. It carries the renamed and transformed inputs, the output renaming back to the
// requirement vocabulary, the transport that performs the call, and the evidence that produced
// it (confidence and explanation lines). Adapters are data: they round trip through JSON, and a
// generated C++ translation unit can materialize the same definition inside a host program.
//
// Field transforms are a closed, deterministic registry: identity, to_string, to_int, to_real,
// to_bool, lowercase, uppercase, trim. Synthesis rejects unknown transform names, and so does
// parsing, so a malformed adapter file fails loudly instead of degrading silently.
#include <map>
#include <string>
#include <utility>
#include <vector>

#include "careweave/core/types.hpp"

namespace careweave {
namespace adapter {

// One rename plus transform. For inputs `from` is the requirement input and `to` is the provider
// input; for outputs `from` is the provider output and `to` is the requirement output. `required`
// is only meaningful on input mappings: when the requirement declares the input optional, the
// runner skips it instead of failing the call when the caller omits it.
struct FieldMapping {
  std::string from;
  std::string to;
  std::string transform = "identity";
  bool required = true;

  bool operator==(const FieldMapping& o) const {
    return from == o.from && to == o.to && transform == o.transform &&
           required == o.required;
  }
  bool operator!=(const FieldMapping& o) const { return !(*this == o); }
  std::string render() const;
};

struct AdapterDefinition {
  std::string id;
  std::string requirementId;
  std::string requirementName;
  std::string targetModule;
  std::string targetCapabilityId;
  std::string targetCapabilityName;
  // One of: http, form, sqlite, file, computation, local.
  std::string transportKind;
  // HTTP and form transports.
  std::string baseUrl;
  std::string endpoint;
  std::string method = "POST";
  // SQLite transport.
  std::string sqlitePath;
  std::string table;
  // insert, update or select_one.
  std::string operation;
  // File transport.
  std::string filePath;
  // write or read.
  std::string fileOperation = "write";
  std::string fileFormat = "json";
  // Computation transport: output name to arithmetic expression, evaluated left to right over
  // the provider inputs plus earlier computation outputs.
  std::vector<std::pair<std::string, std::string>> computations;
  // Local transport: registered handler name.
  std::string handler;
  std::vector<FieldMapping> inputMap;
  std::vector<FieldMapping> outputMap;
  double confidence = 0.0;
  std::vector<std::string> explanation;

  bool operator==(const AdapterDefinition& o) const;
  bool operator!=(const AdapterDefinition& o) const { return !(*this == o); }
  // Human readable rendering used by the mapping studio, the command line tool and the logs.
  std::string render() const;
};

// ---- Field transform registry ----

const std::vector<std::string>& knownTransforms();
bool isKnownTransform(const std::string& name);
// Applies a transform. Returns false and fills `err` on unknown names or values that cannot be
// converted (for example to_int on "abc"). Never guesses: a bad conversion is an error.
bool applyTransform(const std::string& name, const core::Value& in, core::Value* out,
                    std::string* err);

// ---- JSON round trip ----

const std::vector<std::string>& knownTransportKinds();
std::string toJsonString(const AdapterDefinition& def, bool pretty = true);
bool parseAdapter(const std::string& json, AdapterDefinition* out, std::string* err);

}  // namespace adapter
}  // namespace careweave
