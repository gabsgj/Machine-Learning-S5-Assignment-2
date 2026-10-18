#!/bin/sh
# Stops every process started by scripts/start_all.sh. The recorded pids are the server
# processes themselves. Idempotent: a second run reports that nothing is left to stop.
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
logs="$root/logs"
if [ ! -d "$logs" ]; then
  echo "nothing to stop"
  exit 0
fi

pids=""
for pidfile in "$logs"/*.pid; do
  [ -e "$pidfile" ] || continue
  pid="$(cat "$pidfile")"
  name="$(basename "$pidfile" .pid)"
  if kill -0 "$pid" 2>/dev/null; then
    pids="$pids $pid"
    echo "stopping $name (pid $pid)"
  else
    echo "$name was not running (stale pid $pid)"
  fi
  rm -f "$pidfile"
done

if [ -z "$pids" ]; then
  echo "nothing to stop"
  exit 0
fi

for pid in $pids; do kill "$pid" 2>/dev/null || true; done
sleep 1
survivors=""
for pid in $pids; do
  if kill -0 "$pid" 2>/dev/null; then survivors="$survivors $pid"; fi
done
for pid in $survivors; do kill -9 "$pid" 2>/dev/null || true; done
if [ -n "$survivors" ]; then
  echo "forced down:$survivors"
fi
echo "stopped $(echo "$pids" | wc -w | tr -d ' ') processes"
