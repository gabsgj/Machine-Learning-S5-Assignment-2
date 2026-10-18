#pragma once
// Delivery bundler.
//
// Assembles a self contained runnable bundle out of a built checkout: the Flask module servers
// without their runtime databases or caches, the specification sheets the gateway and the
// dashboard read, the built dashboard when it exists, the built gateway binary, generated
// setup, start and stop scripts and a manifest. Everything the generated scripts and documents
// contain is relative to the bundle root, which they derive from their own location, so a bundle
// can be copied anywhere and started from any working directory. The same function backs the
// `bundle` command of the command line front end and the management endpoint the dashboard
// calls. A caller can select which modules and workflow sheets travel in the bundle; the
// bundler then follows the workflow references and adds every module a shipped workflow binds,
// reporting each addition (the closure) in the result and the manifest.
#include <string>
#include <utility>
#include <vector>

namespace careweave {
namespace bundle {

struct BundleOptions {
  std::string rootDir;            // checkout root to assemble from
  std::string outDir;             // destination directory, created or replaced
  std::string displayPath;        // the path as the caller wrote it, echoed in the result
  bool includeDashboard = true;   // copy dashboard/ when it has been built
  bool includeSpecs = true;       // copy specs/
  bool replaceExisting = true;    // clear outDir before assembling
  // Module selection: empty bundles every module in the checkout; a non empty list bundles
  // exactly those modules plus the closure over the module ids the shipped workflow sheets
  // bind.
  std::vector<std::string> selectedModules;
  // Workflow selection: when includeWorkflows is true, an empty list ships every workflow
  // sheet, and a non empty list ships only the sheets whose file name stem or workflow_id is
  // named here.
  std::vector<std::string> selectedWorkflows;
  bool includeWorkflows = true;
};

struct BundleResult {
  bool ok = false;
  std::string error;
  std::string outDir;             // display path of the destination
  size_t modules = 0;
  size_t files = 0;               // regular files copied plus generated files
  bool dashboardIncluded = false;
  bool gatewayBinaryIncluded = false;
  std::vector<std::string> requestedModules;  // echoed selection; empty when everything bundled
  // Modules the bundle carries on top of the request because a shipped workflow sheet binds
  // them, each with its reason ("referenced by workflow <id>").
  std::vector<std::pair<std::string, std::string>> closureAdded;
  std::vector<std::string> workflows;         // shipped workflow sheet file names
  std::vector<std::string> warnings;
  std::string render() const;     // JSON summary for the CLI and the management endpoint
};

BundleResult createBundle(const BundleOptions& options);

}  // namespace bundle
}  // namespace careweave
