#include "careweave/embedding/text.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <numeric>
#include <set>
#include <sstream>

namespace careweave {
namespace embedding {

namespace {

uint64_t fnv1a(const std::string& s) {
  uint64_t h = 1469598103934665603ULL;
  for (char ch : s) {
    const uint64_t c = static_cast<uint64_t>(static_cast<unsigned char>(ch));
    h ^= c;
    h *= 1099511628211ULL;
  }
  return h;
}

// Concept table. Each line lists a canonical concept followed by the terms that map to it with
// full weight. The table is deliberately small and curated: it covers the hospital, commerce
// and document domains used by the dataset plus the vocabulary of HTTP APIs. Adding a term is a
// one-line change, documented in documents/10_DEVELOPER_GUIDE.md.
struct ConceptEntry {
  const char* concept;
  const char* terms;
};

const ConceptEntry kConcepts[] = {
    {"patient", "patient pat pt client customer person individual subject mrn member beneficiary"},
    {"register", "register reg enroll enrol signup onboarding intake new_form"},
    {"admit", "admit admission hospitalize inpatient ward bed occupy"},
    {"discharge", "discharge release dismiss leave summary_discharge"},
    {"queue", "queue line waiting wait token ticket slot turn enqueue resequence"},
    {"triage", "triage priority urgency severity acuity urgent emergency escalate"},
    {"encounter", "encounter visit consultation consult appointment session episode meet"},
    {"vitals", "vitals vital temperature temp pulse heart heart_rate blood pressure bp spo2 respiration"},
    {"prescription", "prescription prescribe rx medication medicine drug dosage dose"},
    {"stock", "stock inventory quantity qty supply batch expiry replenish restock"},
    {"dispense", "dispense issue allocate give deliver handover"},
    {"invoice", "invoice bill billing statement charge fee receipt cost amount total"},
    {"payment", "pay payment settle checkout transaction tender refund capture"},
    {"lab", "lab laboratory pathology investigation specimen sample result report"},
    {"notify", "notify notification notice alert inform message email sms"},
    {"order", "order purchase sales_order demand"},
    {"cart", "cart basket bag trolley"},
    {"item", "item product sku goods article line_item"},
    {"shipment", "ship shipment shipping dispatch fulfillment fulfil delivery"},
    {"auth", "auth authenticate login signin credential permission role token"},
    {"user", "user account profile actor staff employee operator admin doctor nurse clinician technician"},
    {"document", "document doc file pdf upload attachment"},
    {"parse", "parse extract analyse analyze ocr parse_text"},
    {"index", "index catalog vectorize embed_index search_index"},
    {"summary", "summary summarize summarise abstract brief digest"},
    {"archive", "archive persist_file store_file"},
    {"compute", "compute calculate aggregate eval score rank statistics metric"},
    {"event", "event trigger hook listener callback fired"},
    {"message", "msg topic channel broker kafka mq publish subscribe"},
    {"service", "service api endpoint http rest rpc url gateway port"},
    {"database", "database db table row record sql sqlite postgres columns"},
    {"gui", "ui gui form button click page screen view widget component"},
    {"retrieve", "get fetch read retrieve find search query lookup list all show"},
    {"create", "create add insert make new submit post append push"},
    {"update", "update modify change patch edit set"},
    {"delete", "delete remove cancel drop discard purge"},
    {"verify", "verify check validate confirm assurance consistent"},
    {"start", "start begin open activate initiate launch"},
    {"close", "close finish complete end finalize finalise"},
    {"process", "process handle execute run perform"},
    {"send", "send dispatch_send transmit forward"},
    {"id", "id ref reference number no identifier key handle code"},
    {"date_of_birth", "dob birth birthdate"},
    {"address", "addr address location residence"},
    {"amount", "amount total price sum value"},
    {"status", "status state condition phase stage"},
    {"count", "count number_of total_of cardinality"},
};

// Lower weight links: terms that are related to a concept without being canonical members.
// They let the encoder see that admissibility and registration live in the same neighbourhood
// without claiming they are the same operation.
struct RelatedEntry {
  const char* term;
  const char* concept;
  double weight;
};

const RelatedEntry kRelated[] = {
    {"admit", "register", 0.45},   {"register", "admit", 0.45},
    {"encounter", "queue", 0.35},  {"queue", "encounter", 0.35},
    {"prescription", "dispense", 0.4}, {"dispense", "prescription", 0.4},
    {"invoice", "payment", 0.45},  {"payment", "invoice", 0.45},
    {"order", "cart", 0.4},        {"cart", "order", 0.4},
    {"cart", "item", 0.35},        {"item", "cart", 0.35},
    {"lab", "notify", 0.3},        {"notify", "lab", 0.3},
    {"patient", "user", 0.3},      {"user", "patient", 0.3},
    {"stock", "dispense", 0.4},    {"dispense", "stock", 0.4},
    {"document", "parse", 0.4},    {"parse", "document", 0.4},
    {"index", "document", 0.35},   {"document", "index", 0.35},
    {"summary", "compute", 0.35},  {"compute", "summary", 0.35},
    {"message", "notify", 0.4},    {"notify", "message", 0.4},
    {"shipment", "order", 0.4},    {"order", "shipment", 0.4},
    {"verify", "patient", 0.25},   {"close", "encounter", 0.3},
    {"triage", "queue", 0.4},      {"queue", "triage", 0.4},
};

const char* kStopwords[] = {"the", "a",   "an",   "of",  "to",  "for", "and", "or",
                            "is",  "are", "was",  "be",  "by",  "on",  "in",  "with",
                            "that", "this", "it", "as",  "at",  "from", "into"};

const char* kCommonApiVerbs[] = {"create", "add", "get", "list",   "update",
                                 "delete", "find", "search", "read", "post",
                                 "put",    "set",  "show", "fetch"};

const char* kHighIdf[] = {"mrn",  "dob",     "spo2",     "triage", "acuity", "tender",
                          "fulfil", "sqlite", "kafka",  "dosage", "batch",  "specimen",
                          "invoice", "dispense", "ward", "replenish"};

bool contains(const char* const* arr, size_t n, const std::string& value) {
  for (size_t i = 0; i < n; ++i) {
    if (value == arr[i]) return true;
  }
  return false;
}

}  // namespace

const Lexicon& Lexicon::instance() {
  static Lexicon lex;
  return lex;
}

Lexicon::Lexicon() {
  int next = 0;
  for (const auto& entry : kConcepts) {
    concepts_[entry.concept] = next++;
    std::istringstream is(entry.terms);
    std::string term;
    while (is >> term) {
      termIndex_[term].push_back({entry.concept, 1.0});
    }
  }
  for (const auto& entry : kRelated) {
    if (concepts_.count(entry.concept) == 0) concepts_[entry.concept] = next++;
    auto& list = termIndex_[entry.term];
    bool already = false;
    for (const auto& m : list) {
      if (m.concept == entry.concept) {
        already = true;
        break;
      }
    }
    if (!already) list.push_back({entry.concept, entry.weight});
  }
}

const std::vector<ConceptMatch>& Lexicon::conceptsFor(const std::string& token) const {
  static const std::vector<ConceptMatch> empty;
  auto it = termIndex_.find(token);
  return it == termIndex_.end() ? empty : it->second;
}

double Lexicon::conceptWeight(const std::string& token, const std::string& concept) const {
  const auto& list = conceptsFor(token);
  for (const auto& m : list) {
    if (m.concept == concept) return m.weight;
  }
  return 0.0;
}

double Lexicon::idf(const std::string& token) const {
  if (contains(kStopwords, sizeof(kStopwords) / sizeof(kStopwords[0]), token)) return 0.15;
  if (contains(kHighIdf, sizeof(kHighIdf) / sizeof(kHighIdf[0]), token)) return 1.4;
  // Very common API verbs discriminate less than domain words.
  if (contains(kCommonApiVerbs, sizeof(kCommonApiVerbs) / sizeof(kCommonApiVerbs[0]), token)) {
    return 0.6;
  }
  return 1.0;
}

std::vector<std::string> TextFeatures::tokenize(const std::string& text) {
  std::vector<std::string> tokens;
  std::string current;
  const auto flush = [&]() {
    if (!current.empty()) {
      tokens.push_back(current);
      current.clear();
    }
  };
  for (size_t i = 0; i < text.size(); ++i) {
    const char c = text[i];
    const bool alnum = std::isalnum(static_cast<unsigned char>(c)) != 0;
    if (!alnum) {
      flush();
      continue;
    }
    if (!current.empty()) {
      const char prev = current.back();
      const bool prevLower = std::islower(static_cast<unsigned char>(prev)) != 0;
      const bool prevUpper = std::isupper(static_cast<unsigned char>(prev)) != 0;
      const bool curUpper = std::isupper(static_cast<unsigned char>(c)) != 0;
      const bool prevDigit = std::isdigit(static_cast<unsigned char>(prev)) != 0;
      const bool curDigit = std::isdigit(static_cast<unsigned char>(c)) != 0;
      // camelCase or PascalCase boundary
      if (curUpper && (prevLower || prevDigit)) {
        flush();
      } else if (curUpper && prevUpper && i + 1 < text.size() &&
                 std::islower(static_cast<unsigned char>(text[i + 1])) != 0) {
        // HTTPServer -> HTTP, Server
        flush();
      } else if (curDigit != prevDigit) {
        // keep letter/digit groups separate: pat2 -> pat, 2
        flush();
      }
    }
    current += static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
  }
  flush();
  std::vector<std::string> filtered;
  for (auto& t : tokens) {
    if (t.size() < 2) continue;
    if (std::all_of(t.begin(), t.end(),
                    [](char c) { return std::isdigit(static_cast<unsigned char>(c)) != 0; })) {
      continue;
    }
    filtered.push_back(t);
  }
  return filtered;
}

std::vector<Feature> TextFeatures::featuresForToken(const std::string& token) {
  std::vector<Feature> features;
  const Lexicon& lex = Lexicon::instance();
  const double idf = lex.idf(token);
  // The token itself, at reduced weight, so exact spellings still matter.
  features.push_back({"t:" + token, 0.6 * idf});
  // Light plural stemming: patients -> patient.
  if (token.size() > 4 && token.back() == 's' && lex.conceptsFor(token).empty()) {
    const std::string stem = token.substr(0, token.size() - 1);
    features.push_back({"t:" + stem, 0.4 * idf});
    for (const auto& m : lex.conceptsFor(stem)) {
      features.push_back({"c:" + m.concept, 0.8 * m.weight * idf});
    }
  }
  for (const auto& m : lex.conceptsFor(token)) {
    features.push_back({"c:" + m.concept, m.weight * idf});
  }
  // Character trigrams, weight capped so morphology cannot dominate the concept signal.
  if (token.size() >= 3) {
    const size_t grams = token.size() - 2;
    const double w = 0.18 / std::sqrt(static_cast<double>(grams));
    for (size_t i = 0; i + 3 <= token.size(); ++i) {
      features.push_back({"g:" + token.substr(i, 3), w});
    }
  }
  return features;
}

std::vector<Feature> TextFeatures::featuresForText(const std::string& text) {
  const std::vector<std::string> tokens = tokenize(text);
  std::map<std::string, double> counts;
  std::map<std::string, double> weights;
  for (const auto& token : tokens) {
    counts[token] += 1.0;
  }
  for (const auto& token : tokens) {
    // Term frequency with the usual sub-linear damping.
    const double tf = 1.0 + std::log(counts[token]);
    for (const auto& f : featuresForToken(token)) {
      weights[f.id] += f.weight * tf;
    }
  }
  std::vector<Feature> out;
  out.reserve(weights.size());
  for (const auto& kv : weights) {
    out.push_back({kv.first, std::min(kv.second, 4.0)});
  }
  return out;
}

std::vector<std::string> TextFeatures::explain(const std::string& text) {
  const std::vector<Feature> features = featuresForText(text);
  std::vector<std::string> lines;
  for (const auto& f : features) {
    std::ostringstream os;
    os << f.id << "=" << f.weight;
    lines.push_back(os.str());
  }
  return lines;
}

Vector TextFeatures::project(const std::vector<Feature>& features, size_t dims, uint64_t seed) {
  Vector v(dims, 0.0);
  if (dims == 0) return v;
  // Each feature spreads over kSlots slots with independent signs (a signed count sketch). A
  // feature present in both texts adds coherently to the dot product (the 1/sqrt(slots) scale
  // cancels against slots identical contributions), while collisions between different features
  // carry independent signs and average out, so short strings such as field names do not pick up
  // spurious cosine from single slot collisions in a small space.
  constexpr size_t kSlots = 4;
  const double spread = 1.0 / std::sqrt(static_cast<double>(kSlots));
  for (const auto& f : features) {
    for (size_t k = 0; k < kSlots; ++k) {
      std::ostringstream key1;
      key1 << seed << ":" << k << ":" << f.id;
      const uint64_t h = fnv1a(key1.str());
      const size_t slot = static_cast<size_t>(h % static_cast<uint64_t>(dims));
      std::ostringstream key2;
      key2 << seed << "|sign|" << k << "|" << f.id;
      const double sign = (fnv1a(key2.str()) % 2ULL) == 0ULL ? 1.0 : -1.0;
      v[slot] += f.weight * spread * sign;
    }
  }
  return VectorMath::normalize(v);
}

Vector TextFeatures::encodeText(const std::string& text, size_t dims, uint64_t seed) {
  return project(featuresForText(text), dims, seed);
}

double TextFeatures::sparseCosine(const std::string& textA, const std::string& textB) {
  const std::vector<Feature> a = featuresForText(textA);
  const std::vector<Feature> b = featuresForText(textB);
  std::map<std::string, double> bWeights;
  for (const auto& f : b) bWeights[f.id] += f.weight;
  double dot = 0.0, normASquared = 0.0, normBSquared = 0.0;
  for (const auto& f : a) {
    normASquared += f.weight * f.weight;
    auto it = bWeights.find(f.id);
    if (it != bWeights.end()) dot += f.weight * it->second;
  }
  for (const auto& kv : bWeights) normBSquared += kv.second * kv.second;
  if (normASquared <= 0.0 || normBSquared <= 0.0) return 0.0;
  return dot / std::sqrt(normASquared * normBSquared);
}

}  // namespace embedding
}  // namespace careweave
