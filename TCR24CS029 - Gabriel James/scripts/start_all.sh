#!/bin/sh
# Starts the seven module servers and the gateway, then waits until the gateway reports every
# module healthy. Idempotent: processes that are already running are left alone. Pids and logs
# live under logs/; the recorded pid is the server process itself.
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
logs="$root/logs"
python="${CAREWEAVE_PYTHON:-$root/.venv/bin/python3}"
gateway_port="${CAREWEAVE_GATEWAY_PORT:-5100}"
gateway="$root/core/build/careweave_gateway"

if [ ! -x "$python" ]; then
  echo "no Python environment found for the modules; run scripts/setup_modules.sh once" >&2
  exit 1
fi
if [ ! -x "$gateway" ]; then
  echo "the gateway is not built; run scripts/build.sh once" >&2
  exit 1
fi
mkdir -p "$logs"

alive() { [ -n "$1" ] && kill -0 "$1" 2>/dev/null; }

start_module() {
  name="$1"
  port="$2"
  pidfile="$logs/$name.pid"
  if [ -f "$pidfile" ] && alive "$(cat "$pidfile")"; then
    echo "$name already running (pid $(cat "$pidfile"))"
    return 0
  fi
  (cd "$root/modules/$name" && exec env CAREWEAVE_PORT="$port" "$python" run.py) \
      > "$logs/$name.log" 2>&1 &
  echo $! > "$pidfile"
  echo "started $name on port $port (pid $(cat "$pidfile"))"
}

for module in "$root"/modules/*/; do
  name="$(basename "$module")"
  [ -f "$module/run.py" ] || continue
  [ -f "$module/spec.json" ] || continue
  port="$(sed -n 's/.*"port": *\([0-9][0-9]*\).*/\1/p' "$module/spec.json" | head -1)"
  if [ -z "$port" ]; then
    echo "no port found in $module/spec.json" >&2
    exit 1
  fi
  start_module "$name" "$port"
done

if [ -f "$logs/gateway.pid" ] && alive "$(cat "$logs/gateway.pid")"; then
  echo "gateway already running (pid $(cat "$logs/gateway.pid"))"
else
  if [ -f "$root/dashboard/index.html" ]; then
    "$gateway" --root "$root" --port "$gateway_port" --dashboard "$root/dashboard" \
        > "$logs/gateway.log" 2>&1 &
  else
    "$gateway" --root "$root" --port "$gateway_port" > "$logs/gateway.log" 2>&1 &
  fi
  echo $! > "$logs/gateway.pid"
  echo "started gateway on port $gateway_port (pid $(cat "$logs/gateway.pid"))"
fi

attempt=0
while [ "$attempt" -lt 60 ]; do
  attempt=$((attempt + 1))
  if [ "$attempt" = "1" ] || [ "$attempt" = "10" ] || [ "$attempt" = "25" ] || [ "$attempt" = "40" ]; then
    curl -fsS -X POST "http://127.0.0.1:$gateway_port/api/discover" > /dev/null 2>&1 || true
  fi
  body="$(curl -fsS "http://127.0.0.1:$gateway_port/health" 2>/dev/null || true)"
  healthy="$(printf '%s' "$body" | tr -d ' ' | sed -n 's/.*"modules_healthy":\([0-9][0-9]*\).*/\1/p')"
  total="$(printf '%s' "$body" | tr -d ' ' | sed -n 's/.*"modules_total":\([0-9][0-9]*\).*/\1/p')"
  if [ -n "$healthy" ] && [ "$healthy" = "$total" ] && [ "$total" != "0" ]; then
    echo "gateway healthy: $healthy of $total modules live"
    exit 0
  fi
  sleep 1
done
echo "the gateway did not report every module healthy within 60 seconds" >&2
exit 1
