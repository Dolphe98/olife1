"""Trivial Echo graph — Gemini proof-of-life for Phase 3A."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import TypedDict

import certifi
from django.conf import settings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

# Declared dependency (plan); REST used for reliability on Windows + timeouts.
import google.generativeai as _genai  # noqa: F401


def _ensure_ssl_certs() -> None:
    """Prefer OS trust store (Windows); fall back to certifi."""
    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception:
        ca = certifi.where()
        os.environ["SSL_CERT_FILE"] = ca
        os.environ["REQUESTS_CA_BUNDLE"] = ca
        os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = ca


class EchoState(TypedDict, total=False):
    command: str
    response: str


def _call_gemini(command: str, model_name: str, api_key: str) -> str:
    """Generate content via Gemini REST (stable vs hung gRPC SDK on some hosts)."""
    _ensure_ssl_certs()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={api_key}"
    )
    payload = json.dumps(
        {"contents": [{"parts": [{"text": command}]}]}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini HTTP {exc.code}: {body[:500]}") from exc

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Gemini response: {data!r}"[:500]) from exc
    text = (text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response")
    return text


def respond(state: EchoState) -> EchoState:
    """Single node: call Gemini with the job command string only."""
    api_key = getattr(settings, "GEMINI_API_KEY", "") or os.environ.get(
        "GEMINI_API_KEY", ""
    )
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model_name = getattr(settings, "GEMINI_MODEL", None) or os.environ.get(
        "GEMINI_MODEL", "gemini-3.5-flash"
    )
    command = (state.get("command") or "").strip()
    if not command:
        raise ValueError("Echo command is empty")

    return {"response": _call_gemini(command, model_name, api_key)}


def build_graph(checkpointer: PostgresSaver):
    builder = StateGraph(EchoState)
    builder.add_node("respond", respond)
    builder.add_edge(START, "respond")
    builder.add_edge("respond", END)
    return builder.compile(checkpointer=checkpointer)


def _checkpoint_conn_string() -> str:
    """
    Session-mode Postgres URL for langgraph-checkpoint-postgres.
    Prefer LANGGRAPH_DATABASE_URL, then DATABASE_URL (session pooler :5432),
    then DIRECT_URL. Skip transaction pooler (:6543) — it breaks checkpoints.
    Railway often cannot reach Supabase direct IPv6 hosts.
    """
    candidates = [
        os.environ.get("LANGGRAPH_DATABASE_URL", "").strip(),
        getattr(settings, "DIRECT_URL", "") or os.environ.get("DIRECT_URL", "").strip(),
        os.environ.get("DATABASE_URL", "").strip(),
    ]
    # Prefer non-6543 URLs; among those, prefer pooler / LANGGRAPH over raw IPv6 direct last.
    ordered = []
    for url in candidates:
        if not url:
            continue
        if ":6543" in url:
            continue
        ordered.append(url)
    # Prefer session pooler (pooler.supabase.com) over db.*.supabase.co when both present
    for url in ordered:
        if "pooler.supabase.com" in url:
            return url
    if ordered:
        return ordered[0]
    raise RuntimeError(
        "Need LANGGRAPH_DATABASE_URL, DATABASE_URL (session :5432), or DIRECT_URL "
        "for langgraph-checkpoint-postgres (not transaction pooler :6543)"
    )


def run_echo(command: str, thread_id: str) -> str:
    """Invoke Echo with Postgres checkpointing (session-mode connection)."""
    conn = _checkpoint_conn_string()

    with PostgresSaver.from_conn_string(conn) as checkpointer:
        checkpointer.setup()
        graph = build_graph(checkpointer)
        out = graph.invoke(
            {"command": command},
            config={"configurable": {"thread_id": thread_id}},
        )
    return (out.get("response") or "").strip()
