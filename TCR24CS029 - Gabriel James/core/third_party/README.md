# Vendored third party components

This directory holds the only third party code in the project. Everything is vendored as plain
source so the build works offline with no package manager. Includes are marked `SYSTEM` in
CMake, so warnings from these headers never appear in project builds.

| Component | Version | Files | License | Source |
| --- | --- | --- | --- | --- |
| nlohmann/json | 3.12.0 | `nlohmann/json.hpp`, `nlohmann/json_fwd.hpp` | MIT | https://github.com/nlohmann/json/releases/download/v3.12.0/json.hpp and https://raw.githubusercontent.com/nlohmann/json/v3.12.0/single_include/nlohmann/json_fwd.hpp |
| cpp-httplib | 0.53.1 | `httplib/httplib.h` | MIT | https://github.com/yhirose/cpp-httplib/releases/download/v0.53.1/httplib.h |
| SQLite amalgamation | 3.46.1 | `sqlite/sqlite3.c`, `sqlite/sqlite3.h` | Public domain | https://www.sqlite.org/2024/sqlite-amalgamation-3460100.zip |

SQLite is compiled into a small separate static library (`careweave_sqlite`) with only the
default features, no shell and no extensions, matching the amalgamation defaults.
