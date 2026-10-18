#include "careweave/bundle/bundler.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <map>
#include <set>
#include <system_error>
#include <utility>

#include "nlohmann/json.hpp"

namespace careweave {
namespace bundle {

namespace fs = std::filesystem;
using nlohmann::json;

namespace {

struct ModuleInfo {
  std::string id;
  int port = 0;
  std::string directory;  // bundle relative directory name under modules/
};

bool endsWith(const std::string& text, const std::string& suffix) {
  return text.size() >= suffix.size() &&
         text.compare(text.size() - suffix.size(), suffix.size(), suffix) == 0;
}

// Runtime databases never travel in a bundle: every module creates and seeds its own database
// on first start.
bool isDatabaseFile(const std::string& name) {
  return endsWith(name, ".db") || endsWith(name, ".db-wal") || endsWith(name, ".db-shm") ||
         endsWith(name, ".sqlite") || endsWith(name, ".sqlite3");
}

bool skipEntry(const std::string& name) {
  return name == "__pycache__" || name == ".pytest_cache" || name == ".venv" ||
         name == ".git" || endsWith(name, ".pyc");
}

bool copyFiltered(const fs::path& source, const fs::path& destination, size_t* files,
                  std::string* error, const std::vector<fs::path>& skip = {}) {
  std::error_code ec;
  fs::create_directories(destination, ec);
  if (ec) {
    *error = "cannot create " + destination.string() + ": " + ec.message();
    return false;
  }
  for (const fs::directory_entry& entry : fs::directory_iterator(source, ec)) {
    if (ec) {
      *error = "cannot read " + source.string() + ": " + ec.message();
      return false;
    }
    const std::string name = entry.path().filename().string();
    if (skipEntry(name)) continue;
    if (std::find(skip.begin(), skip.end(), entry.path()) != skip.end()) continue;
    if (entry.is_directory(ec)) {
      if (!copyFiltered(entry.path(), destination / name, files, error, skip)) return false;
    } else if (entry.is_regular_file(ec)) {
      if (isDatabaseFile(name)) continue;
      fs::copy_file(entry.path(), destination / name, fs::copy_options::overwrite_existing, ec);
      if (ec) {
        *error = "cannot copy " + entry.path().string() + ": " + ec.message();
        return false;
      }
      ++(*files);
    }
  }
  return true;
}

bool writeGenerated(const fs::path& path, const std::string& content, bool executable,
                    std::string* error) {
  std::ofstream out(path, std::ios::binary | std::ios::trunc);
  if (!out) {
    *error = "cannot write " + path.string();
    return false;
  }
  out << content;
  out.close();
  if (executable) {
    std::error_code ec;
    fs::permissions(path,
                    fs::perms::owner_exec | fs::perms::group_exec | fs::perms::others_exec,
                    fs::perm_options::add, ec);
  }
  return true;
}

bool readModuleInfo(const fs::path& moduleDir, ModuleInfo* info, std::string* error) {
  const fs::path specPath = moduleDir / "spec.json";
  std::ifstream file(specPath);
  if (!file) {
    *error = "module " + moduleDir.filename().string() + " has no spec.json";
    return false;
  }
  const json document = json::parse(file, nullptr, false);
  if (document.is_discarded() || !document.contains("module")) {
    *error = "module " + moduleDir.filename().string() + " has an unreadable spec.json";
    return false;
  }
  info->id = document["module"].value("module_id", moduleDir.filename().string());
  info->port = document["module"].value("port", 0);
  info->directory = moduleDir.filename().string();
  if (info->port <= 0) {
    *error = "module " + info->id + " declares no port in its spec.json";
    return false;
  }
  return true;
}

// A workflow sheet under specs/workflows as the bundler sees it: the file name, the workflow_id
// its steps belong to, and the module ids its bound steps reference (a mapped step names a
// requirement sheet instead and references no module directly).
struct WorkflowSheet {
  std::string file;
  std::string stem;
  std::string id;
  std::vector<std::string> moduleIds;
};

std::string relativeTo(const fs::path& root, const fs::path& path) {
  std::error_code ec;
  const fs::path relative = fs::relative(path, root, ec);
  return ec ? path.filename().string() : relative.generic_string();
}

bool readWorkflowSheet(const fs::path& path, const fs::path& root, WorkflowSheet* sheet,
                       std::string* error) {
  const std::string display = relativeTo(root, path);
  sheet->file = path.filename().string();
  sheet->stem = path.stem().string();
  std::ifstream file(path);
  if (!file) {
    *error = "cannot read workflow sheet " + display;
    return false;
  }
  const json document = json::parse(file, nullptr, false);
  if (document.is_discarded()) {
    *error = "workflow sheet " + display + " is not JSON";
    return false;
  }
  if (!document.contains("workflow_id") || !document["workflow_id"].is_string() ||
      document["workflow_id"].get<std::string>().empty()) {
    *error = "workflow sheet " + display + " has no workflow_id";
    return false;
  }
  sheet->id = document["workflow_id"].get<std::string>();
  if (!document.contains("steps") || !document["steps"].is_array() ||
      document["steps"].empty()) {
    *error = "workflow sheet " + display + " needs a non empty steps array";
    return false;
  }
  for (const json& step : document["steps"]) {
    if (!step.is_object()) {
      *error = "workflow sheet " + display + " has a step that is not an object";
      return false;
    }
    if (!step.contains("module")) continue;
    if (!step["module"].is_string() || step["module"].get<std::string>().empty()) {
      *error = "workflow sheet " + display + " has a step whose module is not a module id";
      return false;
    }
    sheet->moduleIds.push_back(step["module"].get<std::string>());
  }
  return true;
}

std::string joinNames(const std::vector<std::string>& names, const std::string& separator) {
  std::string text;
  for (const std::string& name : names) {
    if (!text.empty()) text += separator;
    text += name;
  }
  return text;
}

std::string moduleCatalogue(const std::vector<ModuleInfo>& modules) {
  std::vector<std::string> ids;
  ids.reserve(modules.size());
  for (const ModuleInfo& module : modules) ids.push_back(module.id);
  return joinNames(ids, ", ");
}

std::string workflowCatalogue(const std::vector<WorkflowSheet>& sheets) {
  if (sheets.empty()) return "none";
  std::vector<std::string> names;
  names.reserve(sheets.size());
  for (const WorkflowSheet& sheet : sheets) names.push_back(sheet.stem + " (" + sheet.id + ")");
  return joinNames(names, ", ");
}

// "referenced by workflow X" or "referenced by workflows X, Y".
std::string closureReason(const std::vector<std::string>& workflowIds) {
  return "referenced by " + std::string(workflowIds.size() == 1 ? "workflow " : "workflows ") +
         joinNames(workflowIds, ", ");
}

bool pathIsInside(const fs::path& candidate, const fs::path& parent) {
  std::error_code ec;
  const fs::path relative = fs::relative(candidate, parent, ec);
  if (ec) return false;
  const std::string text = relative.generic_string();
  return !text.empty() && text != "." && text.rfind("..", 0) != 0;
}

std::string startScript(const std::vector<ModuleInfo>& modules) {
  std::string script;
  script += "#!/bin/sh\n";
  script += "# Starts the bundle: the module servers, then the gateway, then waits for health.\n";
  script += "set -eu\n";
  script += "root=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\n";
  script += "python=\"${CAREWEAVE_PYTHON:-$root/.venv/bin/python3}\"\n";
  script += "if [ ! -x \"$python\" ]; then\n";
  script += "  echo \"no Python environment found; run scripts/setup.sh once first\" >&2\n";
  script += "  exit 1\n";
  script += "fi\n";
  script += "run=\"$root/.run\"\n";
  script += "mkdir -p \"$run\"\n";
  script += "start_module() {\n";
  script += "  name=\"$1\"\n";
  script += "  port=\"$2\"\n";
  // exec makes the recorded pid the server itself, so stop.sh kills the server, not a wrapper.
  script += "  (cd \"$root/modules/$name\" && exec env CAREWEAVE_PORT=\"$port\" \"$python\" "
            "run.py > \"$run/$name.log\" 2>&1) &\n";
  script += "  echo $! > \"$run/$name.pid\"\n";
  script += "}\n";
  for (const ModuleInfo& module : modules) {
    script += "start_module " + module.directory + " " + std::to_string(module.port) + "\n";
  }
  script += "gateway_port=\"${CAREWEAVE_GATEWAY_PORT:-5100}\"\n";
  script += "\"$root/bin/careweave_gateway\" --root \"$root\" --port \"$gateway_port\" > "
            "\"$run/gateway.log\" 2>&1 &\n";
  script += "echo $! > \"$run/gateway.pid\"\n";
  script += "\"$python\" - \"http://127.0.0.1:$gateway_port\" <<'PY'\n";
  script += "import json\n";
  script += "import sys\n";
  script += "import time\n";
  script += "import urllib.request\n";
  script += "base = sys.argv[1]\n";
  script += "last = None\n";
  script += "for attempt in range(90):\n";
  script += "    try:\n";
  script += "        with urllib.request.urlopen(base + \"/health\", timeout=1) as response:\n";
  script += "            last = json.loads(response.read())\n";
  script += "        if last.get(\"modules_healthy\") == last.get(\"modules_total\"):\n";
  script += "            break\n";
  script += "    except Exception:\n";
  script += "        pass\n";
  script += "    if attempt == 10:\n";
  script += "        try:\n";
  script += "            request = urllib.request.Request(\n";
  script += "                base + \"/api/discover\",\n";
  script += "                data=b\"{}\",\n";
  script += "                headers={\"Content-Type\": \"application/json\"},\n";
  script += "            )\n";
  script += "            urllib.request.urlopen(request, timeout=5).read()\n";
  script += "        except Exception:\n";
  script += "            pass\n";
  script += "    time.sleep(0.5)\n";
  script += "if last is None:\n";
  script += "    raise SystemExit(\"the gateway did not answer on \" + base)\n";
  script += "print(\"gateway ready:\", base)\n";
  script += "print(\"modules healthy:\", last.get(\"modules_healthy\"), \"of\", "
            "last.get(\"modules_total\"))\n";
  script += "PY\n";
  return script;
}

std::string setupScript() {
  return "#!/bin/sh\n"
         "# Creates the bundle's Python virtual environment and installs the module\n"
         "# requirements. Needs network access once; afterwards the bundle runs offline.\n"
         "set -eu\n"
         "root=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\n"
         "python=\"${CAREWEAVE_PYTHON:-python3}\"\n"
         "\"$python\" -m venv \"$root/.venv\"\n"
         "\"$root/.venv/bin/pip\" install --quiet --upgrade pip\n"
         "for requirements in \"$root\"/modules/*/requirements.txt; do\n"
         "  \"$root/.venv/bin/pip\" install --quiet -r \"$requirements\"\n"
         "done\n"
         "echo \"environment ready: $root/.venv\"\n";
}

std::string stopScript() {
  return "#!/bin/sh\n"
         "# Stops every process this bundle started.\n"
         "set -eu\n"
         "root=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\n"
         "run=\"$root/.run\"\n"
         "if [ ! -d \"$run\" ]; then\n"
         "  echo \"nothing to stop\"\n"
         "  exit 0\n"
         "fi\n"
         "for pidfile in \"$run\"/*.pid; do\n"
         "  [ -e \"$pidfile\" ] || continue\n"
         "  pid=\"$(cat \"$pidfile\")\"\n"
         "  name=\"$(basename \"$pidfile\" .pid)\"\n"
         "  if kill \"$pid\" 2>/dev/null; then\n"
         "    echo \"stopped $name ($pid)\"\n"
         "  else\n"
         "    echo \"no process for $name (pid $pid)\"\n"
         "  fi\n"
         "  rm -f \"$pidfile\"\n"
         "done\n";
}

std::string readmeText(const std::vector<ModuleInfo>& modules, bool dashboardIncluded,
                       const std::string& workflowLine,
                       const std::vector<std::string>& selectionNotes) {
  std::string text;
  text += "CareWeave Mini bundle\n";
  text += "=====================\n\n";
  text += "Contents\n";
  text += "  modules/    the module servers, each with its specification sheets\n";
  for (const ModuleInfo& module : modules) {
    text += "              " + module.directory + " (port " + std::to_string(module.port) + ")\n";
  }
  text += "  specs/      specification sheets, applications and requirement examples\n";
  if (!workflowLine.empty()) {
    text += "              workflow sheets shipped: " + workflowLine + "\n";
  }
  if (dashboardIncluded) {
    text += "  dashboard/  the static dashboard\n";
  }
  text += "  bin/        careweave_gateway\n";
  text += "  scripts/    setup.sh, start.sh, stop.sh\n";
  text += "  MANIFEST.json\n";
  if (!selectionNotes.empty()) {
    text += "\nSelection\n";
    for (const std::string& note : selectionNotes) text += "  " + note + "\n";
  }
  text += "\nStart\n";
  text += "  1. scripts/setup.sh   creates .venv and installs the module requirements once\n";
  text += "  2. scripts/start.sh   starts the modules and the gateway and waits for health\n";
  text += "  3. open http://127.0.0.1:5100/health (management API) or http://127.0.0.1:5100/ "
          "(dashboard)\n";
  text += "     POST http://127.0.0.1:5100/api/discover refreshes module discovery\n\n";
  text += "Stop\n";
  text += "  scripts/stop.sh\n\n";
  text += "Runtime data\n";
  text += "  Every module creates and seeds its own database under modules/<name>/data on first\n";
  text += "  start, so no database files travel inside this bundle.\n";
  return text;
}

}  // namespace

BundleResult createBundle(const BundleOptions& options) {
  BundleResult result;
  result.outDir = options.displayPath.empty() ? options.outDir : options.displayPath;

  std::error_code ec;
  if (options.rootDir.empty() || options.outDir.empty()) {
    result.error = "both a root directory and an output directory are required";
    return result;
  }
  const fs::path root = fs::weakly_canonical(fs::path(options.rootDir), ec);
  if (ec || !fs::is_directory(root)) {
    result.error = "root directory not found: " + options.rootDir;
    return result;
  }
  const fs::path out = fs::weakly_canonical(fs::path(options.outDir), ec);
  if (ec) {
    result.error = "cannot resolve the output directory: " + options.outDir;
    return result;
  }
  if (out == root || pathIsInside(root, out)) {
    result.error = "refusing to assemble a bundle that contains or replaces the checkout";
    return result;
  }

  // ---- collect the module inventory first, so a broken module is reported before anything is
  // ---- written
  const fs::path modulesSource = root / "modules";
  std::vector<ModuleInfo> modules;
  if (fs::is_directory(modulesSource, ec)) {
    std::vector<fs::path> directories;
    for (const fs::directory_entry& entry : fs::directory_iterator(modulesSource, ec)) {
      if (entry.is_directory(ec) && fs::exists(entry.path() / "run.py")) {
        directories.push_back(entry.path());
      }
    }
    std::sort(directories.begin(), directories.end());
    for (const fs::path& directory : directories) {
      ModuleInfo info;
      if (!readModuleInfo(directory, &info, &result.error)) return result;
      modules.push_back(std::move(info));
    }
  }
  if (modules.empty()) {
    result.error = "no module servers found under " + modulesSource.string();
    return result;
  }

  // ---- resolve the requested selection before anything is written: unknown module ids and
  // ---- unknown workflow names are refusals, and the closure below decides the module list
  std::map<std::string, size_t> moduleIndexById;
  for (size_t i = 0; i < modules.size(); ++i) {
    if (!moduleIndexById.emplace(modules[i].id, i).second) {
      result.error = "two module directories declare the id " + modules[i].id;
      return result;
    }
  }

  std::vector<fs::path> workflowPaths;
  if (!options.includeSpecs && !options.selectedWorkflows.empty()) {
    result.error = "workflows can only be selected when the specification sheets are included";
    return result;
  }
  if (options.includeSpecs) {
    const fs::path workflowsDir = root / "specs" / "workflows";
    if (fs::is_directory(workflowsDir, ec)) {
      for (const fs::directory_entry& entry : fs::directory_iterator(workflowsDir, ec)) {
        if (entry.is_regular_file(ec) && entry.path().extension() == ".json") {
          workflowPaths.push_back(entry.path());
        }
      }
      std::sort(workflowPaths.begin(), workflowPaths.end());
    }
  }
  std::vector<WorkflowSheet> workflowInventory;
  if (options.includeWorkflows) {
    for (const fs::path& path : workflowPaths) {
      WorkflowSheet sheet;
      if (!readWorkflowSheet(path, root, &sheet, &result.error)) return result;
      workflowInventory.push_back(std::move(sheet));
    }
  }

  std::set<size_t> shippedWorkflows;
  if (options.includeWorkflows) {
    if (options.selectedWorkflows.empty()) {
      for (size_t i = 0; i < workflowInventory.size(); ++i) shippedWorkflows.insert(i);
    } else {
      for (const std::string& requested : options.selectedWorkflows) {
        bool matched = false;
        for (size_t i = 0; i < workflowInventory.size(); ++i) {
          if (workflowInventory[i].stem == requested || workflowInventory[i].id == requested) {
            shippedWorkflows.insert(i);
            matched = true;
          }
        }
        if (!matched) {
          result.error = "no workflow sheet matches " + requested + " (available: " +
                         workflowCatalogue(workflowInventory) + ")";
          return result;
        }
      }
    }
  }
  for (size_t index : shippedWorkflows) result.workflows.push_back(workflowInventory[index].file);

  std::set<size_t> bundledIndexes;
  if (options.selectedModules.empty()) {
    for (size_t i = 0; i < modules.size(); ++i) bundledIndexes.insert(i);
  } else {
    for (const std::string& requested : options.selectedModules) {
      const auto found = moduleIndexById.find(requested);
      if (found == moduleIndexById.end()) {
        result.error = "no module with id " + requested + " is in this checkout (known ids: " +
                       moduleCatalogue(modules) + ")";
        return result;
      }
      if (std::find(result.requestedModules.begin(), result.requestedModules.end(), requested) ==
          result.requestedModules.end()) {
        result.requestedModules.push_back(requested);
      }
      bundledIndexes.insert(found->second);
    }
  }

  // The closure: every module a shipped workflow step binds must exist in the checkout and must
  // travel in the bundle, so even a selected bundle stays runnable exactly as shipped.
  std::map<size_t, std::vector<std::string>> closureReasons;
  for (size_t sheetIndex : shippedWorkflows) {
    const WorkflowSheet& sheet = workflowInventory[sheetIndex];
    for (const std::string& moduleId : sheet.moduleIds) {
      const auto found = moduleIndexById.find(moduleId);
      if (found == moduleIndexById.end()) {
        result.error = "workflow " + sheet.id + " binds unknown module " + moduleId;
        return result;
      }
      if (bundledIndexes.insert(found->second).second) {
        closureReasons[found->second].push_back(sheet.id);
      }
    }
  }

  std::vector<ModuleInfo> bundledModules;
  for (size_t i = 0; i < modules.size(); ++i) {
    if (bundledIndexes.count(i) == 0) continue;
    bundledModules.push_back(modules[i]);
    const auto reasons = closureReasons.find(i);
    if (reasons != closureReasons.end()) {
      result.closureAdded.emplace_back(modules[i].id, closureReason(reasons->second));
    }
  }
  std::vector<fs::path> skipWorkflows;
  for (size_t i = 0; i < workflowPaths.size(); ++i) {
    if (shippedWorkflows.count(i) == 0) skipWorkflows.push_back(workflowPaths[i]);
  }

  const fs::path gatewayBinary = root / "core" / "build" / "careweave_gateway";
  if (!fs::exists(gatewayBinary)) {
    result.error = "the gateway binary was not built; build the core first "
                   "(core/build/careweave_gateway)";
    return result;
  }

  // ---- assemble
  if (fs::exists(out, ec)) {
    if (!options.replaceExisting) {
      result.error = "the output directory already exists: " + options.outDir;
      return result;
    }
    fs::remove_all(out, ec);
    if (ec) {
      result.error = "cannot clear " + options.outDir + ": " + ec.message();
      return result;
    }
  }
  fs::create_directories(out / "bin", ec);
  if (ec) {
    result.error = "cannot create " + options.outDir + ": " + ec.message();
    return result;
  }

  size_t files = 0;
  for (const ModuleInfo& module : bundledModules) {
    if (!copyFiltered(modulesSource / module.directory, out / "modules" / module.directory,
                      &files, &result.error)) {
      return result;
    }
    fs::create_directories(out / "modules" / module.directory / "data", ec);
  }
  result.modules = bundledModules.size();

  if (options.includeSpecs && fs::is_directory(root / "specs", ec)) {
    if (!copyFiltered(root / "specs", out / "specs", &files, &result.error, skipWorkflows)) {
      return result;
    }
  }

  const bool dashboardBuilt = options.includeDashboard &&
                              fs::is_directory(root / "dashboard", ec) &&
                              fs::exists(root / "dashboard" / "index.html");
  if (dashboardBuilt) {
    if (!copyFiltered(root / "dashboard", out / "dashboard", &files, &result.error)) {
      return result;
    }
    result.dashboardIncluded = true;
  } else {
    result.warnings.push_back(
        options.includeDashboard
            ? "the dashboard has not been built; the bundle serves the management API only"
            : "the dashboard was excluded by request");
  }

  fs::copy_file(gatewayBinary, out / "bin" / "careweave_gateway",
                fs::copy_options::overwrite_existing, ec);
  if (ec) {
    result.error = "cannot copy the gateway binary: " + ec.message();
    return result;
  }
  fs::permissions(out / "bin" / "careweave_gateway",
                  fs::perms::owner_exec | fs::perms::group_exec | fs::perms::others_exec,
                  fs::perm_options::add, ec);
  result.gatewayBinaryIncluded = true;
  ++files;

  fs::create_directories(out / "scripts", ec);
  std::string workflowLine;
  if (!options.includeWorkflows) {
    workflowLine = "none";
  } else if (!options.selectedWorkflows.empty()) {
    workflowLine = joinNames(result.workflows, ", ");
  }
  std::vector<std::string> selectionNotes;
  if (!result.requestedModules.empty()) {
    selectionNotes.push_back("requested modules: " + joinNames(result.requestedModules, ", "));
  }
  for (const auto& entry : result.closureAdded) {
    selectionNotes.push_back("added by workflow references: " + entry.first + " (" +
                             entry.second + ")");
  }
  if (!writeGenerated(out / "scripts" / "setup.sh", setupScript(), true, &result.error))
    return result;
  if (!writeGenerated(out / "scripts" / "start.sh", startScript(bundledModules), true,
                      &result.error)) {
    return result;
  }
  if (!writeGenerated(out / "scripts" / "stop.sh", stopScript(), true, &result.error))
    return result;
  if (!writeGenerated(out / "README.txt",
                      readmeText(bundledModules, result.dashboardIncluded, workflowLine,
                                 selectionNotes),
                      false, &result.error)) {
    return result;
  }
  files += 4;

  json manifest;
  manifest["format"] = 1;
  manifest["tool"] = "careweave bundle";
  manifest["modules"] = json::array();
  for (const ModuleInfo& module : bundledModules) {
    manifest["modules"].push_back(
        {{"id", module.id}, {"directory", module.directory}, {"port", module.port}});
  }
  manifest["requested_modules"] = result.requestedModules;
  json closureAdded = json::array();
  for (const auto& entry : result.closureAdded) {
    closureAdded.push_back({{"module", entry.first}, {"reason", entry.second}});
  }
  manifest["closure_added"] = closureAdded;
  manifest["workflows"] = result.workflows;
  ++files;  // the manifest itself belongs to the bundle inventory
  manifest["files"] = files;
  manifest["dashboard"] = result.dashboardIncluded;
  manifest["gateway_binary"] = "bin/careweave_gateway";
  manifest["notes"] = result.warnings;
  if (!writeGenerated(out / "MANIFEST.json", manifest.dump(2) + "\n", false, &result.error)) {
    return result;
  }

  result.files = files;
  result.ok = true;
  return result;
}

std::string BundleResult::render() const {
  json document;
  document["ok"] = ok;
  document["out_dir"] = outDir;
  document["modules"] = modules;
  document["files"] = files;
  document["dashboard"] = dashboardIncluded;
  document["gateway_binary"] = gatewayBinaryIncluded;
  document["requested_modules"] = requestedModules;
  json closureAddedJson = json::array();
  for (const auto& entry : closureAdded) {
    closureAddedJson.push_back({{"module", entry.first}, {"reason", entry.second}});
  }
  document["closure_added"] = closureAddedJson;
  document["workflows"] = workflows;
  document["warnings"] = warnings;
  if (!error.empty()) document["error"] = error;
  return document.dump(2) + "\n";
}

}  // namespace bundle
}  // namespace careweave
