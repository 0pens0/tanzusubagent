"""Load and validate the a2a-peers.yaml peer registry."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

_ALIAS_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")
_PEERS_FILENAME = "a2a-peers.yaml"


def _peers_path() -> Path:
    root = Path(os.environ.get("APP_ROOT", "/home/vcap/app"))
    return root / _PEERS_FILENAME


def _validate_alias(alias: str) -> None:
    if not alias or not _ALIAS_RE.match(alias):
        raise ValueError(f"invalid_peer_alias: {alias!r}")


def load_peers(path: Path | None = None) -> list[dict[str, str]]:
    """
    Return list of {alias, url} from a2a-peers.yaml.
    Returns [] when the file is absent (not an error).
    """
    p = path or _peers_path()
    if not p.is_file():
        return []
    raw = p.read_text(encoding="utf-8")
    data: Any = yaml.safe_load(raw)
    if not isinstance(data, dict):
        return []
    entries = data.get("peers")
    if not isinstance(entries, list):
        return []
    result: list[dict[str, str]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        alias = str(entry.get("alias") or "").strip()
        url = str(entry.get("url") or "").strip()
        if not alias or not url:
            continue
        try:
            _validate_alias(alias)
        except ValueError:
            continue
        if not url.startswith(("http://", "https://")):
            continue
        result.append({"alias": alias, "url": url.rstrip("/")})
    return result


def get_peer_url(alias: str, path: Path | None = None) -> str | None:
    """Return the URL for the given alias, or None if not found."""
    for peer in load_peers(path):
        if peer["alias"] == alias:
            return peer["url"]
    return None
