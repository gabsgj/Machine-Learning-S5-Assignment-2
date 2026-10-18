// Gateway front end.
//
//   careweave_gateway [--root <dir>] [--host <addr>] [--port <n>] [--audit <path>]
//                     [--dashboard <dir>] [--no-audit]
//
// Discovers the seven hospital modules (live GET /spec with their spec files as fallbacks),
// opens the SQLite audit trail, prints the discovery result and serves the management API, the
// canonical hospital API, the workflow endpoint and the dashboard.
#include <cstdio>
#include <iostream>
#include <string>
#include <utility>

#include "careweave/gateway/gateway.hpp"

namespace {

int printUsage() {
  std::fprintf(stderr,
               "usage: careweave_gateway [--root <dir>] [--host <addr>] [--port <n>]\n"
               "                        [--audit <path>] [--dashboard <dir>] [--no-audit]\n");
  return 2;
}

bool takeValue(int argc, char** argv, int* index, std::string* out) {
  if (*index + 1 >= argc) return false;
  *out = argv[++(*index)];
  return true;
}

}  // namespace

int main(int argc, char** argv) {
  careweave::gateway::GatewayConfig config;
  config.rootDir = ".";
  std::string modulesDir;
  std::string auditPath;
  std::string dashboardDir;
  bool auditEnabled = true;

  for (int i = 1; i < argc; ++i) {
    const std::string argument = argv[i];
    if (argument == "--root") {
      if (!takeValue(argc, argv, &i, &config.rootDir)) return printUsage();
    } else if (argument == "--host") {
      if (!takeValue(argc, argv, &i, &config.host)) return printUsage();
    } else if (argument == "--port") {
      std::string value;
      if (!takeValue(argc, argv, &i, &value)) return printUsage();
      try {
        config.port = std::stoi(value);
      } catch (const std::exception&) {
        std::fprintf(stderr, "the port must be a number, got '%s'\n", value.c_str());
        return 2;
      }
    } else if (argument == "--modules") {
      if (!takeValue(argc, argv, &i, &modulesDir)) return printUsage();
    } else if (argument == "--audit") {
      if (!takeValue(argc, argv, &i, &auditPath)) return printUsage();
    } else if (argument == "--dashboard") {
      if (!takeValue(argc, argv, &i, &dashboardDir)) return printUsage();
    } else if (argument == "--no-audit") {
      auditEnabled = false;
    } else {
      std::fprintf(stderr, "unknown option '%s'\n", argument.c_str());
      return printUsage();
    }
  }

  if (modulesDir.empty()) modulesDir = config.rootDir + "/modules";
  if (auditPath.empty()) auditPath = config.rootDir + "/logs/gateway_audit.db";
  if (dashboardDir.empty()) dashboardDir = config.rootDir + "/dashboard";
  config.modulesDir = modulesDir;
  config.auditDbPath = auditEnabled ? auditPath : std::string();
  config.dashboardDir = dashboardDir;

  careweave::gateway::Gateway gateway(std::move(config));
  gateway.discover();

  const std::vector<careweave::gateway::ModuleRecord>& modules = gateway.modules();
  size_t available = 0;
  for (const careweave::gateway::ModuleRecord& module : modules) {
    if (module.available) ++available;
  }
  std::cout << "discovered " << available << " of " << modules.size() << " modules\n";
  for (const careweave::gateway::ModuleRecord& module : modules) {
    std::string status;
    if (!module.available) {
      status = "unavailable (" + module.healthMessage + ")";
    } else if (module.healthy) {
      status = "healthy, spec from " + module.specSource;
    } else {
      status = "not running, spec from " + module.specSource;
    }
    std::cout << "  " << module.model.moduleId << ": " << status << "\n";
  }
  std::cout.flush();

  gateway.listen();
  return 0;
}
