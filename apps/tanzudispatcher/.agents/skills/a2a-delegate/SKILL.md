---
name: a2a-delegate
description: Forward inbound A2A tasks from tanzubot to tanzusubagent. Router skill for tanzudispatcher only.
---

# When to use

Use when **`[A2A inbound]`** is from peer **tanzubot** and the task requires a skill on **tanzusubagent**.

# Steps

1. Confirm **`tanzusubagent`** is in `list_a2a_peers`.
2. `call_a2a_peer(alias="tanzusubagent", message="Follow your <skill-id> skill to ... raw output without summarising.")`
3. On worker reply, `call_a2a_peer(alias="tanzubot", message=<worker reply unchanged>)`

# Do not use

- End-user chat (humans use production tanzubot).
- Tasks you can answer without the worker.
