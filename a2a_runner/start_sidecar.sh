#!/usr/bin/env bash
set -euo pipefail
export DEPS_DIR="${DEPS_DIR:-/home/vcap/deps}"
if [[ -d /home/vcap/profile.d ]]; then
  for s in /home/vcap/profile.d/*.sh; do
    # shellcheck source=/dev/null
    [[ -f "$s" ]] && . "$s"
  done
fi
cd /home/vcap/app
exec python3 -m a2a_runner.main
