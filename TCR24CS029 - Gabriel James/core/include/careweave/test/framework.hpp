#pragma once
// Minimal test framework for the CareWeave Mini C++ suites.
//
// The parent project used plain main() functions with a check(cond, message) helper. This
// header keeps that shape and adds named test cases, a summary line and a non-zero exit code
// on failure, which is what ctest needs. No external dependency.
#include <cmath>
#include <functional>
#include <iostream>
#include <string>
#include <vector>

namespace careweave {
namespace testing {

struct Case {
  std::string name;
  std::function<void()> body;
};

class Registry {
 public:
  static Registry& instance() {
    static Registry r;
    return r;
  }
  void add(const std::string& name, std::function<void()> body) {
    cases_.push_back({name, std::move(body)});
  }
  const std::vector<Case>& cases() const { return cases_; }

 private:
  std::vector<Case> cases_;
};

struct SuiteState {
  int checks = 0;
  int failures = 0;
  int casesRun = 0;
  int casesFailed = 0;
  std::string current;
};

inline SuiteState& state() {
  static SuiteState s;
  return s;
}

inline void reportFailure(const std::string& message, const char* file, int line) {
  ++state().failures;
  std::cout << "  FAIL [" << state().current << "] " << message << " (" << file << ":" << line
            << ")\n";
}

inline bool nearlyEqual(double a, double b, double epsilon) { return std::fabs(a - b) <= epsilon; }

inline int runAll(const std::string& suiteName) {
  SuiteState& s = state();
  std::cout << "=== " << suiteName << " ===\n";
  for (const auto& c : Registry::instance().cases()) {
    s.current = c.name;
    const int failuresBefore = s.failures;
    ++s.casesRun;
    try {
      c.body();
    } catch (const std::exception& e) {
      // An exception thrown by a case is a failure of that case, not a reason to abort the
      // whole suite: the remaining cases still run and the summary stays complete.
      reportFailure(std::string("case threw an exception: ") + e.what(), __FILE__, __LINE__);
    } catch (...) {
      reportFailure("case threw a non standard exception", __FILE__, __LINE__);
    }
    if (s.failures == failuresBefore) {
      std::cout << "PASS " << c.name << "\n";
    } else {
      ++s.casesFailed;
    }
  }
  std::cout << "--- " << suiteName << ": " << s.casesRun << " cases, " << s.checks << " checks, "
            << s.failures << " failures\n";
  return s.failures == 0 ? 0 : 1;
}

}  // namespace testing
}  // namespace careweave

#define CW_TEST_CASE(name)                                                        \
  static void cw_test_##name();                                                   \
  namespace {                                                                     \
  struct cw_registrar_##name {                                                    \
    cw_registrar_##name() {                                                       \
      ::careweave::testing::Registry::instance().add(#name, cw_test_##name);       \
    }                                                                             \
  } cw_registrar_instance_##name;                                                 \
  }                                                                               \
  static void cw_test_##name()

#define CW_CHECK(cond)                                                            \
  do {                                                                            \
    ++::careweave::testing::state().checks;                                       \
    if (!(cond)) {                                                                \
      ::careweave::testing::reportFailure("check failed: " #cond, __FILE__, __LINE__); \
    }                                                                             \
  } while (0)

#define CW_CHECK_MSG(cond, msg)                                                   \
  do {                                                                            \
    ++::careweave::testing::state().checks;                                       \
    if (!(cond)) {                                                                \
      ::careweave::testing::reportFailure(std::string("check failed: ") + (msg), __FILE__, __LINE__); \
    }                                                                             \
  } while (0)

#define CW_CHECK_NEAR(a, b, eps)                                                  \
  do {                                                                            \
    ++::careweave::testing::state().checks;                                       \
    if (!::careweave::testing::nearlyEqual((a), (b), (eps))) {                     \
      std::ostringstream cw_os;                                                   \
      cw_os << "expected " #a " ~= " #b " but got " << (a) << " vs " << (b)        \
            << " (eps " << (eps) << ")";                                          \
      ::careweave::testing::reportFailure(cw_os.str(), __FILE__, __LINE__);       \
    }                                                                             \
  } while (0)
