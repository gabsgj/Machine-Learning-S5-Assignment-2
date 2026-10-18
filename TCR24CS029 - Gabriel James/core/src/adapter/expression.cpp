#include "careweave/adapter/expression.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <memory>
#include <set>

namespace careweave {
namespace adapter {

namespace {

struct Node;
using NodePtr = std::unique_ptr<Node>;

struct Node {
  enum class Kind { NUMBER, VARIABLE, NEGATE, ARITHMETIC, CALL };
  Kind kind = Kind::NUMBER;
  double number = 0.0;
  std::string name;       // variable or function name
  char op = '+';          // for Kind::ARITHMETIC
  std::vector<NodePtr> kids;
};

class Parser {
 public:
  Parser(const std::string& text, std::string* err) : text_(text), err_(err) {}

  NodePtr parse() {
    skipSpaces();
    NodePtr root = parseExpression();
    if (!root) return nullptr;
    skipSpaces();
    if (pos_ != text_.size()) {
      fail("unexpected character '" + std::string(1, text_[pos_]) + "' after expression");
      return nullptr;
    }
    return root;
  }

 private:
  void fail(const std::string& message) {
    if (err_ && err_->empty()) *err_ = message;
  }

  void skipSpaces() {
    while (pos_ < text_.size() && std::isspace(static_cast<unsigned char>(text_[pos_])) != 0) {
      ++pos_;
    }
  }

  bool atEnd() const { return pos_ >= text_.size(); }
  char peek() const { return atEnd() ? '\0' : text_[pos_]; }

  NodePtr parseExpression() {
    NodePtr left = parseTerm();
    if (!left) return nullptr;
    while (true) {
      skipSpaces();
      const char c = peek();
      if (c != '+' && c != '-') break;
      ++pos_;
      NodePtr right = parseTerm();
      if (!right) return nullptr;
      auto node = std::make_unique<Node>();
      node->kind = Node::Kind::ARITHMETIC;
      node->op = c;
      node->kids.push_back(std::move(left));
      node->kids.push_back(std::move(right));
      left = std::move(node);
    }
    return left;
  }

  NodePtr parseTerm() {
    NodePtr left = parseFactor();
    if (!left) return nullptr;
    while (true) {
      skipSpaces();
      const char c = peek();
      if (c != '*' && c != '/' && c != '%') break;
      ++pos_;
      NodePtr right = parseFactor();
      if (!right) return nullptr;
      auto node = std::make_unique<Node>();
      node->kind = Node::Kind::ARITHMETIC;
      node->op = c;
      node->kids.push_back(std::move(left));
      node->kids.push_back(std::move(right));
      left = std::move(node);
    }
    return left;
  }

  NodePtr parseFactor() {
    skipSpaces();
    if (peek() == '-') {
      ++pos_;
      NodePtr inner = parseFactor();
      if (!inner) return nullptr;
      auto node = std::make_unique<Node>();
      node->kind = Node::Kind::NEGATE;
      node->kids.push_back(std::move(inner));
      return node;
    }
    if (peek() == '+') {
      ++pos_;
      return parseFactor();
    }
    return parsePrimary();
  }

  NodePtr parsePrimary() {
    skipSpaces();
    const char c = peek();
    if (c == '(') {
      ++pos_;
      NodePtr inner = parseExpression();
      if (!inner) return nullptr;
      skipSpaces();
      if (peek() != ')') {
        fail("missing closing parenthesis");
        return nullptr;
      }
      ++pos_;
      return inner;
    }
    if (std::isdigit(static_cast<unsigned char>(c)) != 0 || c == '.') {
      return parseNumber();
    }
    if (std::isalpha(static_cast<unsigned char>(c)) != 0 || c == '_') {
      return parseIdentifier();
    }
    fail(c == '\0' ? "unexpected end of expression"
                   : "unexpected character '" + std::string(1, c) + "'");
    return nullptr;
  }

  NodePtr parseNumber() {
    const size_t start = pos_;
    bool seenDot = false;
    while (!atEnd()) {
      const char c = peek();
      if (std::isdigit(static_cast<unsigned char>(c)) != 0) {
        ++pos_;
        continue;
      }
      if (c == '.' && !seenDot) {
        seenDot = true;
        ++pos_;
        continue;
      }
      break;
    }
    const std::string token = text_.substr(start, pos_ - start);
    try {
      size_t consumed = 0;
      const double value = std::stod(token, &consumed);
      if (consumed != token.size()) {
        fail("malformed number \"" + token + "\"");
        return nullptr;
      }
      auto node = std::make_unique<Node>();
      node->kind = Node::Kind::NUMBER;
      node->number = value;
      return node;
    } catch (...) {
      fail("malformed number \"" + token + "\"");
      return nullptr;
    }
  }

  NodePtr parseIdentifier() {
    const size_t start = pos_;
    while (!atEnd()) {
      const char c = peek();
      if (std::isalnum(static_cast<unsigned char>(c)) != 0 || c == '_') {
        ++pos_;
      } else {
        break;
      }
    }
    std::string name = text_.substr(start, pos_ - start);
    skipSpaces();
    if (peek() == '(') {
      ++pos_;
      auto node = std::make_unique<Node>();
      node->kind = Node::Kind::CALL;
      node->name = name;
      skipSpaces();
      if (peek() == ')') {
        ++pos_;
        return node;
      }
      while (true) {
        NodePtr arg = parseExpression();
        if (!arg) return nullptr;
        node->kids.push_back(std::move(arg));
        skipSpaces();
        if (peek() == ',') {
          ++pos_;
          continue;
        }
        if (peek() == ')') {
          ++pos_;
          break;
        }
        fail("missing ')' in call to " + name);
        return nullptr;
      }
      return node;
    }
    auto node = std::make_unique<Node>();
    node->kind = Node::Kind::VARIABLE;
    node->name = std::move(name);
    return node;
  }

  const std::string& text_;
  std::string* err_;
  size_t pos_ = 0;
};

const std::set<std::string>& knownFunctions() {
  static const std::set<std::string> fns = {"abs", "min", "max", "round", "floor", "ceil", "sqrt"};
  return fns;
}

bool checkTree(const Node& node, const std::set<std::string>& variables, std::string* err) {
  switch (node.kind) {
    case Node::Kind::NUMBER:
      return true;
    case Node::Kind::VARIABLE:
      if (variables.count(node.name) == 0) {
        if (err) *err = "unknown variable \"" + node.name + "\"";
        return false;
      }
      return true;
    case Node::Kind::NEGATE:
      return checkTree(*node.kids[0], variables, err);
    case Node::Kind::ARITHMETIC:
      return checkTree(*node.kids[0], variables, err) && checkTree(*node.kids[1], variables, err);
    case Node::Kind::CALL: {
      if (knownFunctions().count(node.name) == 0) {
        if (err) *err = "unknown function \"" + node.name + "\"";
        return false;
      }
      const size_t arity = node.name == "min" || node.name == "max" ? 2 : 1;
      if (node.kids.size() != arity) {
        if (err) {
          *err = "function " + node.name + " takes " + std::to_string(arity) + " argument" +
                 (arity == 1 ? "" : "s") + ", got " + std::to_string(node.kids.size());
        }
        return false;
      }
      for (const auto& kid : node.kids) {
        if (!checkTree(*kid, variables, err)) return false;
      }
      return true;
    }
  }
  return false;
}

bool evaluateTree(const Node& node, const std::map<std::string, core::Value>& vars, double* out,
                  std::string* err) {
  switch (node.kind) {
    case Node::Kind::NUMBER:
      *out = node.number;
      return true;
    case Node::Kind::VARIABLE: {
      const auto it = vars.find(node.name);
      if (it == vars.end()) {
        if (err) *err = "missing variable \"" + node.name + "\"";
        return false;
      }
      const core::Value& v = it->second;
      if (v.type() == core::ValueType::BOOL) {
        *out = v.asBool() ? 1.0 : 0.0;
        return true;
      }
      if (v.type() == core::ValueType::INT || v.type() == core::ValueType::REAL) {
        *out = v.asDouble();
        return true;
      }
      if (v.type() == core::ValueType::STRING) {
        try {
          size_t consumed = 0;
          const double parsed = std::stod(v.asString(), &consumed);
          if (consumed != v.asString().size()) {
            if (err) *err = "variable \"" + node.name + "\" is not numeric";
            return false;
          }
          *out = parsed;
          return true;
        } catch (...) {
          if (err) *err = "variable \"" + node.name + "\" is not numeric";
          return false;
        }
      }
      if (err) *err = "variable \"" + node.name + "\" is not numeric";
      return false;
    }
    case Node::Kind::NEGATE: {
      double v = 0.0;
      if (!evaluateTree(*node.kids[0], vars, &v, err)) return false;
      *out = -v;
      return true;
    }
    case Node::Kind::ARITHMETIC: {
      double a = 0.0;
      double b = 0.0;
      if (!evaluateTree(*node.kids[0], vars, &a, err)) return false;
      if (!evaluateTree(*node.kids[1], vars, &b, err)) return false;
      switch (node.op) {
        case '+': *out = a + b; return true;
        case '-': *out = a - b; return true;
        case '*': *out = a * b; return true;
        case '/':
          if (b == 0.0) {
            if (err) *err = "division by zero";
            return false;
          }
          *out = a / b;
          return true;
        case '%':
          if (b == 0.0) {
            if (err) *err = "modulo by zero";
            return false;
          }
          *out = std::fmod(a, b);
          return true;
        default:
          return false;
      }
    }
    case Node::Kind::CALL: {
      std::vector<double> args(node.kids.size());
      for (size_t i = 0; i < node.kids.size(); ++i) {
        if (!evaluateTree(*node.kids[i], vars, &args[i], err)) return false;
      }
      if (node.name == "abs") {
        *out = std::fabs(args[0]);
        return true;
      }
      if (node.name == "min") {
        *out = std::min(args[0], args[1]);
        return true;
      }
      if (node.name == "max") {
        *out = std::max(args[0], args[1]);
        return true;
      }
      if (node.name == "round") {
        *out = std::round(args[0]);
        return true;
      }
      if (node.name == "floor") {
        *out = std::floor(args[0]);
        return true;
      }
      if (node.name == "ceil") {
        *out = std::ceil(args[0]);
        return true;
      }
      if (node.name == "sqrt") {
        if (args[0] < 0.0) {
          if (err) *err = "sqrt of a negative value";
          return false;
        }
        *out = std::sqrt(args[0]);
        return true;
      }
      if (err) *err = "unknown function \"" + node.name + "\"";
      return false;
    }
  }
  return false;
}

}  // namespace

bool evaluateExpression(const std::string& expr, const std::map<std::string, core::Value>& vars,
                        double* out, std::string* err) {
  std::string parseError;
  Parser parser(expr, &parseError);
  NodePtr root = parser.parse();
  if (!root) {
    if (err) *err = parseError.empty() ? "malformed expression" : parseError;
    return false;
  }
  return evaluateTree(*root, vars, out, err);
}

bool checkExpression(const std::string& expr, const std::vector<std::string>& variableNames,
                     std::string* err) {
  std::string parseError;
  Parser parser(expr, &parseError);
  NodePtr root = parser.parse();
  if (!root) {
    if (err) *err = parseError.empty() ? "malformed expression" : parseError;
    return false;
  }
  std::set<std::string> variables(variableNames.begin(), variableNames.end());
  return checkTree(*root, variables, err);
}

}  // namespace adapter
}  // namespace careweave
