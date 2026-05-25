# Tanzubot subagent roadmap

## Done

- [x] Fork upstream to `0pens0/tanzusubagent`
- [x] Rename apps: `tanzubot` (orchestrator), `tanzusubagent` (worker)
- [x] Peer aliases `tanzubot` / `tanzusubagent` in `a2a-peers.yaml.example`
- [x] Skills: `a2a-delegate`, `a2a-worker`, `cf-space-auditor` on worker
- [x] [USE_CASES_AND_SCENARIOS.md](USE_CASES_AND_SCENARIOS.md)

## Next

- [ ] Deploy pair to `demo` foundation; validate scenarios 1-3
- [ ] Bind Cloud Foundry MCP on `tanzusubagent` for live `cf-space-auditor` audits
- [ ] Align production `tanzubot` AGENTS.md in [tanzubot repo](https://github.com/0pens0/tanzubot) with orchestrator delegation section
- [ ] Optional: split worker into domain-specific apps (`tanzu-cf-worker`, `tanzu-bosh-worker`) when tool surface grows

## Future workers

| Worker | Responsibility | Source |
| --- | --- | --- |
| `tanzu-bosh-worker` | Deployments, instances, errands | `tanzubot-bosh` MCP |
| `tanzu-hub-worker` | Hub assessment (read-only) | `tanzu-assess` skill |
| `tanzu-data-worker` | Postgres / vectors | `tanzubot-postgres` MCP |

Orchestrator retains memory (`tanzumem`), mail, and cross-domain answers.

## Open questions

1. One space (`demo/tanzubot`) vs dedicated `tanzubot-workers` space for network policies?
2. Shared vs per-app genai service instances?
3. Replace existing standalone `tanzubot` droplet with this manifest push, or deploy workers only first?
