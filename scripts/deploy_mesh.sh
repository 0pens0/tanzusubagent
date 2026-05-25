#!/usr/bin/env bash
# Deploy tanzudispatcher + tanzusubagent to demo/tanzubot (or CF_ORG / CF_SPACE).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ORG="${CF_ORG:-demo}"
SPACE="${CF_SPACE:-tanzubot}"
TANZUBOT_ROOT="${TANZUBOT_ROOT:-$(cd "${ROOT}/../tanzubot" 2>/dev/null && pwd || echo "")}"

echo "Target: org ${ORG} space ${SPACE}"
cf target -o "${ORG}" -s "${SPACE}"

if [[ -d "${ROOT}/../cf-agent-skill-script/skill_runner" ]]; then
  bash "${ROOT}/scripts/sync_shared.sh"
else
  echo "skip sync_shared: cf-agent-skill-script not found; using bundled skill_runner"
fi

for app in tanzudispatcher tanzusubagent; do
  if [[ ! -f "${ROOT}/apps/${app}/a2a-peers.yaml" ]]; then
    cp "${ROOT}/apps/${app}/a2a-peers.yaml.example" "${ROOT}/apps/${app}/a2a-peers.yaml"
    echo "created apps/${app}/a2a-peers.yaml from example"
  fi
done

echo "Pushing tanzudispatcher and tanzusubagent..."
cf push -f "${ROOT}/manifest.yml"

if [[ -n "${TANZUBOT_ROOT}" && -f "${TANZUBOT_ROOT}/manifest.yml" ]]; then
  if [[ ! -f "${TANZUBOT_ROOT}/a2a-peers.yaml" ]]; then
    cp "${TANZUBOT_ROOT}/a2a-peers.yaml.example" "${TANZUBOT_ROOT}/a2a-peers.yaml"
  fi
  cp "${TANZUBOT_ROOT}/mesh-topology.yaml" "${TANZUBOT_ROOT}/mesh-app/mesh-topology.yaml" 2>/dev/null || true
  echo "Pushing tanzubot + tanzubot-mesh from ${TANZUBOT_ROOT}..."
  cf push -f "${TANZUBOT_ROOT}/manifest.yml"
fi

echo ""
echo "done. Apps in ${ORG}/${SPACE}:"
cf apps

echo ""
echo "Routes:"
cf app tanzudispatcher 2>/dev/null | grep routes || true
cf app tanzusubagent 2>/dev/null | grep routes || true
cf app tanzubot 2>/dev/null | grep routes || true
cf app tanzubot-mesh 2>/dev/null | grep routes || true
