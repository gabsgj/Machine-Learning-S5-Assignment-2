// Experiment 4: irrelevant capabilities.
//
// The full corpus of 53 application capabilities is extended with the 24 unrelated decoys of
// experiments/specs/irrelevant_decoys.yaml, so every requirement is ranked against 77
// candidates out of which only one or two are the intended answer. The experiment measures
// precision@k, recall@k, the mean reciprocal rank, the ROC AUC of the ranking against the
// relevant set, and the ceiling of the irrelevant capabilities (the hardest decoy is reported,
// not hidden), with the name-only ranking as the similarity baseline.
//
// Assertions: every intended capability is ranked first; every decoy stays below the calibrated
// threshold and strictly below the weakest intended answer; MRR is 1; the ranking AUC beats the
// name-only baseline and reaches 0.95; the decoy sheet holds at least twenty capabilities.

#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

#include "careweave/mapper/mapper.hpp"
#include "experiment_support.hpp"
#include "nlohmann/json.hpp"

namespace exp = careweave::experiments;
namespace mapper = careweave::mapper;
namespace core = careweave::core;
using nlohmann::json;
using exp::fmt;
using exp::require;

namespace {

struct Requirement {
  std::string name;
  std::string sheet;
  std::vector<std::string> relevant;
};

}  // namespace

int main(int argc, char** argv) {
  const std::vector<std::string> args(argv + 1, argv + argc);
  const exp::fs::path out = exp::outDir(args);
  const exp::fs::path root = exp::rootDir();

  const std::vector<exp::fs::path> poolSheets = {
      root / "specs" / "app" / "ecommerce_purchase.yaml",
      root / "specs" / "app" / "hospital_clinic_visit.yaml",
      root / "specs" / "app" / "hospital_alias_resolution.yaml",
      root / "specs" / "app" / "document_processing.yaml",
      root / "specs" / "app" / "compliance_audit.yaml",
  };
  std::vector<core::CapabilitySpec> pool = exp::loadCapabilities(poolSheets);
  const std::vector<core::CapabilitySpec> decoys =
      exp::loadCapabilities({root / "experiments" / "specs" / "irrelevant_decoys.yaml"});
  require(decoys.size() >= 20, "the decoy sheet must hold at least twenty capabilities");
  for (const core::CapabilitySpec& decoy : decoys) pool.push_back(decoy);
  require(pool.size() == 77, "the distractor pool is 53 corpus capabilities plus 24 decoys");

  std::vector<std::string> decoyIds;
  for (const core::CapabilitySpec& decoy : decoys) decoyIds.push_back(decoy.id);

  const std::vector<Requirement> requirements = {
      {"register_pat", "specs/app/requirements/register_pat.yaml", {"AR-PatReg"}},
      {"register_patient",
       "specs/app/requirements/register_patient.yaml",
       {"CV-RegisterPatient", "AR-RegisterPatient"}},
      {"place_order", "specs/app/requirements/place_order.yaml", {"EC-PlaceOrder"}},
      {"summarize_document",
       "specs/app/requirements/summarize_document.yaml",
       {"DOC-Summarize"}},
      {"export_audit_report",
       "specs/app/requirements/export_audit_report.yaml",
       {"AUD-ExportReport"}},
  };

  mapper::Mapper mapper;
  // The calibrated selection threshold; see Mapper::select and documents/12_DATASET_SPEC.md.
  constexpr double kThreshold = 0.55;
  json resultsJson = json::array();
  std::vector<std::vector<std::string>> rows;
  rows.push_back({"requirement", "rank of intended", "P@1", "P@3", "P@5", "R@5", "MRR",
                  "AUC", "best decoy", "best decoy score", "intended margin"});
  std::vector<double> mrrs;
  double weakestIntended = 1.0;
  double strongestDecoy = 0.0;
  std::string strongestDecoyId;

  for (const Requirement& requirement : requirements) {
    const core::ApplicationModel sheet = exp::loadApplication(root / requirement.sheet);
    require(sheet.capabilities.size() == 1, "a requirement sheet declares one capability");
    const core::CapabilitySpec& asked = sheet.capabilities.front();
    const std::vector<mapper::MatchResult> ranked = mapper.rank(asked, pool);
    require(!ranked.empty(), "ranked pool must not be empty");

    // Rank of each relevant capability and the metrics over the relevant set.
    std::vector<int> relevantRanks;
    std::vector<double> scores;
    std::vector<int> labels;
    for (size_t i = 0; i < ranked.size(); ++i) {
      const bool relevant =
          std::find(requirement.relevant.begin(), requirement.relevant.end(),
                    ranked[i].candidateId) != requirement.relevant.end();
      scores.push_back(ranked[i].total);
      labels.push_back(relevant ? 1 : 0);
      if (relevant) relevantRanks.push_back(static_cast<int>(i) + 1);
    }
    require(relevantRanks.size() == requirement.relevant.size(),
            "every labeled relevant capability must be in the pool");
    const int topRank = relevantRanks.empty() ? -1 : *std::min_element(
        relevantRanks.begin(), relevantRanks.end());
    require(topRank == 1,
            requirement.name + ": the intended capability must rank first, got rank " +
                std::to_string(topRank) + " (" + ranked.front().candidateId + ")");

    // The name-only baseline: same pool, ranked by the mapper's name view alone.
    std::vector<mapper::MatchResult> nameRanked = ranked;
    std::sort(nameRanked.begin(), nameRanked.end(),
              [](const mapper::MatchResult& a, const mapper::MatchResult& b) {
                return a.nameSimilarity > b.nameSimilarity;
              });
    std::vector<int> nameRelevantRanks;
    std::vector<double> nameScores;
    for (size_t i = 0; i < nameRanked.size(); ++i) {
      nameScores.push_back(nameRanked[i].nameSimilarity);
      if (std::find(requirement.relevant.begin(), requirement.relevant.end(),
                    nameRanked[i].candidateId) != requirement.relevant.end()) {
        nameRelevantRanks.push_back(static_cast<int>(i) + 1);
      }
    }

    const double precision1 = exp::precisionAtK(relevantRanks, 1);
    const double precision3 = exp::precisionAtK(relevantRanks, 3);
    const double precision5 = exp::precisionAtK(relevantRanks, 5);
    const double recall5 = exp::recallAtK(relevantRanks, 5, requirement.relevant.size());
    const double mrr = exp::reciprocalRank(relevantRanks);
    const double auc = exp::rocAuc(scores, labels);
    const double nameAuc = exp::rocAuc(nameScores, labels);
    mrrs.push_back(mrr);
    require(mrr == 1.0, requirement.name + ": the first relevant answer must be rank 1");
    require(auc >= 0.95, requirement.name + ": ranking AUC " + fmt(auc) + " below 0.95");
    require(auc >= nameAuc,
            requirement.name + ": the full mapping must not lose to the name-only baseline (" +
                fmt(auc) + " vs " + fmt(nameAuc) + ")");

    // Decoy ceiling: the best irrelevant capability and how far it is from the intended one.
    std::string bestDecoyId;
    double bestDecoyScore = -1.0;
    int bestDecoyRank = 0;
    for (size_t i = 0; i < ranked.size(); ++i) {
      if (std::find(decoyIds.begin(), decoyIds.end(), ranked[i].candidateId) == decoyIds.end()) {
        continue;
      }
      if (ranked[i].total > bestDecoyScore) {
        bestDecoyScore = ranked[i].total;
        bestDecoyId = ranked[i].candidateId;
        bestDecoyRank = static_cast<int>(i) + 1;
      }
    }
    require(bestDecoyScore < kThreshold,
            requirement.name + ": decoy " + bestDecoyId + " reached " + fmt(bestDecoyScore) +
                ", above the calibrated threshold " + fmt(kThreshold));
    const double lowestIntended = ranked[static_cast<size_t>(*std::max_element(
                                      relevantRanks.begin(), relevantRanks.end())) - 1]
                                      .total;
    require(bestDecoyScore < lowestIntended,
            requirement.name + ": the best decoy must stay below the weakest intended answer");
    weakestIntended = std::min(weakestIntended, lowestIntended);
    if (bestDecoyScore > strongestDecoy) {
      strongestDecoy = bestDecoyScore;
      strongestDecoyId = bestDecoyId;
    }

    // The selection must land on an intended capability; a reported ambiguity is recorded, not
    // suppressed (the legacy requirement genuinely ties with the canonical registration).
    const mapper::Mapper::Selection selection = mapper.select(ranked);
    require(selection.bestIndex >= 0, requirement.name + ": the selection must not reject");
    require(std::find(requirement.relevant.begin(), requirement.relevant.end(),
                      ranked[static_cast<size_t>(selection.bestIndex)].candidateId) !=
                requirement.relevant.end(),
            requirement.name + ": the selection must land on an intended capability");

    rows.push_back({requirement.name, std::to_string(topRank), fmt(precision1),
                    fmt(precision3), fmt(precision5), fmt(recall5), fmt(mrr), fmt(auc),
                    bestDecoyId + " (rank " + std::to_string(bestDecoyRank) + ")",
                    fmt(bestDecoyScore), fmt(ranked[0].total - lowestIntended)});

    resultsJson.push_back({{"requirement", requirement.name},
                           {"pool_size", pool.size()},
                           {"top_rank", topRank},
                           {"precision_at_1", precision1},
                           {"precision_at_3", precision3},
                           {"precision_at_5", precision5},
                           {"recall_at_5", recall5},
                           {"mrr", mrr},
                           {"auc", auc},
                           {"name_baseline_auc", nameAuc},
                           {"best_decoy", bestDecoyId},
                           {"best_decoy_rank", bestDecoyRank},
                           {"best_decoy_score", bestDecoyScore},
                           {"weakest_intended_score", lowestIntended},
                           {"selected", ranked[static_cast<size_t>(selection.bestIndex)].candidateId},
                           {"selection_ambiguous", selection.ambiguous},
                           {"selection_kind_tie_break", selection.kindTieBreak},
                           {"threshold", kThreshold}});
  }

  const double meanMrr = exp::mean(mrrs);
  require(meanMrr == 1.0, "the mean reciprocal rank over the five requirements must be 1");

  std::printf("experiment 4: irrelevant capabilities\n");
  std::printf("pool: %zu capabilities (%zu corpus + %zu decoys)\n", pool.size(),
              pool.size() - decoys.size(), decoys.size());
  std::printf("%s", exp::markdownTable(rows).c_str());
  std::printf("weakest intended answer %s, strongest decoy %s (%s)\n",
              fmt(weakestIntended).c_str(), fmt(strongestDecoy).c_str(),
              strongestDecoyId.c_str());

  // ---- Outputs ----
  json result;
  result["experiment"] = "exp4_irrelevant_capabilities";
  result["pool_size"] = pool.size();
  result["decoy_count"] = decoys.size();
  result["requirements"] = resultsJson;
  result["mean_mrr"] = meanMrr;
  result["weakest_intended_score"] = weakestIntended;
  result["strongest_decoy"] = strongestDecoyId;
  result["strongest_decoy_score"] = strongestDecoy;
  exp::writeFile(out / "exp4_irrelevant_capabilities.json", result.dump(2) + "\n");

  std::string csv = "requirement,top_rank,precision_at_1,precision_at_3,precision_at_5,"
                    "recall_at_5,mrr,auc,name_baseline_auc,best_decoy,best_decoy_score\n";
  for (const auto& entry : resultsJson) {
    csv += exp::csvField(entry["requirement"].get<std::string>()) + "," +
           std::to_string(entry["top_rank"].get<int>()) + "," +
           fmt(entry["precision_at_1"].get<double>()) + "," +
           fmt(entry["precision_at_3"].get<double>()) + "," +
           fmt(entry["precision_at_5"].get<double>()) + "," +
           fmt(entry["recall_at_5"].get<double>()) + "," + fmt(entry["mrr"].get<double>()) + "," +
           fmt(entry["auc"].get<double>()) + "," +
           fmt(entry["name_baseline_auc"].get<double>()) + "," +
           exp::csvField(entry["best_decoy"].get<std::string>()) + "," +
           fmt(entry["best_decoy_score"].get<double>()) + "\n";
  }
  exp::writeFile(out / "exp4_irrelevant_capabilities.csv", csv);

  std::string markdown = "# Experiment 4: irrelevant capabilities\n\n";
  markdown += "Distractor pool: " + std::to_string(pool.size()) + " capabilities (" +
              std::to_string(pool.size() - decoys.size()) + " corpus plus " +
              std::to_string(decoys.size()) + " unrelated decoys, three of them sharing a token "
              "with a requirement on purpose).\n\n";
  markdown += exp::markdownTable(rows);
  markdown += "\nWeakest intended answer " + fmt(weakestIntended) + "; strongest decoy " +
              fmt(strongestDecoy) + " (" + strongestDecoyId + ").\n";
  exp::writeFile(out / "exp4_irrelevant_capabilities.md", markdown);

  std::printf("results written to %s\n", out.string().c_str());
  return 0;
}
