#include "careweave/spec/yaml_lite.hpp"

#include <cctype>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <vector>

namespace careweave {
namespace spec {

namespace {

using json = nlohmann::json;

struct Line {
  int indent = 0;
  std::string text;   // content without indentation and without trailing newline
  std::string raw;    // original line
  int number = 0;     // 1-based line number
};

std::string trim(const std::string& s) {
  size_t a = 0, b = s.size();
  while (a < b && std::isspace(static_cast<unsigned char>(s[a]))) ++a;
  while (b > a && std::isspace(static_cast<unsigned char>(s[b - 1]))) --b;
  return s.substr(a, b - a);
}

// Strip a trailing comment that is not inside quotes.
std::string stripComment(const std::string& s) {
  bool inSingle = false, inDouble = false;
  for (size_t i = 0; i < s.size(); ++i) {
    const char c = s[i];
    if (c == '\'' && !inDouble) inSingle = !inSingle;
    else if (c == '"' && !inSingle) {
      if (inDouble && i > 0 && s[i - 1] == '\\') continue;
      inDouble = !inDouble;
    } else if (c == '#' && !inSingle && !inDouble) {
      if (i == 0 || std::isspace(static_cast<unsigned char>(s[i - 1]))) {
        return s.substr(0, i);
      }
    }
  }
  return s;
}

std::string unescapeDouble(const std::string& body) {
  std::string out;
  out.reserve(body.size());
  for (size_t i = 0; i < body.size(); ++i) {
    if (body[i] == '\\' && i + 1 < body.size()) {
      const char n = body[++i];
      switch (n) {
        case 'n': out += '\n'; break;
        case 't': out += '\t'; break;
        case 'r': out += '\r'; break;
        case '"': out += '"'; break;
        case '\\': out += '\\'; break;
        case '/': out += '/'; break;
        default: out += n; break;
      }
    } else {
      out += body[i];
    }
  }
  return out;
}

// Parse a scalar token into a JSON value.
json parseScalar(const std::string& token) {
  const std::string t = trim(token);
  if (t.empty()) return json(nullptr);
  if (t == "null" || t == "~" || t == "Null" || t == "NULL") return json(nullptr);
  if (t == "true" || t == "True" || t == "TRUE") return json(true);
  if (t == "false" || t == "False" || t == "FALSE") return json(false);
  if (t.size() >= 2 && t.front() == '"' && t.back() == '"') {
    return json(unescapeDouble(t.substr(1, t.size() - 2)));
  }
  if (t.size() >= 2 && t.front() == '\'' && t.back() == '\'') {
    return json(t.substr(1, t.size() - 2));
  }
  // Numbers: strict, so that version strings such as 1.0.0 stay strings.
  {
    char* end = nullptr;
    const long long asInt = std::strtoll(t.c_str(), &end, 10);
    if (end && *end == '\0' && !t.empty()) return json(static_cast<int64_t>(asInt));
  }
  {
    char* end = nullptr;
    const double asDouble = std::strtod(t.c_str(), &end);
    if (end && *end == '\0' && !t.empty() &&
        (t.find('.') != std::string::npos || t.find('e') != std::string::npos ||
         t.find('E') != std::string::npos)) {
      return json(asDouble);
    }
  }
  return json(t);
}

class Parser {
 public:
  Parser(std::vector<Line> lines, std::string* err) : lines_(std::move(lines)), err_(err) {}

  bool parse(json* out) {
    skipIgnorable();
    if (pos_ >= lines_.size()) {
      *out = json(nullptr);
      return true;
    }
    const int baseIndent = lines_[pos_].indent;
    // A top level "- ..." starts a sequence, everything else starts a mapping.
    if (isSeqEntry(lines_[pos_].text)) {
      return parseSequenceBody(baseIndent, out);
    }
    return parseMappingBody(baseIndent, out);
  }

  // Blank lines and comment-only lines carry no structure.
  static bool isIgnorable(const std::string& text) {
    const std::string t = trim(text);
    return t.empty() || t[0] == '#' || t == "---" || t == "...";
  }

 private:
  std::vector<Line> lines_;
  size_t pos_ = 0;
  std::string* err_ = nullptr;

  bool fail(int line, const std::string& reason) {
    if (err_) {
      std::ostringstream os;
      os << "line " << line << ": " << reason;
      *err_ = os.str();
    }
    return false;
  }

  void skipIgnorable() {
    while (pos_ < lines_.size()) {
      const std::string t = trim(lines_[pos_].text);
      if (t.empty() || t == "---" || t == "..." || t[0] == '#') {
        ++pos_;
        continue;
      }
      break;
    }
  }

  static bool isSeqEntry(const std::string& text) {
    return text.size() >= 1 && text[0] == '-' &&
           (text.size() == 1 || text[1] == ' ' || text[1] == '\t');
  }

  // Find the byte offset of the ": " or trailing ":" that separates a mapping key from its
  // value, skipping quoted regions and flow collections.
  static size_t findKeySeparator(const std::string& text, bool* found) {
    bool inSingle = false, inDouble = false;
    int depth = 0;
    for (size_t i = 0; i < text.size(); ++i) {
      const char c = text[i];
      if (c == '\'' && !inDouble) inSingle = !inSingle;
      else if (c == '"' && !inSingle) inDouble = !inDouble;
      else if (!inSingle && !inDouble) {
        if (c == '[' || c == '{') ++depth;
        else if (c == ']' || c == '}') --depth;
        else if (c == ':' && depth == 0) {
          if (i + 1 == text.size() || text[i + 1] == ' ' || text[i + 1] == '\t') {
            *found = true;
            return i;
          }
        }
      }
    }
    *found = false;
    return 0;
  }

  bool parseFlow(const std::string& text, json* out) {
    // Minimal recursive descent over flow collections, reusing parseScalar for leaves.
    size_t i = 0;
    struct FlowParser {
      const std::string& s;
      size_t& i;
      bool ok = true;
      std::string message;
      FlowParser(const std::string& str, size_t& index) : s(str), i(index) {}
      json parseValue() {
        skipWs();
        if (i >= s.size()) {
          ok = false;
          message = "unexpected end of flow collection";
          return json();
        }
        if (s[i] == '[') return parseSeq();
        if (s[i] == '{') return parseMap();
        return parseLeaf();
      }
      void skipWs() {
        while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) ++i;
      }
      json parseLeaf() {
        std::string token;
        bool inSingle = false, inDouble = false;
        while (i < s.size()) {
          const char c = s[i];
          if (c == ',' || c == ']' || c == '}') {
            if (!inSingle && !inDouble) break;
          }
          if (c == '\'' && !inDouble) inSingle = !inSingle;
          if (c == '"' && !inSingle) inDouble = !inDouble;
          token += c;
          ++i;
        }
        return parseScalar(token);
      }
      json parseSeq() {
        ++i;  // consume '['
        json arr = json::array();
        skipWs();
        if (i < s.size() && s[i] == ']') {
          ++i;
          return arr;
        }
        while (i < s.size()) {
          json v = parseValue();
          if (!ok) return arr;
          arr.push_back(v);
          skipWs();
          if (i < s.size() && s[i] == ',') {
            ++i;
            continue;
          }
          if (i < s.size() && s[i] == ']') {
            ++i;
            return arr;
          }
          ok = false;
          message = "expected ',' or ']' in flow sequence";
          return arr;
        }
        ok = false;
        message = "unterminated flow sequence";
        return arr;
      }
      json parseMap() {
        ++i;  // consume '{'
        json obj = json::object();
        skipWs();
        if (i < s.size() && s[i] == '}') {
          ++i;
          return obj;
        }
        while (i < s.size()) {
          skipWs();
          std::string key;
          bool inSingle = false, inDouble = false;
          while (i < s.size()) {
            const char c = s[i];
            if (c == ':' && !inSingle && !inDouble) break;
            if (c == '\'' && !inDouble) inSingle = !inSingle;
            if (c == '"' && !inSingle) inDouble = !inDouble;
            key += c;
            ++i;
          }
          skipWs();
          if (i >= s.size() || s[i] != ':') {
            ok = false;
            message = "expected ':' in flow mapping";
            return obj;
          }
          ++i;
          json v = parseValue();
          if (!ok) return obj;
          obj[trim(key)] = v;
          skipWs();
          if (i < s.size() && s[i] == ',') {
            ++i;
            continue;
          }
          if (i < s.size() && s[i] == '}') {
            ++i;
            return obj;
          }
          ok = false;
          message = "expected ',' or '}' in flow mapping";
          return obj;
        }
        ok = false;
        message = "unterminated flow mapping";
        return obj;
      }
    };
    FlowParser fp(text, i);
    json v = fp.parseValue();
    if (!fp.ok) return fail(0, fp.message);
    fp.skipWs();
    if (i != text.size()) return fail(0, "trailing characters after flow collection");
    *out = v;
    return true;
  }

  // Parse the value that follows "key:" or "-" on the same line, possibly continuing on
  // following lines (nested block or literal scalar).
  // Consume the current line when the value is inline, or the current line plus the nested
  // block when the value is empty (the block belongs to the parent line).
  bool parseValueAfterSeparator(const std::string& rest, int lineNumber, json* out) {
    const std::string t = trim(rest);
    if (t.empty()) {
      ++pos_;  // consume the parent line
      return parseDeeperBlock(lines_[pos_ - 1].indent, out);
    }
    if (t == "|" || t == "|-" || t == ">" || t == ">-") {
      const int parentIndent = lines_[pos_].indent;
      ++pos_;  // consume the parent line
      return parseBlockScalar(t[0] == '|', parentIndent, out);
    }
    if (t[0] == '[' || t[0] == '{') {
      json flowValue;
      if (!parseFlow(t, &flowValue)) {
        std::string msg = err_ ? *err_ : std::string("invalid flow collection");
        return fail(lineNumber, msg);
      }
      *out = flowValue;
      ++pos_;
      return true;
    }
    *out = parseScalar(t);
    ++pos_;
    return true;
  }

  bool parseBlockScalar(bool literal, int parentIndent, json* out) {
    // The content indentation is taken from the first non-empty line of the block, which is
    // what the YAML specification requires for block scalars.
    int contentIndent = -1;
    std::string joined;
    bool first = true;
    while (pos_ < lines_.size()) {
      const Line& l = lines_[pos_];
      if (trim(l.text).empty()) {
        joined += literal ? "\n" : " ";
        ++pos_;
        continue;
      }
      if (l.indent <= parentIndent) break;
      if (contentIndent < 0) contentIndent = l.indent;
      std::string body = l.raw;
      if (static_cast<int>(body.size()) > contentIndent) {
        body = body.substr(static_cast<size_t>(contentIndent));
      } else {
        body = std::string();
      }
      if (!first) joined += literal ? "\n" : " ";
      first = false;
      joined += body;
      ++pos_;
    }
    *out = json(joined);
    return true;
  }

  // A nested block must be indented deeper than `parentIndent`. Comments and blank lines are
  // skipped. Returns a null value when nothing deeper follows.
  bool parseDeeperBlock(int parentIndent, json* out) {
    size_t probe = pos_;
    while (probe < lines_.size() && isIgnorable(lines_[probe].text)) ++probe;
    if (probe >= lines_.size() || lines_[probe].indent <= parentIndent) {
      *out = json(nullptr);
      return true;
    }
    pos_ = probe;
    const int childIndent = lines_[probe].indent;
    if (isSeqEntry(lines_[probe].text)) {
      return parseSequenceBody(childIndent, out);
    }
    return parseMappingBody(childIndent, out);
  }

  bool parseMappingBody(int indent, json* out) {
    json obj = json::object();
    while (pos_ < lines_.size()) {
      if (isIgnorable(lines_[pos_].text)) {
        ++pos_;
        continue;
      }
      if (lines_[pos_].indent < indent) break;
      if (lines_[pos_].indent > indent) {
        return fail(lines_[pos_].number, "unexpected extra indentation in mapping");
      }
      if (isSeqEntry(lines_[pos_].text)) break;
      const Line& l = lines_[pos_];
      bool found = false;
      const size_t sep = findKeySeparator(l.text, &found);
      if (!found) {
        return fail(l.number, "expected 'key: value'");
      }
      std::string key = trim(l.text.substr(0, sep));
      if (key.size() >= 2 && ((key.front() == '"' && key.back() == '"') ||
                              (key.front() == '\'' && key.back() == '\''))) {
        key = key.substr(1, key.size() - 2);
      }
      json value;
      if (!parseValueAfterSeparator(stripComment(l.text.substr(sep + 1)), l.number, &value)) {
        return false;
      }
      if (obj.contains(key)) {
        return fail(l.number, "duplicate key '" + key + "'");
      }
      obj[key] = value;
    }
    *out = obj;
    return true;
  }

  bool parseSequenceBody(int indent, json* out) {
    json arr = json::array();
    while (pos_ < lines_.size()) {
      if (isIgnorable(lines_[pos_].text)) {
        ++pos_;
        continue;
      }
      if (lines_[pos_].indent < indent) break;
      if (lines_[pos_].indent > indent) {
        return fail(lines_[pos_].number, "unexpected extra indentation in sequence");
      }
      if (!isSeqEntry(lines_[pos_].text)) break;
      const Line& dashLine = lines_[pos_];
      const std::string rest = dashLine.text.size() > 1 ? dashLine.text.substr(1) : std::string();
      const std::string restTrim = trim(stripComment(rest));
      if (restTrim.empty()) {
        ++pos_;  // consume the dash line
        json value;
        if (!parseDeeperBlock(indent, &value)) return false;
        arr.push_back(value);
        continue;
      }
      bool found = false;
      const size_t sep = findKeySeparator(restTrim, &found);
      if (found) {
        // Compact mapping entry: "- key: value" with optional sibling keys at indent + 2.
        json item = json::object();
        const std::string firstKey = trim(restTrim.substr(0, sep));
        json firstValue;
        if (!parseValueAfterSeparator(stripComment(restTrim.substr(sep + 1)), dashLine.number,
                                      &firstValue)) {
          return false;
        }
        item[firstKey] = firstValue;
        const int siblingIndent = indent + 2;
        while (pos_ < lines_.size()) {
          size_t probe = pos_;
          while (probe < lines_.size() && isIgnorable(lines_[probe].text)) ++probe;
          if (probe >= lines_.size()) break;
          if (lines_[probe].indent != siblingIndent) break;
          if (isSeqEntry(lines_[probe].text)) break;
          pos_ = probe;
          const Line& sl = lines_[pos_];
          bool f2 = false;
          const size_t s2 = findKeySeparator(sl.text, &f2);
          if (!f2) break;
          const std::string k2 = trim(sl.text.substr(0, s2));
          json v2;
          if (!parseValueAfterSeparator(stripComment(sl.text.substr(s2 + 1)), sl.number, &v2)) {
            return false;
          }
          if (item.contains(k2)) return fail(sl.number, "duplicate key '" + k2 + "'");
          item[k2] = v2;
        }
        arr.push_back(item);
        continue;
      }
      json value;
      if (!parseValueAfterSeparator(restTrim, dashLine.number, &value)) return false;
      arr.push_back(value);
    }
    *out = arr;
    return true;
  }
};

}  // namespace

bool parseYaml(const std::string& text, nlohmann::json* out, std::string* error) {
  std::vector<Line> lines;
  std::istringstream is(text);
  std::string raw;
  int number = 0;
  while (std::getline(is, raw)) {
    ++number;
    if (!raw.empty() && raw.back() == '\r') raw.pop_back();
    Line l;
    l.raw = raw;
    l.number = number;
    size_t i = 0;
    while (i < raw.size() && raw[i] == ' ') ++i;
    if (i < raw.size() && raw[i] == '\t') {
      if (error) *error = "line " + std::to_string(number) + ": tab indentation is not supported";
      return false;
    }
    l.indent = static_cast<int>(i);
    l.text = raw.substr(i);
    lines.push_back(l);
  }
  Parser p(std::move(lines), error);
  return p.parse(out);
}

bool parseYamlFile(const std::string& path, nlohmann::json* out, std::string* error) {
  std::ifstream in(path, std::ios::binary);
  if (!in) {
    if (error) *error = "cannot open file: " + path;
    return false;
  }
  std::ostringstream buf;
  buf << in.rdbuf();
  const std::string text = buf.str();
  if (!parseYaml(text, out, error)) {
    if (error) *error = path + ":" + (*error);
    return false;
  }
  return true;
}

}  // namespace spec
}  // namespace careweave
