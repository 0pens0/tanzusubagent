"""Register SkillRunner MCP tools on a shared FastMCP server."""

from __future__ import annotations

from fastmcp import FastMCP

from skill_runner.core import list_skill_scripts_json, run_skill_script_json


def register_skill_tools(mcp: FastMCP) -> None:
    @mcp.tool
    def list_skill_scripts() -> str:
        """List discoverable Python files under .agents/skills/*/scripts/*.py (policy B)."""
        return list_skill_scripts_json()

    @mcp.tool
    def run_skill_script(
        skill_id: str,
        script_relpath: str,
        args: list[str] | None = None,
        timeout_sec: int | None = None,
    ) -> str:
        """
        Run a Python file under .agents/skills/<skill_id>/scripts/ (path must stay inside scripts/).

        script_relpath is relative to the skill root (e.g. scripts/pivnet_release.py).
        args are passed after the script path. timeout_sec defaults from env SKILL_RUNNER_TIMEOUT.
        """
        return run_skill_script_json(skill_id, script_relpath, args, timeout_sec)
