# tanzusubagent

Fork of [yannicklevederpvtl/cf-agent-a2a-skill-script](https://github.com/yannicklevederpvtl/cf-agent-a2a-skill-script) for **Tanzubot multi-agent (A2A) workloads** on Tanzu Platform Elastic Application Runtime.

Upstream demonstrates two Agent Buildpack apps talking peer-to-peer via native A2A (`list_a2a_peers`, `call_a2a_peer`) plus a **SkillRunner MCP sidecar** for local Python skill scripts.

This repo evolves that pattern so **Tanzubot** orchestrates specialist subagents (CF operations, BOSH, Hub assessment, space audit, and similar) instead of the generic alpha/beta demo pair.

## Status

| Phase | Goal | State |
| --- | --- | --- |
| 0 | Fork upstream into `0pens0/tanzusubagent` | Done |
| 1 | Document target architecture (`docs/ROADMAP.md`) | In progress |
| 2 | Rename apps: `tanzubot` (orchestrator) + task-specific workers | Planned |
| 3 | Wire `a2a-peers.yaml` to live routes on `demo` foundation | Planned |
| 4 | Port Tanzubot skills/MCP bindings to worker agents | Planned |

## Target architecture

```
CF app: tanzubot (orchestrator)          CF apps: specialist workers
+---------------------------+            +---------------------------+
|  Tanzubot principal PSE |            |  tanzu-cf-worker          |
|  AGENTS.md + delegation   |<--------->|  tanzu-bosh-worker        |
|  list_a2a_peers          |   A2A     |  tanzu-hub-worker         |
|  call_a2a_peer           |   HTTP    |  (skills + MCP per role)  |
|  User-facing chat UI    |            +---------------------------+
+---------------------------+
```

- **Orchestrator** keeps Tanzubot identity (`AGENTS.md` from [tanzubot](https://github.com/0pens0/tanzubot)).
- **Workers** own narrow skills and platform bindings (MCP via CF service bindings, SkillRunner scripts where needed).
- **A2A** uses Agent Buildpack native tools; no message broker.

## Current demo apps (upstream names)

Until Phase 2 rename, manifests still use upstream app names:

| CF App | Role | Notes |
| --- | --- | --- |
| `agent-a2a-alpha` | Orchestrator | Delegates via `call_a2a_peer` |
| `agent-a2a-beta` | Worker | Runs skill scripts; replies to alpha |

See [docs/ROADMAP.md](docs/ROADMAP.md) for the Tanzubot mapping and worker catalog.

## Prerequisites

- `cf` CLI v8 (sidecars require CAPI v3)
- Multi-buildpack: `python_buildpack` then `agent_buildpack`
- Optional sibling clone: [cf-agent-skill-script](https://github.com/yannicklevederpvtl/cf-agent-skill-script) (SkillRunner sidecar sync)
- Space service instances:
  - **`Qwen3.6`** (or your bound genai service)
  - **`skill-runner-mcp-local`** (CUPS MCP; see `scripts/setup_mcp_binding.sh`)

## Deploy (upstream demo)

```bash
bash scripts/setup_mcp_binding.sh
bash scripts/sync_shared.sh
cf push -f manifest.yml
```

Copy peer templates and set your apps domain:

```bash
cp apps/agent-a2a-alpha/a2a-peers.yaml.example apps/agent-a2a-alpha/a2a-peers.yaml
cp apps/agent-a2a-beta/a2a-peers.yaml.example apps/agent-a2a-beta/a2a-peers.yaml
# Edit URLs, then cf push -f manifest.yml
```

## Provenance

- **Source:** `yannicklevederpvtl/cf-agent-a2a-skill-script`
- **Fork:** https://github.com/0pens0/tanzusubagent
- **Related:** https://github.com/0pens0/tanzubot (principal agent)

## Security

SkillRunner Policy A can execute any `skills/*/scripts/*.py` shipped in the droplet. MCP listens on `127.0.0.1` only; do not expose the sidecar port on a public route.
