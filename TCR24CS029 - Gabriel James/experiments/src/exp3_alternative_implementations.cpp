// Experiment 3: alternative implementations.
//
// The same logical operation offered through different mechanisms: an API call, a direct row
// write, a screen, a file intake, an event handler. The dataset labels these as equivalence
// groups; this experiment drives the real components over them and measures whether the
// representation captures the functional relationship without treating the implementations as
// identical:
//
//   functional view   preconditions, effects, delta, inputs, outputs: the groups must be close
//   implementation view   type, mechanism, resources, quality: the personas must stay apart
//   partition table   per block cosine against the group reference, so the difference is
//                     attributed to the blocks that should carry it (mechanism, type) and not
//                     to the semantic ones
//   adapter synthesis   the rename and transport tables the synthesizer produces when one
//                     persona is asked to satisfy the requirement of another
//
// Assertions: every cross mechanism pair inside a group is functionally more similar than it is
// implementationally; the mechanisms land on the right transports (http, sqlite, form); the
// vocabulary rename is present when the words differ; and within group functional similarity
// exceeds the cross group baseline.

#include <algorithm>
#include <cstdio>
#include <fstream>
#include <map>
#include <string>
#include <vector>

#include "careweave/adapter/synthesizer.hpp"
#include "careweave/embedding/encoders.hpp"
#include "careweave/embedding/vector.hpp"
#include "careweave/mapper/mapper.hpp"
#include "experiment_support.hpp"
#include "nlohmann/json.hpp"

namespace exp = careweave::experiments;
namespace adapter = careweave::adapter;
namespace embedding = careweave::embedding;
namespace mapper = careweave::mapper;
namespace core = careweave::core;
using nlohmann::json;
using exp::fmt;
using exp::require;

namespace {

struct Member {
  std::string appPath;
  core::ApplicationModel app;
  std::string capabilityId;
  std::string persona;
};

struct Group {
  std::string problem;
  std::string logicalOperation;
  std::vector<Member> members;
};

Member loadMember(const exp::fs::path& root, const std::string& appPath,
                  const std::string& capabilityId, const std::string& persona,
                  std::map<std::string, core::ApplicationModel>& cache) {
  Member member;
  member.appPath = appPath;
  auto it = cache.find(appPath);
  if (it == cache.end()) {
    it = cache.emplace(appPath, exp::loadApplication(root / appPath)).first;
  }
  member.app = it->second;
  member.capabilityId = capabilityId;
  member.persona = persona;
  (void)exp::findCapability(member.app, capabilityId);
  return member;
}

const core::CapabilitySpec& specOf(const Member& member) {
  return exp::findCapability(member.app, member.capabilityId);
}

std::string mappingText(const std::vector<adapter::FieldMapping>& mappings) {
  std::string out;
  for (const adapter::FieldMapping& m : mappings) {
    out += (out.empty() ? "" : ", ") + m.from + " -> " + m.to +
           (m.transform == "identity" ? "" : " [" + m.transform + "]");
  }
  return out;
}

}  // namespace

int main(int argc, char** argv) {
  const std::vector<std::string> args(argv + 1, argv + argc);
  const exp::fs::path out = exp::outDir(args);
  const exp::fs::path root = exp::rootDir();

  // ---- Load the labeled equivalence groups ----
  std::vector<Group> groups;
  std::map<std::string, core::ApplicationModel> appCache;
  const std::vector<std::string> problems = {"hospital_alias", "ecommerce_purchase",
                                             "document_processing"};
  for (const std::string& problem : problems) {
    std::ifstream stream(root / "dataset" / problem / "problem.json");
    require(stream.good(), "cannot open dataset/" + problem + "/problem.json");
    json document;
    stream >> document;
    for (const auto& groupJson : document["equivalence_groups"]) {
      Group group;
      group.problem = problem;
      group.logicalOperation = groupJson["logical_operation"].get<std::string>();
      for (const auto& memberJson : groupJson["members"]) {
        group.members.push_back(loadMember(root, memberJson["app"].get<std::string>(),
                                           memberJson["capability_id"].get<std::string>(),
                                           memberJson["persona"].get<std::string>(), appCache));
      }
      require(group.members.size() >= 2, "an equivalence group needs at least two members");
      groups.push_back(std::move(group));
    }
  }
  require(groups.size() == 4, "the dataset labels four equivalence groups");

  embedding::Encoder encoder;
  mapper::Mapper mapper;
  adapter::AdapterSynthesizer synthesizer;

  // ---- Per group measurements ----
  json groupsJson = json::array();
  std::vector<double> withinFunctional;
  std::vector<double> withinImplementation;
  std::vector<double> crossFunctional;
  std::vector<double> crossImplementation;
  std::string groupTables;

  for (const Group& group : groups) {
    const core::CapabilitySpec& reference = specOf(group.members.front());
    const embedding::EncodedCapability referenceEncoded =
        encoder.encodeCapabilityDetailed(reference);

    // Partition table: block cosine of each member against the reference.
    std::vector<std::string> blockNames;
    for (const auto& kv : referenceEncoded.blocks) blockNames.push_back(kv.first);
    std::vector<std::vector<std::string>> partitionRows;
    partitionRows.push_back({"block"});
    for (const Member& member : group.members) {
      partitionRows[0].push_back(member.capabilityId);
      const embedding::EncodedCapability memberEncoded =
          encoder.encodeCapabilityDetailed(specOf(member));
      (void)memberEncoded;
    }
    for (const std::string& block : blockNames) {
      std::vector<std::string> row{block};
      for (const Member& member : group.members) {
        const embedding::EncodedCapability memberEncoded =
            encoder.encodeCapabilityDetailed(specOf(member));
        const double cosine = embedding::VectorMath::cosine(referenceEncoded.block(block),
                                                            memberEncoded.block(block));
        row.push_back(fmt(cosine));
      }
      partitionRows.push_back(row);
    }

    json groupJson;
    groupJson["problem"] = group.problem;
    groupJson["logical_operation"] = group.logicalOperation;
    groupJson["members"] = json::array();
    for (const Member& member : group.members) {
      const core::CapabilitySpec& spec = specOf(member);
      groupJson["members"].push_back({{"capability", member.capabilityId},
                                      {"persona", member.persona},
                                      {"kind", core::capabilityTypeToString(spec.type)}});
    }

    // Pairwise measurements inside the group.
    std::vector<std::vector<std::string>> pairRows;
    pairRows.push_back({"pair", "kinds", "functional", "implementation", "full cosine",
                        "mapper total", "kind match"});
    json pairsJson = json::array();
    for (size_t i = 0; i < group.members.size(); ++i) {
      for (size_t j = 0; j < group.members.size(); ++j) {
        if (i == j) continue;
        const core::CapabilitySpec& a = specOf(group.members[i]);
        const core::CapabilitySpec& b = specOf(group.members[j]);
        const embedding::EncodedCapability encodedA = encoder.encodeCapabilityDetailed(a);
        const embedding::EncodedCapability encodedB = encoder.encodeCapabilityDetailed(b);
        const double functional = embedding::VectorMath::cosine(encodedA.functionalView(),
                                                                encodedB.functionalView());
        const double implementation = embedding::VectorMath::cosine(
            encodedA.implementationView(), encodedB.implementationView());
        const double full = embedding::VectorMath::cosine(encodedA.vector, encodedB.vector);
        const mapper::MatchResult match = mapper.score(a, b);
        const std::string kinds =
            core::capabilityTypeToString(a.type) + " to " + core::capabilityTypeToString(b.type);
        pairRows.push_back({group.members[i].capabilityId + " -> " +
                                group.members[j].capabilityId,
                            kinds, fmt(functional), fmt(implementation), fmt(full),
                            fmt(match.total), match.kindMatches ? "yes" : "no"});
        pairsJson.push_back({{"from", group.members[i].capabilityId},
                             {"to", group.members[j].capabilityId},
                             {"functional", functional},
                             {"implementation", implementation},
                             {"full_cosine", full},
                             {"mapper_total", match.total},
                             {"kind_match", match.kindMatches}});
        if (group.members[i].persona != group.members[j].persona) {
          require(functional > implementation,
                  "within " + group.logicalOperation + ": " + group.members[i].capabilityId +
                      " vs " + group.members[j].capabilityId +
                      " must be functionally closer than implementationally, got functional " +
                      fmt(functional) + " implementation " + fmt(implementation));
          withinFunctional.push_back(functional);
          withinImplementation.push_back(implementation);
        }
      }
    }
    groupJson["pairs"] = pairsJson;

    // Adapter synthesis inside the group: the reference persona becomes the requirement, each
    // other persona the provider; the transport and the renames are recorded.
    json adaptations = json::array();
    std::vector<std::vector<std::string>> adaptationRows;
    adaptationRows.push_back({"requirement to provider", "kinds", "transport", "input renames",
                              "output renames"});
    for (size_t j = 1; j < group.members.size(); ++j) {
      const core::CapabilitySpec& requirement = specOf(group.members.front());
      const core::CapabilitySpec& provider = specOf(group.members[j]);
      adapter::SynthesisRequest request;
      request.requirement = requirement;
      request.match = mapper.score(requirement, provider);
      request.candidate = provider;
      request.targetModule = group.members[j].app.moduleId;
      request.baseUrl = group.members[j].app.baseUrl;
      request.databasePath = group.members[j].app.databaseFile.empty()
                                 ? "data/careweave_experiment.sqlite3"
                                 : group.members[j].app.databaseFile;
      const adapter::SynthesisResult synthesis = synthesizer.synthesize(request);
      require(synthesis.ok, "adapter synthesis failed for " + group.logicalOperation + ": " +
                                synthesis.render());
      const std::string kinds =
          core::capabilityTypeToString(requirement.type) + " to " +
          core::capabilityTypeToString(provider.type);
      adaptationRows.push_back({group.members.front().capabilityId + " -> " +
                                    group.members[j].capabilityId,
                                kinds, synthesis.adapter.transportKind,
                                mappingText(synthesis.adapter.inputMap),
                                mappingText(synthesis.adapter.outputMap)});
      adaptations.push_back({{"from", group.members.front().capabilityId},
                             {"to", group.members[j].capabilityId},
                             {"transport", synthesis.adapter.transportKind},
                             {"input_map", mappingText(synthesis.adapter.inputMap)},
                             {"output_map", mappingText(synthesis.adapter.outputMap)},
                             {"confidence", synthesis.adapter.confidence}});
    }
    groupJson["adaptations"] = adaptations;
    groupsJson.push_back(groupJson);

    groupTables += "### " + group.logicalOperation + " (" + group.problem + ")\n\n";
    groupTables += exp::markdownTable(pairRows);
    groupTables += "\nPartition table, per block cosine against " +
                   group.members.front().capabilityId + ":\n\n";
    groupTables += exp::markdownTable(partitionRows);
    groupTables += "\nAdapter synthesis from " + group.members.front().capabilityId + ":\n\n";
    groupTables += exp::markdownTable(adaptationRows);
    groupTables += "\n";
  }

  // ---- The acceptance shape: canonical requirement synthesized onto the legacy personas ----
  // register_patient (AR-RegisterPatient) against the legacy registration group, the case the
  // integrated system solves live: the vocabulary rename and the persona transports.
  const core::ApplicationModel& aliasApp =
      appCache["specs/app/hospital_alias_resolution.yaml"];
  const core::CapabilitySpec& canonical =
      exp::findCapability(aliasApp, "AR-RegisterPatient");
  std::vector<std::vector<std::string>> acceptanceRows;
  acceptanceRows.push_back({"canonical to legacy provider", "kind", "transport", "input renames",
                            "output renames"});
  json acceptanceJson = json::array();
  for (const std::string& providerId :
       {"AR-PatReg", "AR-PatRowWrite", "AR-PatRegForm"}) {
    const core::CapabilitySpec& provider = exp::findCapability(aliasApp, providerId);
    adapter::SynthesisRequest request;
    request.requirement = canonical;
    request.match = mapper.score(canonical, provider);
    request.candidate = provider;
    request.targetModule = aliasApp.moduleId;
    request.baseUrl = aliasApp.baseUrl;
    request.databasePath = "data/patient_registry_alt.sqlite3";
    const adapter::SynthesisResult synthesis = synthesizer.synthesize(request);
    require(synthesis.ok, "canonical synthesis failed for " + providerId + ": " +
                              synthesis.render());
    require(synthesis.adapter.transportKind == "http" ||
                synthesis.adapter.transportKind == "sqlite" ||
                synthesis.adapter.transportKind == "form",
            "unexpected transport " + synthesis.adapter.transportKind);
    acceptanceRows.push_back({providerId,
                              core::capabilityTypeToString(provider.type),
                              synthesis.adapter.transportKind,
                              mappingText(synthesis.adapter.inputMap),
                              mappingText(synthesis.adapter.outputMap)});
    acceptanceJson.push_back({{"provider", providerId},
                              {"kind", core::capabilityTypeToString(provider.type)},
                              {"transport", synthesis.adapter.transportKind},
                              {"input_map", mappingText(synthesis.adapter.inputMap)},
                              {"output_map", mappingText(synthesis.adapter.outputMap)}});
  }
  // The transports must match the mechanisms: API http, DATABASE sqlite, GUI form.
  require(acceptanceJson[0]["transport"] == "http", "the API persona must synthesize onto http");
  require(acceptanceJson[1]["transport"] == "sqlite",
          "the DATABASE persona must synthesize onto sqlite");
  require(acceptanceJson[2]["transport"] == "form",
          "the GUI persona must synthesize onto form");
  // The legacy word for the patient number differs from the canonical one; the rename table
  // must carry it.
  require(!acceptanceJson[0]["input_map"].get<std::string>().empty(),
          "the canonical to legacy synthesis must rename at least one input");

  // ---- Cross group baseline for the functional view ----
  const double withinFunctionalMean = exp::mean(withinFunctional);
  const double withinImplementationMean = exp::mean(withinImplementation);
  const std::vector<std::string> referenceId = {"AR-PatReg", "EC-PlaceOrder",
                                                "DOC-UploadDocument"};
  for (size_t i = 0; i < referenceId.size(); ++i) {
    for (size_t j = i + 1; j < referenceId.size(); ++j) {
      const std::string& appA = i == 0 ? "specs/app/hospital_alias_resolution.yaml"
                                       : (i == 1 ? "specs/app/ecommerce_purchase.yaml"
                                                 : "specs/app/document_processing.yaml");
      const std::string& appB = j == 0 ? "specs/app/hospital_alias_resolution.yaml"
                                       : (j == 1 ? "specs/app/ecommerce_purchase.yaml"
                                                 : "specs/app/document_processing.yaml");
      const embedding::EncodedCapability encodedA =
          encoder.encodeCapabilityDetailed(exp::findCapability(appCache[appA], referenceId[i]));
      const embedding::EncodedCapability encodedB =
          encoder.encodeCapabilityDetailed(exp::findCapability(appCache[appB], referenceId[j]));
      crossFunctional.push_back(embedding::VectorMath::cosine(encodedA.functionalView(),
                                                              encodedB.functionalView()));
      crossImplementation.push_back(embedding::VectorMath::cosine(
          encodedA.implementationView(), encodedB.implementationView()));
    }
  }
  const double crossFunctionalMean = exp::mean(crossFunctional);
  require(withinFunctionalMean > crossFunctionalMean,
          "within group functional similarity must exceed the cross group baseline: " +
              fmt(withinFunctionalMean) + " vs " + fmt(crossFunctionalMean));

  // ---- Report ----
  std::printf("experiment 3: alternative implementations\n");
  std::printf("within group (cross mechanism) mean functional %s, mean implementation %s\n",
              fmt(withinFunctionalMean).c_str(), fmt(withinImplementationMean).c_str());
  std::printf("cross group baseline mean functional %s, mean implementation %s\n",
              fmt(crossFunctionalMean).c_str(), fmt(exp::mean(crossImplementation)).c_str());
  std::printf("canonical to legacy synthesis\n%s",
              exp::markdownTable(acceptanceRows).c_str());
  std::printf("%s", groupTables.c_str());

  // ---- Outputs ----
  json result;
  result["experiment"] = "exp3_alternative_implementations";
  result["groups"] = groupsJson;
  result["acceptance_synthesis"] = acceptanceJson;
  result["metrics"]["within_functional_mean"] = withinFunctionalMean;
  result["metrics"]["within_implementation_mean"] = withinImplementationMean;
  result["metrics"]["cross_functional_mean"] = crossFunctionalMean;
  result["metrics"]["cross_implementation_mean"] = exp::mean(crossImplementation);
  exp::writeFile(out / "exp3_alternative_implementations.json", result.dump(2) + "\n");

  std::string csv = "group,from,to,functional,implementation,full_cosine,mapper_total,kind_match\n";
  for (const Group& group : groups) {
    for (size_t i = 0; i < group.members.size(); ++i) {
      for (size_t j = 0; j < group.members.size(); ++j) {
        if (i == j) continue;
        const core::CapabilitySpec& a = specOf(group.members[i]);
        const core::CapabilitySpec& b = specOf(group.members[j]);
        const embedding::EncodedCapability encodedA = encoder.encodeCapabilityDetailed(a);
        const embedding::EncodedCapability encodedB = encoder.encodeCapabilityDetailed(b);
        csv += exp::csvField(group.logicalOperation) + "," + group.members[i].capabilityId + "," +
               group.members[j].capabilityId + "," +
               fmt(embedding::VectorMath::cosine(encodedA.functionalView(),
                                                 encodedB.functionalView())) +
               "," +
               fmt(embedding::VectorMath::cosine(encodedA.implementationView(),
                                                 encodedB.implementationView())) +
               "," + fmt(embedding::VectorMath::cosine(encodedA.vector, encodedB.vector)) + "," +
               fmt(mapper.score(a, b).total) + "," +
               (mapper.score(a, b).kindMatches ? "yes" : "no") + "\n";
      }
    }
  }
  exp::writeFile(out / "exp3_alternative_implementations.csv", csv);

  std::string markdown = "# Experiment 3: alternative implementations\n\n";
  markdown += "Within group (cross mechanism) mean functional similarity " +
              fmt(withinFunctionalMean) + " against cross group baseline " +
              fmt(crossFunctionalMean) + "; within group mean implementation similarity " +
              fmt(withinImplementationMean) + " against cross group " +
              fmt(exp::mean(crossImplementation)) + ".\n\n";
  markdown += "## Canonical requirement onto the legacy personas\n\n" +
              exp::markdownTable(acceptanceRows);
  markdown += "\n## Groups\n\n" + groupTables;
  exp::writeFile(out / "exp3_alternative_implementations.md", markdown);

  std::printf("results written to %s\n", out.string().c_str());
  return 0;
}
