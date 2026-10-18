#pragma once
// Adapter synthesis.
//
// Turns the output of the mapper into an executable AdapterDefinition: assigned field matches
// become the input and output maps with type driven transforms, the provider mechanism decides
// the transport, and every requirement that cannot be satisfied (a required provider input with
// no binding, an unbound required requirement input, an expected output the provider does not
// declare, a mechanism missing its transport coordinates, a malformed computation expression)
// is reported in `errors` instead of being papered over.
#include <string>
#include <vector>

#include "careweave/adapter/adapter.hpp"
#include "careweave/core/types.hpp"
#include "careweave/mapper/mapper.hpp"

namespace careweave {
namespace adapter {

struct SynthesisRequest {
  core::CapabilitySpec requirement;
  mapper::MatchResult match;
  core::CapabilitySpec candidate;
  std::string targetModule;
  std::string baseUrl;       // HTTP and form targets
  std::string databasePath;  // sqlite targets
  std::string fileOperation; // optional override for FILE capabilities, "write" when empty
};

struct SynthesisResult {
  bool ok = false;
  AdapterDefinition adapter;
  std::vector<std::string> errors;
  std::string render() const;
};

class AdapterSynthesizer {
 public:
  SynthesisResult synthesize(const SynthesisRequest& request) const;
};

// Chooses the transform that converts a requirement value of type `from` into the provider
// type `to`: identity when the types line up, otherwise the conversion toward the provider
// type. Exposed for the mapping studio and the tests.
std::string chooseTransform(const std::string& from, const std::string& to);

}  // namespace adapter
}  // namespace careweave
