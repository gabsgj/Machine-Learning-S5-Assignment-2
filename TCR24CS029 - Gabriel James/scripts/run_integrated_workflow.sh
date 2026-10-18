#!/bin/sh
# Runs the integrated clinic visit twice against the live system: first with the canonical
# registry module, then with the legacy alias module swapped in, resolved through the alias
# requirement sheet and the synthesized adapter. Verifies the module databases afterwards.
# Requires scripts/start_all.sh to have started the system.
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
logs="$root/logs"
gateway_url="http://127.0.0.1:${CAREWEAVE_GATEWAY_PORT:-5100}"
stamp="$(date +%Y%m%d%H%M%S)"
mkdir -p "$logs"

if ! command -v sqlite3 > /dev/null 2>&1; then
  echo "sqlite3 is needed for the database verification" >&2
  exit 1
fi
if ! curl -fsS "$gateway_url/health" > /dev/null 2>&1; then
  echo "the gateway is not running; run scripts/start_all.sh first" >&2
  exit 1
fi

check() { # label expected actual
  if [ "$2" != "$3" ]; then
    echo "VERIFY FAILED: $1 expected [$2] got [$3]" >&2
    exit 1
  fi
  echo "verified $1: $3"
}

registry_db="$root/modules/patient-registry/data/patient_registry.db"
alt_db="$root/modules/patient-registry-alt/data/patient_registry_alt.db"
ehr_db="$root/modules/opd-ehr/data/opd_ehr.db"
queue_db="$root/modules/appointment-queue/data/appointment_queue.db"
billing_db="$root/modules/pos-billing/data/pos_billing.db"
ehr_port="$(sed -n 's/.*"port": *\([0-9][0-9]*\).*/\1/p' "$root/modules/opd-ehr/spec.json" | head -1)"

# A run that stopped midway can leave its encounter active, and opd-ehr allows a single active
# encounter; close stale ones through the module's own capability before starting a fresh visit.
for stale in $(sqlite3 "$ehr_db" "SELECT encounter_id FROM encounters WHERE status = 'active';"); do
  curl -fsS -X POST "http://127.0.0.1:$ehr_port/api/close_encounter" \
      -H 'Content-Type: application/json' \
      --data "{\"encounter_id\": \"$stale\", \"summary\": \"closed by the workflow runner\"}" \
      > /dev/null
  echo "closed stale active encounter $stale"
done

workflow_a="$logs/workflow_visit_$stamp.json"
workflow_b="$logs/workflow_visit_legacy_$stamp.json"
sed "s/VISIT-DEMO-1/VISIT-$stamp-A/" "$root/specs/workflows/visit.json" > "$workflow_a"
sed "s/LEGACY-DEMO-1/LEGACY-$stamp-B/" "$root/specs/workflows/visit_legacy.json" > "$workflow_b"

run_workflow() { # name filename step-count
  name="$1"
  file="$2"
  expected_steps="$3"
  response="$logs/workflow_${name}_${stamp}_response.json"
  code="$(curl -sS -o "$response" -w '%{http_code}' -H 'Content-Type: application/json' \
      --data "{\"workflow\": \"logs/$(basename "$file")\"}" "$gateway_url/api/workflow")"
  ok="$(sed -n 's/^  "ok": //p' "$response" | head -1 | tr -d ',')"
  if [ "$code" != "200" ] || [ "$ok" != "true" ]; then
    echo "the $name workflow failed (http $code, ok ${ok:-unknown}):" >&2
    sed -n '1,80p' "$response" >&2
    exit 1
  fi
  echo "workflow $name completed: $(grep -c '"verdict":' "$response") of $expected_steps steps, http $code"
  grep -E '"(name|verdict|module_id)":' "$response" | sed 's/^ *//'
  check "$name workflow step count" "$expected_steps" "$(grep -c '"verdict":' "$response")"
}

run_workflow canonical "$workflow_a" 7
run_workflow legacy "$workflow_b" 5

echo "== database verification"

mrn_a="VISIT-$stamp-A"
patient_id="$(sqlite3 "$registry_db" "SELECT patient_id FROM patients WHERE mrn = '$mrn_a';")"
check "canonical patient row" "yes" "$([ -n "$patient_id" ] && echo yes || echo no)"
check "canonical patient admitted flag" "1" \
      "$(sqlite3 "$registry_db" "SELECT admitted FROM patients WHERE mrn = '$mrn_a';")"
check "canonical active admission" "1" \
      "$(sqlite3 "$registry_db" "SELECT COUNT(*) FROM admissions WHERE patient_id = '$patient_id' AND active = 1;")"
check "canonical closed encounter" "1" \
      "$(sqlite3 "$ehr_db" "SELECT COUNT(*) FROM encounters WHERE patient_mrn = '$mrn_a' AND status = 'closed';")"
check "canonical recorded vitals" "1" \
      "$(sqlite3 "$ehr_db" "SELECT COUNT(*) FROM vitals WHERE encounter_id IN (SELECT encounter_id FROM encounters WHERE patient_mrn = '$mrn_a');")"
check "canonical paid invoice" "1" \
      "$(sqlite3 "$billing_db" "SELECT COUNT(*) FROM invoices WHERE patient_mrn = '$mrn_a' AND status = 'paid';")"

pat_no_b="LEGACY-$stamp-B"
pat_reg="$(sqlite3 "$alt_db" "SELECT pat_reg FROM patients WHERE pat_no = '$pat_no_b';")"
check "legacy patient row" "yes" "$([ -n "$pat_reg" ] && echo yes || echo no)"
check "legacy verified flag" "1" \
      "$(sqlite3 "$alt_db" "SELECT verified FROM patients WHERE pat_no = '$pat_no_b';")"
check "legacy registration answered by the alias module" "patient-registry-alt" \
      "$(sed -n 's/.*"module_id": "\(patient-registry-alt\)".*/\1/p' "$logs/workflow_legacy_${stamp}_response.json" | head -1)"
check "legacy open queue ticket" "1" \
      "$(sqlite3 "$queue_db" "SELECT COUNT(*) FROM tickets WHERE patient_mrn = '$pat_reg' AND open = 1;")"
check "legacy paid invoice" "1" \
      "$(sqlite3 "$billing_db" "SELECT COUNT(*) FROM invoices WHERE patient_mrn = '$pat_reg' AND status = 'paid';")"

echo "integrated workflow ok: run $stamp verified in the module databases"
