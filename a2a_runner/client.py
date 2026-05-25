"""HTTP client for posting to a peer agent's native A2A endpoint."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx


def _agent_id() -> str:
    return os.environ.get("AGENT_ID", "unknown-agent").strip()


def _peer_path() -> str:
    """Endpoint path on the peer (env A2A_PEER_PATH, default /api/chat)."""
    return os.environ.get("A2A_PEER_PATH", "/api/chat").strip()


def _default_timeout() -> float:
    return float(os.environ.get("A2A_SEND_TIMEOUT_SEC", "120"))


def _format_message_text(envelope: dict[str, Any]) -> str:
    """Format the envelope as a user-visible text for the peer agent's /api/chat."""
    payload = envelope.get("payload", {})
    return (
        "[A2A inbound]\n"
        f"From: {envelope.get('from', 'unknown')}\n"
        f"correlation_id: {envelope.get('correlation_id', '')}\n"
        f"message_type: {envelope.get('message_type', '')}\n\n"
        "Payload (JSON):\n"
        f"{json.dumps(payload, indent=2)}\n\n"
        "Instructions:\n"
        "- This message was delivered by the A2A sidecar. Do NOT call a2a_send recursively.\n"
        "- Follow the a2a-worker skill for inbound tasks.\n"
        "- Summarize briefly when done."
    )


def _build_chat_body(envelope: dict[str, Any]) -> dict[str, Any]:
    """Build a /api/chat request body from an A2A envelope."""
    from_agent = str(envelope.get("from") or "unknown")
    cid = str(envelope.get("correlation_id") or envelope.get("id") or "unknown")
    return {
        "trigger": "submit-message",
        "id": f"a2a-inbound-{from_agent}",
        "messages": [
            {
                "id": f"a2a-{cid}",
                "role": "user",
                "parts": [{"type": "text", "text": _format_message_text(envelope)}],
            }
        ],
    }


def send_to_peer(
    peer_url: str,
    payload: dict[str, Any],
    *,
    message_type: str = "task_request",
    correlation_id: str | None = None,
    timeout_sec: float | None = None,
) -> dict[str, Any]:
    """
    POST to <peer_url><A2A_PEER_PATH> with the given payload.

    Returns dict with ok, status_code, correlation_id, and response body.
    """
    cid = correlation_id or str(uuid4())
    envelope: dict[str, Any] = {
        "from": _agent_id(),
        "message_type": message_type,
        "payload": payload,
        "correlation_id": cid,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    path = _peer_path()
    url = f"{peer_url.rstrip('/')}{path}"
    timeout = timeout_sec if timeout_sec is not None else _default_timeout()

    headers = {"Content-Type": "application/json", "Accept": "application/json,text/event-stream"}

    # For /api/chat we POST the chat wrapper; for other paths post the raw envelope.
    if path.rstrip("/") == "/api/chat":
        body = _build_chat_body(envelope)
    else:
        body = envelope

    try:
        with httpx.Client(
            timeout=httpx.Timeout(connect=10.0, read=timeout, write=30.0, pool=10.0)
        ) as client:
            response = client.post(url, json=body, headers=headers)
            ok = response.status_code < 400
            try:
                resp_body = response.json()
            except Exception:
                resp_body = {"raw": response.text[:4000]}
            return {
                "ok": ok,
                "status_code": response.status_code,
                "correlation_id": cid,
                "peer_url": peer_url,
                "endpoint": url,
                "response": resp_body,
            }
    except httpx.TimeoutException:
        return {"ok": False, "error": "timeout", "correlation_id": cid, "peer_url": peer_url}
    except Exception as e:
        return {
            "ok": False,
            "error": "send_failed",
            "detail": str(e),
            "correlation_id": cid,
            "peer_url": peer_url,
        }
