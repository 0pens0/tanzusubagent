# tanzusubagent

Fork of [cf-agent-a2a-skill-script](https://github.com/yannicklevederpvtl/cf-agent-a2a-skill-script) for the **Tanzubot A2A mesh** on Tanzu Platform Elastic Application Runtime.

Three-app pattern:

| CF app | Role |
| --- | --- |
| **tanzubot** (production, [tanzubot repo](https://github.com/0pens0/tanzubot)) | User-facing PSE; MCP bindings; A2A to dispatcher and worker |
| **tanzudispatcher** (this repo) | A2A router; forwards to tanzusubagent |
| **tanzusubagent** (this repo) | Worker; SkillRunner scripts + optional MCP |

```
User -> tanzubot ->|direct|-> tanzusubagent
              \-> tanzudispatcher -> tanzusubagent
```

Native A2A: `list_a2a_peers`, `call_a2a_peer`. SkillRunner sidecar on dispatcher and worker.

## Deploy (this repo only)

```bash
bash scripts/setup_mcp_binding.sh
bash scripts/sync_shared.sh
cp apps/tanzudispatcher/a2a-peers.yaml.example apps/tanzudispatcher/a2a-peers.yaml
cp apps/tanzusubagent/a2a-peers.yaml.example apps/tanzusubagent/a2a-peers.yaml
cf push -f manifest.yml
```

Does **not** push production `tanzubot` (separate repo; `cf restage` after adding `a2a-peers.yaml`).

## Docs

- [docs/USE_CASES_AND_SCENARIOS.md](docs/USE_CASES_AND_SCENARIOS.md)
- [docs/ROADMAP.md](docs/ROADMAP.md)

## Related

- https://github.com/0pens0/tanzubot
- https://github.com/0pens0/tanzusubagent
