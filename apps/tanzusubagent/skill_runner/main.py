"""
Skill-runner MCP sidecar: HTTP MCP on 127.0.0.1 + run Python under .agents/skills/<id>/scripts/.

Policy A: any script file under a skill's scripts/ directory may be run (strict path checks, no ..).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

mcp = FastMCP("SkillRunner")

APP_ROOT = Path(os.environ.get("APP_ROOT", "/home/vcap/app")).resolve()
PYTHON_BIN = os.environ.get("SKILL_RUNNER_PYTHON", "python3")
_MAX_OUT = int(os.environ.get("SKILL_RUNNER_MAX_OUTPUT", "12000"))
_DEFAULT_TIMEOUT = int(os.environ.get("SKILL_RUNNER_TIMEOUT", "120"))
_MAX_ARGS = int(os.environ.get("SKILL_RUNNER_MAX_ARGS", "64"))
_MAX_ARG_LEN = int(os.environ.get("SKILL_RUNNER_MAX_ARG_LEN", "4096"))

_SKILL_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")


def _skills_root() -> Path:
    return (APP_ROOT / ".agents" / "skills").resolve()


def _validate_skill_id(skill_id: str) -> None:
    if not skill_id or not _SKILL_ID_RE.match(skill_id):
        raise ValueError("invalid_skill_id")
    if ".." in skill_id or "/" in skill_id or "\\" in skill_id:
        raise ValueError("invalid_skill_id")


def _resolve_script_in_scripts_dir(skill_id: str, script_relpath: str) -> tuple[Path, Path]:
    """
    Return (script_path, skill_root). script_path must lie under .../skills/<id>/scripts/.
    """
    _validate_skill_id(skill_id)
    rel = (script_relpath or "").strip().replace("\\", "/")
    if not rel or rel.startswith("/"):
        raise ValueError("invalid_script_relpath")
    if ".." in Path(rel).parts:
        raise ValueError("path_traversal")

    skills_root = _skills_root()
    if not skills_root.is_dir():
        raise ValueError("missing_skills_root")

    skill_root = (skills_root / skill_id).resolve()
    skill_root.relative_to(skills_root)

    scripts_dir = (skill_root / "scripts").resolve()
    try:
        scripts_dir.relative_to(skill_root)
    except ValueError:
        raise ValueError("invalid_scripts_dir") from None

    candidate = (skill_root / rel).resolve()
    candidate.relative_to(scripts_dir)

    return candidate, skill_root


def _run_skill_python(
    script: Path,
    skill_root: Path,
    args: list[str],
    timeout_sec: int,
) -> dict:
    if not script.is_file():
        return {"ok": False, "error": "missing_script", "path": str(script)}
    if len(args) > _MAX_ARGS:
        return {"ok": False, "error": "too_many_args", "max": _MAX_ARGS}
    for a in args:
        if len(a) > _MAX_ARG_LEN:
            return {"ok": False, "error": "arg_too_long", "max_len": _MAX_ARG_LEN}

    started = time.perf_counter()
    try:
        proc = subprocess.run(
            [PYTHON_BIN, str(script), *args],
            cwd=str(skill_root),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "timeout_sec": timeout_sec}

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    out = (proc.stdout or "")[-_MAX_OUT:]
    err = (proc.stderr or "")[-_MAX_OUT // 2 :]
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout": out,
        "stderr": err,
        "duration_ms": elapsed_ms,
        "skill_cwd": str(skill_root),
        "script": str(script),
    }


@mcp.tool
def ping() -> str:
    """Return JSON proving the SkillRunner MCP sidecar is reachable."""
    return json.dumps({"ok": True, "service": "skill-runner-mcp"})


@mcp.tool
def list_skill_scripts() -> str:
    """List discoverable Python files under .agents/skills/*/scripts/*.py (policy A)."""
    root = _skills_root()
    if not root.is_dir():
        return json.dumps({"ok": False, "error": "missing_skills_root", "path": str(root)})
    items: list[dict[str, str]] = []
    try:
        for skill_dir in sorted(root.iterdir()):
            if not skill_dir.is_dir():
                continue
            sid = skill_dir.name
            try:
                _validate_skill_id(sid)
            except ValueError:
                continue
            scripts = skill_dir / "scripts"
            if not scripts.is_dir():
                continue
            for py in sorted(scripts.rglob("*.py")):
                try:
                    rel = py.relative_to(skill_dir).as_posix()
                except ValueError:
                    continue
                items.append({"skill_id": sid, "script_relpath": rel})
    except OSError as e:
        return json.dumps({"ok": False, "error": "scan_failed", "detail": str(e)})
    return json.dumps({"ok": True, "scripts": items, "count": len(items)})


@mcp.tool
def run_skill_script(
    skill_id: str,
    script_relpath: str,
    args: list[str] | None = None,
    timeout_sec: int | None = None,
) -> str:
    """
    Run a Python file under .agents/skills/<skill_id>/scripts/ (path must stay inside scripts/).

    script_relpath is relative to the skill root (e.g. scripts/smoke_check.py).
    args are passed after the script path. timeout_sec defaults from env SKILL_RUNNER_TIMEOUT.
    """
    to = int(timeout_sec) if timeout_sec is not None else _DEFAULT_TIMEOUT
    if to < 1 or to > 3600:
        return json.dumps({"ok": False, "error": "invalid_timeout", "min": 1, "max": 3600})

    extra = list(args or [])
    try:
        script, skill_root = _resolve_script_in_scripts_dir(skill_id, script_relpath)
    except ValueError as e:
        return json.dumps({"ok": False, "error": str(e.args[0]) if e.args else "invalid_path"})

    try:
        APP_ROOT.resolve()
        skill_root.relative_to(APP_ROOT)
    except ValueError:
        return json.dumps({"ok": False, "error": "invalid_app_root"})

    result = _run_skill_python(script, skill_root, extra, to)
    return json.dumps(result)


@mcp.tool
def run_smoke_skill() -> str:
    """Run python-script-smoke/scripts/smoke_check.py (convenience wrapper)."""
    return run_skill_script("python-script-smoke", "scripts/smoke_check.py", None, None)


def _create_hybrid_app() -> FastAPI:
    mcp_app = mcp.http_app(path="/")
    app = FastAPI(
        title="SkillRunner MCP",
        description="Localhost MCP; policy A runs scripts under .agents/skills/<id>/scripts/",
        version="0.2.0",
        lifespan=mcp_app.lifespan,
    )
    app.mount("/mcp", mcp_app)

    @app.get("/")
    async def root():
        return {
            "name": "skill-runner-mcp",
            "policy": "A",
            "endpoints": {"/": "info", "/health": "liveness", "/mcp": "MCP HTTP"},
        }

    @app.get("/health")
    async def health():
        return JSONResponse(content={"status": "ok", "service": "skill-runner-mcp"})

    return app


app = _create_hybrid_app()


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("SKILL_RUNNER_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("SKILL_RUNNER_MCP_PORT", "8765"))
    uvicorn.run(app, host=host, port=port, log_level="info")
