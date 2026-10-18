#pragma once
// Adapter runner.
//
// Executes a stored adapter against a transport: renames and transforms the requirement inputs
// into the provider vocabulary, performs the call, renames the provider outputs back, and
// returns a full trace. A missing requirement input, a failed transform, a transport error or a
// provider output that the requirement expects but the response does not contain each stop the
// run with a specific error; nothing is defaulted silently.
#include <map>
#include <string>
#include <vector>

#include "careweave/adapter/adapter.hpp"
#include "careweave/adapter/transport.hpp"
#include "careweave/core/types.hpp"

namespace careweave {
namespace adapter {

struct AdapterResult {
  bool ok = false;
  // True once the transport was actually invoked. A run that stops during input validation never
  // reached the provider, so callers must not count it as a module failure.
  bool transportAttempted = false;
  // Outputs in the requirement vocabulary.
  std::map<std::string, core::Value> outputs;
  // The provider response before renaming, kept for the trace and the UI.
  std::map<std::string, core::Value> providerOutputs;
  std::string error;
  int status = 0;
  std::vector<std::string> trace;
  std::string render() const;
};

class AdapterRunner {
 public:
  explicit AdapterRunner(Transport& transport) : transport_(transport) {}
  AdapterResult run(const AdapterDefinition& def,
                    const std::map<std::string, core::Value>& inputs);
  Transport& transport() { return transport_; }

 private:
  Transport& transport_;
};

}  // namespace adapter
}  // namespace careweave
