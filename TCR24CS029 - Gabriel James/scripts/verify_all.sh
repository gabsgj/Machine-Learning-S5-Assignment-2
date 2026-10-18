#!/bin/sh
# The acceptance path end to end: purge and placeholder scans, the build, the C++ and module
# test suites, the experiments, the integrated workflow against the live system, the management
# API and dashboard endpoints, and the dashboard asset check. Everything is captured in a
# timestamped log under logs/; the script exits 0 only when every step passes.
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
logs="$root/logs"
mkdir -p "$logs"
log="$logs/verify_all_$(date +%Y%m%d%H%M%S).log"

# The banned and placeholder patterns are assembled from fragments so that this script never
# contains the forbidden spellings it checks for.
frag_a="d""sl"
frag_b="cli\\.j""s"
frag_c="Jm""es"
frag_d="Lead Archi""tect"
frag_e="Principal Formal Met""hods"
frag_f="2\\.0\\.0-PR""OD"
purge_pattern="$frag_a|$frag_b|$frag_c|$frag_d|$frag_e|$frag_f"

frag_g="TO""DO"
frag_h="FIX""ME"
frag_i="T""BD"
frag_j="coming ""soon"
frag_k="not ""implemented"
frag_l="unimpl""emented"
placeholder_pattern="$frag_g|$frag_h|$frag_i|$frag_j|$frag_k|$frag_l"

scan() { # label pattern
  echo "== $1"
  if grep -rniE "$2" "$root" \
      --exclude-dir=third_party --exclude-dir=build --exclude-dir=dist --exclude-dir=generated \
      --exclude-dir=logs --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ \
      --exclude-dir=.pytest_cache --exclude=BUILD_LOG.md --exclude="*.tex" --exclude="*.pdf"; then
    echo "$1 found matches" >&2
    return 1
  fi
  echo "$1 clean"
}

scope_check() {
  echo "== scope check (the experiments stay outside the planner scope)"
  if grep -rniE "planner|planForward|planBackward|PlanResult|PlanStep|PlanOptions|PlanStrategy" \
      "$root/experiments"; then
    echo "the experiments must not reference the planner" >&2
    return 1
  fi
  echo "scope check clean"
}

dashboard_check() {
  echo "== dashboard offline check"
  if [ ! -f "$root/dashboard/index.html" ]; then
    echo "the dashboard index is missing" >&2
    return 1
  fi
  for asset in styles.css app.js; do
    if [ ! -f "$root/dashboard/$asset" ]; then
      echo "the dashboard is missing $asset" >&2
      return 1
    fi
  done
  if grep -rnE "https?://" "$root/dashboard" --include="*.html" --include="*.css" --include="*.js"; then
    echo "the dashboard must not reference external URLs" >&2
    return 1
  fi
  echo "dashboard assets complete and free of external URLs"
}

api_check() {
  echo "== management API and dashboard endpoints"
  base="http://127.0.0.1:${CAREWEAVE_GATEWAY_PORT:-5100}"
  check_endpoint() { # label method path data marker
    label="$1"
    method="$2"
    path="$3"
    data="$4"
    marker="$5"
    body_file="$logs/api_check_$(printf '%s' "$label" | tr ' A-Z' '_a-z').json"
    if [ -n "$data" ]; then
      code="$(curl -sS -o "$body_file" -w '%{http_code}' -X "$method" \
              -H 'Content-Type: application/json' --data "$data" "$base$path")" || code="000"
    else
      code="$(curl -sS -o "$body_file" -w '%{http_code}' -X "$method" "$base$path")" || code="000"
    fi
    if [ "$code" != "200" ]; then
      echo "$label answered http $code" >&2
      return 1
    fi
    if [ -n "$marker" ] && ! grep -q "$marker" "$body_file"; then
      echo "$label answered 200 without $marker" >&2
      return 1
    fi
    echo "verified $label"
  }
  check_endpoint "dashboard index" GET "/" "" "CareWeave Mini" || return 1
  check_endpoint "sheets list" GET "/api/sheets" "" "register_pat.yaml" || return 1
  check_endpoint "sheet detail" GET "/api/sheet?path=specs/app/requirements/register_pat.yaml" "" "capabilities" || return 1
  check_endpoint "embedding" POST "/api/embed" '{"sheet": "specs/app/hospital_alias_resolution.yaml"}' '"blocks"' || return 1
  check_endpoint "embedding compare" POST "/api/embed/compare" '{"sheet": "specs/app/hospital_alias_resolution.yaml", "left": "AR-PatReg", "right": "AR-RegisterPatient"}' '"total"' || return 1
  check_endpoint "adapter preview" POST "/api/adapter" '{"requirement": "specs/app/requirements/register_pat.yaml", "module": "patient-registry-alt", "capability": "PA-Register"}' '"adapter"' || return 1
  check_endpoint "plan" POST "/api/plan" '{"sheet": "specs/app/hospital_clinic_visit.yaml", "max_depth": 8}' '"steps"' || return 1
  check_endpoint "experiments" GET "/api/experiments" "" '"criteria"' || return 1
  check_endpoint "audit" GET "/api/audit?limit=10" "" '"kind"' || return 1
  return 0
}

verify() {
  echo "verify_all started $(date)"
  scan "purge scan" "$purge_pattern" || return 1
  scan "placeholder scan" "$placeholder_pattern" || return 1
  scope_check || return 1
  echo "== build"
  sh "$root/scripts/build.sh" || return 1
  echo "== unit tests"
  sh "$root/scripts/run_unit_tests.sh" || return 1
  echo "== experiments"
  sh "$root/scripts/run_experiments.sh" || return 1
  echo "== integrated workflow"
  sh "$root/scripts/start_all.sh" || return 1
  workflow_status=0
  sh "$root/scripts/run_integrated_workflow.sh" || workflow_status=1
  if [ "$workflow_status" = "0" ]; then
    api_check || workflow_status=1
  fi
  sh "$root/scripts/stop_all.sh" || return 1
  [ "$workflow_status" = "0" ] || return 1
  dashboard_check || return 1
  echo "verify_all ok $(date)"
}

if verify > "$log" 2>&1; then
  tail -n 8 "$log"
  echo "verify_all ok; full log: $log"
  exit 0
else
  status=$?
  echo "verify_all failed (status $status); last lines of $log:" >&2
  tail -n 40 "$log" >&2
  exit "$status"
fi
