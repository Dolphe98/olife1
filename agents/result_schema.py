"""Helpers for AgentJob.result JSON payloads (Phase 3D-1)."""

from __future__ import annotations

import json
from typing import Any


BACKEND_BUILDER_RESULT_KEYS = (
    "ok",
    "pr_url",
    "branch",
    "diff_summary",
    "files_changed",
    "files_blocked_attempted",
    "django_check",
    "reason",
)


def empty_backend_builder_result(**overrides: Any) -> dict[str, Any]:
    """Canonical BackendBuilder result shape for AgentJob.result."""
    base: dict[str, Any] = {
        "ok": False,
        "pr_url": None,
        "branch": None,
        "diff_summary": {"files": [], "lines_changed": 0, "summary": ""},
        "files_changed": [],
        "files_blocked_attempted": [],
        "django_check": {"ok": False, "output": ""},
        "reason": "",
    }
    base.update(overrides)
    return base


def dumps_backend_builder_result(payload: dict[str, Any]) -> str:
    """Serialize BackendBuilder result for AgentJob.result TextField."""
    out = empty_backend_builder_result()
    out.update(payload or {})
    # Keep only known keys + allow extras for debugging
    return json.dumps(out, indent=2)


def loads_backend_builder_result(raw: str | None) -> dict[str, Any]:
    if not raw:
        return empty_backend_builder_result(reason="empty result")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return empty_backend_builder_result(reason="invalid JSON result")
    if not isinstance(data, dict):
        return empty_backend_builder_result(reason="result is not an object")
    return empty_backend_builder_result(**data)
