# Roadmap

## Done

- [x] Fork upstream to `0pens0/tanzusubagent`
- [x] Worker app `tanzusubagent` with skills and SkillRunner
- [x] Router app `tanzudispatcher` (renamed from example `tanzubot` to avoid CF name collision)
- [x] Worker replies to inbound caller alias (`tanzubot` or `tanzudispatcher`)
- [x] Production tanzubot mesh: peers + `a2a-delegate` skill (tanzubot repo)

## Next

- [ ] Deploy `tanzudispatcher` + `tanzusubagent` to demo foundation
- [ ] `cf restage tanzubot` with `a2a-peers.yaml`
- [ ] Bind CF MCP on `tanzusubagent` for remote audits, or use local MCP on tanzubot
- [ ] Network policies if apps span spaces

## Future workers

| Worker | Responsibility |
| --- | --- |
| `tanzu-bosh-worker` | BOSH MCP tasks |
| `tanzu-hub-worker` | Hub assessment |

Production **tanzubot** keeps memory, mail, and cross-domain synthesis.
