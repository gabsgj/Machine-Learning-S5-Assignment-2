#pragma once
// Arithmetic expression evaluator used by computation capabilities and the computation
// transport.
//
// Grammar: expressions over + - * / % with unary minus, parentheses, numeric literals,
// variable names, and the functions abs, min, max, round, floor, ceil, sqrt. There are no
// side effects, no assignment and no strings with operators; anything outside the grammar is
// rejected with an error. Variables come from a typed binding map and must be numeric
// (booleans count as 0/1, numeric strings are parsed, anything else is an error).
#include <map>
#include <string>
#include <vector>

#include "careweave/core/types.hpp"

namespace careweave {
namespace adapter {

// Evaluates `expr` over `vars`. On success sets `*out` and returns true. On any lexical,
// syntactic or type error returns false and fills `err` with a precise reason.
bool evaluateExpression(const std::string& expr, const std::map<std::string, core::Value>& vars,
                        double* out, std::string* err);

// True when `expr` parses cleanly against a variable set consisting of the given names
// (all treated as numeric). Used at synthesis time to reject malformed expressions before an
// adapter is stored.
bool checkExpression(const std::string& expr, const std::vector<std::string>& variableNames,
                     std::string* err);

}  // namespace adapter
}  // namespace careweave
