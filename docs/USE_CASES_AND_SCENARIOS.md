# Use cases and scenarios

## Mesh roles

| App | Entry | A2A peers |
| --- | --- | --- |
| `tanzubot` | Human users | `tanzudispatcher`, `tanzusubagent` |
| `tanzudispatcher` | A2A from tanzubot only | `tanzusubagent` |
| `tanzusubagent` | A2A from tanzubot or tanzudispatcher; optional direct UI | `tanzudispatcher`, `tanzubot` |

## Scenario 1 - Direct: Tanzu Network (one hop)

**User on tanzubot:**

> List latest `cf` product versions on Tanzu Network.

**Flow:** tanzubot -> `call_a2a_peer(tanzusubagent, ...)` -> `tanzu-network-release` script -> reply to `tanzubot`.

## Scenario 2 - Routed: same task via dispatcher

**User on tanzubot:**

> Ask tanzudispatcher to have tanzusubagent list `cf` product versions; return raw JSON.

**Flow:** tanzubot -> `tanzudispatcher` -> `tanzusubagent` -> reply to `tanzudispatcher` -> reply to `tanzubot`.

## Scenario 3 - CF audit via local MCP on tanzubot

**User on tanzubot:**

> Audit org demo space tanzubot for compliance.

**Flow:** tanzubot uses **local** `tanzubot-tanzu` MCP (no A2A) unless CF MCP is bound only on tanzusubagent.

## Scenario 4 - CF audit via worker

**User on tanzubot:**

> Use tanzusubagent to audit org demo space tanzubot per cf-space-auditor.

**Flow:** tanzubot -> tanzusubagent (direct or via dispatcher); worker needs CF MCP binding.

## Scenario 5 - Smoke test

**User on tanzubot:**

> Ask tanzusubagent to run python-script-smoke and show raw output.

## Scenario 6 - Dispatcher-only routing

**Inbound on tanzudispatcher** from tanzubot with skill named in message; dispatcher forwards unchanged to tanzusubagent; passes worker reply back to tanzubot.

## Scenario 7 - Local expertise (no A2A)

**User on tanzubot:** architecture / best-practice questions -> tanzubot answers; no peer call.

## Deploy checklist

**tanzusubagent repo:**

```bash
cf target -o demo -s tanzubot
bash scripts/setup_mcp_binding.sh
bash scripts/sync_shared.sh
cp apps/tanzudispatcher/a2a-peers.yaml.example apps/tanzudispatcher/a2a-peers.yaml
cp apps/tanzusubagent/a2a-peers.yaml.example apps/tanzusubagent/a2a-peers.yaml
cf push -f manifest.yml
```

**tanzubot repo:**

```bash
cp a2a-peers.yaml.example a2a-peers.yaml
cf restage tanzubot
```

## Verify

```bash
cf app tanzubot | grep routes
cf app tanzudispatcher | grep routes
cf app tanzusubagent | grep routes
```

On tanzubot debug UI: peers `tanzudispatcher` and `tanzusubagent` listed.

Prompts:

- Direct smoke: "Ask tanzusubagent to run python-script-smoke and return raw output."
- Routed: "Send tanzudispatcher a request to run python-script-smoke on tanzusubagent and return the raw output."
