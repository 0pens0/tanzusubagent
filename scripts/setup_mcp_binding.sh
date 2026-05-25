#!/usr/bin/env bash
# Create user-provided MCP service (mcp-server tag) for agent buildpack discovery.
# Bindings are applied by manifest.yml on cf push (services: skill-runner-mcp-local).
# Run once per foundation/space before the first push.
set -euo pipefail

SERVICE_NAME="${1:-skill-runner-mcp-local}"
MCP_URL="${SKILL_RUNNER_MCP_URL:-http://127.0.0.1:8765/mcp/}"

echo "Creating user-provided MCP service: ${SERVICE_NAME}"
echo "  url=${MCP_URL}"

if cf service "${SERVICE_NAME}" >/dev/null 2>&1; then
  echo "Service ${SERVICE_NAME} already exists."
else
  cf cups "${SERVICE_NAME}" \
    -p "{\"url\":\"${MCP_URL}\",\"api_key\":\"\"}" \
    -t "mcp-server"
fi

echo ""
echo "Next: ensure manifest.yml lists ${SERVICE_NAME} under services: (default), then:"
echo "  cf push -f manifest.yml"
