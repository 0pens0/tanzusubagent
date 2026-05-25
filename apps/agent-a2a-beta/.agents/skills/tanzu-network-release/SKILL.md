---
name: tanzu-network-release
description: Tanzu Network public API — list versions or release metadata (JSON). Use via run_skill_script or inbound A2A delegate from agent-a2a-alpha.
---

# When to use

Use when the user asks for **Tanzu Network / Broadcom network** information about a **product slug** (`elastic-runtime`, `cf`, `p-concourse`, etc.): **list versions**, or **metadata for one exact version** (dates, release notes URL, product file names, dependency specifiers).

Do not invent versions or file names; use this skill's script or the **SkillRunner** MCP `run_skill_script` so results come from the API.

# Python (Tanzu / Cloud Foundry)

On the app droplet, prefer **`/home/vcap/deps/0/bin/python3`** if `python3` is missing from `PATH`, or load `/home/vcap/profile.d` after `DEPS_DIR=/home/vcap/deps`.

# Available scripts

- **`scripts/pivnet_release.py`** — Stdlib-only HTTP GET to `https://network.tanzu.vmware.com/`. No API token is sent (same as the legacy `tanzu_api` curl flow). Exits non-zero if the payload has `"ok": false`.

# CLI

List versions:

```bash
python3 scripts/pivnet_release.py --product elastic-runtime --list-versions
```

Full metadata for one version:

```bash
python3 scripts/pivnet_release.py --product elastic-runtime --version 10.3.0
```

Pretty JSON:

```bash
python3 scripts/pivnet_release.py --product cf --list-versions --pretty
```

If HTTPS fails with certificate errors (corporate TLS inspection), use **`--insecure`** only in trusted lab environments (MITM risk).

# SkillRunner MCP (in-container)

1. `list_skill_scripts` includes this skill when deployed.
2. Example `run_skill_script` args:
   `skill_id=tanzu-network-release`, `script_relpath=scripts/pivnet_release.py`,
   `args=["--product","cf","--list-versions"]` or with `--version`, `10.12.0` (exact string from the network).
   Add `"--insecure"` to `args` only if TLS verification fails in a known-inspected environment.

# A2A inbound (from agent-a2a-alpha)

When **`[A2A inbound]`** carries a generic task, use **`a2a-worker`**: same `run_skill_script` call, then reply via `call_a2a_peer(alias="alpha", message="<structured result>")`. Alpha sends a plain-text instruction naming this skill (see **`a2a-requester`** on alpha).

# Output

- **Stdout:** single JSON object. On success: `ok`, `product`, and either `versions` / `count` or `release`, `product_files`, `dependency_specifiers`, `om_download_hint`.
- **Stderr:** empty on success; HTTP failures may print one JSON line and exit non-zero.

# Limits

- Requires **egress** from the app cell to `network.tanzu.vmware.com`.
- **Download** of bits is **not** performed; `om_download_hint` is a template for operators (token placeholder only).
