#!/usr/bin/env bash
# Sync the skill_runner sidecar from cf-agent-skill-script into each app push root.
# Run before cf push.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_RUNNER_SRC="$(cd "${ROOT}/../cf-agent-skill-script/skill_runner" && pwd)"
APPS=(tanzubot tanzusubagent)

if [[ ! -d "${SKILL_RUNNER_SRC}" ]]; then
  echo "error: skill_runner source not found at ${SKILL_RUNNER_SRC}" >&2
  exit 1
fi

for name in "${APPS[@]}"; do
  dest="${ROOT}/apps/${name}"
  if [[ ! -d "${dest}" ]]; then
    echo "missing ${dest}" >&2
    exit 1
  fi
  echo "sync -> apps/${name}"
  rsync -a --delete \
    "${SKILL_RUNNER_SRC}/" "${dest}/skill_runner/"
  cp "${ROOT}/apps/${name}/requirements.txt" "${dest}/requirements.txt" 2>/dev/null || true
done

echo "done."
