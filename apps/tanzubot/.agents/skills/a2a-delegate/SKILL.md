---
name: a2a-delegate
description: Delegate tasks to the tanzusubagent A2A peer. Use when live script output or worker-only skills are required.
---

# When to use

Use when the user's request matches a skill on **tanzusubagent** (see `list_a2a_peers`, or ask the peer what skills it has).

Typical triggers:

- Tanzu Network product versions or release metadata
- CF space **audit** / compliance against memory and instance standards
- Smoke-test the worker's Python / SkillRunner stack

# Steps

1. Confirm peer **`tanzusubagent`** is listed (`list_a2a_peers`).
2. Call `call_a2a_peer` with a message that names the **skill id** and asks for **raw output**:

```text
Follow your <skill-id> skill to <specific action> and return the raw output without summarising.
```

3. Parse the structured reply (`TOOL USED`, `RESULT`, `SUMMARY`).
4. Present findings to the user in plain language; keep raw JSON in a fenced block if useful.

# Do not use

- General Tanzu architecture questions you can answer without live data.
- Tasks you already completed in the same turn.
- Retries after `NO TOOL AVAILABLE` for the same skill.
