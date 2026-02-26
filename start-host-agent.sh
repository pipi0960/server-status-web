#!/usr/bin/env zsh
set -euo pipefail
cd /Users/pipidan/sandbox/server-status-web
TOKEN=$(grep '^HOST_METRICS_TOKEN=' .env | cut -d= -f2-)
if [[ -z "$TOKEN" ]]; then
  echo "HOST_METRICS_TOKEN is empty in .env"
  exit 1
fi
if [[ -f /tmp/host-metrics-agent.pid ]] && kill -0 "$(cat /tmp/host-metrics-agent.pid)" 2>/dev/null; then
  echo "host-metrics-agent already running (pid $(cat /tmp/host-metrics-agent.pid))"
  exit 0
fi
EXISTING_PID=$(lsof -tiTCP:19100 -sTCP:LISTEN 2>/dev/null | head -n1 || true)
if [[ -n "${EXISTING_PID:-}" ]]; then
  echo "$EXISTING_PID" >/tmp/host-metrics-agent.pid
  echo "host-metrics-agent already running (pid $EXISTING_PID)"
  exit 0
fi
nohup env HOST_METRICS_TOKEN="$TOKEN" HOST_METRICS_BIND=127.0.0.1 HOST_METRICS_PORT=19100 \
  python3 host-metrics-agent.py >/tmp/host-metrics-agent.log 2>&1 &
echo $! >/tmp/host-metrics-agent.pid
sleep 0.5
if kill -0 "$(cat /tmp/host-metrics-agent.pid)" 2>/dev/null; then
  echo "host-metrics-agent started (pid $(cat /tmp/host-metrics-agent.pid))"
else
  echo "failed to start host-metrics-agent"
  exit 1
fi
