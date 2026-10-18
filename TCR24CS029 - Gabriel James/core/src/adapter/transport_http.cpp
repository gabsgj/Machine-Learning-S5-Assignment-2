#include "careweave/adapter/transport.hpp"

#include <cctype>
#include <ctime>
#include <sstream>

#include "careweave/core/value_json.hpp"
#include "httplib.h"
#include "nlohmann/json.hpp"

namespace careweave {
namespace adapter {

namespace {

// Shared response convention for the HTTP and form transports, documented in
// documents/04_MAPPING_AND_ADAPTERS.md:
//   {"status":"ok","outputs":{...}}          success with named outputs
//   {"status":"error","error":"..."}         failure with a message
//   {...}                                    a bare object is taken as the outputs
//   anything else                            an error
bool parseResponseBody(const std::string& body, int status, TransportResult* out) {
  out->status = status;
  const bool httpError = status < 200 || status >= 300;
  if (httpError && body.empty()) {
    out->error = "HTTP status " + std::to_string(status) + " with no body";
    return false;
  }
  nlohmann::json j = nlohmann::json::parse(body, nullptr, false);
  if (j.is_discarded()) {
    if (httpError) {
      out->error = "HTTP status " + std::to_string(status) + " with a non JSON body";
    } else {
      out->error = "provider returned a non JSON body";
    }
    return false;
  }
  if (!j.is_object()) {
    out->error = "provider response must be a JSON object";
    return false;
  }
  const auto statusIt = j.find("status");
  if (statusIt != j.end() && statusIt->is_string()) {
    const std::string s = statusIt->get<std::string>();
    if (s == "error" || s == "failed") {
      const auto errIt = j.find("error");
      out->error = errIt != j.end() && errIt->is_string() ? errIt->get<std::string>()
                                                          : "provider reported an error";
      return false;
    }
  }
  if (httpError) {
    out->error = "HTTP status " + std::to_string(status);
    return false;
  }
  const auto outputsIt = j.find("outputs");
  if (outputsIt != j.end()) {
    if (!outputsIt->is_object()) {
      out->error = "provider \"outputs\" must be a JSON object";
      return false;
    }
    for (auto it = outputsIt->begin(); it != outputsIt->end(); ++it) {
      core::Value v;
      std::string err;
      if (!core::jsonToValue(it.value(), &v, &err)) {
        out->error = "output \"" + it.key() + "\": " + err;
        return false;
      }
      out->outputs.emplace(it.key(), std::move(v));
    }
    return true;
  }
  // A bare object response: every entry is an output.
  for (auto it = j.begin(); it != j.end(); ++it) {
    if (it.key() == "status") continue;
    core::Value v;
    std::string err;
    if (!core::jsonToValue(it.value(), &v, &err)) {
      out->error = "output \"" + it.key() + "\": " + err;
      return false;
    }
    out->outputs.emplace(it.key(), std::move(v));
  }
  return true;
}

nlohmann::json payloadToJson(const std::map<std::string, core::Value>& payload) {
  nlohmann::json j = nlohmann::json::object();
  for (const auto& kv : payload) j[kv.first] = core::valueToJson(kv.second);
  return j;
}

std::string urlEncode(const std::string& s) {
  static const char* hex = "0123456789ABCDEF";
  std::string out;
  for (const char ch : s) {
    const unsigned char c = static_cast<unsigned char>(ch);
    if (std::isalnum(c) != 0 || c == '-' || c == '_' || c == '.' || c == '~') {
      out.push_back(static_cast<char>(c));
    } else {
      out.push_back('%');
      out.push_back(hex[c >> 4]);
      out.push_back(hex[c & 0x0F]);
    }
  }
  return out;
}

// Ensures the endpoint starts with a single slash relative to the base URL.
std::string normalizeEndpoint(const std::string& endpoint) {
  if (endpoint.empty()) return "/";
  return endpoint[0] == '/' ? endpoint : "/" + endpoint;
}

std::string stripTrailingSlash(const std::string& url) {
  std::string s = url;
  while (!s.empty() && s.back() == '/') s.pop_back();
  return s;
}

}  // namespace

TransportResult HttpTransport::invoke(const AdapterDefinition& def,
                                      const std::map<std::string, core::Value>& payload) {
  TransportResult result;
  const std::string base = stripTrailingSlash(def.baseUrl);
  if (base.empty()) {
    result.error = "adapter has no base URL";
    return result;
  }
  httplib::Client client(base);
  client.set_connection_timeout(static_cast<time_t>(timeoutSeconds_));
  client.set_read_timeout(static_cast<time_t>(timeoutSeconds_));
  client.set_write_timeout(static_cast<time_t>(timeoutSeconds_));
  const std::string path = normalizeEndpoint(def.endpoint);
  const std::string body = payloadToJson(payload).dump();
  result.trace.push_back("http " + def.method + " " + base + path);
  httplib::Result response;
  if (def.method == "GET") {
    if (!payload.empty()) {
      result.error = "GET cannot carry inputs; declare POST for this adapter";
      return result;
    }
    response = client.Get(path.c_str());
  } else if (def.method == "POST" || def.method == "PUT" || def.method == "PATCH") {
    response = client.Post(path.c_str(), body, "application/json");
  } else {
    result.error = "unsupported HTTP method \"" + def.method + "\"";
    return result;
  }
  if (!response) {
    result.error = "connection failed: " + httplib::to_string(response.error());
    return result;
  }
  if (!parseResponseBody(response->body, response->status, &result)) return result;
  result.ok = true;
  return result;
}

TransportResult FormTransport::invoke(const AdapterDefinition& def,
                                      const std::map<std::string, core::Value>& payload) {
  TransportResult result;
  const std::string base = stripTrailingSlash(def.baseUrl);
  if (base.empty()) {
    result.error = "adapter has no base URL";
    return result;
  }
  std::ostringstream form;
  bool first = true;
  for (const auto& kv : payload) {
    if (!first) form << '&';
    first = false;
    form << urlEncode(kv.first) << '=' << urlEncode(kv.second.toString());
  }
  httplib::Client client(base);
  client.set_connection_timeout(static_cast<time_t>(timeoutSeconds_));
  client.set_read_timeout(static_cast<time_t>(timeoutSeconds_));
  client.set_write_timeout(static_cast<time_t>(timeoutSeconds_));
  const std::string path = normalizeEndpoint(def.endpoint);
  result.trace.push_back("form POST " + base + path);
  httplib::Result response =
      client.Post(path.c_str(), form.str(), "application/x-www-form-urlencoded");
  if (!response) {
    result.error = "connection failed: " + httplib::to_string(response.error());
    return result;
  }
  if (!parseResponseBody(response->body, response->status, &result)) return result;
  result.ok = true;
  return result;
}

}  // namespace adapter
}  // namespace careweave
