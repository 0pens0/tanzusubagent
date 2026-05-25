---
name: python-script-smoke
description: Verify that Python skill scripts execute correctly via the SkillRunner MCP sidecar.
---

# When to use

Use to verify Python runtime and the SkillRunner MCP sidecar are functional.

# Available scripts

- **`scripts/smoke_check.py`** — prints `{"ok": true, "python": "3.x.y", "message": "smoke ok"}` and exits 0.

# CLI

```bash
python3 scripts/smoke_check.py
```

# SkillRunner MCP

```json
{
  "skill_id": "python-script-smoke",
  "script_relpath": "scripts/smoke_check.py",
  "args": []
}
```

Expect `stdout` to contain `{"ok": true, ...}` and `exit_code: 0`.
