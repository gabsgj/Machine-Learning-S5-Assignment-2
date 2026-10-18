#include <algorithm>
#include <cstring>

#include "careweave/adapter/transport.hpp"
#include "sqlite3.h"

namespace careweave {
namespace adapter {

namespace {

std::string quoteIdentifier(const std::string& name) {
  std::string out = "\"";
  for (char c : name) {
    if (c == '"') out += '"';
    out += c;
  }
  out += '"';
  return out;
}

void bindValue(sqlite3_stmt* stmt, int index, const core::Value& v) {
  switch (v.type()) {
    case core::ValueType::BOOL:
      sqlite3_bind_int(stmt, index, v.asBool() ? 1 : 0);
      break;
    case core::ValueType::INT:
      sqlite3_bind_int64(stmt, index, v.asInt());
      break;
    case core::ValueType::REAL:
      sqlite3_bind_double(stmt, index, v.asDouble());
      break;
    case core::ValueType::STRING:
      sqlite3_bind_text(stmt, index, v.asString().c_str(), -1, SQLITE_TRANSIENT);
      break;
    case core::ValueType::ENUM:
      sqlite3_bind_text(stmt, index, v.asString().c_str(), -1, SQLITE_TRANSIENT);
      break;
    case core::ValueType::LIST: {
      std::string joined;
      for (size_t i = 0; i < v.asList().size(); ++i) {
        if (i != 0) joined += ", ";
        joined += v.asList()[i];
      }
      sqlite3_bind_text(stmt, index, joined.c_str(), -1, SQLITE_TRANSIENT);
      break;
    }
  }
}

bool columnToValue(sqlite3_stmt* stmt, int column, core::Value* out, std::string* err) {
  const char* name = sqlite3_column_name(stmt, column);
  const std::string columnName = name != nullptr ? name : std::to_string(column);
  switch (sqlite3_column_type(stmt, column)) {
    case SQLITE_NULL:
      return false;  // NULL columns are omitted from the outputs
    case SQLITE_INTEGER:
      *out = core::Value(static_cast<int64_t>(sqlite3_column_int64(stmt, column)));
      return true;
    case SQLITE_FLOAT:
      *out = core::Value(sqlite3_column_double(stmt, column));
      return true;
    case SQLITE_TEXT: {
      const unsigned char* text = sqlite3_column_text(stmt, column);
      const int bytes = sqlite3_column_bytes(stmt, column);
      *out = core::Value(std::string(reinterpret_cast<const char*>(text),
                                     static_cast<size_t>(std::max(0, bytes))));
      return true;
    }
    default:
      if (err) *err = "column \"" + columnName + "\" holds a BLOB, which has no typed form";
      return false;
  }
}

}  // namespace

TransportResult SqliteTransport::invoke(const AdapterDefinition& def,
                                        const std::map<std::string, core::Value>& payload) {
  TransportResult result;
  if (def.sqlitePath.empty()) {
    result.error = "adapter has no SQLite path";
    return result;
  }
  if (def.table.empty()) {
    result.error = "adapter has no SQLite table";
    return result;
  }
  sqlite3* db = nullptr;
  const int openRc =
      sqlite3_open_v2(def.sqlitePath.c_str(), &db, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE, nullptr);
  if (openRc != SQLITE_OK) {
    result.error = "cannot open database \"" + def.sqlitePath + "\": " +
                   (db != nullptr ? sqlite3_errmsg(db) : "unknown error");
    if (db != nullptr) sqlite3_close(db);
    return result;
  }
  sqlite3_exec(db, "PRAGMA journal_mode=WAL;", nullptr, nullptr, nullptr);
  sqlite3_exec(db, "PRAGMA busy_timeout=5000;", nullptr, nullptr, nullptr);

  std::vector<std::pair<std::string, core::Value>> entries(payload.begin(), payload.end());
  const std::string table = quoteIdentifier(def.table);
  std::string sql;
  if (def.operation == "insert") {
    if (entries.empty()) {
      result.error = "insert requires at least one input";
      sqlite3_close(db);
      return result;
    }
    std::string columns;
    std::string placeholders;
    for (size_t i = 0; i < entries.size(); ++i) {
      if (i != 0) {
        columns += ", ";
        placeholders += ", ";
      }
      columns += quoteIdentifier(entries[i].first);
      placeholders += "?" + std::to_string(i + 1);
    }
    sql = "INSERT INTO " + table + " (" + columns + ") VALUES (" + placeholders + ")";
  } else if (def.operation == "update") {
    std::string key;
    for (const auto& entry : entries) {
      if (entry.first.size() > 3 &&
          entry.first.compare(entry.first.size() - 3, 3, "_id") == 0) {
        key = entry.first;
        break;
      }
    }
    if (key.empty()) {
      result.error = "update requires an input ending in _id to use as the row key";
      sqlite3_close(db);
      return result;
    }
    std::string assignments;
    int parameter = 1;
    for (const auto& entry : entries) {
      if (entry.first == key) continue;
      if (!assignments.empty()) assignments += ", ";
      assignments += quoteIdentifier(entry.first) + " = ?" + std::to_string(parameter++);
    }
    if (assignments.empty()) {
      result.error = "update has no columns to change besides the key \"" + key + "\"";
      sqlite3_close(db);
      return result;
    }
    sql = "UPDATE " + table + " SET " + assignments + " WHERE " + quoteIdentifier(key) + " = ?" +
          std::to_string(parameter);
  } else if (def.operation == "select_one") {
    std::string where;
    for (size_t i = 0; i < entries.size(); ++i) {
      if (i != 0) where += " AND ";
      where += quoteIdentifier(entries[i].first) + " = ?" + std::to_string(i + 1);
    }
    sql = "SELECT * FROM " + table + (where.empty() ? "" : " WHERE " + where) + " LIMIT 1";
  } else {
    result.error = "unknown SQLite operation \"" + def.operation + "\"";
    sqlite3_close(db);
    return result;
  }
  result.trace.push_back("sqlite " + def.operation + " on " + def.table + " at " + def.sqlitePath);

  sqlite3_stmt* stmt = nullptr;
  const int prepareRc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);
  if (prepareRc != SQLITE_OK) {
    result.error = "cannot prepare statement: " + std::string(sqlite3_errmsg(db));
    sqlite3_close(db);
    return result;
  }
  int parameter = 1;
  if (def.operation == "update") {
    // Non key columns first, then the key, matching the SET ... WHERE order above.
    std::string key;
    for (const auto& entry : entries) {
      if (entry.first.size() > 3 && entry.first.compare(entry.first.size() - 3, 3, "_id") == 0) {
        key = entry.first;
        break;
      }
    }
    for (const auto& entry : entries) {
      if (entry.first == key) continue;
      bindValue(stmt, parameter++, entry.second);
    }
    bindValue(stmt, parameter++, payload.at(key));
  } else {
    for (const auto& entry : entries) bindValue(stmt, parameter++, entry.second);
  }

  const int stepRc = sqlite3_step(stmt);
  if (def.operation == "select_one") {
    if (stepRc == SQLITE_ROW) {
      const int columns = sqlite3_column_count(stmt);
      for (int i = 0; i < columns; ++i) {
        core::Value v;
        std::string err;
        if (columnToValue(stmt, i, &v, &err)) {
          const char* name = sqlite3_column_name(stmt, i);
          result.outputs[name != nullptr ? name : std::to_string(i)] = std::move(v);
        } else if (!err.empty()) {
          result.error = err;
          sqlite3_finalize(stmt);
          sqlite3_close(db);
          return result;
        }
      }
    } else if (stepRc != SQLITE_DONE) {
      result.error = "query failed: " + std::string(sqlite3_errmsg(db));
      sqlite3_finalize(stmt);
      sqlite3_close(db);
      return result;
    }
  } else {
    if (stepRc != SQLITE_DONE) {
      result.error = "statement failed: " + std::string(sqlite3_errmsg(db));
      sqlite3_finalize(stmt);
      sqlite3_close(db);
      return result;
    }
    result.outputs["rows_changed"] = core::Value(static_cast<int64_t>(sqlite3_changes(db)));
    if (def.operation == "insert") {
      result.outputs["row_id"] =
          core::Value(static_cast<int64_t>(sqlite3_last_insert_rowid(db)));
    }
  }
  sqlite3_finalize(stmt);
  sqlite3_close(db);
  result.ok = true;
  return result;
}

}  // namespace adapter
}  // namespace careweave
