// Experiment 1: capability compatibility.
//
// The assignment pattern: C_1 CreateOrder establishes Order.exists = true, C_2 MakePayment
// requires it, C_3 CancelCart requires its opposite. C_1 -> C_2 must be compatible and
// C_1 -> C_3 incompatible, however similar the three capabilities may look as vectors.
//
// The experiment measures four things on the real components:
//   1. the symbolic verdicts for the pattern triples and for every labeled pair of the shipped
//      dataset (seventeen pairs covering compatible, uncertain and incompatible cases);
//   2. the vector side of the same pairs: the vector compatibility score, functional and
//      implementation similarity, and the mapper's name view as a pure similarity baseline;
//   3. the separation between similar and composable: the high similarity low compatibility
//      pairs, the noise floor from unrelated capabilities, and the ROC AUC of each viewpoint
//      against the composability labels;
//   4. the vocabulary name pair labels: equivalent pairs (register_pat against Pat_reg) must
//      score above distinct pairs under the same sparse text cosine the matcher builds on.
//
// Assertions: the pattern verdicts are exact; every labeled dataset pair keeps its frozen
// verdict; the compatible pattern pair scores strictly above the incompatible one on the
// vector compatibility score. When one of these claims stops holding the run fails.

#include <algorithm>
#include <cstdio>
#include <fstream>
#include <map>
#include <string>
#include <vector>

#include "careweave/compat/compat_engine.hpp"
#include "careweave/embedding/encoders.hpp"
#include "careweave/mapper/mapper.hpp"
#include "experiment_support.hpp"
#include "nlohmann/json.hpp"

namespace exp = careweave::experiments;
namespace compat = careweave::compat;
namespace embedding = careweave::embedding;
namespace mapper = careweave::mapper;
namespace core = careweave::core;
using nlohmann::json;
using exp::fmt;
using exp::require;

namespace {

struct PatternPair {
  std::string earlier;
  std::string later;
  compat::CompatibilityReport report;
};

json reportToJson(const compat::CompatibilityReport& report) {
  json out;
  out["earlier"] = report.earlierId;
  out["later"] = report.laterId;
  out["verdict"] = compat::verdictToString(report.verdict);
  out["vector_score"] = report.scores.vectorScore;
  out["coverage"] = report.scores.coverage;
  out["signed_cosine"] = report.scores.signedCosine;
  out["functional_similarity"] = report.scores.functionalSimilarity;
  out["implementation_similarity"] = report.scores.implementationSimilarity;
  json checks = json::array();
  for (const auto& check : report.checks) {
    checks.push_back({{"name", check.name},
                      {"outcome", compat::outcomeToString(check.outcome)},
                      {"detail", check.detail}});
  }
  out["checks"] = checks;
  return out;
}

struct CorePair {
  std::string problem;
  std::string caseId;
  std::string label;
  compat::CompatibilityReport report;
};

}  // namespace

int main(int argc, char** argv) {
  const std::vector<std::string> args(argv + 1, argv + argc);
  const exp::fs::path out = exp::outDir(args);
  const exp::fs::path root = exp::rootDir();

  // ---- The pattern triple ----
  const std::string patternPath = (root / "experiments" / "specs" / "order_pattern.yaml").string();
  const core::ApplicationModel pattern = exp::loadApplication(patternPath);
  const core::CapabilitySpec& createOrder = exp::findCapability(pattern, "PAT-CreateOrder");
  const core::CapabilitySpec& makePayment = exp::findCapability(pattern, "PAT-MakePayment");
  const core::CapabilitySpec& cancelCart = exp::findCapability(pattern, "PAT-CancelCart");

  const compat::CompatEngine engine(pattern);
  const compat::CompatibilityReport report12 = engine.check(createOrder, makePayment);
  const compat::CompatibilityReport report13 = engine.check(createOrder, cancelCart);
  const compat::CompatibilityReport report31 = engine.check(cancelCart, createOrder);

  require(report12.verdict == compat::Verdict::COMPATIBLE,
          "the assignment pattern requires C_1 -> C_2 to be compatible, got " +
              compat::verdictToString(report12.verdict) + "\n" + report12.render());
  require(report13.verdict == compat::Verdict::INCOMPATIBLE,
          "the assignment pattern requires C_1 -> C_3 to be incompatible, got " +
              compat::verdictToString(report13.verdict) + "\n" + report13.render());
  require(report13.scores.signedCosine < 0.0,
          "the incompatible pair must show a negative signed effect-precondition cosine");
  require(report12.scores.vectorScore > report13.scores.vectorScore,
          "the vector compatibility score must rank C_1 -> C_2 above C_1 -> C_3");

  // ---- Vector side of the pattern ----
  embedding::Encoder encoder;
  const embedding::Vector v1 = encoder.encodeCapability(createOrder);
  const embedding::Vector v2 = encoder.encodeCapability(makePayment);
  const embedding::Vector v3 = encoder.encodeCapability(cancelCart);
  const double cos12 = embedding::VectorMath::cosine(v1, v2);
  const double cos13 = embedding::VectorMath::cosine(v1, v3);
  const double cos23 = embedding::VectorMath::cosine(v2, v3);
  require(std::abs(cos12 - cos13) < 0.05,
          "the raw full-vector cosine is expected to be blind on the pattern pairs (it measures "
          "overall resemblance, not composability); the exhibit lost its point");

  mapper::Mapper mapper;
  const mapper::MatchResult name12 = mapper.score(createOrder, makePayment);
  const mapper::MatchResult name13 = mapper.score(createOrder, cancelCart);

  // ---- Noise floor: one pattern capability against unrelated capabilities ----
  const std::vector<core::CapabilitySpec> decoys =
      exp::loadCapabilities({root / "experiments" / "specs" / "irrelevant_decoys.yaml"});
  std::vector<double> decoyCosines;
  std::vector<double> decoyNameSimilarities;
  for (const core::CapabilitySpec& decoy : decoys) {
    decoyCosines.push_back(embedding::VectorMath::cosine(v1, encoder.encodeCapability(decoy)));
    decoyNameSimilarities.push_back(mapper.score(createOrder, decoy).nameSimilarity);
  }

  // ---- The shipped dataset pairs ----
  std::vector<CorePair> corpus;
  const std::vector<std::string> problems = {"hospital_alias", "ecommerce_purchase",
                                             "document_processing"};
  std::map<std::string, core::ApplicationModel> appCache;
  const auto loadApp = [&](const std::string& relative) -> const core::ApplicationModel& {
    auto it = appCache.find(relative);
    if (it == appCache.end()) {
      it = appCache.emplace(relative, exp::loadApplication(root / relative)).first;
    }
    return it->second;
  };
  for (const std::string& problem : problems) {
    std::ifstream stream(root / "dataset" / problem / "problem.json");
    require(stream.good(), "cannot open dataset/" + problem + "/problem.json");
    json document;
    stream >> document;
    for (const auto& c : document["compatibility_cases"]) {
      const std::string appPath = c["app"].get<std::string>();
      const core::ApplicationModel& app = loadApp(appPath);
      const core::CapabilitySpec& earlier = exp::findCapability(app, c["sequence"][0].get<std::string>());
      const core::CapabilitySpec& later = exp::findCapability(app, c["sequence"][1].get<std::string>());
      const compat::CompatEngine appEngine(app);
      CorePair pair;
      pair.problem = problem;
      pair.caseId = c["case_id"].get<std::string>();
      pair.label = c["expectation"].get<std::string>();
      pair.report = appEngine.check(earlier, later);
      corpus.push_back(std::move(pair));
    }
  }

  size_t mismatches = 0;
  for (const CorePair& pair : corpus) {
    if (pair.label != compat::verdictToString(pair.report.verdict)) ++mismatches;
  }
  require(mismatches == 0,
          std::to_string(mismatches) + " labeled dataset pairs changed their frozen verdict");
  require(corpus.size() == 17, "the dataset must hold the seventeen labeled pairs by now");

  // ROC AUC of three viewpoints against "compatible" as the positive class. The symbolic
  // verdict itself is the accuracy column; the two continuous viewpoints show what pure
  // similarity can and cannot see.
  std::vector<double> vectorScores;
  std::vector<double> functionalScores;
  std::vector<double> nameScores;
  std::vector<double> rawCosines;
  std::vector<int> labels;
  for (const CorePair& pair : corpus) {
    vectorScores.push_back(pair.report.scores.vectorScore);
    functionalScores.push_back(pair.report.scores.functionalSimilarity);
    labels.push_back(pair.label == "compatible" ? 1 : 0);
  }
  // Name similarity and raw full-vector cosine per corpus pair, measured over the pair's own
  // application; the raw cosine is the naive baseline that treats the full vector as one
  // undifferentiated similarity.
  size_t index = 0;
  for (const std::string& problem : problems) {
    std::ifstream stream(root / "dataset" / problem / "problem.json");
    json document;
    stream >> document;
    for (const auto& c : document["compatibility_cases"]) {
      const core::ApplicationModel& app = loadApp(c["app"].get<std::string>());
      const core::CapabilitySpec& earlier =
          exp::findCapability(app, c["sequence"][0].get<std::string>());
      const core::CapabilitySpec& later =
          exp::findCapability(app, c["sequence"][1].get<std::string>());
      nameScores.push_back(mapper.score(earlier, later).nameSimilarity);
      rawCosines.push_back(
          embedding::VectorMath::cosine(encoder.encodeCapability(earlier),
                                        encoder.encodeCapability(later)));
      ++index;
    }
  }
  require(index == corpus.size(), "the baselines must cover every labeled pair");

  // ---- Vocabulary name pair labels ----
  // The dataset labels name level pairs as equivalent (alias variants a human reads as the same
  // operation, register_pat against Pat_reg) or distinct. The measurement uses the sparse
  // feature cosine, the same text comparison the matcher builds on; the projected vector is not
  // used here because short identifiers carry too few features for the hashed projection to
  // stay discriminative.
  struct NamePair {
    std::string problem;
    std::string left;
    std::string right;
    std::string label;
    double similarity = 0.0;
  };
  std::vector<NamePair> namePairs;
  for (const std::string& problem : problems) {
    std::ifstream stream(root / "dataset" / problem / "problem.json");
    require(stream.good(), "cannot open dataset/" + problem + "/problem.json");
    json document;
    stream >> document;
    for (const auto& entry : document["name_pairs"]) {
      NamePair pair;
      pair.problem = problem;
      pair.left = entry["left"].get<std::string>();
      pair.right = entry["right"].get<std::string>();
      pair.label = entry["label"].get<std::string>();
      pair.similarity = embedding::TextFeatures::sparseCosine(pair.left, pair.right);
      namePairs.push_back(std::move(pair));
    }
  }
  require(namePairs.size() == 18, "the dataset must hold the eighteen name pairs by now");
  std::vector<double> equivalentSimilarities;
  std::vector<double> distinctSimilarities;
  std::vector<double> mechanismSimilarities;
  std::vector<double> namePairScores;
  std::vector<int> namePairLabels;
  for (const NamePair& pair : namePairs) {
    namePairScores.push_back(pair.similarity);
    namePairLabels.push_back(pair.label == "equivalent" ? 1 : 0);
    if (pair.label == "equivalent") {
      equivalentSimilarities.push_back(pair.similarity);
    } else if (pair.label == "mechanism") {
      mechanismSimilarities.push_back(pair.similarity);
    } else {
      distinctSimilarities.push_back(pair.similarity);
    }
  }
  require(equivalentSimilarities.size() == 5 && distinctSimilarities.size() == 11 &&
              mechanismSimilarities.size() == 2,
          "the name pair labels must split into five equivalent, eleven distinct and two "
          "mechanism pairs");
  const double equivalentMean = exp::mean(equivalentSimilarities);
  const double distinctMean = exp::mean(distinctSimilarities);
  const double equivalentMin = exp::minValue(equivalentSimilarities);
  const double distinctMax = exp::maxValue(distinctSimilarities);
  const double mechanismMax = exp::maxValue(mechanismSimilarities);
  const double namePairAuc = exp::rocAuc(namePairScores, namePairLabels);
  require(equivalentMean > distinctMean,
          "equivalent name pairs must score above distinct pairs on average");
  require(namePairAuc >= 0.9, "the name view must rank equivalent above distinct pairs, AUC " +
                                  fmt(namePairAuc));
  require(mechanismMax < equivalentMin,
          "a mechanism pair shares no name vocabulary and must stay below every equivalent pair; "
          "the operation equality is pinned by the equivalence groups instead");

  const double aucVector = exp::rocAuc(vectorScores, labels);
  const double aucFunctional = exp::rocAuc(functionalScores, labels);
  const double aucName = exp::rocAuc(nameScores, labels);

  // The decidable discrimination: composable pairs against provably incompatible ones, leaving
  // the honest uncertainties aside. This is where the assignment's claim lives, because pure
  // similarity baselines have no way to express "cannot prove".
  std::vector<double> discVector;
  std::vector<double> discFunctional;
  std::vector<double> discName;
  std::vector<double> discCosine;
  std::vector<int> discLabels;
  for (size_t i = 0; i < corpus.size(); ++i) {
    if (corpus[i].label == "compatible") {
      discLabels.push_back(1);
    } else if (corpus[i].label == "incompatible") {
      discLabels.push_back(0);
    } else {
      continue;
    }
    discVector.push_back(vectorScores[i]);
    discFunctional.push_back(functionalScores[i]);
    discName.push_back(nameScores[i]);
    discCosine.push_back(rawCosines[i]);
  }
  require(discLabels.size() == 6, "the decidable discrimination holds three versus three pairs");
  const double discVectorAuc = exp::rocAuc(discVector, discLabels);
  const double discFunctionalAuc = exp::rocAuc(discFunctional, discLabels);
  const double discNameAuc = exp::rocAuc(discName, discLabels);
  const double discCosineAuc = exp::rocAuc(discCosine, discLabels);

  require(discVectorAuc >= 0.95,
          "the vector compatibility score must separate composable from incompatible pairs, "
          "AUC " + fmt(discVectorAuc));
  require(discFunctionalAuc < discVectorAuc,
          "effects alignment must beat resemblance on the decidable pairs");
  require(discNameAuc <= 0.5,
          "name similarity must not separate composable from incompatible pairs; measured AUC " +
              fmt(discNameAuc));

  double symbolicAccuracy = 0.0;
  for (size_t i = 0; i < corpus.size(); ++i) {
    const int predicted = corpus[i].report.verdict == compat::Verdict::COMPATIBLE ? 1 : 0;
    if (predicted == labels[i]) symbolicAccuracy += 1.0;
  }
  symbolicAccuracy /= static_cast<double>(corpus.size());

  // ---- Report table for the pattern ----
  std::vector<std::vector<std::string>> patternRows;
  patternRows.push_back({"pair", "verdict", "vector score", "coverage", "signed cosine",
                         "functional sim", "implementation sim", "name sim", "full cosine"});
  const auto patternRow = [&](const std::string& name, const compat::CompatibilityReport& r,
                              const mapper::MatchResult& m, double cosine) {
    patternRows.push_back({name, compat::verdictToString(r.verdict), fmt(r.scores.vectorScore),
                           fmt(r.scores.coverage), fmt(r.scores.signedCosine),
                           fmt(r.scores.functionalSimilarity),
                           fmt(r.scores.implementationSimilarity), fmt(m.nameSimilarity),
                           fmt(cosine)});
  };
  patternRow("C_1 -> C_2 (composable)", report12, name12, cos12);
  patternRow("C_1 -> C_3 (incompatible)", report13, name13, cos13);
  patternRows.push_back({"C_2 -> C_3", compat::verdictToString(report31.verdict), "", "", "", "",
                         "", "", ""});

  // ---- Report table for the dataset pairs ----
  std::vector<std::vector<std::string>> corpusRows;
  corpusRows.push_back({"problem", "case", "label", "verdict", "vector score", "functional sim",
                        "name sim", "raw cosine"});
  for (size_t i = 0; i < corpus.size(); ++i) {
    corpusRows.push_back({corpus[i].problem, corpus[i].caseId, corpus[i].label,
                          compat::verdictToString(corpus[i].report.verdict),
                          fmt(corpus[i].report.scores.vectorScore),
                          fmt(corpus[i].report.scores.functionalSimilarity),
                          fmt(nameScores[i]), fmt(rawCosines[i])});
  }

  // ---- Console summary ----
  std::printf("experiment 1: capability compatibility\n");
  std::printf("pattern pairs\n%s", exp::markdownTable(patternRows).c_str());
  std::printf("dataset pairs\n%s", exp::markdownTable(corpusRows).c_str());
  std::printf("noise floor against %zu unrelated decoys: cosine mean %s max %s; name sim mean "
              "%s max %s\n",
              decoys.size(), fmt(exp::mean(decoyCosines)).c_str(),
              fmt(exp::maxValue(decoyCosines)).c_str(),
              fmt(exp::mean(decoyNameSimilarities)).c_str(),
              fmt(exp::maxValue(decoyNameSimilarities)).c_str());
  std::printf("three-class agreement (17 pairs): symbolic accuracy %s; scalar viewpoints: vector "
              "score AUC %s, functional sim AUC %s, name sim AUC %s (a scalar has no \"cannot "
              "prove\" class, which is the point of the symbolic verdict)\n",
              fmt(symbolicAccuracy).c_str(), fmt(aucVector).c_str(),
              fmt(aucFunctional).c_str(), fmt(aucName).c_str());
  std::printf("decidable discrimination (3 composable vs 3 incompatible): vector score AUC %s, "
              "functional sim AUC %s, name sim AUC %s, raw cosine AUC %s\n",
              fmt(discVectorAuc).c_str(), fmt(discFunctionalAuc).c_str(),
              fmt(discNameAuc).c_str(), fmt(discCosineAuc).c_str());
  std::printf("vocabulary name pairs (%zu pairs): equivalent mean %s (min %s), distinct mean %s "
              "(max %s), mechanism pairs max %s, AUC %s\n",
              namePairs.size(), fmt(equivalentMean).c_str(), fmt(equivalentMin).c_str(),
              fmt(distinctMean).c_str(), fmt(distinctMax).c_str(), fmt(mechanismMax).c_str(),
              fmt(namePairAuc).c_str());

  // ---- Outputs ----
  json result;
  result["experiment"] = "exp1_compatibility";
  result["pattern"]["sheet"] = "experiments/specs/order_pattern.yaml";
  result["pattern"]["pairs"] = json::array();
  for (const PatternPair& pair :
       std::vector<PatternPair>{{"PAT-CreateOrder", "PAT-MakePayment", report12},
                                {"PAT-CreateOrder", "PAT-CancelCart", report13},
                                {"PAT-CancelCart", "PAT-CreateOrder", report31}}) {
    result["pattern"]["pairs"].push_back(reportToJson(pair.report));
  }
  result["pattern"]["cosine_create_payment"] = cos12;
  result["pattern"]["cosine_create_cancel"] = cos13;
  result["pattern"]["cosine_payment_cancel"] = cos23;
  result["dataset"]["pairs"] = json::array();
  for (size_t i = 0; i < corpus.size(); ++i) {
    json entry = reportToJson(corpus[i].report);
    entry["problem"] = corpus[i].problem;
    entry["case"] = corpus[i].caseId;
    entry["label"] = corpus[i].label;
    entry["name_similarity"] = nameScores[i];
    result["dataset"]["pairs"].push_back(entry);
  }
  result["noise_floor"]["decoy_cosine_mean"] = exp::mean(decoyCosines);
  result["noise_floor"]["decoy_cosine_max"] = exp::maxValue(decoyCosines);
  result["noise_floor"]["decoy_name_sim_mean"] = exp::mean(decoyNameSimilarities);
  result["noise_floor"]["decoy_name_sim_max"] = exp::maxValue(decoyNameSimilarities);
  result["metrics"]["symbolic_accuracy"] = symbolicAccuracy;
  result["metrics"]["vector_score_auc"] = aucVector;
  result["metrics"]["functional_similarity_auc"] = aucFunctional;
  result["metrics"]["name_similarity_auc"] = aucName;
  result["metrics"]["discrimination_vector_score_auc"] = discVectorAuc;
  result["metrics"]["discrimination_functional_auc"] = discFunctionalAuc;
  result["metrics"]["discrimination_name_auc"] = discNameAuc;
  result["metrics"]["discrimination_raw_cosine_auc"] = discCosineAuc;
  result["name_pairs"] = json::array();
  for (const NamePair& pair : namePairs) {
    result["name_pairs"].push_back({{"problem", pair.problem},
                                    {"left", pair.left},
                                    {"right", pair.right},
                                    {"label", pair.label},
                                    {"similarity", pair.similarity}});
  }
  result["metrics"]["name_pair_auc"] = namePairAuc;
  result["metrics"]["name_pair_equivalent_mean"] = equivalentMean;
  result["metrics"]["name_pair_equivalent_min"] = equivalentMin;
  result["metrics"]["name_pair_distinct_mean"] = distinctMean;
  result["metrics"]["name_pair_distinct_max"] = distinctMax;
  result["metrics"]["name_pair_mechanism_max"] = mechanismMax;
  exp::writeFile(out / "exp1_compatibility.json", result.dump(2) + "\n");

  std::string csv = "pair,verdict,vector_score,coverage,signed_cosine,functional_sim,"
                    "implementation_sim\n";
  for (const CorePair& pair : corpus) {
    csv += exp::csvField(pair.problem + "/" + pair.caseId) + "," +
           compat::verdictToString(pair.report.verdict) + "," +
           fmt(pair.report.scores.vectorScore) + "," + fmt(pair.report.scores.coverage) + "," +
           fmt(pair.report.scores.signedCosine) + "," +
           fmt(pair.report.scores.functionalSimilarity) + "," +
           fmt(pair.report.scores.implementationSimilarity) + "\n";
  }
  exp::writeFile(out / "exp1_compatibility.csv", csv);

  std::string markdown = "# Experiment 1: capability compatibility\n\n";
  markdown += "The assignment pattern (C_1 CreateOrder, C_2 MakePayment, C_3 CancelCart):\n\n";
  markdown += exp::markdownTable(patternRows);
  markdown += "\nThe seventeen labeled dataset pairs:\n\n";
  markdown += exp::markdownTable(corpusRows);
  markdown += "\nThree-class agreement over the seventeen labels: symbolic accuracy " +
              fmt(symbolicAccuracy) + " (the outcome is reported, never guessed). A scalar "
              "viewpoint has no way to express \"cannot prove\", so its AUC understates the "
              "symbolic system; the vector compatibility score still ranks composable pairs "
              "highest (AUC " + fmt(aucVector) + "), functional similarity is weaker (" +
              fmt(aucFunctional) + ") and name similarity is below chance (" + fmt(aucName) +
              ").\n\n";
  markdown += "Decidable discrimination (composable against provably incompatible): vector "
              "compatibility score AUC " + fmt(discVectorAuc) + ", functional similarity AUC " +
              fmt(discFunctionalAuc) + ", name similarity AUC " + fmt(discNameAuc) +
              ", raw full-vector cosine AUC " + fmt(discCosineAuc) + ".\n\n";
  markdown += "Vocabulary name pair labels (" + std::to_string(namePairs.size()) +
              " pairs): the sparse text cosine scores equivalent pairs at mean " +
              fmt(equivalentMean) + " (minimum " + fmt(equivalentMin) + ") and distinct pairs at "
              "mean " + fmt(distinctMean) + " (maximum " + fmt(distinctMax) + "), AUC " +
              fmt(namePairAuc) + ". The two mechanism pairs (the same operation through a "
              "different delivery persona, names deliberately disjoint) stay at or below " +
              fmt(mechanismMax) + ": name similarity is the wrong instrument for them, and their "
              "operation equality is pinned by the equivalence groups.\n\n";
  markdown += "Noise floor from the " + std::to_string(decoys.size()) +
              " unrelated capabilities: full-vector cosine mean " + fmt(exp::mean(decoyCosines)) +
              " max " + fmt(exp::maxValue(decoyCosines)) + " (the full vector shares positive "
              "structure everywhere, which is why comparisons use the partitioned views), name "
              "similarity mean " + fmt(exp::mean(decoyNameSimilarities)) + " max " +
              fmt(exp::maxValue(decoyNameSimilarities)) + ".\n";
  exp::writeFile(out / "exp1_compatibility.md", markdown);

  std::printf("results written to %s\n", out.string().c_str());
  return 0;
}
