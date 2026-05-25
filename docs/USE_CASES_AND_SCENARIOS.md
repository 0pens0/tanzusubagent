# Use cases and scenarios

Tanzubot (`tanzubot`) and **tanzusubagent** (`tanzusubagent`) form an orchestrator/worker pair on Tanzu Platform Elastic Application Runtime. Communication uses native Agent Buildpack A2A (`list_a2a_peers`, `call_a2a_peer`) plus SkillRunner for Python skill scripts on the worker.

## Roles

| App | Role | Talks to |
| --- | --- | --- |
| `tanzubot` | User-facing PSE orchestrator; delegates specialist work | Humans, `tanzusubagent` |
| `tanzusubagent` | Worker; runs skills (scripts + MCP when bound) | `tanzubot` (A2A), optional direct humans |

## Scenario 1 - Tanzu Network version lookup (script skill)

**Actor:** Solutions Engineer in Tanzubot chat

**User prompt (tanzubot):**

> What are the latest published versions of the `cf` product on Tanzu Network?

**Expected flow:**

1. Tanzubot recognizes this needs live Network API data (not in model weights).
2. Tanzubot uses `a2a-delegate` -> `call_a2a_peer(alias="tanzusubagent", message="Follow your tanzu-network-release skill ... product cf --list-versions ...")`.
3. tanzusubagent receives `[A2A inbound]`, runs `a2a-worker` -> `run_skill_script` for `pivnet_release.py`.
4. tanzusubagent replies with `TOOL USED` / `RESULT` / `SUMMARY`.
5. Tanzubot summarizes for the user and optionally shows raw JSON.

**Success criteria:** JSON in `RESULT` contains `ok: true` and a `versions` list; user sees accurate slugs/versions.

**Failure modes:**

| Symptom | Likely cause | Mitigation |
| --- | --- | --- |
| TLS / certificate errors | Corporate inspection on cell egress | `--insecure` in lab only (skill doc) |
| Peer not found | `a2a-peers.yaml` missing or wrong URL | Copy `.example`, `cf push`, verify routes |
| Empty versions | Wrong product slug | User corrects slug; retry |

## Scenario 2 - CF space compliance audit (MCP skill)

**Actor:** Platform operator

**User prompt (tanzubot):**

> Audit org `demo` space `tanzubot` for memory and instance compliance.

**Expected flow:**

1. Tanzubot delegates to tanzusubagent with `cf-space-auditor` named in the message.
2. tanzusubagent runs audit via **Cloud Foundry MCP** (must be bound on the worker app for production; demo may use shared MCP CUPS).
3. Structured reply returns app-level violations (memory != 1024M Java / 512M non-Java, instances > 1, stale deploys).

**Success criteria:** Report lists only the three audit dimensions; no extra "health check" noise.

**Prerequisites:**

- CF MCP reachable from tanzusubagent (service binding or gateway).
- Org/space names exact.

**Demo prompt (direct on worker UI):**

> Audit org demo space tanzubot for compliance.

Same skill; no A2A hop (human -> tanzusubagent directly).

## Scenario 3 - SkillRunner smoke test (platform verify)

**Actor:** You, after `cf push` both apps

**User prompt (tanzubot):**

> Ask tanzusubagent to run the python-script-smoke skill and show me the raw output.

**Expected flow:** A2A delegate -> `run_skill_script` -> stdout `{"ok": true, ...}`.

**Success criteria:** `exit_code: 0` in SkillRunner response; Tanzubot debug UI shows MCP connected on both apps.

## Scenario 4 - Discover worker capabilities

**Actor:** Tanzubot before delegating an unfamiliar task

**User prompt (tanzubot):**

> What skills and tools does tanzusubagent support?

**Expected flow:** `call_a2a_peer` with a discovery message; worker lists skills from `.agents/skills` and MCP tools.

**Use when:** Adding new skills without updating Tanzubot `AGENTS.md` immediately.

## Scenario 5 - Operator bypass (worker UI only)

**Actor:** Engineer debugging the worker

**User prompt (on tanzusubagent chat):**

> Use tanzu-network-release to fetch metadata for elastic-runtime version 10.3.0.

**Expected flow:** Local `run_skill_script` only; **no** `call_a2a_peer` to tanzubot.

**Use when:** Isolating worker issues vs A2A routing.

## Scenario 6 - Delegation declined (orchestrator keeps the task)

**User prompt (tanzubot):**

> Explain when to use Diego cells vs Kubernetes nodes for batch workloads.

**Expected flow:** Tanzubot answers from expertise; **no** A2A call (no live platform query).

## Scenario 7 - Missing capability

**User prompt (tanzubot):**

> Run a BOSH errand on deployment `cf` via tanzusubagent.

**Expected flow (today):** tanzusubagent returns `NO TOOL AVAILABLE` (BOSH worker not implemented yet). Tanzubot explains gap and roadmap item.

**Future:** Add `tanzu-bosh-worker` peer or extend tanzusubagent skills.

## Conversation patterns (copy-paste)

**Tanzubot -> tanzusubagent (Network):**

```text
Follow your tanzu-network-release skill to list versions for product elastic-runtime and return the raw JSON without summarising.
```

**Tanzubot -> tanzusubagent (audit):**

```text
Follow your cf-space-auditor skill to audit org demo space tanzubot. Return the full audit report as RESULT without summarising.
```

**tanzusubagent -> tanzubot (success template):**

```text
TOOL USED: tanzu-network-release
RESULT:
{"ok":true,"product":"cf","versions":[...]}
SUMMARY:
Listed cf product versions from Tanzu Network API.
```

## Deploy checklist (demo foundation)

```bash
bash scripts/setup_mcp_binding.sh
bash scripts/sync_shared.sh
cp apps/tanzubot/a2a-peers.yaml.example apps/tanzubot/a2a-peers.yaml
cp apps/tanzusubagent/a2a-peers.yaml.example apps/tanzusubagent/a2a-peers.yaml
# Edit URLs if domain differs from apps.tp.penso.io
cf target -o demo -s tanzubot   # or your target space
cf push -f manifest.yml
```

**Naming note:** If a standalone `tanzubot` app already exists in the space, `cf push` updates that app when names collide. Plan route and binding changes accordingly.

## Verify A2A wiring

```bash
cf app tanzubot | grep routes
cf app tanzusubagent | grep routes
# Debug UI on tanzubot: peer tanzusubagent listed under A2A PEERS
# Prompt: "Ask tanzusubagent to run python-script-smoke and return raw output"
```

## Roadmap scenarios (not implemented)

| Scenario | Planned peer / skill |
| --- | --- |
| Hub portfolio assessment | `tanzu-hub-worker` or Hub MCP on worker |
| BOSH deployment health | `tanzu-bosh-worker` |
| Postgres / pgvector memory | Bind `tanzumem` on orchestrator only |
| Parallel audits (multi-space) | Multiple `call_a2a_peer` rounds or future workers |

See [ROADMAP.md](ROADMAP.md) for phase tracking.
