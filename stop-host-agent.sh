#!/usr/bin/env zsh
set -euo pipefail
if [[ -f /tmp/host-metrics-agent.pid ]]; then
  PID=$(cat /tmp/host-metrics-agent.pid)
  kill "$PID" 2>/dev/null || true
  rm -f /tmp/host-metrics-agent.pid
  echo "host-metrics-agent stopped"
else
  EXISTING_PID=$(lsof -tiTCP:19100 -sTCP:LISTEN 2>/dev/null | head -n1 || true)
  if [[ -n "${EXISTING_PID:-}" ]]; then
    kill "$EXISTING_PID" 2>/dev/null || true
    echo "host-metrics-agent stopped"
  else
    echo "host-metrics-agent pid file not found"
  fi
fi
