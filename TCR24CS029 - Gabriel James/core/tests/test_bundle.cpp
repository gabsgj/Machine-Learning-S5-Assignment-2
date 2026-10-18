// Bundler tests.
//
// The bundler is exercised against a fake checkout that mirrors the real layout: two module
// directories with specification sheets and runtime leftovers (databases, caches), a specs
// directory, a fake gateway binary and optionally a built dashboard. The tests then cover the
// assembly itself (inventory, exclusions, generated scripts, manifest, executable bits), the
// refusals (replacing the checkout, a missing gateway binary, a protected destination) and the
// path hygiene rule: nothing generated may contain an absolute path of the machine.
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#include <unistd.h>

#include "careweave/bundle/bundler.hpp"
#include "careweave/test/framework.hpp"
#include "nlohmann/json.hpp"

namespace fs = std::filesystem;
using careweave::bundle::BundleOptions;
using careweave::bundle::BundleResult;

namespace {

fs::path workspace() {
  static const fs::path dir = [] {
    const fs::path path =
        fs::temp_directory_path() / ("careweave_bundle_" + std::to_string(::getpid()));
    std::error_code error;
    fs::remove_all(path, error);
    fs::create_directories(path, error);
    return path;
  }();
  return dir;
}

void writeFile(const fs::path& path, const std::string& content) {
  fs::create_directories(path.parent_path());
  std::ofstream out(path, std::ios::binary | std::ios::trunc);
  out << content;
}

std::string readFile(const fs::path& path) {
  std::ifstream in(path, std::ios::binary);
  std::string content;
  in.seekg(0, std::ios::end);
  content.resize(static_cast<size_t>(in.tellg()));
  in.seekg(0);
  in.read(&content[0], static_cast<std::streamsize>(content.size()));
  return content;
}

// The fake checkout used by every case in this file. The name keeps independent cases apart,
// because a checkout may collect workflow sheets that other cases must not see.
fs::path makeCheckout(const std::string& name = "checkout") {
  const fs::path root = workspace() / name;
  writeFile(root / "modules" / "alpha" / "run.py", "print('alpha')\n");
  writeFile(root / "modules" / "alpha" / "requirements.txt", "flask\n");
  writeFile(root / "modules" / "alpha" / "spec.json",
            R"({"module": {"module_id": "alpha", "port": 5601}})");
  writeFile(root / "modules" / "alpha" / "data" / "alpha.db", "database bytes");
  writeFile(root / "modules" / "alpha" / "__pycache__" / "app.cpython-312.pyc", "cache bytes");
  writeFile(root / "modules" / "beta" / "run.py", "print('beta')\n");
  writeFile(root / "modules" / "beta" / "spec.json",
            R"({"module": {"module_id": "beta", "port": 5602}})");
  writeFile(root / "modules" / "beta" / "data" / "beta.db-wal", "wal bytes");
  writeFile(root / "specs" / "capability.schema.json", "{}\n");
  writeFile(root / "core" / "build" / "careweave_gateway", "#!/bin/sh\necho fake\n");
  return root;
}

bool isExecutable(const fs::path& path) {
  std::error_code error;
  const fs::perms permissions = fs::status(path, error).permissions();
  if (error) return false;
  return (permissions & fs::perms::owner_exec) != fs::perms::none;
}

size_t countMatching(const fs::path& root, const std::string& suffix) {
  size_t count = 0;
  std::error_code error;
  for (const fs::directory_entry& entry : fs::recursive_directory_iterator(root, error)) {
    const std::string name = entry.path().filename().string();
    if (name.size() >= suffix.size() &&
        name.compare(name.size() - suffix.size(), suffix.size(), suffix) == 0) {
      ++count;
    }
  }
  return count;
}

bool pathExists(const fs::path& path) {
  std::error_code error;
  return fs::exists(path, error);
}

}  // namespace

CW_TEST_CASE(bundle_assembles_modules_scripts_and_manifest) {
  const fs::path root = makeCheckout();
  const fs::path out = workspace() / "dist-mini";
  BundleOptions options;
  options.rootDir = root.string();
  options.outDir = out.string();
  options.displayPath = "dist-mini";
  const BundleResult result = careweave::bundle::createBundle(options);
  CW_CHECK_MSG(result.ok, result.error);
  if (!result.ok) return;
  CW_CHECK(result.modules == 2);
  CW_CHECK(result.gatewayBinaryIncluded);
  CW_CHECK(!result.dashboardIncluded);
  CW_CHECK(!result.warnings.empty());
  CW_CHECK(result.outDir == "dist-mini");
  CW_CHECK(result.files >= 10);

  // Modules travel with their sources and sheets but never with runtime data or caches.
  CW_CHECK(pathExists(out / "modules" / "alpha" / "run.py"));
  CW_CHECK(pathExists(out / "modules" / "alpha" / "requirements.txt"));
  CW_CHECK(pathExists(out / "modules" / "alpha" / "spec.json"));
  CW_CHECK(pathExists(out / "modules" / "beta" / "run.py"));
  CW_CHECK(fs::is_directory(out / "modules" / "alpha" / "data"));
  CW_CHECK(countMatching(out, ".db") == 0);
  CW_CHECK(countMatching(out, ".db-wal") == 0);
  CW_CHECK(countMatching(out, ".pyc") == 0);
  CW_CHECK(!pathExists(out / "modules" / "alpha" / "__pycache__"));

  CW_CHECK(pathExists(out / "specs" / "capability.schema.json"));
  CW_CHECK(isExecutable(out / "bin" / "careweave_gateway"));
  CW_CHECK(isExecutable(out / "scripts" / "setup.sh"));
  CW_CHECK(isExecutable(out / "scripts" / "start.sh"));
  CW_CHECK(isExecutable(out / "scripts" / "stop.sh"));

  const std::string start = readFile(out / "scripts" / "start.sh");
  CW_CHECK(start.find("start_module alpha 5601") != std::string::npos);
  CW_CHECK(start.find("start_module beta 5602") != std::string::npos);
  CW_CHECK(start.find("careweave_gateway") != std::string::npos);
  CW_CHECK(start.find("api/discover") != std::string::npos);
  // The pid file records the server process itself, not a wrapper, so stop.sh can stop it.
  CW_CHECK(start.find("exec env CAREWEAVE_PORT") != std::string::npos);
  const std::string stop = readFile(out / "scripts" / "stop.sh");
  CW_CHECK(stop.find("no process for") != std::string::npos);
  CW_CHECK(stop.find("\"$pid\"") != std::string::npos);

  // Nothing generated may contain an absolute path of this machine.
  const std::string rootText = root.string();
  CW_CHECK(start.find(rootText) == std::string::npos);
  const std::string readme = readFile(out / "README.txt");
  CW_CHECK(readme.find(rootText) == std::string::npos);
  const std::string manifestText = readFile(out / "MANIFEST.json");
  CW_CHECK(manifestText.find(rootText) == std::string::npos);

  const nlohmann::json manifest = nlohmann::json::parse(manifestText, nullptr, false);
  CW_CHECK(!manifest.is_discarded());
  CW_CHECK(manifest["modules"].size() == 2);
  CW_CHECK(manifest["modules"][0]["id"].get<std::string>() == "alpha");
  CW_CHECK(manifest["modules"][0]["port"].get<int>() == 5601);
  CW_CHECK(manifest["dashboard"].get<bool>() == false);
  CW_CHECK(manifest["gateway_binary"].get<std::string>() == "bin/careweave_gateway");
  CW_CHECK(manifest["files"].get<size_t>() == result.files);

  const std::string rendered = result.render();
  const nlohmann::json summary = nlohmann::json::parse(rendered, nullptr, false);
  CW_CHECK(!summary.is_discarded());
  CW_CHECK(summary["ok"].get<bool>());
  CW_CHECK(summary["out_dir"].get<std::string>() == "dist-mini");
}

CW_TEST_CASE(bundle_includes_the_dashboard_when_built_and_replaces_old_output) {
  const fs::path root = makeCheckout();
  writeFile(root / "dashboard" / "index.html", "<html>dashboard</html>\n");
  writeFile(root / "dashboard" / "app.js", "console.log('offline')\n");

  const fs::path out = workspace() / "dist-with-dashboard";
  BundleOptions options;
  options.rootDir = root.string();
  options.outDir = out.string();
  const BundleResult first = careweave::bundle::createBundle(options);
  CW_CHECK_MSG(first.ok, first.error);
  if (!first.ok) return;
  CW_CHECK(first.dashboardIncluded);
  CW_CHECK(first.warnings.empty());
  CW_CHECK(pathExists(out / "dashboard" / "index.html"));
  CW_CHECK(pathExists(out / "dashboard" / "app.js"));

  // A second run replaces the destination, so stale files never survive a rebuild.
  writeFile(out / "stale.txt", "old output\n");
  const BundleResult second = careweave::bundle::createBundle(options);
  CW_CHECK_MSG(second.ok, second.error);
  CW_CHECK(!pathExists(out / "stale.txt"));
}

CW_TEST_CASE(bundle_refuses_unsafe_assemblies) {
  const fs::path root = makeCheckout();

  // Replacing the checkout itself, or a directory that contains it, is refused.
  BundleOptions overRoot;
  overRoot.rootDir = root.string();
  overRoot.outDir = root.string();
  const BundleResult self = careweave::bundle::createBundle(overRoot);
  CW_CHECK(!self.ok);
  CW_CHECK(self.error.find("refusing") != std::string::npos);
  CW_CHECK(pathExists(root / "modules" / "alpha" / "run.py"));

  BundleOptions ancestor;
  ancestor.rootDir = root.string();
  ancestor.outDir = root.parent_path().string();
  const BundleResult over = careweave::bundle::createBundle(ancestor);
  CW_CHECK(!over.ok);
  CW_CHECK(pathExists(root / "modules" / "alpha" / "run.py"));

  // A missing gateway binary is a clear error, not a broken bundle.
  const fs::path bare = workspace() / "bare";
  writeFile(bare / "modules" / "alpha" / "run.py", "print('alpha')\n");
  writeFile(bare / "modules" / "alpha" / "spec.json",
            R"({"module": {"module_id": "alpha", "port": 5601}})");
  BundleOptions noBinary;
  noBinary.rootDir = bare.string();
  noBinary.outDir = (workspace() / "dist-bare").string();
  const BundleResult missing = careweave::bundle::createBundle(noBinary);
  CW_CHECK(!missing.ok);
  CW_CHECK(missing.error.find("gateway binary") != std::string::npos);

  // replaceExisting=false protects an existing destination.
  const fs::path out = workspace() / "dist-protected";
  writeFile(out / "keep.txt", "keep\n");
  BundleOptions protectedOut;
  protectedOut.rootDir = root.string();
  protectedOut.outDir = out.string();
  protectedOut.replaceExisting = false;
  const BundleResult kept = careweave::bundle::createBundle(protectedOut);
  CW_CHECK(!kept.ok);
  CW_CHECK(kept.error.find("already exists") != std::string::npos);
  CW_CHECK(pathExists(out / "keep.txt"));
}

CW_TEST_CASE(bundle_selects_modules_and_adds_the_workflow_closure) {
  const fs::path root = makeCheckout("checkout-closure");
  writeFile(root / "specs" / "workflows" / "alpha_visit.json",
            R"({"workflow_id": "alpha-visit", "steps": [
                 {"name": "register", "module": "alpha", "capability": "A-Register"}]})");
  writeFile(root / "specs" / "workflows" / "beta_visit.json",
            R"({"workflow_id": "beta-visit", "steps": [
                 {"name": "pay", "module": "beta", "capability": "B-Pay"},
                 {"name": "report", "requirement": "specs/app/requirements/report.yaml"}]})");
  const std::string rootText = root.string();

  // A selected bundle ships the requested module and the requested workflow, nothing else. The
  // workflow may be named by its id or by its file stem.
  const fs::path out = workspace() / "dist-selected";
  BundleOptions selected;
  selected.rootDir = root.string();
  selected.outDir = out.string();
  selected.displayPath = "dist-selected";
  selected.selectedModules = {"alpha"};
  selected.selectedWorkflows = {"alpha-visit"};
  const BundleResult selectedResult = careweave::bundle::createBundle(selected);
  CW_CHECK_MSG(selectedResult.ok, selectedResult.error);
  if (!selectedResult.ok) return;
  CW_CHECK(selectedResult.modules == 1);
  CW_CHECK(selectedResult.requestedModules.size() == 1);
  CW_CHECK(selectedResult.requestedModules[0] == "alpha");
  CW_CHECK(selectedResult.closureAdded.empty());
  CW_CHECK(selectedResult.workflows.size() == 1);
  if (!selectedResult.workflows.empty()) {
    CW_CHECK(selectedResult.workflows[0] == "alpha_visit.json");
  }
  CW_CHECK(pathExists(out / "modules" / "alpha" / "run.py"));
  CW_CHECK(!pathExists(out / "modules" / "beta"));
  CW_CHECK(pathExists(out / "specs" / "workflows" / "alpha_visit.json"));
  CW_CHECK(!pathExists(out / "specs" / "workflows" / "beta_visit.json"));
  const std::string start = readFile(out / "scripts" / "start.sh");
  CW_CHECK(start.find("start_module alpha 5601") != std::string::npos);
  CW_CHECK(start.find("start_module beta") == std::string::npos);
  const std::string readme = readFile(out / "README.txt");
  CW_CHECK(readme.find("requested modules: alpha") != std::string::npos);
  CW_CHECK(readme.find("workflow sheets shipped: alpha_visit.json") != std::string::npos);
  CW_CHECK(readme.find(rootText) == std::string::npos);
  const std::string manifestText = readFile(out / "MANIFEST.json");
  CW_CHECK(manifestText.find(rootText) == std::string::npos);
  const nlohmann::json manifest = nlohmann::json::parse(manifestText, nullptr, false);
  CW_CHECK(!manifest.is_discarded());
  CW_CHECK(manifest["modules"].size() == 1);
  CW_CHECK(manifest["modules"][0]["id"].get<std::string>() == "alpha");
  CW_CHECK(manifest["requested_modules"].size() == 1);
  CW_CHECK(manifest["closure_added"].empty());
  CW_CHECK(manifest["workflows"].size() == 1);
  const nlohmann::json summary = nlohmann::json::parse(selectedResult.render(), nullptr, false);
  CW_CHECK(!summary.is_discarded());
  CW_CHECK(summary["requested_modules"].size() == 1);
  CW_CHECK(summary["closure_added"].empty());
  CW_CHECK(summary["workflows"].size() == 1);

  // Without a workflow filter the other workflow ships too, and the bundler adds the module its
  // steps bind: the closure keeps a selected bundle runnable exactly as shipped.
  const fs::path closureOut = workspace() / "dist-closure";
  BundleOptions closure;
  closure.rootDir = root.string();
  closure.outDir = closureOut.string();
  closure.selectedModules = {"alpha"};
  const BundleResult closureResult = careweave::bundle::createBundle(closure);
  CW_CHECK_MSG(closureResult.ok, closureResult.error);
  if (!closureResult.ok) return;
  CW_CHECK(closureResult.modules == 2);
  CW_CHECK(closureResult.closureAdded.size() == 1);
  if (closureResult.closureAdded.size() == 1) {
    CW_CHECK(closureResult.closureAdded[0].first == "beta");
    CW_CHECK(closureResult.closureAdded[0].second == "referenced by workflow beta-visit");
  }
  CW_CHECK(pathExists(closureOut / "modules" / "beta" / "run.py"));
  const std::string closureStart = readFile(closureOut / "scripts" / "start.sh");
  CW_CHECK(closureStart.find("start_module beta 5602") != std::string::npos);
  const std::string closureReadme = readFile(closureOut / "README.txt");
  CW_CHECK(closureReadme.find(
               "added by workflow references: beta (referenced by workflow beta-visit)") !=
           std::string::npos);
  const nlohmann::json closureManifest =
      nlohmann::json::parse(readFile(closureOut / "MANIFEST.json"), nullptr, false);
  CW_CHECK(!closureManifest.is_discarded());
  CW_CHECK(closureManifest["closure_added"].size() == 1);
  CW_CHECK(closureManifest["closure_added"][0]["module"].get<std::string>() == "beta");

  // Inside a filtered workflow set the closure follows only the sheets that ship, so the
  // unfiltered sibling stays out.
  const fs::path subsetOut = workspace() / "dist-subset";
  BundleOptions subset;
  subset.rootDir = root.string();
  subset.outDir = subsetOut.string();
  subset.selectedModules = {"alpha"};
  subset.selectedWorkflows = {"beta_visit"};
  const BundleResult subsetResult = careweave::bundle::createBundle(subset);
  CW_CHECK_MSG(subsetResult.ok, subsetResult.error);
  if (!subsetResult.ok) return;
  CW_CHECK(subsetResult.modules == 2);
  CW_CHECK(subsetResult.workflows.size() == 1);
  if (!subsetResult.workflows.empty()) {
    CW_CHECK(subsetResult.workflows[0] == "beta_visit.json");
  }
  CW_CHECK(!pathExists(subsetOut / "specs" / "workflows" / "alpha_visit.json"));
  CW_CHECK(subsetResult.closureAdded.size() == 1);

  // A bundle may travel without workflows at all: no sheets, no closure, and the README says so.
  const fs::path frozenOut = workspace() / "dist-frozen";
  BundleOptions frozen;
  frozen.rootDir = root.string();
  frozen.outDir = frozenOut.string();
  frozen.selectedModules = {"alpha"};
  frozen.includeWorkflows = false;
  const BundleResult frozenResult = careweave::bundle::createBundle(frozen);
  CW_CHECK_MSG(frozenResult.ok, frozenResult.error);
  if (!frozenResult.ok) return;
  CW_CHECK(frozenResult.modules == 1);
  CW_CHECK(frozenResult.workflows.empty());
  CW_CHECK(!pathExists(frozenOut / "specs" / "workflows" / "alpha_visit.json"));
  CW_CHECK(!pathExists(frozenOut / "specs" / "workflows" / "beta_visit.json"));
  const std::string frozenReadme = readFile(frozenOut / "README.txt");
  CW_CHECK(frozenReadme.find("workflow sheets shipped: none") != std::string::npos);
  const nlohmann::json frozenManifest =
      nlohmann::json::parse(readFile(frozenOut / "MANIFEST.json"), nullptr, false);
  CW_CHECK(!frozenManifest.is_discarded());
  CW_CHECK(frozenManifest["workflows"].empty());
}

CW_TEST_CASE(bundle_refuses_unknown_selections) {
  const fs::path root = makeCheckout("checkout-refusals");
  writeFile(root / "specs" / "workflows" / "alpha_visit.json",
            R"({"workflow_id": "alpha-visit", "steps": [
                 {"name": "register", "module": "alpha", "capability": "A-Register"}]})");

  // Unknown module ids and workflow names are refusals that name the known values.
  const fs::path unknownModuleOut = workspace() / "dist-unknown-module";
  BundleOptions unknownModule;
  unknownModule.rootDir = root.string();
  unknownModule.outDir = unknownModuleOut.string();
  unknownModule.selectedModules = {"ghost"};
  const BundleResult moduleRefusal = careweave::bundle::createBundle(unknownModule);
  CW_CHECK(!moduleRefusal.ok);
  CW_CHECK(moduleRefusal.error.find("ghost") != std::string::npos);
  CW_CHECK(moduleRefusal.error.find("known ids: alpha, beta") != std::string::npos);

  BundleOptions unknownWorkflow;
  unknownWorkflow.rootDir = root.string();
  unknownWorkflow.outDir = (workspace() / "dist-unknown-workflow").string();
  unknownWorkflow.selectedWorkflows = {"ghost"};
  const BundleResult workflowRefusal = careweave::bundle::createBundle(unknownWorkflow);
  CW_CHECK(!workflowRefusal.ok);
  CW_CHECK(workflowRefusal.error.find("no workflow sheet matches ghost") != std::string::npos);
  CW_CHECK(workflowRefusal.error.find("alpha_visit (alpha-visit)") != std::string::npos);

  // A shipped workflow that binds a module the checkout does not have is a refusal.
  writeFile(root / "specs" / "workflows" / "ghost_visit.json",
            R"({"workflow_id": "ghost-visit", "steps": [
                 {"name": "call", "module": "ghost", "capability": "G-Call"}]})");
  BundleOptions unknownBinding;
  unknownBinding.rootDir = root.string();
  unknownBinding.outDir = (workspace() / "dist-unknown-binding").string();
  unknownBinding.selectedModules = {"alpha"};
  const BundleResult bindingRefusal = careweave::bundle::createBundle(unknownBinding);
  CW_CHECK(!bindingRefusal.ok);
  CW_CHECK(bindingRefusal.error.find("ghost-visit binds unknown module ghost") !=
           std::string::npos);

  // A workflow sheet that is not JSON is a refusal too, before anything is written.
  const fs::path broken = makeCheckout("checkout-broken");
  writeFile(broken / "specs" / "workflows" / "broken.json", "not a json document\n");
  BundleOptions brokenSheet;
  brokenSheet.rootDir = broken.string();
  brokenSheet.outDir = (workspace() / "dist-broken-sheet").string();
  const BundleResult brokenRefusal = careweave::bundle::createBundle(brokenSheet);
  CW_CHECK(!brokenRefusal.ok);
  CW_CHECK(brokenRefusal.error.find("not JSON") != std::string::npos);
  CW_CHECK(brokenRefusal.error.find("specs/workflows/broken.json") != std::string::npos);

  // Selecting workflows without shipping the specification sheets is refused.
  BundleOptions noSpecs;
  noSpecs.rootDir = root.string();
  noSpecs.outDir = (workspace() / "dist-no-specs").string();
  noSpecs.includeSpecs = false;
  noSpecs.selectedWorkflows = {"alpha_visit"};
  const BundleResult noSpecsRefusal = careweave::bundle::createBundle(noSpecs);
  CW_CHECK(!noSpecsRefusal.ok);
  CW_CHECK(noSpecsRefusal.error.find("specification sheets") != std::string::npos);

  // No refusal wrote anything.
  CW_CHECK(!pathExists(unknownModuleOut));
  CW_CHECK(!pathExists(workspace() / "dist-unknown-workflow"));
  CW_CHECK(!pathExists(workspace() / "dist-unknown-binding"));
  CW_CHECK(!pathExists(workspace() / "dist-broken-sheet"));
  CW_CHECK(!pathExists(workspace() / "dist-no-specs"));
}

int main() { return careweave::testing::runAll("test_bundle"); }