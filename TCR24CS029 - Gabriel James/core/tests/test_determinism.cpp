// Determinism across the whole pipeline.
//
// Every stage of the system is deterministic by construction: the encoders hash into fixed
// dimensions with no random state, the mapper sorts with stable ties, the compatibility engine
// is symbolic, the synthesizer derives from the match, and the planner orders the frontier with
// a total order. This suite loads the real shipped sheets and runs each stage twice with fresh
// objects, then compares the results exactly: the same bytes, the same order, the same numbers.
#include <string>
#include <vector>

#include <filesystem>

#include "careweave/adapter/adapter.hpp"
#include "careweave/adapter/cpp_emitter.hpp"
#include "careweave/adapter/synthesizer.hpp"
#include "careweave/compat/compat_engine.hpp"
#include "careweave/embedding/encoders.hpp"
#include "careweave/mapper/mapper.hpp"
#include "careweave/planner/planner.hpp"
#include "careweave/spec/spec_parser.hpp"
#include "careweave/test/framework.hpp"

namespace fs = std::filesystem;

namespace {

fs::path miniRoot() { return fs::path(CAREWEAVE_CORE_DIR).parent_path(); }

careweave::spec::SpecParseResult load(const fs::path& path) {
  careweave::spec::SpecParseOptions options;
  options.requireSchema = true;
  return careweave::spec::loadSpecFile(path.string(), options);
}

const careweave::core::CapabilitySpec* findCapability(
    const careweave::core::ApplicationModel& model, const std::string& id) {
  for (const careweave::core::CapabilitySpec& capability : model.capabilities) {
    if (capability.id == id) return &capability;
  }
  return nullptr;
}

}  // namespace

CW_TEST_CASE(capability_and_state_encoding_is_byte_stable_across_runs) {
  const careweave::spec::SpecParseResult app =
      load(miniRoot() / "specs" / "app" / "hospital_clinic_visit.yaml");
  CW_CHECK_MSG(app.ok, app.renderIssues());
  if (!app.ok) return;

  careweave::embedding::Encoder first;
  careweave::embedding::Encoder second;
  CW_CHECK(app.model.capabilities.size() >= 8);
  for (const careweave::core::CapabilitySpec& capability : app.model.capabilities) {
    const careweave::embedding::EncodedCapability a = first.encodeCapabilityDetailed(capability);
    const careweave::embedding::EncodedCapability b = second.encodeCapabilityDetailed(capability);
    CW_CHECK_MSG(a.vector == b.vector, capability.id);
    CW_CHECK(a.blocks == b.blocks);
    CW_CHECK(a.vector.size() == 259);
  }

  const careweave::core::AppState state =
      careweave::core::AppState::fromMap(app.model.initialState);
  careweave::core::Goal goal;
  goal.conditions = app.model.goal;
  CW_CHECK(first.encodeState(state) == second.encodeState(state));
  CW_CHECK(first.encodeGoal(goal) == second.encodeGoal(goal));
}

CW_TEST_CASE(ranking_and_selection_are_stable_across_runs) {
  const careweave::spec::SpecParseResult requirement =
      load(miniRoot() / "specs" / "app" / "requirements" / "register_pat.yaml");
  CW_CHECK_MSG(requirement.ok, requirement.renderIssues());
  const careweave::spec::SpecParseResult poolA =
      load(miniRoot() / "modules" / "patient-registry" / "spec.json");
  CW_CHECK_MSG(poolA.ok, poolA.renderIssues());
  const careweave::spec::SpecParseResult poolB =
      load(miniRoot() / "modules" / "patient-registry-alt" / "spec.json");
  CW_CHECK_MSG(poolB.ok, poolB.renderIssues());
  if (!requirement.ok || !poolA.ok || !poolB.ok) return;

  std::vector<careweave::core::CapabilitySpec> candidates = poolA.model.capabilities;
  candidates.insert(candidates.end(), poolB.model.capabilities.begin(),
                    poolB.model.capabilities.end());

  careweave::mapper::Mapper first;
  careweave::mapper::Mapper second;
  const std::vector<careweave::mapper::MatchResult> rankedFirst =
      first.rank(requirement.model.capabilities.front(), candidates);
  const std::vector<careweave::mapper::MatchResult> rankedSecond =
      second.rank(requirement.model.capabilities.front(), candidates);
  CW_CHECK(rankedFirst.size() == rankedSecond.size());
  if (rankedFirst.size() != rankedSecond.size()) return;
  CW_CHECK(rankedFirst.size() == candidates.size());
  for (size_t i = 0; i < rankedFirst.size(); ++i) {
    CW_CHECK(rankedFirst[i].candidateId == rankedSecond[i].candidateId);
    CW_CHECK(rankedFirst[i].total == rankedSecond[i].total);
  }
  const careweave::mapper::Mapper::Selection selectionFirst = first.select(rankedFirst);
  const careweave::mapper::Mapper::Selection selectionSecond = second.select(rankedSecond);
  CW_CHECK(selectionFirst.bestIndex == selectionSecond.bestIndex);
  CW_CHECK(selectionFirst.ambiguous == selectionSecond.ambiguous);
  CW_CHECK(selectionFirst.margin == selectionSecond.margin);
}

CW_TEST_CASE(compatibility_reports_are_byte_stable_across_runs) {
  const careweave::spec::SpecParseResult app =
      load(miniRoot() / "specs" / "app" / "ecommerce_purchase.yaml");
  CW_CHECK_MSG(app.ok, app.renderIssues());
  if (!app.ok) return;

  careweave::compat::CompatEngine first(app.model);
  careweave::compat::CompatEngine second(app.model);
  size_t checked = 0;
  for (const careweave::core::CapabilitySpec& earlier : app.model.capabilities) {
    for (const careweave::core::CapabilitySpec& later : app.model.capabilities) {
      if (earlier.id == later.id) continue;
      const careweave::compat::CompatibilityReport a = first.check(earlier, later);
      const careweave::compat::CompatibilityReport b = second.check(earlier, later);
      CW_CHECK(a.verdict == b.verdict);
      CW_CHECK(a.toJsonString() == b.toJsonString());
      CW_CHECK(a.rejections == b.rejections);
      ++checked;
    }
  }
  CW_CHECK(checked == 132);
}

CW_TEST_CASE(adapter_synthesis_and_emitted_code_are_byte_stable_across_runs) {
  const careweave::spec::SpecParseResult requirement =
      load(miniRoot() / "specs" / "app" / "requirements" / "register_pat.yaml");
  const careweave::spec::SpecParseResult pool =
      load(miniRoot() / "modules" / "patient-registry-alt" / "spec.json");
  CW_CHECK_MSG(requirement.ok, requirement.renderIssues());
  CW_CHECK_MSG(pool.ok, pool.renderIssues());
  if (!requirement.ok || !pool.ok) return;

  const careweave::core::CapabilitySpec& requirementCapability =
      requirement.model.capabilities.front();
  careweave::mapper::Mapper mapper;
  const std::vector<careweave::mapper::MatchResult> ranked =
      mapper.rank(requirementCapability, pool.model.capabilities);
  CW_CHECK(!ranked.empty());
  if (ranked.empty()) return;

  careweave::adapter::SynthesisRequest request;
  request.requirement = requirementCapability;
  request.match = ranked.front();
  const careweave::core::CapabilitySpec* candidate =
      findCapability(pool.model, ranked.front().candidateId);
  CW_CHECK(candidate != nullptr);
  if (candidate == nullptr) return;
  request.candidate = *candidate;
  request.targetModule = pool.model.moduleId;
  request.baseUrl = pool.model.baseUrl;

  careweave::adapter::AdapterSynthesizer synthesizer;
  const careweave::adapter::SynthesisResult first = synthesizer.synthesize(request);
  const careweave::adapter::SynthesisResult second = synthesizer.synthesize(request);
  CW_CHECK_MSG(first.ok, first.render());
  CW_CHECK(first.ok == second.ok);
  if (!first.ok) return;
  CW_CHECK(careweave::adapter::toJsonString(first.adapter) ==
           careweave::adapter::toJsonString(second.adapter));
  CW_CHECK(careweave::adapter::emitAdapterCpp(first.adapter) ==
           careweave::adapter::emitAdapterCpp(second.adapter));
}

CW_TEST_CASE(planning_is_stable_across_runs) {
  const careweave::spec::SpecParseResult app =
      load(miniRoot() / "specs" / "app" / "hospital_clinic_visit.yaml");
  CW_CHECK_MSG(app.ok, app.renderIssues());
  if (!app.ok) return;

  careweave::planner::PlanOptions options;
  options.maxDepth = 12;
  const careweave::planner::Planner first(app.model);
  const careweave::planner::Planner second(app.model);
  const careweave::planner::PlanResult a = first.planForward(app.model.goal, options);
  const careweave::planner::PlanResult b = second.planForward(app.model.goal, options);
  CW_CHECK_MSG(a.found, a.reason);
  CW_CHECK(a.found == b.found);
  if (!a.found) return;
  CW_CHECK(a.validated && b.validated);
  CW_CHECK(a.steps.size() == b.steps.size());
  if (a.steps.size() != b.steps.size()) return;
  for (size_t i = 0; i < a.steps.size(); ++i) {
    CW_CHECK(a.steps[i].capabilityId == b.steps[i].capabilityId);
    CW_CHECK(a.steps[i].capabilityName == b.steps[i].capabilityName);
    CW_CHECK(a.steps[i].consumedPreconditions == b.steps[i].consumedPreconditions);
    CW_CHECK(a.steps[i].established == b.steps[i].established);
  }
  CW_CHECK(a.totalTimeMs == b.totalTimeMs);
  CW_CHECK(a.totalMoney == b.totalMoney);
  CW_CHECK(a.totalRisk == b.totalRisk);
  CW_CHECK(a.totalReliability == b.totalReliability);
  CW_CHECK(a.expandedStates == b.expandedStates);
  CW_CHECK(a.exploredStates == b.exploredStates);
  CW_CHECK(a.explanation == b.explanation);
}

int main() { return careweave::testing::runAll("test_determinism"); }
