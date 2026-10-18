#include "careweave/adapter/cpp_emitter.hpp"

#include <cstdio>
#include <sstream>

namespace careweave {
namespace adapter {

namespace {

std::string sanitizeIdentifier(const std::string& id) {
  std::string out;
  for (char c : id) {
    const bool alnum = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                       (c >= '0' && c <= '9') || c == '_';
    out += alnum ? c : '_';
  }
  if (out.empty() || (out[0] >= '0' && out[0] <= '9')) out = "_" + out;
  return out;
}

std::string quote(const std::string& s) {
  std::string out = "\"";
  for (const char c : s) {
    const unsigned char u = static_cast<unsigned char>(c);
    if (c == '"') {
      out += "\\\"";
    } else if (c == '\\') {
      out += "\\\\";
    } else if (c == '\n') {
      out += "\\n";
    } else if (c == '\t') {
      out += "\\t";
    } else if (c == '\r') {
      out += "\\r";
    } else if (u < 0x20) {
      char buffer[8];
      std::snprintf(buffer, sizeof(buffer), "\\%03o", u);
      out += buffer;
    } else {
      out += c;
    }
  }
  out += "\"";
  return out;
}

}  // namespace

std::string emittedFunctionName(const AdapterDefinition& def) {
  return "make_" + sanitizeIdentifier(def.id);
}

std::string emitAdapterCpp(const AdapterDefinition& def) {
  std::ostringstream os;
  os << "// Generated adapter definition for " << def.id << ".\n";
  os << "// Produced by the CareWeave adapter emitter from the stored adapter; edit the adapter\n";
  os << "// definition and regenerate this file instead of editing it by hand.\n";
  os << "#include <string>\n";
  os << "#include <utility>\n";
  os << "#include <vector>\n\n";
  os << "#include \"careweave/adapter/adapter.hpp\"\n\n";
  os << "namespace careweave {\nnamespace adapter {\nnamespace generated {\n\n";
  os << "AdapterDefinition " << emittedFunctionName(def) << "() {\n";
  os << "  AdapterDefinition d;\n";
  os << "  d.id = " << quote(def.id) << ";\n";
  os << "  d.requirementId = " << quote(def.requirementId) << ";\n";
  os << "  d.requirementName = " << quote(def.requirementName) << ";\n";
  os << "  d.targetModule = " << quote(def.targetModule) << ";\n";
  os << "  d.targetCapabilityId = " << quote(def.targetCapabilityId) << ";\n";
  os << "  d.targetCapabilityName = " << quote(def.targetCapabilityName) << ";\n";
  os << "  d.transportKind = " << quote(def.transportKind) << ";\n";
  os << "  d.baseUrl = " << quote(def.baseUrl) << ";\n";
  os << "  d.endpoint = " << quote(def.endpoint) << ";\n";
  os << "  d.method = " << quote(def.method) << ";\n";
  os << "  d.sqlitePath = " << quote(def.sqlitePath) << ";\n";
  os << "  d.table = " << quote(def.table) << ";\n";
  os << "  d.operation = " << quote(def.operation) << ";\n";
  os << "  d.filePath = " << quote(def.filePath) << ";\n";
  os << "  d.fileOperation = " << quote(def.fileOperation) << ";\n";
  os << "  d.fileFormat = " << quote(def.fileFormat) << ";\n";
  os << "  d.handler = " << quote(def.handler) << ";\n";
  if (!def.computations.empty()) {
    os << "  d.computations = {\n";
    for (const auto& c : def.computations) {
      os << "      {" << quote(c.first) << ", " << quote(c.second) << "},\n";
    }
    os << "  };\n";
  }
  if (!def.inputMap.empty()) {
    os << "  d.inputMap = {\n";
    for (const auto& m : def.inputMap) {
      os << "      {" << quote(m.from) << ", " << quote(m.to) << ", " << quote(m.transform)
         << "},\n";
    }
    os << "  };\n";
  }
  if (!def.outputMap.empty()) {
    os << "  d.outputMap = {\n";
    for (const auto& m : def.outputMap) {
      os << "      {" << quote(m.from) << ", " << quote(m.to) << ", " << quote(m.transform)
         << "},\n";
    }
    os << "  };\n";
  }
  os << "  d.confidence = " << def.confidence << ";\n";
  if (!def.explanation.empty()) {
    os << "  d.explanation = {\n";
    for (const auto& line : def.explanation) os << "      " << quote(line) << ",\n";
    os << "  };\n";
  }
  os << "  return d;\n";
  os << "}\n\n";
  os << "}  // namespace generated\n}  // namespace adapter\n}  // namespace careweave\n";
  return os.str();
}

}  // namespace adapter
}  // namespace careweave
