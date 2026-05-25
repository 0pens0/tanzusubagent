"""
Native A2A + SkillRunner MCP sidecar.

HTTP MCP on 127.0.0.1:<A2A_MCP_PORT>. Uses direct HTTP to peer agents via a2a-peers.yaml.
No message broker required.
"""

from __future__ import annotations

import json
import os
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

from a2a_runner.client import send_to_peer
from a2a_runner.peers import get_peer_url, load_peers
from skill_runner import register_skill_tools

mcp = FastMCP("SkillRunner")
register_skill_tools(mcp)


def _agent_id() -> str:
    return os.environ.get("AGENT_ID", "unknown-agent").strip()


@mcp.tool
def ping() -> str:
    """Return JSON proving the SkillRunner MCP sidecar is reachable. Lists peers from a2a-peers.yaml."""
    peers = load_peers()
    return json.dumps(
        {
            "ok": True,
            "service": "skill-runner-mcp",
            "agent_id": _agent_id(),
            "capabilities": ["a2a_native", "skill_runner"],
            "peers": [p["alias"] for p in peers],
        }
    )


@mcp.tool
def a2a_list_peers() -> str:
    """List all peers from a2a-peers.yaml (alias + URL)."""
    peers = load_peers()
    return json.dumps(
        {
            "ok": True,
            "peers": peers,
            "count": len(peers),
            "hint": "Use a2a_send(peer_alias=...) to post a task to a peer.",
        }
    )


@mcp.tool
def a2a_send(
    peer_alias: str,
    payload: dict[str, Any] | str | None = None,
    message_type: str = "task_request",
    timeout_sec: int | None = None,
) -> str:
    """
    POST a task payload to a peer agent's native A2A endpoint (from a2a-peers.yaml).

    peer_alias: alias defined in a2a-peers.yaml.
    payload: dict or JSON string. Defaults to empty object.
    message_type: defaults to task_request.
    timeout_sec: HTTP timeout for the POST (default from A2A_SEND_TIMEOUT_SEC env).
    """
    url = get_peer_url(peer_alias)
    if url is None:
        peers = load_peers()
        aliases = [p["alias"] for p in peers]
        return json.dumps(
            {
                "ok": False,
                "error": "peer_not_found",
                "alias": peer_alias,
                "available_aliases": aliases,
            }
        )

    body: dict[str, Any]
    if payload is None:
        body = {}
    elif isinstance(payload, str):
        try:
            parsed = json.loads(payload.strip() or "{}")
            if not isinstance(parsed, dict):
                return json.dumps({"ok": False, "error": "payload_must_be_object"})
            body = parsed
        except json.JSONDecodeError as e:
            return json.dumps({"ok": False, "error": "invalid_json_payload", "detail": str(e)})
    else:
        body = payload

    to = int(timeout_sec) if timeout_sec is not None else None
    result = send_to_peer(url, body, message_type=message_type, timeout_sec=to)
    return json.dumps(result)


def _create_hybrid_app() -> FastAPI:
    mcp_app = mcp.http_app(path="/")
    app = FastAPI(
        title="SkillRunner MCP",
        description="Native A2A HTTP + SkillRunner; no message broker",
        version="1.0.0",
        lifespan=mcp_app.lifespan,
    )
    app.mount("/mcp", mcp_app)

    @app.get("/")
    async def root():
        peers = load_peers()
        return {
            "name": "skill-runner-mcp",
            "agent_id": _agent_id(),
            "transport": "native_a2a_http",
            "capabilities": ["a2a_native", "skill_runner"],
            "peers": [p["alias"] for p in peers],
            "endpoints": {"/": "info", "/health": "liveness", "/mcp": "MCP HTTP"},
        }

    @app.get("/health")
    async def health():
        return JSONResponse(content={"status": "ok", "service": "skill-runner-mcp", "agent_id": _agent_id()})

    return app


app = _create_hybrid_app()


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("A2A_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("A2A_MCP_PORT", os.environ.get("SKILL_RUNNER_MCP_PORT", "8765")))
    uvicorn.run(app, host=host, port=port, log_level="info")
