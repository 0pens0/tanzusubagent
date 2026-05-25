# Tanzubot subagent roadmap

## Problem

Tanzubot today is a single Agent Buildpack app with many MCP bindings (CF, BOSH, Hub, Postgres, memory, mail). That works for demos but:

- Tool surface area is large for one model context.
- Regulated customers want **separation of duty** (CF ops vs BOSH vs assessment).
- Long-running or script-heavy tasks benefit from **isolated workers**.

## Approach

Reuse the upstream A2A + SkillRunner pattern:

1. **Orchestrator** (`tanzubot`) - user-facing; delegates when a specialist is better fit.
2. **Workers** - one CF app per domain; each has focused `AGENTS.md`, skills, and service bindings.

Communication: native buildpack tools `list_a2a_peers` and `call_a2a_peer` (HTTP between app routes). Inbound tasks arrive on worker `POST /api/chat` as `[A2A inbound]`.

## Planned workers (initial catalog)

| Worker app (planned) | Responsibility | Tanzubot skill / MCP source |
| --- | --- | --- |
| `tanzu-cf-worker` | Apps, spaces, routes, logs, audits | `cf-space-auditor`, `tanzubot-tanzu` MCP |
| `tanzu-bosh-worker` | Deployments, instances, errands | `tanzubot-bosh` MCP |
| `tanzu-hub-worker` | Portfolio assessment (read-only) | `tanzu-assess`, `tanzubot-hub` MCP |
| `tanzu-data-worker` | Postgres / vector queries | `tanzubot-postgres` MCP |

Orchestrator keeps: memory (`tanzumem`), mail notifications, and cross-domain synthesis.

## Implementation phases

### Phase 1 - Foundation (current)

- [x] Fork to `0pens0/tanzusubagent`
- [x] Roadmap and README
- [ ] Commit `a2a-peers.yaml.example` templates
- [ ] Verify `cf push` on `demo` space with peer URLs to existing `tanzubot` route

### Phase 2 - Rename and re-home apps

- [ ] `apps/tanzubot-orchestrator/` from `agent-a2a-alpha` + symlink or copy `AGENTS.md` from tanzubot repo
- [ ] `apps/tanzu-cf-worker/` from `agent-a2a-beta` as first worker
- [ ] Update `manifest.yml` app names and `AGENT_ID` env vars
- [ ] Add `a2a-peers.yaml` on orchestrator listing worker aliases

### Phase 3 - Skills and bindings per worker

- [ ] Copy relevant `.agents/skills/*` from tanzubot into worker push trees
- [ ] Create CF service instances per worker (principle of least privilege)
- [ ] Add `a2a-worker` / `a2a-requester` skills if missing from upstream (alpha had none in fork)

### Phase 4 - Tanzubot repo integration

- [ ] Add `AGENTS.md` section: when to delegate to A2A peers
- [ ] Document deployment: push tanzubot + workers from tanzusubagent manifest
- [ ] Optional: CI in tanzusubagent to sync SkillRunner from cf-agent-skill-script

## Delegation contract (from upstream)

Orchestrator messages to workers should name the skill and request raw output:

```text
Follow your `<skill-name>` skill to <action> and return the raw output without summarising.
```

Workers reply in structured form:

```text
TOOL USED: <tool-name or skill-name>
RESULT:
<raw output>
SUMMARY:
<one sentence>
```

## Foundation targets (Penso demo)

| App | Org/space | Route (example) |
| --- | --- | --- |
| `tanzubot` | `demo` / `tanzubot` | `tanzubot.apps.tp.penso.io` |
| Workers (TBD) | `demo` / `tanzubot` or `demo` | `tanzu-*-worker.apps.tp.penso.io` |

Peer registry lives in gitignored `a2a-peers.yaml`; examples are committed as `a2a-peers.yaml.example`.

## Open questions

1. Single space vs dedicated `tanzubot-workers` space for network policies?
2. Same genai service instance for all agents or per-worker quotas?
3. Which workers are sidecar-only (SkillRunner) vs MCP-only (no Python scripts)?
