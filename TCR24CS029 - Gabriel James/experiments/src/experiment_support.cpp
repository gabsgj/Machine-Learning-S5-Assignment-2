#include "experiment_support.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <numeric>
#include <sstream>

#include "careweave/spec/spec_parser.hpp"

namespace careweave {
namespace experiments {

fs::path rootDir() { return fs::path(CAREWEAVE_ROOT); }

fs::path outDir(const std::vector<std::string>& args) {
  fs::path dir = rootDir() / "experiments" / "out";
  for (size_t i = 0; i + 1 < args.size(); ++i) {
    if (args[i] == "--out") dir = args[i + 1];
  }
  std::error_code ec;
  fs::create_directories(dir, ec);
  require(!ec, "cannot create the output directory " + dir.string());
  return dir;
}

std::vector<std::string> positionalArgs(const std::vector<std::string>& args) {
  std::vector<std::string> out;
  for (size_t i = 0; i < args.size(); ++i) {
    if (args[i] == "--out" && i + 1 < args.size()) {
      ++i;
      continue;
    }
    out.push_back(args[i]);
  }
  return out;
}

void require(bool condition, const std::string& message) {
  if (!condition) {
    std::fprintf(stderr, "ASSERTION FAILED: %s\n", message.c_str());
    std::exit(1);
  }
}

core::ApplicationModel loadApplication(const fs::path& file) {
  spec::SpecParseOptions options;
  options.requireSchema = true;
  const spec::SpecParseResult result = spec::loadSpecFile(file.string(), options);
  require(result.ok, "cannot load " + file.string() + ":" + result.renderIssues());
  return result.model;
}

const core::CapabilitySpec& findCapability(const core::ApplicationModel& app,
                                           const std::string& id) {
  for (const auto& capability : app.capabilities) {
    if (capability.id == id) return capability;
  }
  require(false, "capability " + id + " is not part of the loaded application");
  static const core::CapabilitySpec empty;
  return empty;
}

std::vector<core::CapabilitySpec> loadCapabilities(const std::vector<fs::path>& sheets) {
  std::vector<core::CapabilitySpec> out;
  for (const fs::path& sheet : sheets) {
    const core::ApplicationModel app = loadApplication(sheet);
    for (const auto& capability : app.capabilities) out.push_back(capability);
  }
  return out;
}

void writeFile(const fs::path& file, const std::string& content) {
  std::error_code ec;
  if (file.has_parent_path()) fs::create_directories(file.parent_path(), ec);
  std::ofstream stream(file, std::ios::binary);
  require(stream.good(), "cannot write " + file.string());
  stream << content;
  require(stream.good(), "write failed for " + file.string());
}

double precisionAtK(const std::vector<int>& relevantRanks, size_t k) {
  if (k == 0) return 0.0;
  size_t hits = 0;
  for (int rank : relevantRanks) {
    if (rank >= 1 && static_cast<size_t>(rank) <= k) ++hits;
  }
  return static_cast<double>(hits) / static_cast<double>(k);
}

double recallAtK(const std::vector<int>& relevantRanks, size_t k, size_t relevantTotal) {
  if (relevantTotal == 0) return 0.0;
  size_t hits = 0;
  for (int rank : relevantRanks) {
    if (rank >= 1 && static_cast<size_t>(rank) <= k) ++hits;
  }
  return static_cast<double>(hits) / static_cast<double>(relevantTotal);
}

double reciprocalRank(const std::vector<int>& relevantRanks) {
  int best = 0;
  for (int rank : relevantRanks) {
    if (rank >= 1 && (best == 0 || rank < best)) best = rank;
  }
  return best == 0 ? 0.0 : 1.0 / static_cast<double>(best);
}

double meanReciprocalRank(const std::vector<std::vector<int>>& rankedLists) {
  if (rankedLists.empty()) return 0.0;
  double sum = 0.0;
  for (const auto& ranks : rankedLists) sum += reciprocalRank(ranks);
  return sum / static_cast<double>(rankedLists.size());
}

double rocAuc(const std::vector<double>& scores, const std::vector<int>& binaryLabels) {
  require(scores.size() == binaryLabels.size(), "rocAuc: scores and labels must align");
  std::vector<size_t> order(scores.size());
  std::iota(order.begin(), order.end(), 0);
  // Ascending order so rank 1 is the lowest score; the rank sum formula below assumes that.
  std::sort(order.begin(), order.end(),
            [&](size_t a, size_t b) { return scores[a] < scores[b]; });
  // Average ranks over ties: walk runs of equal scores and assign the mean rank.
  std::vector<double> ranks(scores.size(), 0.0);
  size_t i = 0;
  while (i < order.size()) {
    size_t j = i;
    while (j + 1 < order.size() && scores[order[j + 1]] == scores[order[i]]) ++j;
    const double average = (static_cast<double>(i + 1) + static_cast<double>(j + 1)) / 2.0;
    for (size_t k = i; k <= j; ++k) ranks[order[k]] = average;
    i = j + 1;
  }
  double positiveRanks = 0.0;
  double positives = 0.0;
  double negatives = 0.0;
  for (size_t k = 0; k < scores.size(); ++k) {
    if (binaryLabels[k]) {
      positiveRanks += ranks[k];
      positives += 1.0;
    } else {
      negatives += 1.0;
    }
  }
  if (positives == 0.0 || negatives == 0.0) return 0.0;
  return (positiveRanks - positives * (positives + 1.0) / 2.0) / (positives * negatives);
}

double mean(const std::vector<double>& values) {
  if (values.empty()) return 0.0;
  double sum = 0.0;
  for (double value : values) sum += value;
  return sum / static_cast<double>(values.size());
}

double minValue(const std::vector<double>& values) {
  if (values.empty()) return 0.0;
  return *std::min_element(values.begin(), values.end());
}

double maxValue(const std::vector<double>& values) {
  if (values.empty()) return 0.0;
  return *std::max_element(values.begin(), values.end());
}

std::string fmt(double value, int digits) {
  char buffer[64];
  std::snprintf(buffer, sizeof(buffer), "%.*f", digits, value);
  return std::string(buffer);
}

std::string csvField(const std::string& value) {
  bool needsQuotes = value.find_first_of(",\"\n") != std::string::npos;
  if (!needsQuotes) return value;
  std::string out = "\"";
  for (char c : value) {
    if (c == '"') out += "\"\"";
    else out += c;
  }
  out += "\"";
  return out;
}

std::string markdownTable(const std::vector<std::vector<std::string>>& rows) {
  if (rows.empty()) return std::string();
  std::ostringstream out;
  for (size_t r = 0; r < rows.size(); ++r) {
    out << "|";
    for (const std::string& cell : rows[r]) out << " " << cell << " |";
    out << "\n";
    if (r == 0) {
      out << "|";
      for (size_t c = 0; c < rows[r].size(); ++c) out << " --- |";
      out << "\n";
    }
  }
  return out.str();
}

}  // namespace experiments
}  // namespace careweave
