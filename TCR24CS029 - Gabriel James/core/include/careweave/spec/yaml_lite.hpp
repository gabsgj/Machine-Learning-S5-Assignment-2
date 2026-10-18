#pragma once
// YAML subset parser.
//
// CareWeave Mini ships its formal specification sheets in both JSON and YAML. JSON goes
// through nlohmann/json. YAML goes through this parser, which supports exactly the subset the
// specification sheets and application files use:
//
//   - block mappings with "key: value" at consistent indentation
//   - block sequences introduced by "- " including "- key: value" compact entries
//   - nested mappings and sequences to arbitrary depth
//   - flow collections "[a, b]" and "{k: v, k2: v2}"
//   - scalars: integers, floating point, booleans, null, quoted strings with escapes
//   - comments starting with "#" outside quotes
//   - literal block scalars "|" and ">" for multi line strings
//   - document start markers "---" (ignored) and "..." (end of document)
//
// Anything outside this subset is reported as an error with the 1-based line number, never
// silently accepted. The parser is first-party code under the same licence as the rest of the
// project; it exists because the project must build offline with no external dependency and
// because the specification sheets are machine generated in a known, narrow YAML shape.
#include <string>

#include "nlohmann/json.hpp"

namespace careweave {
namespace spec {

// Parse YAML text into a JSON value. Returns false and fills `error` on the first problem.
// The error message has the form "<line>:<column>: <reason>".
bool parseYaml(const std::string& text, nlohmann::json* out, std::string* error);
// Convenience wrapper reading the file from disk.
bool parseYamlFile(const std::string& path, nlohmann::json* out, std::string* error);

}  // namespace spec
}  // namespace careweave
