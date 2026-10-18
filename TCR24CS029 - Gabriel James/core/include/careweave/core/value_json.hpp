#pragma once
// JSON projection of typed values.
//
// One lossless mapping between core::Value and a JSON value: booleans, integers, reals and
// strings map directly, lists map to arrays of strings. Parsing rejects JSON null, objects and
// arrays that contain non strings, because none of those can be represented as a typed value
// and silently dropping them would corrupt a payload. Used by the adapter transports, the
// specification loader and the gateway.
#include <string>

#include <nlohmann/json_fwd.hpp>

#include "careweave/core/types.hpp"

namespace careweave {
namespace core {

nlohmann::json valueToJson(const Value& v);
// Returns false and fills `err` when the JSON value has no typed value representation.
bool jsonToValue(const nlohmann::json& j, Value* out, std::string* err);

}  // namespace core
}  // namespace careweave
