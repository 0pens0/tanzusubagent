#!/usr/bin/env bash
# Deploy tanzudispatcher + tanzusubagent and restage production tanzubot (separate repo).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ORG="${CF_ORG:-demo}"
SPACE="${CF_SPACE:-tanzubot}"
TANZUBOT_ROOT="${TANZUBOT_ROOT:-$(cd "${ROOT}/../tanzubot" && pwd)}"

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

cf push -f "${ROOT}/manifest.yml"

if [[ -f "${TANZUBOT_ROOT}/a2a-peers.yaml" ]] || [[ -f "${TANZUBOT_ROOT}/a2a-peers.yaml.example" ]]; then
  if [[ ! -f "${TANZUBOT_ROOT}/a2a-peers.yaml" ]]; then
    cp "${TANZUBOT_ROOT}/a2a-peers.yaml.example" "${TANZUBOT_ROOT}/a2a-peers.yaml"
  fi
  echo "restaging tanzubot from ${TANZUBOT_ROOT}"
  cf push "${TANZUBOT_ROOT}" -f "${TANZUBOT_ROOT}/manifest.yml" || cf restage tanzubot
else
  echo "warn: tanzubot repo not found at ${TANZUBOT_ROOT}; skip tanzubot restage"
fi

echo "done. verify routes:"
cf app tanzubot | grep -E 'routes|name' || true
cf app tanzudispatcher | grep routes || true
cf app tanzusubagent | grep routes || true
