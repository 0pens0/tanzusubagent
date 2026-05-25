---
name: a2a-worker
description: Handle inbound A2A tasks from tanzubot. Map the request to a local skill or MCP tool, execute, and reply with structured output.
---

# When to use

Use when the conversation contains **`[A2A inbound]`** from peer alias **tanzubot** (or any registered peer).

# Steps

1. Read the inbound payload. Extract the requested action and any skill name mentioned in the message text.
2. Choose execution path:
   - **Script skill** (e.g. `tanzu-network-release`, `python-script-smoke`): `run_skill_script` with the correct `skill_id` and `script_relpath`.
   - **MCP skill** (e.g. `cf-space-auditor`): use bound MCP tools per that skill's workflow.
3. If no matching skill or tool exists, reply:

```text
NO TOOL AVAILABLE: <one-line reason>
```

4. On success, reply via `call_a2a_peer(alias="tanzubot", message=...)` using this shape:

```text
TOOL USED: <skill-id or mcp-tool-name>
RESULT:
<raw stdout or MCP JSON>
SUMMARY:
<one sentence>
```

# Rules

- Never delegate inbound A2A work back to tanzubot unless the task explicitly requires orchestrator-only context.
- Prefer raw tool/script output in `RESULT`; keep `SUMMARY` to one sentence.
- Do not invent API or audit data.
