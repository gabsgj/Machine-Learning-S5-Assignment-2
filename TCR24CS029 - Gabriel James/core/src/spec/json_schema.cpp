#include "careweave/spec/json_schema.hpp"

#include <cmath>
#include <regex>
#include <sstream>

namespace careweave {
namespace spec {

namespace {

using json = nlohmann::json;

const char* jsonTypeName(const json& v) {
  if (v.is_null()) return "null";
  if (v.is_boolean()) return "boolean";
  if (v.is_number_integer()) return "integer";
  if (v.is_number_unsigned()) return "integer";
  if (v.is_number_float()) return "number";
  if (v.is_string()) return "string";
  if (v.is_array()) return "array";
  if (v.is_object()) return "object";
  return "unknown";
}

bool typeMatches(const json& v, const std::string& expected) {
  if (expected == "object") return v.is_object();
  if (expected == "array") return v.is_array();
  if (expected == "string") return v.is_string();
  if (expected == "boolean") return v.is_boolean();
  if (expected == "integer") return v.is_number_integer() || v.is_number_unsigned() ||
                                       (v.is_number_float() && std::floor(v.get<double>()) == v.get<double>() &&
                                        v.get<double>() >= -9007199254740992.0 && v.get<double>() <= 9007199254740992.0);
  if (expected == "number") return v.is_number();
  if (expected == "null") return v.is_null();
  return true;
}

class Validator {
 public:
  Validator(const json& root, ValidationReport* report) : root_(root), report_(report) {}

  void validate(const json& instance, const json& schema, const std::string& path,
                const std::string& schemaPath) {
    if (schema.is_boolean()) {
      if (!schema.get<bool>()) {
        add(path, schemaPath, "value is not allowed here");
      }
      return;
    }
    if (!schema.is_object()) return;

    if (schema.contains("$ref") && schema["$ref"].is_string()) {
      const std::string ref = schema["$ref"].get<std::string>();
      if (ref.rfind("#/", 0) == 0) {
        std::vector<std::string> tokens;
        std::string cur;
        for (size_t i = 2; i < ref.size(); ++i) {
          if (ref[i] == '/') {
            tokens.push_back(cur);
            cur.clear();
          } else {
            cur += ref[i];
          }
        }
        if (!cur.empty()) tokens.push_back(cur);
        const json* target = &root_;
        bool found = true;
        for (auto& t : tokens) {
          std::string key = t;
          std::replace(key.begin(), key.end(), '~', '~');
          if (!target->is_object() || !target->contains(key)) {
            found = false;
            break;
          }
          target = &(*target)[key];
        }
        if (!found) {
          add(path, schemaPath, "unresolvable $ref " + ref);
          return;
        }
        validate(instance, *target, path, ref);
        return;
      }
      add(path, schemaPath, "unsupported $ref target " + ref);
      return;
    }

    if (schema.contains("type")) {
      const json& t = schema["type"];
      bool matched = false;
      if (t.is_string()) {
        matched = typeMatches(instance, t.get<std::string>());
      } else if (t.is_array()) {
        for (const auto& alt : t) {
          if (alt.is_string() && typeMatches(instance, alt.get<std::string>())) {
            matched = true;
            break;
          }
        }
      }
      if (!matched) {
        std::ostringstream os;
        os << "expected type " << t.dump() << " but found " << jsonTypeName(instance);
        add(path, schemaPath, os.str());
        return;
      }
    }

    if (schema.contains("enum")) {
      bool found = false;
      for (const auto& candidate : schema["enum"]) {
        if (candidate == instance) {
          found = true;
          break;
        }
      }
      if (!found) {
        add(path, schemaPath, "value " + instance.dump() + " is not one of " + schema["enum"].dump());
      }
    }
    if (schema.contains("const") && schema["const"] != instance) {
      add(path, schemaPath, "value must equal " + schema["const"].dump());
    }

    if (instance.is_string()) {
      const std::string s = instance.get<std::string>();
      if (schema.contains("minLength") && s.size() < schema["minLength"].get<size_t>()) {
        add(path, schemaPath, "string shorter than minLength");
      }
      if (schema.contains("maxLength") && s.size() > schema["maxLength"].get<size_t>()) {
        add(path, schemaPath, "string longer than maxLength");
      }
      if (schema.contains("pattern")) {
        try {
          const std::regex re(schema["pattern"].get<std::string>());
          if (!std::regex_search(s, re)) {
            add(path, schemaPath, "string does not match pattern " + schema["pattern"].dump());
          }
        } catch (const std::regex_error&) {
          add(path, schemaPath, "schema pattern is not a valid regular expression");
        }
      }
    }

    if (instance.is_number()) {
      const double d = instance.get<double>();
      if (schema.contains("minimum") && d < schema["minimum"].get<double>()) {
        add(path, schemaPath, "number below minimum");
      }
      if (schema.contains("maximum") && d > schema["maximum"].get<double>()) {
        add(path, schemaPath, "number above maximum");
      }
    }

    if (instance.is_array()) {
      if (schema.contains("minItems") && instance.size() < schema["minItems"].get<size_t>()) {
        add(path, schemaPath, "array has fewer items than minItems");
      }
      if (schema.contains("maxItems") && instance.size() > schema["maxItems"].get<size_t>()) {
        add(path, schemaPath, "array has more items than maxItems");
      }
      if (schema.contains("items")) {
        const json& items = schema["items"];
        if (items.is_object() || items.is_boolean()) {
          for (size_t i = 0; i < instance.size(); ++i) {
            validate(instance[i], items, path + "/" + std::to_string(i), schemaPath + "/items");
          }
        }
      }
    }

    if (instance.is_object()) {
      if (schema.contains("minProperties") &&
          instance.size() < schema["minProperties"].get<size_t>()) {
        add(path, schemaPath, "object has fewer properties than minProperties");
      }
      if (schema.contains("required")) {
        for (const auto& key : schema["required"]) {
          if (!instance.contains(key.get<std::string>())) {
            add(path, schemaPath, "missing required property \"" + key.get<std::string>() + "\"");
          }
        }
      }
      if (schema.contains("properties") && schema["properties"].is_object()) {
        for (auto it = instance.begin(); it != instance.end(); ++it) {
          if (schema["properties"].contains(it.key())) {
            validate(it.value(), schema["properties"][it.key()], path + "/" + it.key(),
                     schemaPath + "/properties/" + it.key());
          }
        }
      }
      if (schema.contains("additionalProperties")) {
        const json& ap = schema["additionalProperties"];
        if (ap.is_boolean() && !ap.get<bool>()) {
          for (auto it = instance.begin(); it != instance.end(); ++it) {
            const bool declared = schema.contains("properties") &&
                                  schema["properties"].is_object() &&
                                  schema["properties"].contains(it.key());
            if (!declared) {
              add(path + "/" + it.key(), schemaPath,
                  "additional property \"" + it.key() + "\" is not allowed");
            }
          }
        } else if (ap.is_object()) {
          for (auto it = instance.begin(); it != instance.end(); ++it) {
            const bool declared = schema.contains("properties") &&
                                  schema["properties"].is_object() &&
                                  schema["properties"].contains(it.key());
            if (!declared) {
              validate(it.value(), ap, path + "/" + it.key(), schemaPath + "/additionalProperties");
            }
          }
        }
      }
    }

    if (schema.contains("allOf")) {
      for (size_t i = 0; i < schema["allOf"].size(); ++i) {
        validate(instance, schema["allOf"][i], path, schemaPath + "/allOf/" + std::to_string(i));
      }
    }
    if (schema.contains("anyOf")) {
      bool any = false;
      for (const auto& alt : schema["anyOf"]) {
        ValidationReport sub;
        Validator v(root_, &sub);
        v.validate(instance, alt, path, schemaPath + "/anyOf");
        if (sub.ok()) {
          any = true;
          break;
        }
      }
      if (!any) {
        add(path, schemaPath, "value matches none of the anyOf alternatives");
      }
    }
    if (schema.contains("oneOf")) {
      int matches = 0;
      for (const auto& alt : schema["oneOf"]) {
        ValidationReport sub;
        Validator v(root_, &sub);
        v.validate(instance, alt, path, schemaPath + "/oneOf");
        if (sub.ok()) ++matches;
      }
      if (matches != 1) {
        std::ostringstream os;
        os << "value matches " << matches << " oneOf alternatives, exactly 1 required";
        add(path, schemaPath, os.str());
      }
    }
  }

 private:
  const json& root_;
  ValidationReport* report_;

  void add(const std::string& path, const std::string& schemaPath, const std::string& message) {
    ValidationIssue issue;
    issue.path = path.empty() ? "/" : path;
    issue.schemaPath = schemaPath;
    issue.message = message;
    report_->issues.push_back(std::move(issue));
  }
};

}  // namespace

std::string ValidationReport::render() const {
  std::ostringstream os;
  if (issues.empty()) {
    os << "ok";
    return os.str();
  }
  for (const auto& issue : issues) {
    os << issue.path << ": " << issue.message << " (schema " << issue.schemaPath << ")\n";
  }
  std::string s = os.str();
  if (!s.empty() && s.back() == '\n') s.pop_back();
  return s;
}

ValidationReport validateAgainstSchema(const nlohmann::json& instance,
                                       const nlohmann::json& schema,
                                       const nlohmann::json& rootSchema) {
  ValidationReport report;
  Validator v(rootSchema.is_null() ? schema : rootSchema, &report);
  v.validate(instance, schema, "", "#");
  return report;
}

}  // namespace spec
}  // namespace careweave
