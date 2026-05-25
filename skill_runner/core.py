"""Run Python under .agents/skills/<id>/scripts/ (policy B — any *.py under scripts/)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

APP_ROOT = Path(os.environ.get("APP_ROOT", "/home/vcap/app")).resolve()
PYTHON_BIN = os.environ.get("SKILL_RUNNER_PYTHON", "python3")
_MAX_OUT = int(os.environ.get("SKILL_RUNNER_MAX_OUTPUT", "12000"))
_DEFAULT_TIMEOUT = int(os.environ.get("SKILL_RUNNER_TIMEOUT", "120"))
_MAX_ARGS = int(os.environ.get("SKILL_RUNNER_MAX_ARGS", "64"))
_MAX_ARG_LEN = int(os.environ.get("SKILL_RUNNER_MAX_ARG_LEN", "4096"))

_SKILL_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")


def skills_root() -> Path:
    return (APP_ROOT / ".agents" / "skills").resolve()


def validate_skill_id(skill_id: str) -> None:
    if not skill_id or not _SKILL_ID_RE.match(skill_id):
        raise ValueError("invalid_skill_id")
    if ".." in skill_id or "/" in skill_id or "\\" in skill_id:
        raise ValueError("invalid_skill_id")


def resolve_script_in_scripts_dir(skill_id: str, script_relpath: str) -> tuple[Path, Path]:
    validate_skill_id(skill_id)
    rel = (script_relpath or "").strip().replace("\\", "/")
    if not rel or rel.startswith("/"):
        raise ValueError("invalid_script_relpath")
    if ".." in Path(rel).parts:
        raise ValueError("path_traversal")

    root = skills_root()
    if not root.is_dir():
        raise ValueError("missing_skills_root")

    skill_root = (root / skill_id).resolve()
    skill_root.relative_to(root)

    scripts_dir = (skill_root / "scripts").resolve()
    try:
        scripts_dir.relative_to(skill_root)
    except ValueError:
        raise ValueError("invalid_scripts_dir") from None

    candidate = (skill_root / rel).resolve()
    candidate.relative_to(scripts_dir)
    return candidate, skill_root


def run_skill_python(
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
    err = (proc.stderr or "")[-_MAX_OUT // 2:]
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout": out,
        "stderr": err,
        "duration_ms": elapsed_ms,
        "skill_cwd": str(skill_root),
        "script": str(script),
    }


def list_skill_scripts_json() -> str:
    root = skills_root()
    if not root.is_dir():
        return json.dumps({"ok": False, "error": "missing_skills_root", "path": str(root)})
    items: list[dict[str, str]] = []
    try:
        for skill_dir in sorted(root.iterdir()):
            if not skill_dir.is_dir():
                continue
            sid = skill_dir.name
            try:
                validate_skill_id(sid)
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


def run_skill_script_json(
    skill_id: str,
    script_relpath: str,
    args: list[str] | None = None,
    timeout_sec: int | None = None,
) -> str:
    to = int(timeout_sec) if timeout_sec is not None else _DEFAULT_TIMEOUT
    if to < 1 or to > 3600:
        return json.dumps({"ok": False, "error": "invalid_timeout", "min": 1, "max": 3600})

    extra = list(args or [])
    try:
        script, skill_root = resolve_script_in_scripts_dir(skill_id, script_relpath)
    except ValueError as e:
        return json.dumps({"ok": False, "error": str(e.args[0]) if e.args else "invalid_path"})

    try:
        APP_ROOT.resolve()
        skill_root.relative_to(APP_ROOT)
    except ValueError:
        return json.dumps({"ok": False, "error": "invalid_app_root"})

    return json.dumps(run_skill_python(script, skill_root, extra, to))
