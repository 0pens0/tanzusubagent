# tanzusubagent

A2A **dispatcher** and **worker** agents for the [Tanzubot](https://github.com/0pens0/tanzubot) hub mesh on Tanzu Platform Elastic Application Runtime.

Forked from [cf-agent-a2a-skill-script](https://github.com/yannicklevederpvtl/cf-agent-a2a-skill-script).

## Apps in this repo

| CF app | Path | Role |
| --- | --- | --- |
| `tanzudispatcher` | `apps/tanzudispatcher/` | Hub router; only peer of production `tanzubot` |
| `tanzusubagent` | `apps/tanzusubagent/` | Worker (SkillRunner + skills) |

Deploy together with **`tanzubot`** and **`tanzubot-mesh`** from the tanzubot repo into the **same CF space** (default `demo/tanzubot`).

Full architecture and deploy steps: **[tanzubot README](https://github.com/0pens0/tanzubot/blob/main/README.md)**.

## Quick deploy

```bash
cf target -o demo -s tanzubot
bash scripts/setup_mcp_binding.sh    # once per space
cp apps/tanzudispatcher/a2a-peers.yaml.example apps/tanzudispatcher/a2a-peers.yaml
cp apps/tanzusubagent/a2a-peers.yaml.example apps/tanzusubagent/a2a-peers.yaml
cf push -f manifest.yml
```

From tanzubot repo (all four apps):

```bash
bash scripts/deploy_all.sh
```

## Docs

- [docs/USE_CASES_AND_SCENARIOS.md](docs/USE_CASES_AND_SCENARIOS.md)
- [docs/ROADMAP.md](docs/ROADMAP.md)
