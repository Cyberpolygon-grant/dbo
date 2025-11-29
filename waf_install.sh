#!/usr/bin/env bash
set -euo pipefail

echo "Installing SafeLine WAF via official setup script..."
echo "Source: https://github.com/chaitin/SafeLine"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Please install Docker and rerun."
  exit 1
fi

curl -fsSLk https://waf.chaitin.com/release/latest/setup.sh | bash

echo "SafeLine stack deployed. If needed, reset admin credentials:"
echo "  docker exec safeline-mgt resetadmin"
echo
echo "Next: In SafeLine UI, create a site and set upstream to your Django app."
echo "If SafeLine runs on the same host, and Django runs in Docker, set upstream to:"
echo "  http://host.docker.internal:8000   (macOS/Windows Docker Desktop)"
echo "or on Linux, use the host IP (e.g., http://127.0.0.1:8000) or publish a port in compose."


