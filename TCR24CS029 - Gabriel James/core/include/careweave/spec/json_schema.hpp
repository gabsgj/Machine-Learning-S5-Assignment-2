#pragma once
// Minimal JSON Schema validator.
//
// Supports the keywords used by specs/capability.schema.json: type, required, properties,
// additionalProperties (boolean), items, enum, const, pattern, minLength, maxLength, minItems,
// maxItems, minProperties, minimum, maximum, oneOf, anyOf, allOf and local $ref into
// "#/$defs/<name>". Unknown keywords are ignored, which is the documented contract: the
// validator enforces the shape the project depends on and reports a JSON pointer path plus a
// reason for every violation. It is not a general purpose validator and does not claim to be.
#include <string>
#include <vector>

#include "nlohmann/json.hpp"

namespace careweave {
namespace spec {

struct ValidationIssue {
  std::string path;     // JSON pointer style path, for example /capabilities/2/type
  std::string message;  // reason in plain prose
  std::string schemaPath;
};

struct ValidationReport {
  std::vector<ValidationIssue> issues;
  bool ok() const { return issues.empty(); }
  std::string render() const;
};

// Validate `instance` against `schema`. `rootSchema` is the document that $ref resolves
// against; pass the same object when validating a whole document.
ValidationReport validateAgainstSchema(const nlohmann::json& instance,
                                       const nlohmann::json& schema,
                                       const nlohmann::json& rootSchema);

}  // namespace spec
}  // namespace careweave
