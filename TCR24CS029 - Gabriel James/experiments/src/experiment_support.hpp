#pragma once
// Shared plumbing for the experiment programs and the evaluation harness.
//
// Every experiment is an ordinary program: it loads the shipped corpus through the real parser,
// drives the real components, prints a readable summary, writes machine readable results into
// experiments/out/ and fails with a non zero exit code when an assertion about the claimed
// property does not hold. The helpers here keep the five experiments and the evaluation harness
// uniform.
#include <filesystem>
#include <string>
#include <vector>

#include "careweave/core/types.hpp"

namespace careweave {
namespace experiments {

namespace fs = std::filesystem;

// The CareWeave Mini root directory, baked in at configure time.
fs::path rootDir();
// Output directory: experiments/out by default, overridable with `--out <dir>`.
fs::path outDir(const std::vector<std::string>& args);
// Parses `--out <dir>` out of an argument vector; the flag itself is tolerated by experiments
// that only care about the output location.
std::vector<std::string> positionalArgs(const std::vector<std::string>& args);

// Assertion with a clear failure line. Exits 1 so a broken claim can never pass silently.
void require(bool condition, const std::string& message);

// Loads one specification sheet with schema validation; exits with the rendered issues on
// failure, because every experiment depends on the corpus being valid.
core::ApplicationModel loadApplication(const fs::path& file);
// Finds a capability by id; exits when the corpus does not contain it (the experiments name
// capabilities explicitly, so a missing one is a hard error, not a skipped case).
const core::CapabilitySpec& findCapability(const core::ApplicationModel& app, const std::string& id);
// All capabilities of every given sheet, in sheet order.
std::vector<core::CapabilitySpec> loadCapabilities(const std::vector<fs::path>& sheets);

// Writes a file, creating parent directories. Exits on failure.
void writeFile(const fs::path& file, const std::string& content);

// ---- Metric helpers ----

// Precision@k over a ranked list: relevant items retrieved in the first k positions, over k.
double precisionAtK(const std::vector<int>& relevantRanks, size_t k);
// Recall@k: relevant items retrieved in the first k positions, over the number of relevant
// items.
double recallAtK(const std::vector<int>& relevantRanks, size_t k, size_t relevantTotal);
// Reciprocal rank of the first relevant item; 0 when none is retrieved.
double reciprocalRank(const std::vector<int>& relevantRanks);
// Mean reciprocal rank of a batch of ranked lists (each list is the ranks of its relevant
// items).
double meanReciprocalRank(const std::vector<std::vector<int>>& rankedLists);
// ROC AUC with average ranks for tied scores. Scores may be any real numbers; higher means
// more relevant. Returns 0.0 when one class is empty.
double rocAuc(const std::vector<double>& scores, const std::vector<int>& binaryLabels);

double mean(const std::vector<double>& values);
double minValue(const std::vector<double>& values);
double maxValue(const std::vector<double>& values);

// Fixed decimal formatting for tables and logs.
std::string fmt(double value, int digits = 4);

// Escape a field for CSV output.
std::string csvField(const std::string& value);
// Render a markdown table with the first row as the header.
std::string markdownTable(const std::vector<std::vector<std::string>>& rows);

}  // namespace experiments
}  // namespace careweave
