# tanzusubagent

Fork of [yannicklevederpvtl/cf-agent-a2a-skill-script](https://github.com/yannicklevederpvtl/cf-agent-a2a-skill-script) for **Tanzubot + tanzusubagent** on Tanzu Platform Elastic Application Runtime.

Two Agent Buildpack apps communicate via native A2A (`list_a2a_peers`, `call_a2a_peer`). The worker ships a **SkillRunner MCP sidecar** for Python skill scripts.

## Apps

| CF app | Role | Key skills |
| --- | --- | --- |
| `tanzubot` | Orchestrator; user-facing PSE | `a2a-delegate` |
| `tanzusubagent` | Worker; scripts + MCP audits | `a2a-worker`, `tanzu-network-release`, `cf-space-auditor`, `python-script-smoke` |

```
CF app: tanzubot                    CF app: tanzusubagent
+------------------------+          +------------------------+
|  Tanzubot (orchestrator)|<------->|  tanzusubagent (worker)|
|  call_a2a_peer         |   A2A   |  run_skill_script      |
|  a2a-delegate skill    |  HTTP   |  cf-space-auditor, etc.|
+------------------------+          +------------------------+
```

Peer registry: `apps/*/a2a-peers.yaml` (gitignored; use `a2a-peers.yaml.example`).

## Documentation

- [docs/USE_CASES_AND_SCENARIOS.md](docs/USE_CASES_AND_SCENARIOS.md) - flows, prompts, verify steps
- [docs/ROADMAP.md](docs/ROADMAP.md) - future workers (BOSH, Hub, ...)

## Prerequisites

- `cf` CLI v8
- Buildpack order: `python_buildpack`, then `agent_buildpack`
- Optional sibling: [cf-agent-skill-script](https://github.com/yannicklevederpvtl/cf-agent-skill-script) for `scripts/sync_shared.sh`
- Services in target space: **`Qwen3.6`**, **`skill-runner-mcp-local`** (`scripts/setup_mcp_binding.sh`)

## Deploy

```bash
bash scripts/setup_mcp_binding.sh
bash scripts/sync_shared.sh
cp apps/tanzubot/a2a-peers.yaml.example apps/tanzubot/a2a-peers.yaml
cp apps/tanzusubagent/a2a-peers.yaml.example apps/tanzusubagent/a2a-peers.yaml
# Set real routes, then:
cf push -f manifest.yml
```

Single app:

```bash
cf push -f manifest.yml tanzubot
cf push -f manifest.yml tanzusubagent
```

## Sample prompts

**On tanzubot:**

> Ask tanzusubagent to use tanzu-network-release to list the latest versions of product `cf` and return raw JSON.

> Audit org `demo` space `tanzubot` for compliance via tanzusubagent.

**On tanzusubagent (direct):**

> Use tanzu-network-release for product `genai` latest versions.

## Related repos

- https://github.com/0pens0/tanzubot - principal agent source (`AGENTS.md`, MCP bindings)
- https://github.com/0pens0/tanzusubagent - this repo
- Upstream: `yannicklevederpvtl/cf-agent-a2a-skill-script`

## Security

SkillRunner executes shipped `skills/*/scripts/*.py` only. MCP sidecar binds `127.0.0.1` - do not expose port 8765 on a public route.
