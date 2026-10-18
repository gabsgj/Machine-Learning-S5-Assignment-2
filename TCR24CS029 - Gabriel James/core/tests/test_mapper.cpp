// Mapper tests: typed field vectors, Hungarian assignment optimality, name resolution across
// vocabularies (register_pat against Pat_reg and the main registry), ambiguity and the negative
// case where nothing passes the threshold.
#include <sstream>

#include "careweave/core/types.hpp"
#include "careweave/mapper/mapper.hpp"
#include "careweave/test/framework.hpp"

using careweave::core::CapabilitySpec;
using careweave::core::CapabilityType;
using careweave::core::Condition;
using careweave::core::ConditionOp;
using careweave::core::Effect;
using careweave::core::EffectOp;
using careweave::core::InputSpec;
using careweave::core::OutputSpec;
using careweave::core::Value;
using careweave::mapper::Mapper;
using careweave::mapper::MatchResult;

namespace {

Condition cond(const std::string& var, ConditionOp op, Value v) {
  Condition c;
  c.variable = var;
  c.op = op;
  c.value = std::move(v);
  return c;
}

Effect eff(const std::string& var, EffectOp op, Value v) {
  Effect e;
  e.variable = var;
  e.op = op;
  e.value = std::move(v);
  return e;
}

InputSpec in(const std::string& name, const std::string& type) {
  InputSpec s;
  s.name = name;
  s.type = type;
  return s;
}

OutputSpec out(const std::string& name, const std::string& type) {
  OutputSpec s;
  s.name = name;
  s.type = type;
  return s;
}

// The client requirement, expressed in the alt vocabulary.
CapabilitySpec requirement() {
  CapabilitySpec s;
  s.id = "REQ-1";
  s.name = "register_pat";
  s.description = "Register a new patient in the clinic registry";
  s.type = CapabilityType::API;
  s.inputs = {in("pat_no", "string"), in("pat_name", "string")};
  s.outputs = {out("pat_reg", "string")};
  s.effects = {eff("pat_reg.created", EffectOp::SET, Value(true))};
  return s;
}

// The alt module capability: same vocabulary.
CapabilitySpec patRegAlt() {
  CapabilitySpec s;
  s.id = "PA-Register";
  s.name = "Pat_reg";
  s.description = "Create a patient registration record";
  s.type = CapabilityType::API;
  s.inputs = {in("pat_no", "string"), in("pat_name", "string")};
  s.outputs = {out("pat_reg", "string")};
  s.effects = {eff("pat_reg.created", EffectOp::SET, Value(true))};
  return s;
}

// The main registry capability: different vocabulary.
CapabilitySpec registerPatientMain() {
  CapabilitySpec s;
  s.id = "PR-Register";
  s.name = "RegisterPatient";
  s.description = "Register a patient and assign a medical record number";
  s.type = CapabilityType::API;
  s.inputs = {in("mrn", "string"), in("full_name", "string")};
  s.outputs = {out("patient_id", "string")};
  s.effects = {eff("Patient.registered", EffectOp::SET, Value(true))};
  return s;
}

CapabilitySpec generateInvoice() {
  CapabilitySpec s;
  s.id = "BILL-GenerateInvoice";
  s.name = "GenerateInvoice";
  s.description = "Produce an invoice for a completed visit";
  s.type = CapabilityType::API;
  s.inputs = {in("visit_id", "string")};
  s.outputs = {out("invoice_id", "string")};
  s.effects = {eff("Invoice.exists", EffectOp::SET, Value(true))};
  return s;
}

// The same registration behind a screen: identical contract, different delivery kind.
CapabilitySpec patRegForm() {
  CapabilitySpec s = patRegAlt();
  s.id = "PA-RegisterForm";
  s.type = CapabilityType::GUI;
  return s;
}

}  // namespace

CW_TEST_CASE(hungarian_assignment_is_optimal_not_greedy) {
  // Greedy would take the 0.90 pair first and then settle the 0.10 pair; the optimal total
  // assignment takes 0.85 + 0.85.
  const std::vector<std::vector<double>> sim = {{0.90, 0.85}, {0.85, 0.10}};
  const std::vector<int> assignment = careweave::mapper::hungarianAssignment(sim);
  CW_CHECK(assignment.size() == 2);
  CW_CHECK(assignment[0] == 1);
  CW_CHECK(assignment[1] == 0);
  // Rectangular: two requirement fields against one candidate field, one stays unassigned.
  const std::vector<std::vector<double>> rect = {{0.9}, {0.2}};
  const std::vector<int> rectAssignment = careweave::mapper::hungarianAssignment(rect);
  CW_CHECK(rectAssignment[0] == 0);
  CW_CHECK(rectAssignment[1] == -1);
  // The assignment is deterministic.
  CW_CHECK(careweave::mapper::hungarianAssignment(sim) == assignment);
}

CW_TEST_CASE(register_pat_resolves_to_pat_reg) {
  const Mapper mapper;
  const std::vector<CapabilitySpec> candidates = {registerPatientMain(), patRegAlt(),
                                                  generateInvoice()};
  const std::vector<MatchResult> ranked = mapper.rank(requirement(), candidates);
  CW_CHECK(ranked.size() == 3);
  CW_CHECK(ranked[0].candidateId == "PA-Register");
  CW_CHECK(ranked[1].candidateId == "PR-Register");
  CW_CHECK(ranked[2].candidateId == "BILL-GenerateInvoice");
  // The alt module wins on every view, not just by noise.
  CW_CHECK(ranked[0].fieldSimilarity > ranked[1].fieldSimilarity + 0.1);
  CW_CHECK(ranked[0].conditionSimilarity > ranked[1].conditionSimilarity + 0.1);
  CW_CHECK(ranked[0].total > ranked[1].total + 0.1);

  const Mapper::Selection selection = mapper.select(ranked);
  CW_CHECK(selection.bestIndex == 0);
  CW_CHECK(!selection.belowThreshold);
  CW_CHECK(!selection.ambiguous);
  CW_CHECK(selection.margin > 0.1);

  // Field level explanation: the exact vocabulary binds to itself.
  const MatchResult& best = ranked[0];
  bool sawPatNo = false;
  for (const auto& m : best.inputs) {
    if (m.required == "pat_no") {
      sawPatNo = true;
      CW_CHECK(m.assigned && m.provided == "pat_no");
      CW_CHECK(m.similarity > 0.95);
    }
  }
  CW_CHECK(sawPatNo);
  bool sawPatReg = false;
  for (const auto& m : best.outputs) {
    if (m.required == "pat_reg") {
      sawPatReg = true;
      CW_CHECK(m.assigned && m.provided == "pat_reg");
    }
  }
  CW_CHECK(sawPatReg);
  // The explanation rendering names the pairs.
  const std::string rendered = best.render();
  CW_CHECK(rendered.find("candidate PA-Register (Pat_reg)") != std::string::npos);
  CW_CHECK(rendered.find("input pat_no -> pat_no") != std::string::npos);
}

CW_TEST_CASE(field_vectors_rank_vocabulary_neighbours) {
  const Mapper mapper;
  const CapabilitySpec req = requirement();
  const MatchResult same = mapper.score(req, patRegAlt());
  const MatchResult other = mapper.score(req, registerPatientMain());
  CW_CHECK(same.fieldSimilarity > 0.95);
  CW_CHECK(other.fieldSimilarity < same.fieldSimilarity);
  CW_CHECK(same.total > other.total + 0.1);
  // Even against the main registry, the shared clinical vocabulary keeps the score above zero:
  // patient and registration tokens survive the vocabulary change.
  CW_CHECK(other.nameSimilarity > 0.0);
  CW_CHECK(other.total > 0.0);
}

CW_TEST_CASE(negative_requirement_stays_below_threshold) {
  CapabilitySpec music;
  music.id = "REQ-2";
  music.name = "play_music_track";
  music.description = "Play an audio recording on the waiting room speakers";
  music.inputs = {in("audio_file", "string")};
  music.outputs = {out("playback_session", "string")};
  const std::vector<CapabilitySpec> candidates = {registerPatientMain(), patRegAlt()};
  const Mapper mapper;
  const std::vector<MatchResult> ranked = mapper.rank(music, candidates);
  const Mapper::Selection selection = mapper.select(ranked);
  CW_CHECK(selection.belowThreshold);
  CW_CHECK(selection.bestIndex == -1);
}

CW_TEST_CASE(ambiguous_requirements_are_reported_not_guessed) {
  // Two registries with the same vocabulary: the requirement cannot be resolved by content
  // alone, and the selection reports the near tie as ambiguous.
  CapabilitySpec twin = patRegAlt();
  twin.id = "PA-Register-Copy";
  twin.name = "Pat_reg_copy";
  const std::vector<CapabilitySpec> candidates = {patRegAlt(), twin};
  const Mapper mapper;
  const std::vector<MatchResult> ranked = mapper.rank(requirement(), candidates);
  CW_CHECK(ranked.size() == 2);
  const Mapper::Selection selection = mapper.select(ranked);
  CW_CHECK(selection.bestIndex == 0);
  CW_CHECK(selection.ambiguous);
  CW_CHECK(selection.margin < 0.05);
  // Both twins offer the requested kind, so the kind cannot decide the tie.
  CW_CHECK(!selection.kindTieBreak);
}

CW_TEST_CASE(near_tie_is_resolved_by_the_requested_delivery_kind) {
  // A screen offering the same registration scores exactly as the API capability; the
  // requirement asks for an API delivery, so the delivery kind decides the near tie instead of
  // reporting an ambiguity that a client could not act on.
  const std::vector<CapabilitySpec> candidates = {patRegAlt(), patRegForm()};
  const Mapper mapper;
  const std::vector<MatchResult> ranked = mapper.rank(requirement(), candidates);
  CW_CHECK(ranked.size() == 2);
  const Mapper::Selection selection = mapper.select(ranked);
  CW_CHECK(selection.bestIndex == 0);
  CW_CHECK(selection.kindTieBreak);
  CW_CHECK(!selection.ambiguous);
}

CW_TEST_CASE(weight_sweep_changes_the_combination) {
  const std::vector<CapabilitySpec> candidates = {registerPatientMain(), patRegAlt()};
  careweave::mapper::Weights fieldHeavy;
  fieldHeavy.name = 0.1;
  fieldHeavy.fields = 0.8;
  fieldHeavy.conditions = 0.1;
  const Mapper mapper(fieldHeavy);
  const std::vector<MatchResult> ranked = mapper.rank(requirement(), candidates);
  CW_CHECK(ranked[0].candidateId == "PA-Register");
  // The weights are visible in the result: totals use the instance weights.
  const MatchResult direct = mapper.score(requirement(), patRegAlt());
  CW_CHECK_NEAR(direct.total, 0.1 * direct.nameSimilarity + 0.8 * direct.fieldSimilarity +
                                  0.1 * direct.conditionSimilarity,
                1e-9);
}

int main() { return careweave::testing::runAll("test_mapper"); }
