#include "careweave/core/value_json.hpp"

#include <cstdint>
#include <limits>

#include "nlohmann/json.hpp"

namespace careweave {
namespace core {

nlohmann::json valueToJson(const Value& v) {
  switch (v.type()) {
    case ValueType::BOOL:
      return nlohmann::json(v.asBool());
    case ValueType::INT:
      return nlohmann::json(v.asInt());
    case ValueType::REAL:
      return nlohmann::json(v.asDouble());
    case ValueType::STRING:
      return nlohmann::json(v.asString());
    case ValueType::ENUM:
      return nlohmann::json(v.asString());
    case ValueType::LIST: {
      nlohmann::json arr = nlohmann::json::array();
      for (const auto& item : v.asList()) arr.push_back(item);
      return arr;
    }
  }
  return nlohmann::json(nullptr);
}

bool jsonToValue(const nlohmann::json& j, Value* out, std::string* err) {
  if (j.is_boolean()) {
    *out = Value(j.get<bool>());
    return true;
  }
  if (j.is_number_integer() || j.is_number_unsigned()) {
    *out = Value(static_cast<int64_t>(j.get<int64_t>()));
    return true;
  }
  if (j.is_number_float()) {
    *out = Value(j.get<double>());
    return true;
  }
  if (j.is_string()) {
    *out = Value(j.get<std::string>());
    return true;
  }
  if (j.is_array()) {
    std::vector<std::string> items;
    for (const auto& item : j) {
      if (!item.is_string()) {
        if (err) *err = "array values must all be strings";
        return false;
      }
      items.push_back(item.get<std::string>());
    }
    *out = Value(std::move(items));
    return true;
  }
  if (err) {
    *err = j.is_null() ? "null has no typed value representation"
                       : "only booleans, numbers, strings and string arrays are supported";
  }
  return false;
}

}  // namespace core
}  // namespace careweave
