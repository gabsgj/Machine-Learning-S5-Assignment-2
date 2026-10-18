// YAML subset parser tests: block mappings, sequences, compact sequence mappings, flow
// collections, quoted strings, comments, literal scalars and error reporting.
#include "careweave/spec/yaml_lite.hpp"
#include "careweave/test/framework.hpp"

using namespace careweave::spec;
using json = nlohmann::json;

CW_TEST_CASE(block_mapping_and_nesting) {
  const std::string text =
      "module:\n"
      "  module_id: patient-registry\n"
      "  port: 5001\n"
      "  enabled: true\n"
      "  ratio: 0.75\n"
      "  nothing: null\n"
      "counts: [1, 2, 3]\n";
  json doc;
  std::string error;
  CW_CHECK_MSG(parseYaml(text, &doc, &error), error);
  CW_CHECK(doc["module"]["module_id"] == "patient-registry");
  CW_CHECK(doc["module"]["port"] == 5001);
  CW_CHECK(doc["module"]["enabled"] == true);
  CW_CHECK(doc["module"]["ratio"] == 0.75);
  CW_CHECK(doc["module"]["nothing"].is_null());
  CW_CHECK(doc["counts"].size() == 3);
}

CW_TEST_CASE(block_sequence_of_mappings) {
  const std::string text =
      "capabilities:\n"
      "  - id: PR-Register\n"
      "    name: register_patient\n"
      "    type: API\n"
      "  - id: PR-Admit\n"
      "    name: admit_patient\n"
      "    type: API\n";
  json doc;
  std::string error;
  CW_CHECK_MSG(parseYaml(text, &doc, &error), error);
  CW_CHECK(doc["capabilities"].size() == 2);
  CW_CHECK(doc["capabilities"][0]["id"] == "PR-Register");
  CW_CHECK(doc["capabilities"][1]["name"] == "admit_patient");
}

CW_TEST_CASE(sequences_and_flow_objects) {
  const std::string text =
      "resources:\n"
      "  - database\n"
      "  - network\n"
      "windows:\n"
      "  - {days: [mon, tue], from: \"08:00\", to: \"20:00\"}\n"
      "  - days: [sat]\n"
      "    from: \"09:00\"\n"
      "    to: \"13:00\"\n";
  json doc;
  std::string error;
  CW_CHECK_MSG(parseYaml(text, &doc, &error), error);
  CW_CHECK(doc["resources"].size() == 2);
  CW_CHECK(doc["resources"][1] == "network");
  CW_CHECK(doc["windows"].size() == 2);
  CW_CHECK(doc["windows"][0]["from"] == "08:00");
  CW_CHECK(doc["windows"][0]["days"].size() == 2);
  CW_CHECK(doc["windows"][1]["to"] == "13:00");
}

CW_TEST_CASE(comments_and_quoted_strings) {
  const std::string text =
      "# leading comment\n"
      "name: \"patient: registry\"  # trailing comment\n"
      "raw: 'single # not a comment'\n"
      "url: http://127.0.0.1:5001/api/v1/patients\n";
  json doc;
  std::string error;
  CW_CHECK_MSG(parseYaml(text, &doc, &error), error);
  CW_CHECK(doc["name"] == "patient: registry");
  CW_CHECK(doc["raw"] == "single # not a comment");
  CW_CHECK(doc["url"] == "http://127.0.0.1:5001/api/v1/patients");
}

CW_TEST_CASE(literal_block_scalar) {
  const std::string text =
      "expression: |\n"
      "  Stock.quantity >= requested\n"
      "  and Stock.quantity > 0\n"
      "next: value\n";
  json doc;
  std::string error;
  CW_CHECK_MSG(parseYaml(text, &doc, &error), error);
  CW_CHECK(doc["expression"].get<std::string>().find("Stock.quantity >= requested") == 0);
  CW_CHECK(doc["next"] == "value");
}

CW_TEST_CASE(errors_are_reported_with_line_numbers) {
  json doc;
  std::string error;
  CW_CHECK(!parseYaml("key: value\n   bad_indent: 1\n", &doc, &error));
  CW_CHECK(error.find("line 2") != std::string::npos);
  CW_CHECK(!parseYaml("key: value\nkey: other\n", &doc, &error));
  CW_CHECK(error.find("duplicate key") != std::string::npos);
}

CW_TEST_CASE(document_markers_and_empty_document) {
  json doc;
  std::string error;
  CW_CHECK_MSG(parseYaml("---\na: 1\n...\n", &doc, &error), error);
  CW_CHECK(doc["a"] == 1);
  CW_CHECK_MSG(parseYaml("", &doc, &error), error);
  CW_CHECK(doc.is_null());
}

int main() { return careweave::testing::runAll("test_yaml_lite"); }
