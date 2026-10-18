// Command line front end of the CareWeave Mini core.
//
// Subcommands:
//
//   validate <spec file>...
//       Parse one or more specification sheets, print every validation issue and exit non zero
//       when any sheet is rejected. Uses the real parser with schema validation enabled.
//
//   spec-yaml <spec.json>... [--out <path>]
//       Generate the YAML form of a specification sheet from its canonical JSON form (next to
//       the input unless --out is given), then reload the generated file and prove that both
//       forms decode to the same application model.
//
//   embed <spec file> [--capability <id>] [--similarity] [--json]
//       Print the partitioned capability vector of every capability of a sheet: the block names,
//       their sizes and norms, and with --similarity the pairwise cosine table in the functional
//       and implementation views.
//
//   compare <application sheet> <earlier capability id> <later capability id> [--json]
//       Run the symbolic compatibility engine on two capabilities of one application and print
//       the full explainable report: entailment items, every check with its outcome, the
//       rejections, the vector scores and the final verdict.
//
//   mapping <requirement sheet> --pool <spec file>... [--min-score X] [--margin Y] [--top N]
//       Rank every capability of the pool sheets against the single requirement capability and
//       print the score breakdown, the ranked list and the selection (selected, ambiguous or
//       rejected). This is the command line form of the resolve step used by the experiments.
//
//   adapters <requirement sheet> --pool <spec file>... [--module <id>] [--base-url <url>]
//            [--out <dir>] [--json]
//       Resolve the requirement, synthesize the executable adapter for the best candidate with
//       the real synthesizer and either print it (--json) or write the adapter JSON and the
//       emitted C++ into generated/adapters/ (or the --out directory).
//
//   plan <spec file> [--goal "var=value"] [--strategy fewest|time|money|reliability]
//        [--max-depth N] [--backward] [--json]
//       Background planner, outside the Assignment 2 evaluation scope: forward or backward
//       search from the sheet's initial state to its goal, with the search statistics, the
//       aggregated operational attributes and the explanation.
//
//   run <requirement sheet> [--inputs k=v,...] [--preferred <module,...>]
//       [--allow-modules <module,...>] [--resolve-only] [--gateway <url>] [--json]
//   run --workflow <workflow file> [--gateway <url>] [--json]
//       Client of a running gateway: resolve candidates, execute a requirement through the
//       canonical API with fallback, or run a workflow file, printing the outcome.
//
//   bundle [--root <dir>] [--out <dir>] [--modules <id,...>] [--workflows <name,...>]
//       [--no-workflows] [--no-dashboard] [--json]
//       Assemble the self contained runtime bundle: the modules, the specification sheets, the
//       dashboard when it has been built, the gateway binary, setup/start/stop scripts and a
//       manifest. A module selection is completed with the workflow closure.
//
//   export <spec file>... [--what specs|compat|embedding] [--out <dir>] [--json]
//       Export machine readable artifacts: the canonical JSON of the sheets, the compatibility
//       matrix of one sheet or the embedding table of one sheet, as CSV and JSON.

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "careweave/adapter/adapter.hpp"
#include "careweave/adapter/cpp_emitter.hpp"
#include "careweave/adapter/synthesizer.hpp"
#include "careweave/bundle/bundler.hpp"
#include "careweave/compat/compat_engine.hpp"
#include "careweave/core/value_json.hpp"
#include "careweave/embedding/encoders.hpp"
#include "careweave/embedding/vector.hpp"
#include "careweave/mapper/mapper.hpp"
#include "careweave/planner/planner.hpp"
#include "careweave/spec/spec_parser.hpp"
#include "httplib.h"
#include "nlohmann/json.hpp"

namespace {

int printUsage() {
  std::fprintf(stderr,
               "usage:\n"
               "  careweave_cli validate <spec file>...\n"
               "  careweave_cli spec-yaml <spec.json>... [--out <path>]\n"
               "  careweave_cli embed <spec file> [--capability <id>] [--similarity] [--json]\n"
               "  careweave_cli compare <application sheet> <earlier id> <later id> [--json]\n"
               "  careweave_cli mapping <requirement sheet> --pool <spec file>..."
               " [--min-score X] [--margin Y] [--top N]\n"
               "  careweave_cli adapters <requirement sheet> --pool <spec file>..."
               " [--module <id>] [--base-url <url>] [--out <dir>] [--json]\n"
               "  careweave_cli plan <spec file> [--goal \"var=value\"]"
               " [--strategy fewest|time|money|reliability] [--max-depth N] [--backward]"
               " [--json]\n"
               "  careweave_cli run <requirement sheet> [--inputs k=v,...]"
               " [--preferred <module,...>] [--allow-modules <module,...>] [--resolve-only]"
               " [--gateway <url>] [--json]\n"
               "  careweave_cli run --workflow <workflow file> [--gateway <url>] [--json]\n"
               "  careweave_cli bundle [--root <dir>] [--out <dir>] [--modules <id,...>]"
               " [--workflows <name,...>] [--no-workflows] [--no-dashboard] [--json]\n"
               "  careweave_cli export <spec file>... [--what specs|compat|embedding]"
               " [--out <dir>]\n");
  return 2;
}

std::string yamlPathFor(const std::string& jsonPath) {
  if (jsonPath.size() > 5 && jsonPath.compare(jsonPath.size() - 5, 5, ".json") == 0) {
    return jsonPath.substr(0, jsonPath.size() - 5) + ".yaml";
  }
  return jsonPath + ".yaml";
}

int commandValidate(const std::vector<std::string>& files) {
  if (files.empty()) return printUsage();
  int failures = 0;
  for (const std::string& file : files) {
    careweave::spec::SpecParseOptions options;
    options.requireSchema = true;
    const careweave::spec::SpecParseResult result = careweave::spec::loadSpecFile(file, options);
    if (result.ok) {
      std::printf("ok   %s (%zu capabilities, %zu state variables)\n", file.c_str(),
                  result.model.capabilities.size(), result.model.stateSchema.size());
    } else {
      ++failures;
      std::printf("fail %s\n%s", file.c_str(), result.renderIssues().c_str());
    }
  }
  if (failures != 0) {
    std::printf("%d specification sheet(s) rejected\n", failures);
  }
  return failures == 0 ? 0 : 1;
}

int commandSpecYaml(const std::vector<std::string>& args) {
  std::vector<std::string> inputs;
  std::string outPath;
  for (size_t i = 0; i < args.size(); ++i) {
    if (args[i] == "--out") {
      if (i + 1 >= args.size()) return printUsage();
      outPath = args[++i];
    } else {
      inputs.push_back(args[i]);
    }
  }
  if (inputs.empty()) return printUsage();
  if (!outPath.empty() && inputs.size() > 1) {
    std::fprintf(stderr, "--out accepts a single input sheet\n");
    return 2;
  }

  int failures = 0;
  for (const std::string& input : inputs) {
    careweave::spec::SpecParseOptions options;
    options.requireSchema = true;
    const careweave::spec::SpecParseResult source = careweave::spec::loadSpecFile(input, options);
    if (!source.ok) {
      ++failures;
      std::printf("fail %s\n%s", input.c_str(), source.renderIssues().c_str());
      continue;
    }
    const std::string target = outPath.empty() ? yamlPathFor(input) : outPath;
    std::string error;
    if (!careweave::spec::writeSpecYaml(source.model, target, &error)) {
      ++failures;
      std::printf("fail %s: %s\n", target.c_str(), error.c_str());
      continue;
    }
    const careweave::spec::SpecParseResult reloaded =
        careweave::spec::loadSpecFile(target, options);
    if (!reloaded.ok) {
      ++failures;
      std::printf("fail %s: the generated YAML does not parse\n%s", target.c_str(),
                  reloaded.renderIssues().c_str());
      continue;
    }
    const nlohmann::json before = careweave::spec::specToJson(source.model);
    const nlohmann::json after = careweave::spec::specToJson(reloaded.model);
    if (before != after) {
      ++failures;
      std::printf("fail %s: the YAML form decodes to a different model\n", target.c_str());
      continue;
    }
    std::printf("ok   %s (equal model, %zu capabilities)\n", target.c_str(),
                reloaded.model.capabilities.size());
  }
  return failures == 0 ? 0 : 1;
}

int commandMapping(const std::vector<std::string>& args) {
  if (args.empty()) return printUsage();
  const std::string requirementPath = args[0];
  std::vector<std::string> poolPaths;
  double minScore = 0.55;  // calibrated: intended mappings >= 0.7909, adversarial decoys <= 0.4962
  double margin = 0.05;
  size_t top = 5;
  for (size_t i = 1; i < args.size(); ++i) {
    const std::string& arg = args[i];
    auto value = [&](const char* name) -> const char* {
      if (i + 1 >= args.size()) {
        std::fprintf(stderr, "%s needs a value\n", name);
        return nullptr;
      }
      return args[++i].c_str();
    };
    if (arg == "--pool") {
      const char* path = value("--pool");
      if (path == nullptr) return 2;
      poolPaths.push_back(path);
    } else if (arg == "--min-score") {
      const char* text = value("--min-score");
      if (text == nullptr) return 2;
      minScore = std::strtod(text, nullptr);
    } else if (arg == "--margin") {
      const char* text = value("--margin");
      if (text == nullptr) return 2;
      margin = std::strtod(text, nullptr);
    } else if (arg == "--top") {
      const char* text = value("--top");
      if (text == nullptr) return 2;
      top = static_cast<size_t>(std::strtoul(text, nullptr, 10));
    } else if (!arg.empty() && arg[0] == '-') {
      std::fprintf(stderr, "unknown mapping argument \"%s\"\n", arg.c_str());
      return printUsage();
    } else {
      poolPaths.push_back(arg);
    }
  }
  if (poolPaths.empty()) {
    std::fprintf(stderr, "mapping needs at least one --pool sheet\n");
    return printUsage();
  }

  careweave::spec::SpecParseOptions options;
  options.requireSchema = true;
  const careweave::spec::SpecParseResult requirement = careweave::spec::loadSpecFile(requirementPath, options);
  if (!requirement.ok) {
    std::printf("fail %s\n%s", requirementPath.c_str(), requirement.renderIssues().c_str());
    return 1;
  }
  if (requirement.model.capabilities.size() != 1) {
    std::printf("fail %s: a requirement sheet declares exactly one capability, found %zu\n",
                requirementPath.c_str(), requirement.model.capabilities.size());
    return 1;
  }

  std::vector<careweave::core::CapabilitySpec> candidates;
  for (const std::string& poolPath : poolPaths) {
    const careweave::spec::SpecParseResult pool = careweave::spec::loadSpecFile(poolPath, options);
    if (!pool.ok) {
      std::printf("fail %s\n%s", poolPath.c_str(), pool.renderIssues().c_str());
      return 1;
    }
    for (const auto& capability : pool.model.capabilities) candidates.push_back(capability);
  }

  const careweave::core::CapabilitySpec& requirementCapability =
      requirement.model.capabilities.front();
  std::printf("requirement %s (%s) against %zu candidate(s)\n", requirementCapability.id.c_str(),
              requirementCapability.name.c_str(), candidates.size());

  const careweave::mapper::Mapper mapper;
  const std::vector<careweave::mapper::MatchResult> ranked = mapper.rank(requirementCapability, candidates);
  const careweave::mapper::Mapper::Selection selection =
      mapper.select(ranked, minScore, margin);
  const size_t shown = top == 0 ? ranked.size() : std::min(top, ranked.size());
  for (size_t i = 0; i < shown; ++i) {
    const careweave::mapper::MatchResult& match = ranked[i];
    std::printf("%2zu. %-28s %-22s total %.4f [name %.4f, fields %.4f, conditions %.4f]\n",
                i + 1, match.candidateId.c_str(), match.candidateName.c_str(), match.total,
                match.nameSimilarity, match.fieldSimilarity, match.conditionSimilarity);
  }

  if (selection.bestIndex < 0) {
    std::printf("REJECTED: the best candidate scores %.4f, below the threshold %.2f\n",
                ranked.empty() ? 0.0 : ranked[0].total, minScore);
    return 1;
  }
  const careweave::mapper::MatchResult& best = ranked[static_cast<size_t>(selection.bestIndex)];
  if (selection.ambiguous) {
    const careweave::mapper::MatchResult& runnerUp =
        ranked[static_cast<size_t>(selection.bestIndex) + 1];
    std::printf("AMBIGUOUS: %s (%.4f) over %s (%.4f), margin %.4f\n", best.candidateId.c_str(),
                best.total, runnerUp.candidateId.c_str(), runnerUp.total, selection.margin);
  } else if (selection.kindTieBreak) {
    const careweave::mapper::MatchResult& over =
        ranked[selection.bestIndex == 0 ? 1 : 0];
    std::printf("SELECTED BY KIND: %s (%.4f) over %s (%.4f), margin %.4f, delivery kind %s\n",
                best.candidateId.c_str(), best.total, over.candidateId.c_str(), over.total,
                selection.margin,
                careweave::core::capabilityTypeToString(requirementCapability.type).c_str());
  } else {
    std::printf("SELECTED: %s (%s) total %.4f, margin %.4f\n", best.candidateId.c_str(),
                best.candidateName.c_str(), best.total, selection.margin);
  }
  std::printf("%s", best.render().c_str());
  return 0;
}

int commandCompare(const std::vector<std::string>& args) {
  std::vector<std::string> positional;
  bool asJson = false;
  for (const std::string& arg : args) {
    if (arg == "--json") {
      asJson = true;
    } else if (!arg.empty() && arg[0] == '-') {
      std::fprintf(stderr, "unknown compare argument \"%s\"\n", arg.c_str());
      return printUsage();
    } else {
      positional.push_back(arg);
    }
  }
  if (positional.size() != 3) return printUsage();
  const std::string& appPath = positional[0];
  const std::string& earlierId = positional[1];
  const std::string& laterId = positional[2];

  careweave::spec::SpecParseOptions options;
  options.requireSchema = true;
  const careweave::spec::SpecParseResult appSheet = careweave::spec::loadSpecFile(appPath, options);
  if (!appSheet.ok) {
    std::printf("fail %s\n%s", appPath.c_str(), appSheet.renderIssues().c_str());
    return 1;
  }
  const auto findCapability = [&](const std::string& id) {
    return std::find_if(appSheet.model.capabilities.begin(), appSheet.model.capabilities.end(),
                        [&](const careweave::core::CapabilitySpec& s) { return s.id == id; });
  };
  const auto earlier = findCapability(earlierId);
  const auto later = findCapability(laterId);
  if (earlier == appSheet.model.capabilities.end()) {
    std::printf("fail %s: capability \"%s\" not found\n", appPath.c_str(), earlierId.c_str());
    return 1;
  }
  if (later == appSheet.model.capabilities.end()) {
    std::printf("fail %s: capability \"%s\" not found\n", appPath.c_str(), laterId.c_str());
    return 1;
  }

  const careweave::compat::CompatEngine engine(appSheet.model);
  const careweave::compat::CompatibilityReport report = engine.check(*earlier, *later);
  if (asJson) {
    std::printf("%s\n", report.toJsonString().c_str());
  } else {
    std::printf("compare %s then %s in %s\n", earlierId.c_str(), laterId.c_str(), appPath.c_str());
    std::printf("verdict %s\n", careweave::compat::verdictToString(report.verdict).c_str());
    std::printf("entailment %s\n", report.entailment.render().c_str());
    for (const careweave::compat::CheckResult& check : report.checks) {
      std::printf("  check %-24s %-8s %s\n", check.name.c_str(),
                  careweave::compat::outcomeToString(check.outcome).c_str(), check.detail.c_str());
    }
    for (const std::string& rejection : report.rejections) {
      std::printf("  rejection %s\n", rejection.c_str());
    }
    std::printf("scores coverage %.4f signed cosine %.4f vector %.4f functional %.4f "
                "implementation %.4f\n",
                report.scores.coverage, report.scores.signedCosine, report.scores.vectorScore,
                report.scores.functionalSimilarity, report.scores.implementationSimilarity);
  }
  return report.hasFailed() ? 1 : 0;
}

// ---- shared helpers for the pipeline commands ----

// Typed parsing for `k=v` values: true and false become booleans, clean integers and reals
// keep their JSON number types, everything else stays a string.
careweave::core::Value parseTypedValue(const std::string& text) {
  if (text == "true") return careweave::core::Value(true);
  if (text == "false") return careweave::core::Value(false);
  if (!text.empty()) {
    char* end = nullptr;
    const long long integer = std::strtoll(text.c_str(), &end, 10);
    if (end != nullptr && *end == '\0') {
      return careweave::core::Value(static_cast<int64_t>(integer));
    }
    end = nullptr;
    const double number = std::strtod(text.c_str(), &end);
    if (end != nullptr && *end == '\0') {
      return careweave::core::Value(number);
    }
  }
  return careweave::core::Value(text);
}

std::vector<std::string> splitList(const std::string& text) {
  std::vector<std::string> parts;
  std::string current;
  for (const char character : text) {
    if (character == ',') {
      if (!current.empty()) parts.push_back(current);
      current.clear();
    } else {
      current.push_back(character);
    }
  }
  if (!current.empty()) parts.push_back(current);
  return parts;
}

std::string joinNames(const std::vector<std::string>& names) {
  std::string text;
  for (const std::string& name : names) {
    if (!text.empty()) text += ", ";
    text += name;
  }
  return text;
}

bool parseInputs(const std::string& text, std::map<std::string, careweave::core::Value>* inputs,
                 std::string* error) {
  for (const std::string& part : splitList(text)) {
    const size_t equals = part.find('=');
    if (equals == std::string::npos || equals == 0) {
      *error = "inputs are written name=value, got \"" + part + "\"";
      return false;
    }
    (*inputs)[part.substr(0, equals)] = parseTypedValue(part.substr(equals + 1));
  }
  return true;
}

bool loadSheet(const std::string& path, careweave::spec::SpecParseResult* sheet) {
  careweave::spec::SpecParseOptions options;
  options.requireSchema = true;
  *sheet = careweave::spec::loadSpecFile(path, options);
  if (!sheet->ok) {
    std::printf("fail %s\n%s", path.c_str(), sheet->renderIssues().c_str());
  }
  return sheet->ok;
}

bool writeText(const std::string& path, const std::string& content, std::string* error) {
  const size_t slash = path.find_last_of('/');
  if (slash != std::string::npos) {
    std::error_code ignored;
    std::filesystem::create_directories(path.substr(0, slash), ignored);
  }
  std::ofstream out(path, std::ios::binary | std::ios::trunc);
  if (!out) {
    *error = "cannot write " + path;
    return false;
  }
  out << content;
  return true;
}

// ---- embed ----

int commandEmbed(const std::vector<std::string>& args) {
  if (args.empty()) return printUsage();
  const std::string sheetPath = args[0];
  std::string onlyId;
  bool similarity = false;
  bool asJson = false;
  for (size_t i = 1; i < args.size(); ++i) {
    const std::string& arg = args[i];
    if (arg == "--capability") {
      if (i + 1 >= args.size()) return printUsage();
      onlyId = args[++i];
    } else if (arg == "--similarity") {
      similarity = true;
    } else if (arg == "--json") {
      asJson = true;
    } else {
      std::fprintf(stderr, "unknown embed argument \"%s\"\n", arg.c_str());
      return printUsage();
    }
  }
  careweave::spec::SpecParseResult sheet;
  if (!loadSheet(sheetPath, &sheet)) return 1;

  const careweave::embedding::Encoder encoder;
  std::vector<careweave::embedding::EncodedCapability> encoded;
  for (const careweave::core::CapabilitySpec& capability : sheet.model.capabilities) {
    if (!onlyId.empty() && capability.id != onlyId) continue;
    encoded.push_back(encoder.encodeCapabilityDetailed(capability));
  }
  if (encoded.empty()) {
    std::printf("fail %s: no capability matches \"%s\"\n", sheetPath.c_str(), onlyId.c_str());
    return 1;
  }

  nlohmann::json document;
  if (asJson) {
    document["sheet"] = sheetPath;
    document["capabilities"] = nlohmann::json::array();
  } else {
    std::printf("embedding of %s (%zu capabilities)\n", sheetPath.c_str(), encoded.size());
  }
  for (const careweave::embedding::EncodedCapability& capability : encoded) {
    if (asJson) {
      nlohmann::json blocks = nlohmann::json::object();
      for (const auto& block : capability.blocks) {
        blocks[block.first] = {{"size", block.second.size()},
                               {"norm", careweave::embedding::VectorMath::norm(block.second)}};
      }
      document["capabilities"].push_back({{"id", capability.id},
                                          {"name", capability.name},
                                          {"dimensions", capability.vector.size()},
                                          {"blocks", blocks}});
    } else {
      std::printf("capability %s %s: %zu dimensions\n", capability.id.c_str(),
                  capability.name.c_str(), capability.vector.size());
      for (const auto& block : capability.blocks) {
        std::printf("  block %-15s %4zu dims, norm %8.4f\n", block.first.c_str(),
                    block.second.size(), careweave::embedding::VectorMath::norm(block.second));
      }
    }
  }

  if (similarity) {
    if (asJson) document["comparisons"] = nlohmann::json::array();
    else std::printf("pairwise similarity (total, functional, implementation)\n");
    for (size_t i = 0; i < encoded.size(); ++i) {
      for (size_t j = i + 1; j < encoded.size(); ++j) {
        const double total =
            careweave::embedding::VectorMath::cosine(encoded[i].vector, encoded[j].vector);
        const double functional = careweave::embedding::VectorMath::cosine(
            encoded[i].functionalView(), encoded[j].functionalView());
        const double implementation = careweave::embedding::VectorMath::cosine(
            encoded[i].implementationView(), encoded[j].implementationView());
        if (asJson) {
          document["comparisons"].push_back({{"earlier", encoded[i].id},
                                             {"later", encoded[j].id},
                                             {"total", total},
                                             {"functional", functional},
                                             {"implementation", implementation}});
        } else {
          std::printf("  %-24s x %-24s %7.4f %7.4f %7.4f\n", encoded[i].id.c_str(),
                      encoded[j].id.c_str(), total, functional, implementation);
        }
      }
    }
  }
  if (asJson) std::printf("%s\n", document.dump(2).c_str());
  return 0;
}

// ---- adapters ----

int commandAdapters(const std::vector<std::string>& args) {
  if (args.empty()) return printUsage();
  const std::string requirementPath = args[0];
  std::vector<std::string> poolPaths;
  std::string moduleFilter;
  std::string baseUrlOverride;
  std::string outDir = "generated/adapters";
  bool asJson = false;
  double minScore = 0.55;
  double margin = 0.05;
  for (size_t i = 1; i < args.size(); ++i) {
    const std::string& arg = args[i];
    auto value = [&](const char* name) -> const char* {
      if (i + 1 >= args.size()) {
        std::fprintf(stderr, "%s needs a value\n", name);
        return nullptr;
      }
      return args[++i].c_str();
    };
    if (arg == "--pool") {
      const char* text = value("--pool");
      if (text == nullptr) return 2;
      poolPaths.push_back(text);
    } else if (arg == "--module") {
      const char* text = value("--module");
      if (text == nullptr) return 2;
      moduleFilter = text;
    } else if (arg == "--base-url") {
      const char* text = value("--base-url");
      if (text == nullptr) return 2;
      baseUrlOverride = text;
    } else if (arg == "--out") {
      const char* text = value("--out");
      if (text == nullptr) return 2;
      outDir = text;
    } else if (arg == "--min-score") {
      const char* text = value("--min-score");
      if (text == nullptr) return 2;
      minScore = std::strtod(text, nullptr);
    } else if (arg == "--margin") {
      const char* text = value("--margin");
      if (text == nullptr) return 2;
      margin = std::strtod(text, nullptr);
    } else if (arg == "--json") {
      asJson = true;
    } else if (!arg.empty() && arg[0] == '-') {
      std::fprintf(stderr, "unknown adapters argument \"%s\"\n", arg.c_str());
      return printUsage();
    } else {
      poolPaths.push_back(arg);
    }
  }
  if (poolPaths.empty()) {
    std::fprintf(stderr, "adapters needs at least one --pool sheet\n");
    return printUsage();
  }

  careweave::spec::SpecParseResult requirement;
  if (!loadSheet(requirementPath, &requirement)) return 1;
  if (requirement.model.capabilities.size() != 1) {
    std::printf("fail %s: a requirement sheet declares exactly one capability, found %zu\n",
                requirementPath.c_str(), requirement.model.capabilities.size());
    return 1;
  }

  // Every candidate keeps the module it came from, so the adapter can be synthesized with the
  // real target module and, when nothing is overridden, the base URL declared by its sheet.
  struct PoolEntry {
    std::string moduleId;
    std::string moduleBaseUrl;
    careweave::core::CapabilitySpec spec;
  };
  std::vector<PoolEntry> pool;
  for (const std::string& poolPath : poolPaths) {
    careweave::spec::SpecParseResult sheet;
    if (!loadSheet(poolPath, &sheet)) return 1;
    for (const careweave::core::CapabilitySpec& capability : sheet.model.capabilities) {
      if (!moduleFilter.empty() && sheet.model.moduleId != moduleFilter) continue;
      pool.push_back({sheet.model.moduleId, sheet.model.baseUrl, capability});
    }
  }
  if (pool.empty()) {
    std::printf("fail: the module filter \"%s\" kept no candidates\n", moduleFilter.c_str());
    return 1;
  }
  std::vector<careweave::core::CapabilitySpec> candidates;
  candidates.reserve(pool.size());
  for (const PoolEntry& entry : pool) candidates.push_back(entry.spec);

  const careweave::core::CapabilitySpec& requirementCapability =
      requirement.model.capabilities.front();
  const careweave::mapper::Mapper mapper;
  const std::vector<careweave::mapper::MatchResult> ranked =
      mapper.rank(requirementCapability, candidates);
  const careweave::mapper::Mapper::Selection selection = mapper.select(ranked, minScore, margin);
  if (selection.bestIndex < 0) {
    std::printf("REJECTED: the best candidate scores %.4f, below the threshold %.2f\n",
                ranked.empty() ? 0.0 : ranked[0].total, minScore);
    return 1;
  }
  const careweave::mapper::MatchResult& best = ranked[static_cast<size_t>(selection.bestIndex)];
  const PoolEntry* chosen = nullptr;
  for (const PoolEntry& entry : pool) {
    if (entry.spec.id == best.candidateId) {
      chosen = &entry;
      break;
    }
  }
  if (chosen == nullptr) {
    std::printf("fail: ranked candidate %s was not found in the pool\n",
                best.candidateId.c_str());
    return 1;
  }
  if (selection.ambiguous) {
    const careweave::mapper::MatchResult& runnerUp =
        ranked[static_cast<size_t>(selection.bestIndex) + 1];
    std::printf("AMBIGUOUS: %s (%.4f) over %s (%.4f), margin %.4f\n", best.candidateId.c_str(),
                best.total, runnerUp.candidateId.c_str(), runnerUp.total, selection.margin);
  } else {
    std::printf("SELECTED: %s (%s) total %.4f, margin %.4f\n", best.candidateId.c_str(),
                best.candidateName.c_str(), best.total, selection.margin);
  }

  careweave::adapter::SynthesisRequest request;
  request.requirement = requirementCapability;
  request.match = best;
  request.candidate = chosen->spec;
  request.targetModule = chosen->moduleId;
  // The base URL comes from the explicit flag, then the capability mechanism, then the base URL
  // the pool sheet declares for its module.
  request.baseUrl = !baseUrlOverride.empty() ? baseUrlOverride
                    : !chosen->spec.mechanism.baseUrl.empty() ? chosen->spec.mechanism.baseUrl
                                                              : chosen->moduleBaseUrl;
  const careweave::adapter::AdapterSynthesizer synthesizer;
  const careweave::adapter::SynthesisResult synthesis = synthesizer.synthesize(request);
  if (!synthesis.ok) {
    std::printf("fail: adapter synthesis rejected\n%s", synthesis.render().c_str());
    return 1;
  }
  const careweave::adapter::AdapterDefinition& definition = synthesis.adapter;
  if (asJson) {
    std::printf("%s\n", careweave::adapter::toJsonString(definition).c_str());
    return 0;
  }

  std::printf("adapter %s\n", definition.id.c_str());
  std::printf("  requirement %s (%s) to %s in module %s\n", definition.requirementName.c_str(),
              definition.requirementId.c_str(), definition.targetCapabilityName.c_str(),
              definition.targetModule.c_str());
  std::printf("  transport %s %s %s%s\n", definition.transportKind.c_str(),
              definition.method.c_str(), definition.baseUrl.c_str(),
              definition.endpoint.c_str());
  for (const careweave::adapter::FieldMapping& mapping : definition.inputMap) {
    std::printf("  input  %s\n", mapping.render().c_str());
  }
  for (const careweave::adapter::FieldMapping& mapping : definition.outputMap) {
    std::printf("  output %s\n", mapping.render().c_str());
  }
  std::printf("  confidence %.4f\n", definition.confidence);

  const std::string jsonPath = outDir + "/" + definition.id + ".json";
  const std::string cppPath = outDir + "/" + definition.id + ".cpp";
  std::string error;
  if (!writeText(jsonPath, careweave::adapter::toJsonString(definition), &error) ||
      !writeText(cppPath, careweave::adapter::emitAdapterCpp(definition), &error)) {
    std::printf("fail: %s\n", error.c_str());
    return 1;
  }
  std::printf("  written %s\n", jsonPath.c_str());
  std::printf("  written %s\n", cppPath.c_str());
  std::printf("  generated function %s\n",
              careweave::adapter::emittedFunctionName(definition).c_str());
  return 0;
}

// ---- plan (background planner, outside the Assignment 2 evaluation scope) ----

int commandPlan(const std::vector<std::string>& args) {
  if (args.empty()) return printUsage();
  const std::string sheetPath = args[0];
  std::vector<std::string> goalTexts;
  careweave::planner::PlanOptions options;
  bool backward = false;
  bool asJson = false;
  for (size_t i = 1; i < args.size(); ++i) {
    const std::string& arg = args[i];
    auto value = [&](const char* name) -> const char* {
      if (i + 1 >= args.size()) {
        std::fprintf(stderr, "%s needs a value\n", name);
        return nullptr;
      }
      return args[++i].c_str();
    };
    if (arg == "--goal") {
      const char* text = value("--goal");
      if (text == nullptr) return 2;
      goalTexts.push_back(text);
    } else if (arg == "--strategy") {
      const char* text = value("--strategy");
      if (text == nullptr) return 2;
      const std::string strategy = text;
      if (strategy == "fewest") {
        options.strategy = careweave::planner::PlanStrategy::FewestSteps;
      } else if (strategy == "time") {
        options.strategy = careweave::planner::PlanStrategy::LeastTime;
      } else if (strategy == "money") {
        options.strategy = careweave::planner::PlanStrategy::LeastMoney;
      } else if (strategy == "reliability") {
        options.strategy = careweave::planner::PlanStrategy::MostReliable;
      } else {
        std::fprintf(stderr, "unknown strategy \"%s\"\n", strategy.c_str());
        return 2;
      }
    } else if (arg == "--max-depth") {
      const char* text = value("--max-depth");
      if (text == nullptr) return 2;
      options.maxDepth = static_cast<size_t>(std::strtoul(text, nullptr, 10));
    } else if (arg == "--max-time") {
      const char* text = value("--max-time");
      if (text == nullptr) return 2;
      options.maxTimeMs = std::strtod(text, nullptr);
    } else if (arg == "--max-money") {
      const char* text = value("--max-money");
      if (text == nullptr) return 2;
      options.maxMoney = std::strtod(text, nullptr);
    } else if (arg == "--max-risk") {
      const char* text = value("--max-risk");
      if (text == nullptr) return 2;
      options.maxRisk = std::strtod(text, nullptr);
    } else if (arg == "--min-reliability") {
      const char* text = value("--min-reliability");
      if (text == nullptr) return 2;
      options.minReliability = std::strtod(text, nullptr);
    } else if (arg == "--backward") {
      backward = true;
    } else if (arg == "--json") {
      asJson = true;
    } else {
      std::fprintf(stderr, "unknown plan argument \"%s\"\n", arg.c_str());
      return printUsage();
    }
  }

  careweave::spec::SpecParseResult sheet;
  if (!loadSheet(sheetPath, &sheet)) return 1;

  std::vector<careweave::core::Condition> goal;
  if (goalTexts.empty()) {
    goal = sheet.model.goal;
  } else {
    for (const std::string& text : goalTexts) {
      for (const std::string& part : splitList(text)) {
        const size_t equals = part.find('=');
        if (equals == std::string::npos || equals == 0) {
          std::printf("fail: --goal entries are written variable=value, got \"%s\"\n",
                      part.c_str());
          return 2;
        }
        careweave::core::Condition condition;
        condition.variable = part.substr(0, equals);
        condition.op = careweave::core::ConditionOp::EQ;
        condition.value = parseTypedValue(part.substr(equals + 1));
        goal.push_back(condition);
      }
    }
  }
  if (goal.empty()) {
    std::printf("fail %s: no goal was given and the sheet declares none\n", sheetPath.c_str());
    return 1;
  }

  const careweave::planner::Planner planner(sheet.model);
  const careweave::planner::PlanResult result =
      backward ? planner.planBackward(goal, options) : planner.planForward(goal, options);

  if (asJson) {
    nlohmann::json document;
    document["found"] = result.found;
    document["validated"] = result.validated;
    if (!result.reason.empty()) document["reason"] = result.reason;
    document["steps"] = nlohmann::json::array();
    for (const careweave::planner::PlanStep& step : result.steps) {
      document["steps"].push_back({{"capability_id", step.capabilityId},
                                   {"capability_name", step.capabilityName},
                                   {"consumed_preconditions", step.consumedPreconditions},
                                   {"established", step.established}});
    }
    document["total_time_ms"] = result.totalTimeMs;
    document["total_money"] = result.totalMoney;
    document["total_risk"] = result.totalRisk;
    document["total_reliability"] = result.totalReliability;
    document["expanded_states"] = result.expandedStates;
    document["explored_states"] = result.exploredStates;
    document["depth"] = result.depth;
    document["explanation"] = result.explanation;
    std::printf("%s\n", document.dump(2).c_str());
    return result.found && result.validated ? 0 : 1;
  }

  std::printf("plan %s (strategy %s, depth limit %zu) for %s\n", backward ? "backward" : "forward",
              careweave::planner::planStrategyToString(options.strategy).c_str(), options.maxDepth,
              sheetPath.c_str());
  if (!result.found) {
    std::printf("no plan found: %s\n", result.reason.c_str());
    std::printf("%s", result.explanation.c_str());
    return 1;
  }
  for (size_t i = 0; i < result.steps.size(); ++i) {
    const careweave::planner::PlanStep& step = result.steps[i];
    std::printf("step %zu: %s (%s)\n", i + 1, step.capabilityName.c_str(),
                step.capabilityId.c_str());
    for (const std::string& line : step.established) {
      std::printf("  establishes %s\n", line.c_str());
    }
    for (const std::string& line : step.consumedPreconditions) {
      std::printf("  consumes    %s\n", line.c_str());
    }
  }
  std::printf("validated %s, depth %zu\n", result.validated ? "yes" : "no", result.depth);
  std::printf("totals: time %.1f ms, money %.2f, risk %.4f, reliability %.4f\n",
              result.totalTimeMs, result.totalMoney, result.totalRisk, result.totalReliability);
  std::printf("search: %zu states expanded, %zu explored\n", result.expandedStates,
              result.exploredStates);
  std::printf("%s", result.explanation.c_str());
  return result.validated ? 0 : 1;
}

// ---- run ----

int commandRun(const std::vector<std::string>& args) {
  if (args.empty()) return printUsage();
  std::string requirementPath;
  std::string workflowPath;
  std::string inputsText;
  std::string preferredText;
  std::string allowText;
  std::string gatewayUrl = "http://127.0.0.1:5100";
  bool resolveOnly = false;
  bool asJson = false;
  for (size_t i = 0; i < args.size(); ++i) {
    const std::string& arg = args[i];
    auto value = [&](const char* name) -> const char* {
      if (i + 1 >= args.size()) {
        std::fprintf(stderr, "%s needs a value\n", name);
        return nullptr;
      }
      return args[++i].c_str();
    };
    if (arg == "--workflow") {
      const char* text = value("--workflow");
      if (text == nullptr) return 2;
      workflowPath = text;
    } else if (arg == "--inputs") {
      const char* text = value("--inputs");
      if (text == nullptr) return 2;
      inputsText = text;
    } else if (arg == "--preferred") {
      const char* text = value("--preferred");
      if (text == nullptr) return 2;
      preferredText = text;
    } else if (arg == "--allow-modules") {
      const char* text = value("--allow-modules");
      if (text == nullptr) return 2;
      allowText = text;
    } else if (arg == "--gateway") {
      const char* text = value("--gateway");
      if (text == nullptr) return 2;
      gatewayUrl = text;
    } else if (arg == "--resolve-only") {
      resolveOnly = true;
    } else if (arg == "--json") {
      asJson = true;
    } else if (!arg.empty() && arg[0] == '-') {
      std::fprintf(stderr, "unknown run argument \"%s\"\n", arg.c_str());
      return printUsage();
    } else if (requirementPath.empty()) {
      requirementPath = arg;
    } else {
      std::fprintf(stderr, "run takes a single requirement sheet\n");
      return printUsage();
    }
  }
  if (!workflowPath.empty() && !requirementPath.empty()) {
    std::fprintf(stderr, "use either a requirement sheet or --workflow, not both\n");
    return 2;
  }
  if (!workflowPath.empty() && !allowText.empty()) {
    std::fprintf(stderr,
                 "--allow-modules applies to requirement runs; a workflow carries allow_modules "
                 "per step\n");
    return 2;
  }
  if (workflowPath.empty() && requirementPath.empty()) return printUsage();

  httplib::Client client(gatewayUrl);
  client.set_connection_timeout(2, 0);
  client.set_read_timeout(30, 0);

  httplib::Result response(nullptr, httplib::Error::Unknown);
  if (!workflowPath.empty()) {
    std::ifstream file(workflowPath);
    if (!file) {
      std::printf("fail: cannot read %s\n", workflowPath.c_str());
      return 1;
    }
    std::stringstream buffer;
    buffer << file.rdbuf();
    const nlohmann::json definition = nlohmann::json::parse(buffer.str(), nullptr, false);
    if (definition.is_discarded()) {
      std::printf("fail: %s is not a JSON workflow document\n", workflowPath.c_str());
      return 1;
    }
    const nlohmann::json body = {{"definition", definition}};
    response = client.Post("/api/workflow", body.dump(), "application/json");
  } else if (resolveOnly) {
    nlohmann::json body = {{"requirement", requirementPath}};
    const std::vector<std::string> allowModules = splitList(allowText);
    if (!allowModules.empty()) body["allow_modules"] = allowModules;
    response = client.Post("/api/resolve", body.dump(), "application/json");
  } else {
    std::map<std::string, careweave::core::Value> inputs;
    if (!inputsText.empty()) {
      std::string error;
      if (!parseInputs(inputsText, &inputs, &error)) {
        std::fprintf(stderr, "%s\n", error.c_str());
        return 2;
      }
    }
    nlohmann::json inputsJson = nlohmann::json::object();
    for (const auto& entry : inputs) {
      inputsJson[entry.first] = careweave::core::valueToJson(entry.second);
    }
    nlohmann::json body = {{"requirement", requirementPath}, {"inputs", inputsJson}};
    const std::vector<std::string> preferred = splitList(preferredText);
    if (!preferred.empty()) body["preferred_modules"] = preferred;
    const std::vector<std::string> allowModules = splitList(allowText);
    if (!allowModules.empty()) body["allow_modules"] = allowModules;
    response = client.Post("/api/call", body.dump(), "application/json");
  }

  if (!response) {
    std::fprintf(stderr, "cannot reach the gateway at %s (%s)\n", gatewayUrl.c_str(),
                 httplib::to_string(response.error()).c_str());
    return 2;
  }
  const int status = response->status;
  const nlohmann::json outcome = nlohmann::json::parse(response->body, nullptr, false);
  if (asJson) {
    if (outcome.is_discarded()) std::printf("%s\n", response->body.c_str());
    else std::printf("%s\n", outcome.dump(2).c_str());
    return status >= 200 && status < 300 ? 0 : 1;
  }

  if (resolveOnly) {
    if (!outcome.is_array()) {
      std::printf("resolve %s -> %d\n%s\n", requirementPath.c_str(), status,
                  response->body.c_str());
      return status == 200 ? 0 : 1;
    }
    std::printf("resolve %s -> %d (%zu candidates)\n", requirementPath.c_str(), status,
                outcome.size());
    for (const nlohmann::json& candidate : outcome) {
      std::printf("  %-26s %-22s %-24s total %.4f%s\n",
                  candidate.value("module_id", std::string()).c_str(),
                  candidate.value("capability_id", std::string()).c_str(),
                  candidate.value("capability_name", std::string()).c_str(),
                  candidate.value("total", 0.0),
                  candidate.value("ambiguous", false) ? " (ambiguous)" : "");
    }
    return status == 200 ? 0 : 1;
  }

  if (!workflowPath.empty()) {
    std::printf("workflow %s -> %d ok %s\n", workflowPath.c_str(), status,
                outcome.value("ok", false) ? "true" : "false");
    if (outcome.contains("error")) {
      std::printf("  error %s\n", outcome.value("error", std::string()).c_str());
    }
    for (const nlohmann::json& step : outcome.value("steps", nlohmann::json::array())) {
      const nlohmann::json call = step.value("call", nlohmann::json::object());
      std::printf("  step %-12s %-26s %-22s verdict %-12s %s (attempts %d)\n",
                  step.value("name", std::string()).c_str(),
                  step.value("module_id", std::string()).c_str(),
                  step.value("capability_id", std::string()).c_str(),
                  step.value("verdict", std::string()).c_str(),
                  call.value("ok", false) ? "ok" : "failed",
                  call.value("attempts", 0));
      if (!call.value("ok", false)) {
        std::printf("      error %s\n", call.value("error", std::string()).c_str());
        for (const nlohmann::json& line : call.value("trace", nlohmann::json::array())) {
          if (line.is_string()) std::printf("      trace %s\n", line.get<std::string>().c_str());
        }
      }
    }
    return outcome.value("ok", false) ? 0 : 1;
  }

  std::printf("call %s -> %d ok %s\n", requirementPath.c_str(), status,
              outcome.value("ok", false) ? "true" : "false");
  std::printf("  module %s capability %s, attempts %d, fallback %s, module called %s\n",
              outcome.value("module_id", std::string()).c_str(),
              outcome.value("capability_id", std::string()).c_str(),
              outcome.value("attempts", 0),
              outcome.value("fallback_used", false) ? "yes" : "no",
              outcome.value("module_called", false) ? "yes" : "no");
  if (outcome.contains("outputs")) {
    std::printf("  outputs %s\n", outcome["outputs"].dump().c_str());
  }
  if (!outcome.value("ok", false)) {
    std::printf("  error %s\n", outcome.value("error", std::string()).c_str());
    for (const nlohmann::json& line : outcome.value("trace", nlohmann::json::array())) {
      if (line.is_string()) std::printf("  trace %s\n", line.get<std::string>().c_str());
    }
  }
  return outcome.value("ok", false) ? 0 : 1;
}

// ---- bundle ----

int commandBundle(const std::vector<std::string>& args) {
  std::string rootDir = ".";
  std::string outDir;
  std::string modulesText;
  std::string workflowsText;
  bool modulesGiven = false;
  bool workflowsGiven = false;
  bool includeDashboard = true;
  bool includeWorkflows = true;
  bool asJson = false;
  for (size_t i = 0; i < args.size(); ++i) {
    const std::string& arg = args[i];
    auto value = [&](const char* name) -> const char* {
      if (i + 1 >= args.size()) {
        std::fprintf(stderr, "%s needs a value\n", name);
        return nullptr;
      }
      return args[++i].c_str();
    };
    if (arg == "--root") {
      const char* text = value("--root");
      if (text == nullptr) return 2;
      rootDir = text;
    } else if (arg == "--out") {
      const char* text = value("--out");
      if (text == nullptr) return 2;
      outDir = text;
    } else if (arg == "--modules") {
      const char* text = value("--modules");
      if (text == nullptr) return 2;
      modulesText = text;
      modulesGiven = true;
    } else if (arg == "--workflows") {
      const char* text = value("--workflows");
      if (text == nullptr) return 2;
      workflowsText = text;
      workflowsGiven = true;
    } else if (arg == "--no-workflows") {
      includeWorkflows = false;
    } else if (arg == "--no-dashboard") {
      includeDashboard = false;
    } else if (arg == "--json") {
      asJson = true;
    } else {
      std::fprintf(stderr, "unknown bundle argument \"%s\"\n", arg.c_str());
      return printUsage();
    }
  }
  if (workflowsGiven && !includeWorkflows) {
    std::fprintf(stderr, "give either --workflows or --no-workflows, not both\n");
    return 2;
  }
  const std::vector<std::string> modules = splitList(modulesText);
  const std::vector<std::string> workflows = splitList(workflowsText);
  if (modulesGiven && modules.empty()) {
    std::fprintf(stderr, "--modules needs at least one module id\n");
    return 2;
  }
  if (workflowsGiven && workflows.empty()) {
    std::fprintf(stderr, "--workflows needs at least one workflow name\n");
    return 2;
  }

  careweave::bundle::BundleOptions options;
  options.rootDir = rootDir;
  options.outDir = outDir.empty() ? rootDir + "/dist/careweave-mini" : outDir;
  options.displayPath = outDir.empty() ? "dist/careweave-mini" : outDir;
  options.includeDashboard = includeDashboard;
  options.selectedModules = modules;
  options.selectedWorkflows = workflows;
  options.includeWorkflows = includeWorkflows;
  const careweave::bundle::BundleResult result = careweave::bundle::createBundle(options);
  if (asJson) {
    std::printf("%s", result.render().c_str());
  } else if (!result.ok) {
    std::printf("fail: %s\n", result.error.c_str());
  } else {
    std::printf("bundle assembled in %s (%zu modules, %zu files)\n", result.outDir.c_str(),
                result.modules, result.files);
    std::printf("  gateway binary %s\n",
                result.gatewayBinaryIncluded ? "bin/careweave_gateway" : "missing");
    std::printf("  dashboard %s\n",
                result.dashboardIncluded ? "included" : "not built yet");
    if (!result.requestedModules.empty()) {
      std::printf("  requested modules: %s\n", joinNames(result.requestedModules).c_str());
    }
    for (const auto& entry : result.closureAdded) {
      std::printf("  added by workflow references: %s (%s)\n", entry.first.c_str(),
                  entry.second.c_str());
    }
    if (!includeWorkflows) {
      std::printf("  workflows: none\n");
    } else if (workflowsGiven) {
      std::printf("  workflows: %s\n", joinNames(result.workflows).c_str());
    }
    for (const std::string& warning : result.warnings) {
      std::printf("  note: %s\n", warning.c_str());
    }
    std::printf("  next: scripts/setup.sh once, then scripts/start.sh\n");
  }
  return result.ok ? 0 : 1;
}

// ---- export ----

std::string fileStem(const std::string& path) {
  const size_t slash = path.find_last_of('/');
  std::string name = slash == std::string::npos ? path : path.substr(slash + 1);
  const size_t dot = name.find_last_of('.');
  if (dot != std::string::npos && dot != 0) name = name.substr(0, dot);
  return name;
}

std::string fixed4(double value) {
  char buffer[32];
  std::snprintf(buffer, sizeof(buffer), "%.4f", value);
  return buffer;
}

int commandExport(const std::vector<std::string>& args) {
  std::vector<std::string> sheets;
  std::string what = "specs";
  std::string outDir;
  bool asJson = false;
  for (size_t i = 0; i < args.size(); ++i) {
    const std::string& arg = args[i];
    auto value = [&](const char* name) -> const char* {
      if (i + 1 >= args.size()) {
        std::fprintf(stderr, "%s needs a value\n", name);
        return nullptr;
      }
      return args[++i].c_str();
    };
    if (arg == "--what") {
      const char* text = value("--what");
      if (text == nullptr) return 2;
      what = text;
    } else if (arg == "--out") {
      const char* text = value("--out");
      if (text == nullptr) return 2;
      outDir = text;
    } else if (arg == "--json") {
      asJson = true;
    } else if (!arg.empty() && arg[0] == '-') {
      std::fprintf(stderr, "unknown export argument \"%s\"\n", arg.c_str());
      return printUsage();
    } else {
      sheets.push_back(arg);
    }
  }
  if (sheets.empty()) return printUsage();
  if (what != "specs" && what != "compat" && what != "embedding") {
    std::fprintf(stderr, "unknown export kind \"%s\"\n", what.c_str());
    return 2;
  }
  if (what != "specs" && sheets.size() != 1) {
    std::fprintf(stderr, "--what %s takes a single sheet\n", what.c_str());
    return 2;
  }

  if (what == "specs") {
    if (!outDir.empty() && sheets.size() > 1) {
      // Multiple sheets with --out: one canonical JSON file per sheet.
      int failures = 0;
      for (const std::string& sheetPath : sheets) {
        careweave::spec::SpecParseResult sheet;
        if (!loadSheet(sheetPath, &sheet)) {
          ++failures;
          continue;
        }
        const std::string path = outDir + "/" + fileStem(sheetPath) + ".json";
        std::string error;
        if (!writeText(path, careweave::spec::specToJson(sheet.model).dump(2) + "\n", &error)) {
          std::printf("fail: %s\n", error.c_str());
          ++failures;
          continue;
        }
        std::printf("ok   %s (canonical JSON, %zu capabilities)\n", path.c_str(),
                    sheet.model.capabilities.size());
      }
      return failures == 0 ? 0 : 1;
    }
    careweave::spec::SpecParseResult sheet;
    if (!loadSheet(sheets.front(), &sheet)) return 1;
    const std::string text = careweave::spec::specToJson(sheet.model).dump(2) + "\n";
    if (outDir.empty()) {
      std::printf("%s", text.c_str());
      return 0;
    }
    const std::string path = outDir + "/" + fileStem(sheets.front()) + ".json";
    std::string error;
    if (!writeText(path, text, &error)) {
      std::printf("fail: %s\n", error.c_str());
      return 1;
    }
    std::printf("ok   %s (canonical JSON, %zu capabilities)\n", path.c_str(),
                sheet.model.capabilities.size());
    return 0;
  }

  careweave::spec::SpecParseResult sheet;
  if (!loadSheet(sheets.front(), &sheet)) return 1;
  const std::string stem = fileStem(sheets.front());

  if (what == "compat") {
    const careweave::compat::CompatEngine engine(sheet.model);
    const std::vector<careweave::core::CapabilitySpec>& capabilities = sheet.model.capabilities;
    nlohmann::json document;
    document["sheet"] = sheets.front();
    document["pairs"] = nlohmann::json::array();
    std::string csv = "earlier,later,verdict\n";
    size_t pairs = 0;
    for (size_t i = 0; i < capabilities.size(); ++i) {
      for (size_t j = 0; j < capabilities.size(); ++j) {
        if (i == j) continue;
        const careweave::compat::CompatibilityReport report =
            engine.check(capabilities[i], capabilities[j]);
        const std::string verdict = careweave::compat::verdictToString(report.verdict);
        document["pairs"].push_back({{"earlier", capabilities[i].id},
                                     {"later", capabilities[j].id},
                                     {"verdict", verdict},
                                     {"rejections", report.rejections}});
        csv += capabilities[i].id + "," + capabilities[j].id + "," + verdict + "\n";
        ++pairs;
      }
    }
    if (outDir.empty()) {
      if (asJson) std::printf("%s\n", document.dump(2).c_str());
      else std::printf("%s", csv.c_str());
      return 0;
    }
    std::string error;
    if (!writeText(outDir + "/" + stem + ".compat.csv", csv, &error) ||
        !writeText(outDir + "/" + stem + ".compat.json", document.dump(2) + "\n", &error)) {
      std::printf("fail: %s\n", error.c_str());
      return 1;
    }
    std::printf("ok   %s.compat.csv and %s.compat.json (%zu capabilities, %zu ordered pairs)\n",
                (outDir + "/" + stem).c_str(), (outDir + "/" + stem).c_str(),
                capabilities.size(), pairs);
    return 0;
  }

  // ---- what == "embedding" ----
  const careweave::embedding::Encoder encoder;
  std::vector<std::string> blockNames;
  nlohmann::json rows = nlohmann::json::array();
  for (const careweave::core::CapabilitySpec& capability : sheet.model.capabilities) {
    const careweave::embedding::EncodedCapability encoded =
        encoder.encodeCapabilityDetailed(capability);
    if (blockNames.empty()) {
      for (const auto& block : encoded.blocks) blockNames.push_back(block.first);
    }
    nlohmann::json blocks = nlohmann::json::object();
    for (const auto& block : encoded.blocks) {
      blocks[block.first] = {{"size", block.second.size()},
                             {"norm", careweave::embedding::VectorMath::norm(block.second)}};
    }
    rows.push_back({{"id", encoded.id},
                    {"name", encoded.name},
                    {"dimensions", encoded.vector.size()},
                    {"blocks", blocks}});
  }
  nlohmann::json document;
  document["sheet"] = sheets.front();
  document["capabilities"] = rows;
  std::string csv = "capability_id,capability_name,dimensions";
  for (const std::string& name : blockNames) csv += "," + name + "_norm";
  csv += "\n";
  for (const careweave::core::CapabilitySpec& capability : sheet.model.capabilities) {
    const careweave::embedding::EncodedCapability encoded =
        encoder.encodeCapabilityDetailed(capability);
    csv += encoded.id + "," + encoded.name + "," + std::to_string(encoded.vector.size());
    for (const std::string& name : blockNames) {
      const auto block = encoded.blocks.find(name);
      csv += "," + fixed4(block == encoded.blocks.end()
                              ? 0.0
                              : careweave::embedding::VectorMath::norm(block->second));
    }
    csv += "\n";
  }
  if (outDir.empty()) {
    if (asJson) std::printf("%s\n", document.dump(2).c_str());
    else std::printf("%s", csv.c_str());
    return 0;
  }
  std::string error;
  if (!writeText(outDir + "/" + stem + ".embedding.csv", csv, &error) ||
      !writeText(outDir + "/" + stem + ".embedding.json", document.dump(2) + "\n", &error)) {
    std::printf("fail: %s\n", error.c_str());
    return 1;
  }
  std::printf("ok   %s.embedding.csv and %s.embedding.json (%zu capabilities, %zu block columns)\n",
              (outDir + "/" + stem).c_str(), (outDir + "/" + stem).c_str(),
              sheet.model.capabilities.size(), blockNames.size());
  return 0;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc < 2) return printUsage();
  const std::string command = argv[1];
  const std::vector<std::string> rest(argv + 2, argv + argc);
  if (command == "validate") return commandValidate(rest);
  if (command == "spec-yaml") return commandSpecYaml(rest);
  if (command == "embed") return commandEmbed(rest);
  if (command == "mapping") return commandMapping(rest);
  if (command == "compare") return commandCompare(rest);
  if (command == "adapters") return commandAdapters(rest);
  if (command == "plan") return commandPlan(rest);
  if (command == "run") return commandRun(rest);
  if (command == "bundle") return commandBundle(rest);
  if (command == "export") return commandExport(rest);
  std::fprintf(stderr, "unknown command \"%s\"\n", command.c_str());
  return printUsage();
}
