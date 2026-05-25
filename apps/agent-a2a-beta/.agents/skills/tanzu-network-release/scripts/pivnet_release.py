#!/usr/bin/env python3
"""
Non-interactive Tanzu Network (Broadcom) public API helper — parity with tanzu_api bash flows.

Uses GET only (no token in requests). Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from typing import Any

BASE = "https://network.tanzu.vmware.com/"
USER_AGENT = "pivnet_release.py/0.1 (cf-agent-skill-script demo; +https://github.com/)"
# Matches tanzu_api override for p-concourse version picker.
CONCOURSE_OVERRIDE_VERSIONS = ("7.9.1+LTS-T", "7.11.2+LTS-T")


def _version_sort_key(version: str) -> list[Any]:
    """Loose version-ish sort similar to sort -V for dotted numeric segments."""

    def part_key(p: str) -> Any:
        return int(p) if p.isdigit() else p.lower()

    return [part_key(x) for x in re.split(r"([0-9]+)", version) if x]


def _ssl_context(insecure: bool) -> ssl.SSLContext:
    if insecure:
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def _fetch_json(path: str, timeout: int, *, insecure: bool) -> Any:
    url = path if path.startswith("http") else f"{BASE.rstrip('/')}/{path.lstrip('/')}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    ctx = _ssl_context(insecure)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:8000]
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "error": "http_error",
                    "status": e.code,
                    "url": url,
                    "body_preview": body,
                }
            )
        ) from e
    except urllib.error.URLError as e:
        raise SystemExit(
            json.dumps({"ok": False, "error": "url_error", "reason": str(e.reason), "url": url})
        ) from e

    if not raw.strip():
        raise SystemExit(json.dumps({"ok": False, "error": "empty_response", "url": url}))
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(
            json.dumps({"ok": False, "error": "invalid_json", "url": url, "detail": str(e)})
        ) from e


def _object_key_display(aws_object_key: str) -> str:
    """Match tanzu_api: cut -d '/' -f2 on aws_object_key."""
    parts = aws_object_key.split("/")
    if len(parts) >= 2:
        return parts[1]
    return parts[0] if parts else aws_object_key


def cmd_list_versions(product: str, timeout: int, *, insecure: bool) -> dict[str, Any]:
    if product == "p-concourse":
        versions = list(CONCOURSE_OVERRIDE_VERSIONS)
    else:
        data = _fetch_json(f"api/v2/products/{product}/releases", timeout, insecure=insecure)
        releases = data.get("releases") if isinstance(data, dict) else None
        if not isinstance(releases, list):
            return {"ok": False, "error": "unexpected_releases_shape", "product": product}
        versions = [r.get("version") for r in releases if isinstance(r, dict) and r.get("version")]
        versions = [v for v in versions if isinstance(v, str)]
        versions = sorted(set(versions), key=_version_sort_key)

    return {"ok": True, "product": product, "versions": versions, "count": len(versions)}


def cmd_release(product: str, version: str, timeout: int, *, insecure: bool) -> dict[str, Any]:
    data = _fetch_json(f"api/v2/products/{product}/releases", timeout, insecure=insecure)
    releases = data.get("releases") if isinstance(data, dict) else None
    if not isinstance(releases, list):
        return {"ok": False, "error": "unexpected_releases_shape", "product": product}

    chosen: dict[str, Any] | None = None
    for r in releases:
        if isinstance(r, dict) and r.get("version") == version:
            chosen = r
            break

    if chosen is None:
        return {
            "ok": False,
            "error": "version_not_found",
            "product": product,
            "version": version,
        }

    release_id = chosen.get("id")
    if release_id is None:
        return {"ok": False, "error": "missing_release_id", "product": product, "version": version}

    meta = {
        "description": chosen.get("description"),
        "became_ga_at": chosen.get("became_ga_at"),
        "release_date": chosen.get("release_date"),
        "end_of_support_date": chosen.get("end_of_support_date"),
        "release_notes_url": chosen.get("release_notes_url"),
        "id": release_id,
        "version": version,
    }

    files_data = _fetch_json(
        f"api/v2/products/{product}/releases/{release_id}/product_files",
        timeout,
        insecure=insecure,
    )
    pfiles = files_data.get("product_files") if isinstance(files_data, dict) else None
    file_names: list[str] = []
    if isinstance(pfiles, list):
        for pf in pfiles:
            if isinstance(pf, dict) and pf.get("aws_object_key"):
                file_names.append(_object_key_display(str(pf["aws_object_key"])))

    deps_data = _fetch_json(
        f"api/v2/products/{product}/releases/{release_id}/dependency_specifiers",
        timeout,
        insecure=insecure,
    )
    dspec = deps_data.get("dependency_specifiers") if isinstance(deps_data, dict) else None
    dependencies: list[str] = []
    if isinstance(dspec, list):
        for d in dspec:
            if not isinstance(d, dict):
                continue
            prod = d.get("product") or {}
            name = prod.get("name") if isinstance(prod, dict) else None
            spec = d.get("specifier")
            if name and spec:
                dependencies.append(f"{name}: {spec}")
            elif spec:
                dependencies.append(str(spec))

    om_hint = (
        f"om download-product --pivnet-api-token $PIVNET_API_TOKEN "
        f"--pivnet-product-slug {product} --product-version {version} "
        f"--file-glob <FILE_FROM_product_files> --output-directory ./"
    )

    return {
        "ok": True,
        "product": product,
        "version": version,
        "release": meta,
        "product_files": file_names,
        "dependency_specifiers": dependencies,
        "om_download_hint": om_hint,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Query Tanzu Network API for product releases (non-interactive, JSON stdout).",
    )
    parser.add_argument("--product", required=True, help="Pivnet / TN slug (e.g. elastic-runtime, cf).")
    mx = parser.add_mutually_exclusive_group(required=True)
    mx.add_argument(
        "--list-versions",
        action="store_true",
        help="List known release versions for the product (sorted).",
    )
    mx.add_argument("--version", help="Exact release version string to fetch metadata for.")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout seconds (default 60).")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification (lab / corporate TLS inspection only).",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args()

    if args.timeout < 5 or args.timeout > 600:
        print(json.dumps({"ok": False, "error": "invalid_timeout"}), file=sys.stderr)
        return 2

    if args.list_versions:
        out = cmd_list_versions(args.product, args.timeout, insecure=args.insecure)
    else:
        out = cmd_release(args.product, args.version, args.timeout, insecure=args.insecure)

    if args.pretty:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(json.dumps(out, separators=(",", ":"), sort_keys=True))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
