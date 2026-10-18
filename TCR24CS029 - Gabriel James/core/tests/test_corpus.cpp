// Corpus test: every specification sheet shipped with the project is parsed by the real parser,
// validated against the real schema, and every module sheet is round tripped through the YAML
// rendering with an equal decoded model.
//
// The test pins the shipped corpus on purpose: seven module sheets, five application sheets and
// five client requirement sheets. A sheet that stops parsing, or a generated YAML form that
// drifts from its JSON source, fails here.
//
// The second half of the file replays the labeled problems of dataset/ against the real mapper
// and the real compatibility engine, so a component change that breaks a dataset label fails
// the suite before the report is rewritten. The last cases pin the shared state vocabulary
// over every shipped sheet and the resource reference rule.

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <map>
#include <set>
#include <string>
#include <vector>

#include "careweave/compat/compat_engine.hpp"
#include "careweave/mapper/mapper.hpp"
#include "careweave/spec/spec_parser.hpp"
#include "careweave/spec/yaml_lite.hpp"
#include "careweave/test/framework.hpp"

namespace spec = careweave::spec;
namespace compat = careweave::compat;
namespace mapper = careweave::mapper;
namespace fs = std::filesystem;

namespace {

fs::path miniRoot() { return fs::path(CAREWEAVE_CORE_DIR).parent_path(); }

std::vector<fs::path> sheetsIn(const fs::path& dir) {
  std::vector<fs::path> files;
  if (!fs::exists(dir)) return files;
  for (const auto& entry : fs::directory_iterator(dir)) {
    if (!entry.is_regular_file()) continue;
    const std::string extension = entry.path().extension().string();
    if (extension == ".yaml" || extension == ".yml" || extension == ".json") {
      files.push_back(entry.path());
    }
  }
  std::sort(files.begin(), files.end());
  return files;
}

spec::SpecParseResult load(const fs::path& file) {
  spec::SpecParseOptions options;
  options.requireSchema = true;
  return spec::loadSpecFile(file.string(), options);
}

std::string join(const std::vector<fs::path>& files) {
  std::string out;
  for (const fs::path& file : files) out += "\n  " + file.string();
  return out;
}

}  // namespace

CW_TEST_CASE(module_sheets_validate_and_round_trip_through_yaml) {
  std::vector<fs::path> sheets;
  const fs::path modules = miniRoot() / "modules";
  CW_CHECK_MSG(fs::exists(modules), "the modules directory must be next to the core");
  for (const auto& entry : fs::directory_iterator(modules)) {
    if (entry.is_directory() && fs::exists(entry.path() / "spec.json")) {
      sheets.push_back(entry.path() / "spec.json");
    }
  }
  std::sort(sheets.begin(), sheets.end());
  CW_CHECK_MSG(sheets.size() == 7, "expected the seven module sheets, found:" + join(sheets));

  for (const fs::path& sheet : sheets) {
    const spec::SpecParseResult result = load(sheet);
    CW_CHECK_MSG(result.ok, sheet.string() + " rejected:" + result.renderIssues());

    const std::string yaml = spec::specToYaml(result.model);
    nlohmann::json doc;
    std::string error;
    CW_CHECK_MSG(careweave::spec::parseYaml(yaml, &doc, &error),
                 sheet.string() + ": the generated YAML does not parse: " + error);
    spec::SpecParseOptions options;
    options.strictVariables = true;
    const spec::SpecParseResult reparsed =
        spec::parseSpecDocument(doc, sheet.string() + " (yaml rendering)", options);
    CW_CHECK_MSG(reparsed.ok, sheet.string() + " YAML rendering rejected:" + reparsed.renderIssues());
    CW_CHECK_MSG(spec::specToJson(result.model) == spec::specToJson(reparsed.model),
                 sheet.string() + ": the YAML form decodes to a different model");
  }
}

CW_TEST_CASE(application_sheets_validate) {
  const std::vector<fs::path> apps = sheetsIn(miniRoot() / "specs" / "app");
  CW_CHECK_MSG(apps.size() == 5, "expected the five application sheets, found:" + join(apps));
  for (const fs::path& sheet : apps) {
    const spec::SpecParseResult result = load(sheet);
    CW_CHECK_MSG(result.ok, sheet.string() + " rejected:" + result.renderIssues());
    CW_CHECK_MSG(!result.model.capabilities.empty(),
                 sheet.string() + " declares no capability");
  }
}

CW_TEST_CASE(requirement_sheets_validate) {
  const std::vector<fs::path> requirements = sheetsIn(miniRoot() / "specs" / "app" / "requirements");
  CW_CHECK_MSG(requirements.size() == 5,
               "expected the five requirement sheets, found:" + join(requirements));
  for (const fs::path& sheet : requirements) {
    const spec::SpecParseResult result = load(sheet);
    CW_CHECK_MSG(result.ok, sheet.string() + " rejected:" + result.renderIssues());
    CW_CHECK_MSG(result.model.capabilities.size() == 1,
                 sheet.string() + " must declare exactly one required capability");
  }
}

CW_TEST_CASE(alias_resolution_corpus_is_shipped) {
  // The alias resolution experiment depends on this exact pair of capabilities: the legacy
  // Pat_reg and the canonical register_patient, inside the same application.
  const spec::SpecParseResult result =
      load(miniRoot() / "specs" / "app" / "hospital_alias_resolution.yaml");
  CW_CHECK_MSG(result.ok, "hospital_alias_resolution.yaml rejected:" + result.renderIssues());
  bool canonical = false;
  bool legacy = false;
  for (const auto& capability : result.model.capabilities) {
    if (capability.name == "register_patient") canonical = true;
    if (capability.name == "Pat_reg") legacy = true;
  }
  CW_CHECK_MSG(canonical, "the alias application must offer register_patient");
  CW_CHECK_MSG(legacy, "the alias application must offer Pat_reg");
}

namespace {

nlohmann::json loadJsonFile(const fs::path& file) {
  std::ifstream stream(file);
  if (!stream.good()) {
    CW_CHECK_MSG(false, "cannot open " + file.string());
    return nlohmann::json::object();
  }
  nlohmann::json doc;
  stream >> doc;
  return doc;
}

// Loads every capability of the listed sheets, all paths relative to the mini root.
std::vector<careweave::core::CapabilitySpec> loadCapabilities(
    const fs::path& root, const nlohmann::json& paths) {
  std::vector<careweave::core::CapabilitySpec> out;
  for (const auto& path : paths) {
    const spec::SpecParseResult result = load(root / path.get<std::string>());
    CW_CHECK_MSG(result.ok,
                 path.get<std::string>() + " rejected:" + result.renderIssues());
    for (const auto& capability : result.model.capabilities) out.push_back(capability);
  }
  return out;
}

std::string idList(const std::vector<std::string>& ids) {
  std::string out;
  for (const std::string& id : ids) out += (out.empty() ? "" : ", ") + id;
  return out;
}

bool contains(const std::vector<std::string>& ids, const std::string& id) {
  return std::find(ids.begin(), ids.end(), id) != ids.end();
}

std::string mappedId(const mapper::MatchResult& match) { return match.candidateId; }

}  // namespace

CW_TEST_CASE(capability_resource_references_are_checked) {
  // A capability that requires a resource the sheet does not declare is a specification error:
  // the compatibility engine's resource check could never resolve it.
  const spec::SpecParseResult base =
      load(miniRoot() / "specs" / "app" / "requirements" / "register_pat.yaml");
  CW_CHECK_MSG(base.ok, "register_pat must parse:" + base.renderIssues());
  if (!base.ok) return;
  nlohmann::json doc = spec::specToJson(base.model);
  doc["resources"] = nlohmann::json::array();
  doc["capabilities"][0]["resources"] = nlohmann::json::array({"missing_db"});
  const spec::SpecParseResult mutated = spec::parseSpecDocument(doc, "<mutated>");
  CW_CHECK_MSG(!mutated.ok, "an undeclared capability resource must be rejected");
  bool mentions = false;
  for (const auto& issue : mutated.issues) {
    if (issue.message.find("undeclared resource") != std::string::npos &&
        issue.message.find("missing_db") != std::string::npos) {
      mentions = true;
    }
  }
  CW_CHECK_MSG(mentions, "the issue must name the missing resource: " + mutated.renderIssues());
}

CW_TEST_CASE(dataset_ground_truth_holds_against_the_real_components) {
  const fs::path root = miniRoot();
  const fs::path datasetDir = root / "dataset";
  std::vector<fs::path> problemFiles;
  CW_CHECK_MSG(fs::exists(datasetDir), "the dataset directory must exist");
  for (const auto& entry : fs::directory_iterator(datasetDir)) {
    if (entry.is_directory() && fs::exists(entry.path() / "problem.json")) {
      problemFiles.push_back(entry.path() / "problem.json");
    }
  }
  std::sort(problemFiles.begin(), problemFiles.end());
  CW_CHECK_MSG(problemFiles.size() == 3,
               "expected the three labeled problems, found:" + join(problemFiles));

  const mapper::Mapper mapper;
  for (const fs::path& problemFile : problemFiles) {
    const nlohmann::json problem = loadJsonFile(problemFile);
    const std::string problemId = problem.value("problem_id", problemFile.string());

    // Required mappings and negative cases: scope a requirement against its candidate sheets.
    std::vector<nlohmann::json> scopedCases = problem["required_mappings"];
    for (const auto& c : problem["negative_cases"]) scopedCases.push_back(c);
    for (const nlohmann::json& c : scopedCases) {
      const std::string caseId = c.value("case_id", std::string());
      const std::string where = problemId + "/" + caseId;
      const spec::SpecParseResult requiredSheet =
          load(root / c["requirement_spec"].get<std::string>());
      CW_CHECK_MSG(requiredSheet.ok, where + ": requirement sheet rejected:" +
                                         requiredSheet.renderIssues());
      CW_CHECK_MSG(requiredSheet.model.capabilities.size() == 1,
                   where + ": the requirement sheet must declare one capability");
      if (!requiredSheet.ok || requiredSheet.model.capabilities.size() != 1) continue;
      const std::vector<careweave::core::CapabilitySpec> candidates =
          loadCapabilities(root, c["candidate_specs"]);
      const std::vector<mapper::MatchResult> ranked =
          mapper.rank(requiredSheet.model.capabilities.front(), candidates);
      const mapper::Mapper::Selection selection = mapper.select(ranked);
      const std::string expectation = c["expectation"].get<std::string>();
      if (expectation == "rejected") {
        CW_CHECK_MSG(selection.bestIndex < 0,
                     where + ": expected a rejection, got " +
                         (ranked.empty() ? std::string("an empty pool") : mappedId(ranked[0])));
        continue;
      }
      std::vector<std::string> expected;
      for (const auto& id : c["expected_capability_ids"]) expected.push_back(id.get<std::string>());
      CW_CHECK_MSG(selection.bestIndex >= 0, where + ": expected a selection, got a rejection");
      if (selection.bestIndex < 0) continue;
      CW_CHECK_MSG(contains(expected, mappedId(ranked[static_cast<size_t>(selection.bestIndex)])),
                   where + ": selected " +
                       mappedId(ranked[static_cast<size_t>(selection.bestIndex)]) +
                       ", expected one of " + idList(expected));
      if (expectation == "resolved_by_kind") {
        CW_CHECK_MSG(selection.kindTieBreak, where + ": expected the delivery kind to decide");
        CW_CHECK_MSG(!selection.ambiguous, where + ": expected the tie to be resolved");
      } else {
        CW_CHECK_MSG(!selection.ambiguous, where + ": unexpected ambiguity");
      }
    }

    // Full pool cases: the requirement against every capability of the five applications.
    for (const nlohmann::json& c : problem["full_pool_cases"]) {
      const std::string caseId = c.value("case_id", std::string());
      const std::string where = problemId + "/" + caseId;
      const spec::SpecParseResult requiredSheet =
          load(root / c["requirement_spec"].get<std::string>());
      CW_CHECK_MSG(requiredSheet.ok, where + ": requirement sheet rejected");
      if (!requiredSheet.ok) continue;
      const std::vector<careweave::core::CapabilitySpec> pool =
          loadCapabilities(root, problem["pool"]);
      CW_CHECK_MSG(pool.size() >= 40,
                   where + ": the full pool should hold the whole corpus");
      const std::vector<mapper::MatchResult> ranked =
          mapper.rank(requiredSheet.model.capabilities.front(), pool);
      CW_CHECK_MSG(!ranked.empty(), where + ": empty pool");
      if (ranked.empty()) continue;
      std::vector<std::string> expected;
      for (const auto& id : c["expected_capability_ids"]) expected.push_back(id.get<std::string>());
      const std::string expectation = c["expectation"].get<std::string>();
      CW_CHECK_MSG(contains(expected, mappedId(ranked[0])),
                   where + ": top 1 is " + mappedId(ranked[0]) + ", expected one of " +
                       idList(expected));
      const mapper::Mapper::Selection selection = mapper.select(ranked);
      if (expectation == "ambiguous") {
        CW_CHECK_MSG(selection.ambiguous, where + ": expected the near tie to be reported");
      } else if (expectation == "top1_with_ambiguity") {
        CW_CHECK_MSG(selection.ambiguous, where + ": expected the near tie to be reported");
      } else if (expectation == "top1") {
        CW_CHECK_MSG(!selection.ambiguous, where + ": unexpected ambiguity");
      }
    }

    // Ambiguity cases: clone a real capability into a twin and require the near tie report.
    for (const nlohmann::json& c : problem["ambiguity_cases"]) {
      const std::string caseId = c.value("case_id", std::string());
      const std::string where = problemId + "/" + caseId;
      const spec::SpecParseResult requiredSheet =
          load(root / c["requirement_spec"].get<std::string>());
      CW_CHECK_MSG(requiredSheet.ok, where + ": requirement sheet rejected");
      if (!requiredSheet.ok) continue;
      std::vector<careweave::core::CapabilitySpec> candidates =
          loadCapabilities(root, c["candidate_specs"]);
      const nlohmann::json inject = c["inject"];
      const std::string cloneId = inject["clone_capability_id"].get<std::string>();
      const auto base = std::find_if(
          candidates.begin(), candidates.end(),
          [&](const careweave::core::CapabilitySpec& s) { return s.id == cloneId; });
      CW_CHECK_MSG(base != candidates.end(), where + ": clone base " + cloneId + " not found");
      if (base == candidates.end()) continue;
      careweave::core::CapabilitySpec twin = *base;
      twin.id = inject["new_capability_id"].get<std::string>();
      twin.name = inject["new_name"].get<std::string>();
      candidates.push_back(twin);
      const std::vector<mapper::MatchResult> ranked =
          mapper.rank(requiredSheet.model.capabilities.front(), candidates);
      const mapper::Mapper::Selection selection = mapper.select(ranked);
      std::vector<std::string> acceptable;
      for (const auto& id : c["acceptable_capability_ids"]) acceptable.push_back(id.get<std::string>());
      CW_CHECK_MSG(selection.ambiguous, where + ": expected an ambiguity report");
      CW_CHECK_MSG(!ranked.empty() && contains(acceptable, mappedId(ranked[0])),
                   where + ": top 1 is " + (ranked.empty() ? std::string("none") : mappedId(ranked[0])));
    }

    // Compatibility cases: adjacent pairs through the symbolic engine.
    for (const nlohmann::json& c : problem["compatibility_cases"]) {
      const std::string caseId = c.value("case_id", std::string());
      const std::string where = problemId + "/" + caseId;
      const spec::SpecParseResult appSheet = load(root / c["app"].get<std::string>());
      CW_CHECK_MSG(appSheet.ok, where + ": application sheet rejected");
      if (!appSheet.ok) continue;
      const compat::CompatEngine engine(appSheet.model);
      std::vector<std::string> sequence;
      for (const auto& id : c["sequence"]) sequence.push_back(id.get<std::string>());
      CW_CHECK_MSG(sequence.size() >= 2, where + ": a compatibility case needs two steps");
      const std::string expectation = c["expectation"].get<std::string>();
      for (size_t i = 0; i + 1 < sequence.size(); ++i) {
        const auto findCapability = [&](const std::string& id) {
          return std::find_if(appSheet.model.capabilities.begin(),
                              appSheet.model.capabilities.end(),
                              [&](const careweave::core::CapabilitySpec& s) { return s.id == id; });
        };
        const auto earlier = findCapability(sequence[i]);
        const auto later = findCapability(sequence[i + 1]);
        CW_CHECK_MSG(earlier != appSheet.model.capabilities.end(),
                     where + ": " + sequence[i] + " not in the application");
        CW_CHECK_MSG(later != appSheet.model.capabilities.end(),
                     where + ": " + sequence[i + 1] + " not in the application");
        if (earlier == appSheet.model.capabilities.end() ||
            later == appSheet.model.capabilities.end()) {
          continue;
        }
        const compat::CompatibilityReport report = engine.check(*earlier, *later);
        const std::string pair = sequence[i] + " then " + sequence[i + 1];
        if (expectation == "compatible") {
          CW_CHECK_MSG(report.verdict == compat::Verdict::COMPATIBLE,
                       where + ": " + pair + " is " + compat::verdictToString(report.verdict) +
                           ", expected compatible");
        } else if (expectation == "uncertain") {
          CW_CHECK_MSG(report.verdict == compat::Verdict::UNCERTAIN,
                       where + ": " + pair + " is " + compat::verdictToString(report.verdict) +
                           ", expected uncertain");
        } else if (expectation == "incompatible") {
          CW_CHECK_MSG(report.verdict == compat::Verdict::INCOMPATIBLE,
                       where + ": " + pair + " is " + compat::verdictToString(report.verdict) +
                           ", expected incompatible");
        }
      }
    }

    // Equivalence groups: every member must exist in its application.
    for (const nlohmann::json& group : problem["equivalence_groups"]) {
      const std::string where =
          problemId + "/" + group.value("logical_operation", std::string());
      for (const auto& member : group["members"]) {
        const spec::SpecParseResult appSheet = load(root / member["app"].get<std::string>());
        CW_CHECK_MSG(appSheet.ok, where + ": application sheet rejected");
        if (!appSheet.ok) continue;
        const std::string id = member["capability_id"].get<std::string>();
        const bool found = std::any_of(
            appSheet.model.capabilities.begin(), appSheet.model.capabilities.end(),
            [&](const careweave::core::CapabilitySpec& s) { return s.id == id; });
        CW_CHECK_MSG(found, where + ": " + id + " not in " + member["app"].get<std::string>());
      }
    }
  }
}

CW_TEST_CASE(state_vocabulary_covers_and_types_every_shipped_sheet) {
  // specs/state_variables.json is the shared typed vocabulary of the project. Every state
  // variable declared by a module, application or requirement sheet must appear there with a
  // type the vocabulary sanctions, so the consistency measurements of the evaluation compare
  // variables that really are the same fact.
  const fs::path root = miniRoot();
  const nlohmann::json vocabulary = loadJsonFile(root / "specs" / "state_variables.json");
  std::map<std::string, std::set<std::string>> types;
  for (const auto& domain : vocabulary["domains"]) {
    for (const auto& variable : domain["variables"]) {
      types[variable["name"].get<std::string>()].insert(variable["type"].get<std::string>());
    }
  }
  CW_CHECK_MSG(types.size() >= 40, "the vocabulary must declare the corpus variables");

  std::vector<fs::path> sheets;
  for (const auto& entry : fs::directory_iterator(root / "modules")) {
    if (entry.is_directory()) sheets.push_back(entry.path() / "spec.json");
  }
  for (const fs::path& sheet : sheetsIn(root / "specs" / "app")) sheets.push_back(sheet);
  for (const fs::path& sheet : sheetsIn(root / "specs" / "app" / "requirements")) {
    sheets.push_back(sheet);
  }
  CW_CHECK_MSG(sheets.size() == 17,
               "expected 17 shipped sheets, found " + std::to_string(sheets.size()));

  for (const fs::path& sheet : sheets) {
    const spec::SpecParseResult result = load(sheet);
    CW_CHECK_MSG(result.ok, sheet.string() + " rejected:" + result.renderIssues());
    if (!result.ok) continue;
    for (const auto& variable : result.model.stateSchema) {
      const auto found = types.find(variable.name);
      if (found == types.end()) {
        CW_CHECK_MSG(false, sheet.string() + " declares state variable " + variable.name +
                                " that the shared vocabulary does not know");
        continue;
      }
      std::string sanctioned;
      for (const std::string& type : found->second) {
        sanctioned += (sanctioned.empty() ? "" : ", ") + type;
      }
      CW_CHECK_MSG(found->second.count(variable.type) != 0,
                   sheet.string() + " types " + variable.name + " as " + variable.type +
                       " while the vocabulary declares " + sanctioned);
    }
  }
}

int main() { return careweave::testing::runAll("test_corpus"); }
