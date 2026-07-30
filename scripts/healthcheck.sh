#!/usr/bin/env bash
set -euo pipefail
PORT="${STREAM_PORT:-8080}"
systemctl --no-pager --full status jetson-vision.service || true
ss -ltnp | grep ":${PORT}" || true
curl -fsS "http://127.0.0.1:${PORT}/health" || true
echo
systemctl is-active nvargus-daemon
