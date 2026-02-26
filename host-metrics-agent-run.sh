#!/usr/bin/env zsh
set -euo pipefail
cd /Users/pipidan/sandbox/server-status-web
TOKEN=$(grep '^HOST_METRICS_TOKEN=' .env | cut -d= -f2-)
if [[ -z "${TOKEN:-}" ]]; then
  echo "HOST_METRICS_TOKEN is empty" >&2
  exit 1
fi
exec env HOST_METRICS_TOKEN="$TOKEN" HOST_METRICS_BIND=127.0.0.1 HOST_METRICS_PORT=19100 \
  python3 /Users/pipidan/sandbox/server-status-web/host-metrics-agent.py
