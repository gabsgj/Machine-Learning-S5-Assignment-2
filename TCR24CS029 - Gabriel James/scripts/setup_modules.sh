#!/bin/sh
# Creates the module virtual environment when it is missing and installs the requirement files
# of all seven modules. Idempotent: existing environments and installed packages are reused.
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
venv="${CAREWEAVE_VENV:-$root/.venv}"
python="${CAREWEAVE_PYTHON:-$venv/bin/python3}"

if [ ! -x "$python" ]; then
  echo "creating $venv"
  python3 -m venv "$venv" || {
    echo "python3 -m venv failed; install Python 3.11 or newer" >&2
    exit 1
  }
fi

for requirement in "$root"/modules/*/requirements.txt; do
  [ -f "$requirement" ] || continue
  echo "installing $(basename "$(dirname "$requirement")")"
  "$python" -m pip install --quiet --disable-pip-version-check -r "$requirement"
done

if ! "$python" -m pytest --version > /dev/null 2>&1; then
  echo "installing pytest and pytest-cov"
  "$python" -m pip install --quiet --disable-pip-version-check pytest pytest-cov
fi

echo "module environment ready: $python"
