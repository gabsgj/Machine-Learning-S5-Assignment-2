#!/bin/sh
# Runs the C++ test suites through ctest and every module pytest suite with coverage.
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
build="${CAREWEAVE_BUILD_DIR:-$root/core/build}"
python="${CAREWEAVE_PYTHON:-$root/.venv/bin/python3}"

if [ ! -d "$build" ]; then
  echo "the build directory is missing; run scripts/build.sh once" >&2
  exit 1
fi
echo "ctest in $build"
ctest --test-dir "$build" --output-on-failure

if [ ! -x "$python" ]; then
  echo "no Python environment found for the modules; run scripts/setup_modules.sh once" >&2
  exit 1
fi
for module in "$root"/modules/*/; do
  name="$(basename "$module")"
  [ -d "$module/tests" ] || continue
  echo "pytest $name"
  (cd "$module" && "$python" -m pytest tests -q --cov=. --cov-report=term)
done
echo "unit tests ok"
