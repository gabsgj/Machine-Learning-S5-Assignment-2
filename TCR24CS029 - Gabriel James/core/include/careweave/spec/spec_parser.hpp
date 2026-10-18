#pragma once
// Specification parser.
//
// Reads a formal capability specification sheet from JSON or YAML, validates it against
// specs/capability.schema.json, checks the semantics that the schema cannot express
// (references from conditions and effects to declared state variables, mechanism and type
// agreement, initial state coverage) and produces a typed core::ApplicationModel.
//
// Every failure is reported with the origin file, a JSON pointer style path and a reason.
#include <string>
#include <vector>

#include "careweave/core/types.hpp"
#include "careweave/spec/json_schema.hpp"
#include "nlohmann/json.hpp"

namespace careweave {
namespace spec {

struct SpecParseOptions {
  // Validate against the JSON Schema document. The schema itself is looked up in this order:
  // an explicit schemaPath, then <repo>/specs/capability.schema.json discovered by walking up
  // from the specification file, then no schema validation (reported as a warning).
  std::string schemaPath;
  bool requireSchema = false;
  // Reject specifications whose conditions reference variables outside the declared state
  // schema. Enabled by default because the encoder depends on it.
  bool strictVariables = true;
};

struct SpecParseResult {
  bool ok = false;
  core::ApplicationModel model;
  std::vector<ValidationIssue> issues;  // schema issues plus semantic issues
  std::string origin;                   // file path or "<inline>"
  std::string renderIssues() const;
};

// Parse a specification file. The format is chosen by extension (.yaml/.yml -> YAML parser,
// anything else -> JSON) and falls back to trying the other parser when the first fails, which
// keeps the error messages useful when a file is misnamed.
SpecParseResult loadSpecFile(const std::string& path, const SpecParseOptions& options = {});

// Parse an already decoded JSON document.
SpecParseResult parseSpecDocument(const nlohmann::json& doc, const std::string& origin,
                                  const SpecParseOptions& options = {});

// Serialize a model back to JSON and to YAML. Both are used by the tooling: spec.json is the
// canonical machine form and spec.yaml is generated from it so the two can never drift.
nlohmann::json specToJson(const core::ApplicationModel& model);
std::string specToYaml(const core::ApplicationModel& model);
bool writeSpecJson(const core::ApplicationModel& model, const std::string& path, std::string* error);
bool writeSpecYaml(const core::ApplicationModel& model, const std::string& path, std::string* error);

// Locate specs/capability.schema.json by walking up from `startPath`. Returns an empty string
// when no schema is found.
std::string findSchemaFile(const std::string& startPath);

}  // namespace spec
}  // namespace careweave
