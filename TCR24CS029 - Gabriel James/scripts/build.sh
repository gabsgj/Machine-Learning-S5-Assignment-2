#!/bin/sh
# Builds the C++ core, command line front end, test suites, experiments and gateway.
# Re-running reconfigures the same build directory in place, so the script is idempotent.
# Every line lands in logs/build.log and the build must finish without warnings.
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
logs="$root/logs"
build="${CAREWEAVE_BUILD_DIR:-$root/core/build}"
jobs="${CAREWEAVE_JOBS:-8}"
mkdir -p "$logs"

echo "configuring $build"
if ! cmake -S "$root/core" -B "$build" -DCMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE:-Release}" \
    > "$logs/build_configure.log" 2>&1; then
  echo "configuration failed:" >&2
  tail -n 40 "$logs/build_configure.log" >&2
  exit 1
fi

echo "building with $jobs jobs"
if ! cmake --build "$build" -j"$jobs" > "$logs/build.log" 2>&1; then
  echo "build failed:" >&2
  tail -n 60 "$logs/build.log" >&2
  exit 1
fi

if grep -n "warning:" "$logs/build.log"; then
  echo "the build printed warnings; the project keeps its builds warning free" >&2
  exit 1
fi
echo "build ok: $build"
