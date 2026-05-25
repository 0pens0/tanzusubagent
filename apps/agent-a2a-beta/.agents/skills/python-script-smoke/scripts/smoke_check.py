#!/usr/bin/env python3
"""Smoke check: print JSON and exit 0 if Python is working."""
import json
import platform
import sys

print(
    json.dumps(
        {
            "ok": True,
            "python": platform.python_version(),
            "executable": sys.executable,
            "message": "smoke ok",
        }
    )
)
