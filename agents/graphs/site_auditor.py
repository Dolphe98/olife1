"""SiteAuditor graph — read-only weekly site health report (Phase 3B)."""

from __future__ import annotations

import json
import os
import re
import socket
import ssl
import time
from datetime import datetime, timezone
from typing import Any, TypedDict
from urllib.parse import urljoin, urlparse

import certifi
import httpx
from django.conf import settings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

DEFAULT_URLS = (
    "https://olife1.com",
    "https://web-staging-12855354.up.railway.app",
)
HTTP_TIMEOUT = 10.0
CERT_TIMEOUT = 5.0
SLOW_MS = 2000
CERT_WARN_DAYS = 30
DARK_TOKEN = "--bg-void"
DARK_TOKEN_PREFIX = "--bg-"
STYLESHEET_HREF_RE = re.compile(
    r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def _ensure_ssl_certs() -> None:
    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception:
        ca = certifi.where()
        os.environ["SSL_CERT_FILE"] = ca
        os.environ["REQUESTS_CA_BUNDLE"] = ca
        os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = ca


class SiteAuditorState(TypedDict, total=False):
    command: str
    job_id: str
    gathered: dict[str, Any]
    report_md: str
    result: str


def _audit_urls() -> list[str]:
    raw = os.environ.get("SITE_AUDIT_URLS", "").strip()
    if not raw:
        return list(DEFAULT_URLS)
    return [u.strip().rstrip("/") for u in raw.split(",") if u.strip()]


def _base(url: str) -> str:
    return url.rstrip("/")


def _cert_days_remaining(hostname: str) -> tuple[int | None, str | None]:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=CERT_TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
        not_after = cert.get("notAfter")
        if not not_after:
            return None, "cert missing notAfter"
        expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=timezone.utc
        )
        days = (expiry - datetime.now(timezone.utc)).days
        return days, None
    except Exception as exc:
        return None, str(exc)[:200]


def _timed_get(
    client: httpx.Client, url: str
) -> tuple[int | None, str, int, str | None]:
    """Returns status_code, body_text, elapsed_ms, error."""
    started = time.perf_counter()
    try:
        resp = client.get(url)
        ms = int((time.perf_counter() - started) * 1000)
        return resp.status_code, resp.text, ms, None
    except Exception as exc:
        ms = int((time.perf_counter() - started) * 1000)
        return None, "", ms, str(exc)[:300]


def _check_healthz(client: httpx.Client, base: str) -> dict[str, Any]:
    code, body, ms, err = _timed_get(client, f"{base}/healthz")
    detail = err or ""
    ok = False
    if err:
        detail = f"request error: {err}"
    elif code != 200:
        detail = f"expected 200, got {code}"
    else:
        try:
            payload = json.loads(body)
            if payload == {"status": "ok"}:
                ok = True
                detail = "200 + {\"status\":\"ok\"}"
            else:
                detail = f"expected {{\"status\":\"ok\"}}, got {payload!r}"[:200]
        except Exception:
            detail = f"non-JSON body: {body[:120]!r}"
    anomalies: list[str] = []
    if not ok:
        anomalies.append(f"healthz FAIL: {detail}")
    if ms > SLOW_MS:
        anomalies.append(f"healthz slow: {ms}ms")
    return {
        "name": "healthz",
        "pass": ok,
        "status_code": code,
        "ms": ms,
        "detail": detail,
        "anomalies": anomalies,
    }


def _check_home(client: httpx.Client, base: str) -> dict[str, Any]:
    """Dark-theme token lives in linked CSS, not inline HTML."""
    code, body, ms, err = _timed_get(client, f"{base}/")
    anomalies: list[str] = []
    if ms > SLOW_MS:
        anomalies.append(f"home slow: {ms}ms")

    if err:
        detail = f"request error: {err}"
        anomalies.append(f"home FAIL: {detail}")
        return {
            "name": "home",
            "pass": False,
            "result": "FAIL",
            "status_code": code,
            "ms": ms,
            "detail": detail,
            "anomalies": anomalies,
        }
    if code != 200:
        detail = f"expected 200, got {code}"
        anomalies.append(f"home FAIL: {detail}")
        return {
            "name": "home",
            "pass": False,
            "result": "FAIL",
            "status_code": code,
            "ms": ms,
            "detail": detail,
            "anomalies": anomalies,
        }

    match = STYLESHEET_HREF_RE.search(body or "")
    if not match:
        detail = "no stylesheet linked"
        anomalies.append(f"home FAIL: {detail}")
        return {
            "name": "home",
            "pass": False,
            "result": "FAIL",
            "status_code": code,
            "ms": ms,
            "detail": detail,
            "anomalies": anomalies,
        }

    css_url = urljoin(f"{base}/", match.group(1))
    css_code, css_body, css_ms, css_err = _timed_get(client, css_url)
    ms_total = ms + css_ms
    if css_ms > SLOW_MS:
        anomalies.append(f"home css slow: {css_ms}ms")

    if css_err or css_code is None or css_code >= 400:
        detail = (
            f"200 HTML; CSS WARN (fetch failed: "
            f"{css_err or f'status {css_code}'} @ {css_url})"
        )
        anomalies.append(f"home WARN: {detail}")
        return {
            "name": "home",
            "pass": True,
            "result": "WARN",
            "status_code": code,
            "ms": ms_total,
            "detail": detail,
            "anomalies": anomalies,
        }

    has_token = DARK_TOKEN in css_body or DARK_TOKEN_PREFIX in css_body
    if has_token:
        detail = f"200 + CSS contains dark token ({DARK_TOKEN} / {DARK_TOKEN_PREFIX})"
        return {
            "name": "home",
            "pass": True,
            "result": "PASS",
            "status_code": code,
            "ms": ms_total,
            "detail": detail,
            "anomalies": anomalies,
        }

    detail = f"200 but CSS missing dark-theme token ({css_url})"
    anomalies.append(f"home FAIL: {detail}")
    return {
        "name": "home",
        "pass": False,
        "result": "FAIL",
        "status_code": code,
        "ms": ms_total,
        "detail": detail,
        "anomalies": anomalies,
    }


def _check_redirect(
    client: httpx.Client, base: str, path: str, name: str
) -> dict[str, Any]:
    code, _body, ms, err = _timed_get(client, f"{base}{path}")
    detail = err or ""
    ok = False
    if err:
        detail = f"request error: {err}"
    elif code in (301, 302):
        ok = True
        detail = f"got {code} (redirect)"
    else:
        detail = f"expected 302/301, got {code}"
    anomalies: list[str] = []
    if not ok:
        anomalies.append(f"{name} FAIL: {detail}")
    if code is not None and code not in (200, 301, 302) and not err:
        anomalies.append(f"{name} unexpected status {code}")
    if ms > SLOW_MS:
        anomalies.append(f"{name} slow: {ms}ms")
    return {
        "name": name,
        "pass": ok,
        "status_code": code,
        "ms": ms,
        "detail": detail,
        "anomalies": anomalies,
    }


def _audit_one(base: str) -> dict[str, Any]:
    base = _base(base)
    host = urlparse(base).hostname or ""
    cert_days, cert_err = _cert_days_remaining(host) if host else (None, "no hostname")
    anomalies: list[str] = []
    if cert_err:
        anomalies.append(f"cert check FAIL: {cert_err}")
    elif cert_days is not None and cert_days < CERT_WARN_DAYS:
        anomalies.append(f"cert <{CERT_WARN_DAYS}d remaining: {cert_days}")

    checks: list[dict[str, Any]] = []
    try:
        with httpx.Client(
            timeout=HTTP_TIMEOUT,
            follow_redirects=False,
            verify=True,
        ) as client:
            checks.append(_check_healthz(client, base))
            checks.append(_check_home(client, base))
            checks.append(
                _check_redirect(client, base, "/django-admin/", "django_admin")
            )
            checks.append(_check_redirect(client, base, "/admin/", "crm_admin"))
    except Exception as exc:
        # Client construction failure — mark all checks failed once.
        for name in ("healthz", "home", "django_admin", "crm_admin"):
            checks.append(
                {
                    "name": name,
                    "pass": False,
                    "status_code": None,
                    "ms": 0,
                    "detail": f"client error: {exc}"[:300],
                    "anomalies": [f"{name} FAIL: client error"],
                }
            )

    for c in checks:
        anomalies.extend(c.get("anomalies") or [])

    status_per_check = {
        c["name"]: (c.get("result") or ("PASS" if c.get("pass") else "FAIL"))
        for c in checks
    }
    response_times_ms = {c["name"]: c["ms"] for c in checks}

    return {
        "url": base,
        "checks": checks,
        "status_per_check": status_per_check,
        "response_times_ms": response_times_ms,
        "cert_days_remaining": cert_days,
        "cert_error": cert_err,
        "anomalies": anomalies,
    }


def gather(state: SiteAuditorState) -> SiteAuditorState:
    """Node 1: HTTP + TLS probes for each SITE_AUDIT_URLS entry."""
    _ensure_ssl_certs()
    urls = _audit_urls()
    results = [_audit_one(u) for u in urls]
    return {
        "gathered": {
            "run_at": datetime.now(timezone.utc).isoformat(),
            "urls": results,
        }
    }


def _call_gemini_rest(prompt: str, model_name: str, api_key: str) -> str:
    _ensure_ssl_certs()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={api_key}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"Gemini HTTP {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Gemini response: {data!r}"[:500]) from exc
    text = (text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response")
    return text


def _deterministic_markdown(gathered: dict[str, Any]) -> str:
    lines = [
        "# SiteAuditor report",
        "",
        f"Run at: `{gathered.get('run_at', '')}`",
        "",
        "| URL | Check | Result | Status | ms | Detail |",
        "|---|---|---|---|---|---|",
    ]
    for entry in gathered.get("urls") or []:
        url = entry.get("url", "")
        for c in entry.get("checks") or []:
            result = c.get("result") or ("PASS" if c.get("pass") else "FAIL")
            lines.append(
                f"| {url} | {c.get('name')} | {result} | "
                f"{c.get('status_code')} | {c.get('ms')} | "
                f"{(c.get('detail') or '').replace('|', '/')} |"
            )
        cert = entry.get("cert_days_remaining")
        cert_s = "n/a" if cert is None else str(cert)
        lines.append(
            f"| {url} | tls_cert_days | "
            f"{'PASS' if cert is not None else 'FAIL'} | — | — | "
            f"days_remaining={cert_s} |"
        )
    lines.extend(["", "## Anomalies", ""])
    any_anom = False
    for entry in gathered.get("urls") or []:
        for a in entry.get("anomalies") or []:
            any_anom = True
            lines.append(f"- **{entry.get('url')}**: {a}")
    if not any_anom:
        lines.append("- None")
    return "\n".join(lines)


def summarize(state: SiteAuditorState) -> SiteAuditorState:
    """Node 2: Gemini REST → concise Markdown report with table."""
    gathered = state.get("gathered") or {}
    fallback = _deterministic_markdown(gathered)

    api_key = getattr(settings, "GEMINI_API_KEY", "") or os.environ.get(
        "GEMINI_API_KEY", ""
    )
    if not api_key:
        return {"report_md": fallback + "\n\n_Note: GEMINI_API_KEY unset; raw table only._"}

    model_name = getattr(settings, "GEMINI_MODEL", None) or os.environ.get(
        "GEMINI_MODEL", "gemini-3.5-flash"
    )
    prompt = (
        "You are SiteAuditor for olife1.com. Given the JSON probe results below, "
        "write a concise human-readable Markdown weekly site-health report.\n"
        "Requirements:\n"
        "- Include a Markdown table with columns: URL, Check, Result (PASS/FAIL), "
        "HTTP status, ms, Detail (expected vs actual when FAIL).\n"
        "- Include TLS cert days-remaining per URL.\n"
        "- List anomalies (slow >2s, unexpected status, missing --bg-void, "
        "cert <30 days).\n"
        "- Do not invent checks; use only the JSON.\n"
        "- Keep tone grounded and brief.\n\n"
        f"JSON:\n{json.dumps(gathered, indent=2)}\n"
    )
    try:
        report = _call_gemini_rest(prompt, model_name, api_key)
    except Exception as exc:
        report = (
            fallback
            + f"\n\n_Note: Gemini summarize failed ({exc}); showing deterministic table._"
        )
    return {"report_md": report}


def finalize(state: SiteAuditorState) -> SiteAuditorState:
    """Node 3: persist optional history rows; return Markdown as result."""
    report = (state.get("report_md") or "").strip()
    gathered = state.get("gathered") or {}
    job_id = (state.get("job_id") or "").strip()

    if job_id and gathered.get("urls"):
        try:
            from agents.models import AgentJob, SiteAudit

            job = AgentJob.objects.filter(pk=job_id).first()
            if job is not None:
                run_at = datetime.now(timezone.utc)
                for entry in gathered["urls"]:
                    SiteAudit.objects.create(
                        url=entry.get("url") or "",
                        status_per_check=entry.get("status_per_check") or {},
                        response_times_ms=entry.get("response_times_ms") or {},
                        cert_days_remaining=entry.get("cert_days_remaining"),
                        run_at=run_at,
                        job=job,
                    )
        except Exception:
            # History is optional; never fail the job over persistence.
            pass

    return {"result": report}


def build_graph(checkpointer: PostgresSaver):
    builder = StateGraph(SiteAuditorState)
    builder.add_node("gather", gather)
    builder.add_node("summarize", summarize)
    builder.add_node("finalize", finalize)
    builder.add_edge(START, "gather")
    builder.add_edge("gather", "summarize")
    builder.add_edge("summarize", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile(checkpointer=checkpointer)


def _checkpoint_conn_string() -> str:
    candidates = [
        os.environ.get("LANGGRAPH_DATABASE_URL", "").strip(),
        getattr(settings, "DIRECT_URL", "") or os.environ.get("DIRECT_URL", "").strip(),
        os.environ.get("DATABASE_URL", "").strip(),
    ]
    ordered = []
    for url in candidates:
        if not url:
            continue
        if ":6543" in url:
            continue
        ordered.append(url)
    for url in ordered:
        if "pooler.supabase.com" in url:
            return url
    if ordered:
        return ordered[0]
    raise RuntimeError(
        "Need LANGGRAPH_DATABASE_URL, DATABASE_URL (session :5432), or DIRECT_URL "
        "for langgraph-checkpoint-postgres (not transaction pooler :6543)"
    )


def run_site_auditor(command: str, thread_id: str, job_id: str | None = None) -> str:
    """Invoke SiteAuditor with Postgres checkpointing (session-mode connection)."""
    conn = _checkpoint_conn_string()
    with PostgresSaver.from_conn_string(conn) as checkpointer:
        checkpointer.setup()
        graph = build_graph(checkpointer)
        out = graph.invoke(
            {
                "command": command or "audit now",
                "job_id": job_id or thread_id,
            },
            config={"configurable": {"thread_id": thread_id}},
        )
    return (out.get("result") or "").strip()
