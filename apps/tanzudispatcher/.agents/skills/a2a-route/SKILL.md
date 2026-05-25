---
name: a2a-route
description: Parse inbound tasks from tanzubot, route to the named worker peer, return structured reply to tanzubot.
---

# When to use

Use for every **`[A2A inbound]`** from **tanzubot**.

# Parse inbound message

Expect a line like:

```text
Route to worker <worker-alias>: Follow skill <skill-id> to <action>. Return raw output without summarising.
```

Extract `<worker-alias>` and forward the skill instruction to that peer.

If no `Route to worker` pattern, default worker alias: **tanzusubagent** and forward the full message.

# Route

1. `list_a2a_peers` - confirm `<worker-alias>` exists.
2. If missing, reply to tanzubot: `NO WORKER AVAILABLE: unknown alias <name>`
3. `call_a2a_peer(alias=<worker-alias>, message="Follow your <skill-id> skill to ...")` using the skill/action from the inbound text.
4. On worker reply, `call_a2a_peer(alias="tanzubot", message=<worker reply unchanged>)`

# Multi-worker (future)

For multiple workers in one task, call each worker sequentially and combine RESULT sections before replying to tanzubot.
