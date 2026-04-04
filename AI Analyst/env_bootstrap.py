"""
Load ``AI Analyst/.env`` into the process environment before any Anthropic calls.

Usage: ``import env_bootstrap`` or ``env_bootstrap.load_dotenv_if_present()`` once at startup.
Does not override variables already set in the shell (export ANTHROPIC_API_KEY wins).
"""

from __future__ import annotations

import os
from pathlib import Path

_AI_ANALYST_ROOT = Path(__file__).resolve().parent
_ENV_FILE = _AI_ANALYST_ROOT / ".env"


def load_dotenv_if_present() -> None:
    if not _ENV_FILE.is_file():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(_ENV_FILE, override=False)
    except ImportError:
        # Minimal fallback if python-dotenv is not installed
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
