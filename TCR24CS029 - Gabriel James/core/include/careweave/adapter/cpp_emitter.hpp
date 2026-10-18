#pragma once
// Generated C++ emission.
//
// Materializes one AdapterDefinition as a small C++ translation unit that includes
// careweave/adapter/adapter.hpp and returns the same definition. The emitted file is what the
// bundling step embeds into a host program when a deployment must not read adapter JSON at
// startup; it compiles against this header with C++17 and nothing else.
#include <string>

#include "careweave/adapter/adapter.hpp"

namespace careweave {
namespace adapter {

std::string emitAdapterCpp(const AdapterDefinition& def);
// The function name the emitted translation unit defines, exposed so callers can link or
// inspect generically.
std::string emittedFunctionName(const AdapterDefinition& def);

}  // namespace adapter
}  // namespace careweave
