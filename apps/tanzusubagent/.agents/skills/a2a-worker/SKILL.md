---
name: a2a-worker
description: Handle inbound A2A tasks from tanzubot or tanzudispatcher. Execute local skill or MCP, reply to the caller alias.
---

# When to use

Use when the conversation contains **`[A2A inbound]`** from any registered peer (typically **tanzubot** or **tanzudispatcher**).

# Steps

1. Read the inbound payload. Extract **`from`** (caller peer alias), the action, and any skill name in the message.
2. Choose execution path:
   - **Script skill** (`tanzu-network-release`, `python-script-smoke`): `run_skill_script`.
   - **MCP skill** (`cf-space-auditor`): bound MCP tools per that skill.
3. If no matching skill or tool, reply to caller:

```text
NO TOOL AVAILABLE: <one-line reason>
```

4. On success, `call_a2a_peer(alias=<from>, message=...)` using:

```text
TOOL USED: <skill-id or mcp-tool-name>
RESULT:
<raw stdout or MCP JSON>
SUMMARY:
<one sentence>
```

**Critical:** Use the inbound **`from`** alias for `call_a2a_peer`, not a hardcoded peer name.

# Rules

- Never delegate inbound A2A back to tanzubot unless the task explicitly requires production MCP only on tanzubot.
- Prefer raw output in `RESULT`.
- Do not invent API or audit data.
