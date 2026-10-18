#!/bin/sh
# Runs the five experiments and the evaluation harness. Results land in experiments/out/.
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
build="${CAREWEAVE_BUILD_DIR:-$root/core/build}"
mkdir -p "$root/logs"

if [ ! -x "$build/experiments/exp1_compatibility" ]; then
  echo "the experiments are not built; running scripts/build.sh first"
  sh "$root/scripts/build.sh"
fi

for program in exp1_compatibility exp2_composition exp3_alternative_implementations \
               exp4_irrelevant_capabilities exp5_operational_attributes careweave_evaluation; do
  echo "== $program"
  if ! "$build/experiments/$program" > "$root/logs/$program.log" 2>&1; then
    echo "$program failed:" >&2
    tail -n 40 "$root/logs/$program.log" >&2
    exit 1
  fi
  tail -n 2 "$root/logs/$program.log"
done
echo "experiments ok; results in $root/experiments/out"
