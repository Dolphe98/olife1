"""Architect graph — read-only code-vs-spec drift report (Phase 3C)."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

import certifi
import httpx
from django.conf import settings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

SPEC_FILES = (
    "DATA_MODEL.md",
    "ARCHITECTURE.md",
    "AGENTS.md",
    "DESIGN.md",
    "ROADMAP.md",
)

# AGENTS.md catalog → expected graph module / phase hint when missing
AGENT_CATALOG = (
    ("Orchestrator", "orchestrator", "MISSING (Phase 3E)"),
    ("Architect", "architect", "IMPLEMENTED"),
    ("Designer", "designer", "MISSING (Phase 3D+)"),
    ("FrontendBuilder", "frontend_builder", "MISSING (Phase 3D)"),
    ("BackendBuilder", "backend_builder", "MISSING (Phase 3D)"),
    ("ContentMigrator", "content_migrator", "MISSING"),
    ("SEOSpecialist", "seo_specialist", "MISSING"),
    ("CRMBuilder", "crm_builder", "MISSING (Phase 4)"),
    ("Deployer", "deployer", "MISSING"),
    ("QAInspector", "qa_inspector", "MISSING"),
    ("BrandVoice", "brand_voice", "MISSING"),
    ("SiteAuditor", "site_auditor", "IMPLEMENTED"),
)

# Extra runtime graphs not named identically in AGENTS.md catalog
EXTRA_GRAPHS = (("echo", "echo.py"),)

SPEC_ROUTES = (
    ("/", "public sitepages"),
    ("/accounts/", "allauth (flagged)"),
    ("/admin/", "custom CRM"),
    ("/django-admin/", "Django admin"),
    ("/healthz", "shared health view"),
    ("/sitemap.xml", "SEO"),
    ("/robots.txt", "SEO"),
    ("/feed.xml", "SEO"),
)

MODEL_HEADER_RE = re.compile(r"^###\s+`(\w+)`", re.MULTILINE)
MODEL_CLASS_RE = re.compile(r"^class\s+(\w+)\(models\.Model\):", re.MULTILINE)
PATH_CALL_RE = re.compile(
    r"""path\(\s*['"]([^'"]*)['"]""",
    re.MULTILINE,
)
DB_TABLE_RE = re.compile(
    r"class\s+(\w+)\(models\.Model\):.*?class Meta:.*?db_table\s*=\s*['\"](\w+)['\"]",
    re.DOTALL,
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


class ArchitectState(TypedDict, total=False):
    command: str
    job_id: str
    scanned: dict[str, Any]
    diff: dict[str, Any]
    report_md: str
    json_payload: dict[str, Any]
    result: str


def _repo_root() -> Path:
    raw = os.environ.get("ARCHITECT_REPO_PATH", ".").strip() or "."
    return Path(raw).resolve()


def _read_text(path: Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception as exc:
        return f"<<read_error: {exc}>>"


def _git_meta(root: Path) -> dict[str, str]:
    meta = {"branch": "unknown", "sha": "unknown"}
    try:
        meta["branch"] = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=root,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            or "unknown"
        )
    except Exception:
        pass
    try:
        meta["sha"] = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            or "unknown"
        )
    except Exception:
        pass
    return meta


def _extract_top_level(py_text: str) -> dict[str, list[str]]:
    classes: list[str] = []
    functions: list[str] = []
    try:
        tree = ast.parse(py_text)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
    except SyntaxError:
        classes = MODEL_CLASS_RE.findall(py_text)
    return {"classes": classes, "functions": functions}


def _default_db_table(model_name: str, app_label: str = "sitepages") -> str:
    return f"{app_label}_{model_name.lower()}"


def _model_db_tables(models_src: str) -> dict[str, str]:
    explicit = {m: t for m, t in DB_TABLE_RE.findall(models_src)}
    names = MODEL_CLASS_RE.findall(models_src)
    out: dict[str, str] = {}
    for name in names:
        out[name] = explicit.get(name) or _default_db_table(name)
    return out


def _normalize_route(p: str) -> str:
    if not p.startswith("/"):
        p = "/" + p
    # Django "" → "/"
    if p == "/":
        return "/"
    return p


def _collect_routes(config_urls: str, sitepages_urls: str) -> list[dict[str, str]]:
    routes: list[dict[str, str]] = []
    for src, label in (
        (config_urls, "config.urls"),
        (sitepages_urls, "sitepages.urls"),
    ):
        for raw in PATH_CALL_RE.findall(src):
            routes.append(
                {
                    "path": _normalize_route(raw),
                    "source": label,
                    "raw": raw or "",
                    "gated": (
                        "FEATURE_GOOGLE_LOGIN" in src and raw.startswith("accounts")
                    ),
                }
            )
    return routes


def _agents_tree(root: Path) -> dict[str, Any]:
    agents_dir = root / "agents"
    files: list[dict[str, Any]] = []
    graphs: list[str] = []
    if not agents_dir.is_dir():
        return {"files": [], "graphs": []}
    for path in sorted(agents_dir.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        text = _read_text(path)
        top = _extract_top_level(text)
        files.append({"path": rel, **top})
        if path.parent.name == "graphs" and path.name != "__init__.py":
            graphs.append(path.stem)
    return {"files": files, "graphs": graphs}


def scan(state: ArchitectState) -> ArchitectState:
    """Node 1: read specs + implementation into a structured dict."""
    root = _repo_root()
    git = _git_meta(root)

    specs: dict[str, str] = {}
    for name in SPEC_FILES:
        specs[name] = _read_text(root / name)

    models_src = _read_text(root / "sitepages" / "models.py")
    config_urls = _read_text(root / "config" / "urls.py")
    sitepages_urls = _read_text(root / "sitepages" / "urls.py")
    settings_src = _read_text(root / "config" / "settings.py")
    requirements = _read_text(root / "requirements.txt")
    agents = _agents_tree(root)

    model_names = MODEL_CLASS_RE.findall(models_src)
    spec_models = MODEL_HEADER_RE.findall(specs.get("DATA_MODEL.md", ""))
    # CRM helpers documented without backticks in ### headers sometimes —
    # also pick ContentPipelineItem / DeployEvent from bold **`Name`**
    for extra in re.findall(
        r"\*\*`(\w+)`\*\*", specs.get("DATA_MODEL.md", "")
    ):
        if extra not in spec_models:
            spec_models.append(extra)

    scanned = {
        "git": git,
        "repo_root": str(root),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "specs": {k: {"chars": len(v), "excerpt": v[:2000]} for k, v in specs.items()},
        "code": {
            "models": {
                "path": "sitepages/models.py",
                "classes": model_names,
                "db_tables": _model_db_tables(models_src),
            },
            "routes": _collect_routes(config_urls, sitepages_urls),
            "settings": {
                "path": "config/settings.py",
                "has_whitenoise": "whitenoise" in settings_src.lower(),
                "has_database_url": "DATABASE_URL" in settings_src,
                "debug_from_env": 'os.environ.get("DEBUG"' in settings_src
                or "os.environ.get('DEBUG'" in settings_src,
                "installed_apps_snip": _settings_list_snip(settings_src, "INSTALLED_APPS"),
                "middleware_snip": _settings_list_snip(settings_src, "MIDDLEWARE"),
            },
            "agents": agents,
            "requirements": {
                "path": "requirements.txt",
                "packages": [
                    line.strip()
                    for line in requirements.splitlines()
                    if line.strip() and not line.strip().startswith("#")
                ],
            },
        },
        "spec_models": spec_models,
    }
    return {"scanned": scanned}


def _settings_list_snip(src: str, name: str) -> str:
    m = re.search(rf"{name}\s*=\s*\[(.*?)\]", src, re.DOTALL)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1))[:500]


def _route_implemented(
    spec_path: str,
    actual_paths: set[str],
    gated_accounts: bool = False,
) -> tuple[str, str]:
    """Return (status, actual note)."""
    if spec_path == "/accounts/":
        if any(p.rstrip("/") == "/accounts" for p in actual_paths):
            if gated_accounts:
                return "PARTIAL", "allauth gated (FEATURE_GOOGLE_LOGIN)"
            return "IMPLEMENTED", "/accounts/"
        return "PARTIAL", "allauth gated (FEATURE_GOOGLE_LOGIN)"

    candidates = {spec_path, spec_path.rstrip("/") or "/"}
    if spec_path == "/healthz":
        candidates.update({"/healthz", "healthz", "/healthz/"})
    for a in actual_paths:
        norm = a if a.startswith("/") else "/" + a
        if norm in candidates or norm.rstrip("/") in {
            c.rstrip("/") for c in candidates
        }:
            return "IMPLEMENTED", norm
        if spec_path == "/" and norm == "/":
            return "IMPLEMENTED", "/"
    if spec_path in ("/sitemap.xml", "/robots.txt", "/feed.xml"):
        return "MISSING", "—"
    return "MISSING", "—"


def diff(state: ArchitectState) -> ArchitectState:
    """Node 2: deterministic claim-by-claim comparison (no LLM)."""
    scanned = state.get("scanned") or {}
    code = scanned.get("code") or {}
    git = scanned.get("git") or {}

    model_classes = set((code.get("models") or {}).get("classes") or [])
    db_tables = (code.get("models") or {}).get("db_tables") or {}
    spec_models = list(scanned.get("spec_models") or [])
    # Prefer canonical DATA_MODEL entities
    preferred = [
        "Profile",
        "Category",
        "Tag",
        "Media",
        "Post",
        "Fragment",
        "Page",
        "Comment",
        "Subscriber",
        "ContactMessage",
        "ContentPipelineItem",
        "DeployEvent",
    ]
    ordered_models = [m for m in preferred if m in spec_models or m in model_classes]
    for m in spec_models:
        if m not in ordered_models and m[0].isupper():
            ordered_models.append(m)

    models_rows: list[dict[str, str]] = []
    for name in ordered_models:
        if name in model_classes:
            table = db_tables.get(name, _default_db_table(name))
            models_rows.append(
                {
                    "spec_model": name,
                    "status": "IMPLEMENTED",
                    "notes": f"db_table={table}",
                }
            )
        else:
            models_rows.append(
                {
                    "spec_model": name,
                    "status": "MISSING",
                    "notes": "not in sitepages/models.py",
                }
            )
    # Extra models in code not in spec
    for name in sorted(model_classes):
        if name not in {r["spec_model"] for r in models_rows}:
            models_rows.append(
                {
                    "spec_model": name,
                    "status": "DIVERGED",
                    "notes": "in code but not listed in DATA_MODEL.md",
                }
            )

    actual_routes = code.get("routes") or []
    actual_paths = {_normalize_route(r["path"]) for r in actual_routes}
    gated_accounts = any(r.get("gated") for r in actual_routes)
    route_lookup = {
        _normalize_route(r["path"]): f"{r['source']}:{r['raw'] or '(home)'}"
        for r in actual_routes
    }

    routes_rows: list[dict[str, str]] = []
    for spec_path, hint in SPEC_ROUTES:
        status, actual = _route_implemented(spec_path, actual_paths, gated_accounts)
        if status == "IMPLEMENTED":
            note = route_lookup.get(actual) or route_lookup.get(spec_path) or actual
            if spec_path == "/healthz":
                note = "sitepages.health.healthz"
            elif spec_path == "/admin/":
                note = "crm.urls (staff CRM)"
            elif spec_path == "/django-admin/":
                note = "django.contrib.admin"
            elif spec_path == "/":
                note = "sitepages.views.home"
            routes_rows.append(
                {"spec_route": spec_path, "status": status, "actual": note}
            )
        else:
            routes_rows.append(
                {
                    "spec_route": spec_path,
                    "status": status,
                    "actual": actual if actual != "—" else hint,
                }
            )

    graphs = set((code.get("agents") or {}).get("graphs") or [])
    agents_rows: list[dict[str, str]] = []
    # Runtime graphs first in report order
    runtime_order = [
        ("echo", "echo"),
        ("site_auditor", "site_auditor"),
        ("architect", "architect"),
    ]
    seen_stems: set[str] = set()
    for label, stem in runtime_order:
        seen_stems.add(stem)
        agents_rows.append(
            {
                "spec_agent": label,
                "status": "IMPLEMENTED" if stem in graphs else "MISSING",
                "file": f"agents/graphs/{stem}.py" if stem in graphs else "—",
            }
        )
    for display, stem, missing_hint in AGENT_CATALOG:
        if stem in seen_stems:
            continue
        if stem in graphs:
            agents_rows.append(
                {
                    "spec_agent": display,
                    "status": "IMPLEMENTED",
                    "file": f"agents/graphs/{stem}.py",
                }
            )
        else:
            agents_rows.append(
                {
                    "spec_agent": display,
                    "status": "MISSING",
                    "file": missing_hint if missing_hint.startswith("MISSING") else "—",
                }
            )

    settings_code = code.get("settings") or {}
    settings_rows = [
        {
            "setting": "DATABASES engine",
            "spec": "Supabase Postgres via DATABASE_URL",
            "actual": (
                "dj_database_url / DATABASE_URL (sqlite fallback if ALLOW_SQLITE)"
                if settings_code.get("has_database_url")
                else "DIVERGED — no DATABASE_URL wiring found"
            ),
        },
        {
            "setting": "STATIC serving",
            "spec": "WhiteNoise",
            "actual": (
                "WhiteNoise CompressedStaticFilesStorage"
                if settings_code.get("has_whitenoise")
                else "MISSING WhiteNoise"
            ),
        },
        {
            "setting": "DEBUG",
            "spec": "per env",
            "actual": (
                "os.environ DEBUG (default True)"
                if settings_code.get("debug_from_env")
                else "hardcoded / unknown"
            ),
        },
    ]

    all_statuses: list[str] = []
    for row in models_rows:
        all_statuses.append(row["status"])
    for row in routes_rows:
        all_statuses.append(row["status"])
    for row in agents_rows:
        all_statuses.append(row["status"])
    # Settings: classify
    for row in settings_rows:
        actual = row["actual"]
        if actual.startswith("MISSING") or "DIVERGED" in actual:
            st = "DIVERGED" if "DIVERGED" in actual else "MISSING"
        else:
            st = "IMPLEMENTED"
        row["status"] = st
        all_statuses.append(st)

    def _count(s: str) -> int:
        return sum(1 for x in all_statuses if x == s)

    missing_list = []
    diverged_list = []
    for row in models_rows + routes_rows + agents_rows:
        label = (
            row.get("spec_model")
            or row.get("spec_route")
            or row.get("spec_agent")
            or "?"
        )
        if row["status"] == "MISSING":
            missing_list.append(str(label))
        elif row["status"] == "DIVERGED":
            diverged_list.append(str(label))

    priority: list[str] = []
    if any(r["spec_route"] == "/sitemap.xml" and r["status"] == "MISSING" for r in routes_rows):
        priority.append(
            "Add SEO routes (/sitemap.xml, /robots.txt, /feed.xml) per ARCHITECTURE.md §7."
        )
    if any(r["spec_agent"] == "BackendBuilder" and r["status"] == "MISSING" for r in agents_rows):
        priority.append(
            "Implement BackendBuilder graph (Phase 3D) — models/views/auth still manual."
        )
    if any(r["spec_agent"] == "Orchestrator" and r["status"] == "MISSING" for r in agents_rows):
        priority.append(
            "Implement Orchestrator (Phase 3E) to route /plan /build and HITL gates."
        )
    if not priority:
        priority.append("No critical drift — keep Phase 3 agents green and merge to staging.")
    while len(priority) < 3:
        if "/accounts/" in missing_list or any(
            r.get("spec_route") == "/accounts/" and r["status"] == "PARTIAL"
            for r in routes_rows
        ):
            priority.append(
                "Document /accounts/ as PARTIAL until FEATURE_GOOGLE_LOGIN is enabled."
            )
        elif "Designer" in missing_list:
            priority.append("Schedule Designer agent after FrontendBuilder (DESIGN.md tokens).")
        else:
            priority.append("Keep SiteAuditor + Architect weekly; defer Telegram to Phase 5.")
        if len(priority) >= 3:
            break

    diff_out = {
        "branch": git.get("branch", "unknown"),
        "sha": git.get("sha", "unknown"),
        "timestamp": scanned.get("scanned_at")
        or datetime.now(timezone.utc).isoformat(),
        "models": models_rows,
        "routes": routes_rows,
        "agents": agents_rows,
        "settings": settings_rows,
        "summary": {
            "total_claims": len(all_statuses),
            "IMPLEMENTED": _count("IMPLEMENTED"),
            "PARTIAL": _count("PARTIAL"),
            "MISSING": _count("MISSING"),
            "DIVERGED": _count("DIVERGED"),
            "missing_list": missing_list,
            "diverged_list": diverged_list,
        },
        "priority_fixes": priority[:3],
    }
    return {"diff": diff_out}


def _deterministic_markdown(diff_out: dict[str, Any]) -> str:
    branch = diff_out.get("branch", "unknown")
    sha = (diff_out.get("sha") or "unknown")[:12]
    ts = diff_out.get("timestamp", "")
    lines = [
        f"## Drift Report — {branch} @ {sha} — {ts}",
        "",
        "### Models (DATA_MODEL.md vs sitepages/models.py)",
        "| Spec model | Status | Notes |",
        "|---|---|---|",
    ]
    for r in diff_out.get("models") or []:
        lines.append(
            f"| {r.get('spec_model')} | {r.get('status')} | {r.get('notes', '')} |"
        )
    lines.extend(
        [
            "",
            "### Routes (ARCHITECTURE.md vs urls.py)",
            "| Spec route | Status | Actual |",
            "|---|---|---|",
        ]
    )
    for r in diff_out.get("routes") or []:
        lines.append(
            f"| {r.get('spec_route')} | {r.get('status')} | {r.get('actual', '')} |"
        )
    lines.extend(
        [
            "",
            "### Agents (AGENTS.md vs agents/)",
            "| Spec agent | Status | File |",
            "|---|---|---|",
        ]
    )
    for r in diff_out.get("agents") or []:
        lines.append(
            f"| {r.get('spec_agent')} | {r.get('status')} | {r.get('file', '')} |"
        )
    lines.extend(
        [
            "",
            "### Settings drift",
            "| Setting | Spec | Actual |",
            "|---|---|---|",
        ]
    )
    for r in diff_out.get("settings") or []:
        lines.append(
            f"| {r.get('setting')} | {r.get('spec')} | {r.get('actual')} |"
        )
    summary = diff_out.get("summary") or {}
    lines.extend(
        [
            "",
            "### Summary",
            f"- Total spec claims: {summary.get('total_claims', 0)}",
            f"- IMPLEMENTED: {summary.get('IMPLEMENTED', 0)}",
            f"- PARTIAL: {summary.get('PARTIAL', 0)}",
            f"- MISSING: {summary.get('MISSING', 0)} ({', '.join(summary.get('missing_list') or []) or 'none'})",
            f"- DIVERGED: {summary.get('DIVERGED', 0)} ({', '.join(summary.get('diverged_list') or []) or 'none'})",
            "",
            "### Priority fixes (top 3)",
        ]
    )
    for i, fix in enumerate(diff_out.get("priority_fixes") or [], 1):
        lines.append(f"{i}. {fix}")
    return "\n".join(lines)


def _call_gemini_rest(prompt: str, model_name: str, api_key: str) -> str:
    _ensure_ssl_certs()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={api_key}"
    )
    with httpx.Client(timeout=90.0) as client:
        resp = client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
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


def narrate(state: ArchitectState) -> ArchitectState:
    """Node 3: Gemini REST Markdown report; deterministic fallback."""
    diff_out = state.get("diff") or {}
    fallback = _deterministic_markdown(diff_out)

    api_key = getattr(settings, "GEMINI_API_KEY", "") or os.environ.get(
        "GEMINI_API_KEY", ""
    )
    if not api_key:
        return {"report_md": fallback, "json_payload": diff_out}

    model_name = getattr(settings, "GEMINI_MODEL", None) or os.environ.get(
        "GEMINI_MODEL", "gemini-3.5-flash"
    )
    prompt = (
        "You are the Architect agent for olife1.com. Given the JSON drift diff "
        "below, write a Markdown report that MUST use this exact shape and "
        "table headers (do not invent claims; use only the JSON):\n\n"
        "## Drift Report — <branch> @ <sha> — <timestamp>\n\n"
        "### Models (DATA_MODEL.md vs sitepages/models.py)\n"
        "| Spec model | Status | Notes |\n"
        "### Routes (ARCHITECTURE.md vs urls.py)\n"
        "| Spec route | Status | Actual |\n"
        "### Agents (AGENTS.md vs agents/)\n"
        "| Spec agent | Status | File |\n"
        "### Settings drift\n"
        "| Setting | Spec | Actual |\n"
        "### Summary\n"
        "(counts + MISSING/DIVERGED lists)\n"
        "### Priority fixes (top 3)\n"
        "(keep the three priority_fixes from JSON; you may tighten wording "
        "but stay action-able)\n\n"
        f"JSON:\n{json.dumps(diff_out, indent=2)}\n"
    )
    try:
        report = _call_gemini_rest(prompt, model_name, api_key)
    except Exception as exc:
        report = (
            fallback
            + f"\n\n_Note: Gemini narrate failed ({exc}); deterministic report used._"
        )
    return {"report_md": report, "json_payload": diff_out}


def finalize(state: ArchitectState) -> ArchitectState:
    """Node 4: persist ArchitectReport; return Markdown as job result."""
    report = (state.get("report_md") or "").strip()
    payload = state.get("json_payload") or state.get("diff") or {}
    job_id = (state.get("job_id") or "").strip()
    branch = payload.get("branch") or "unknown"
    sha = payload.get("sha") or "unknown"

    if job_id:
        try:
            from agents.models import AgentJob, ArchitectReport

            job = AgentJob.objects.filter(pk=job_id).first()
            if job is not None:
                ArchitectReport.objects.create(
                    branch=str(branch)[:128],
                    commit_sha=str(sha)[:64],
                    run_at=datetime.now(timezone.utc),
                    job=job,
                    summary_json=payload,
                    markdown=report,
                )
        except Exception:
            pass

    return {"result": report, "json_payload": payload}


def build_graph(checkpointer: PostgresSaver):
    builder = StateGraph(ArchitectState)
    builder.add_node("scan", scan)
    builder.add_node("diff", diff)
    builder.add_node("narrate", narrate)
    builder.add_node("finalize", finalize)
    builder.add_edge(START, "scan")
    builder.add_edge("scan", "diff")
    builder.add_edge("diff", "narrate")
    builder.add_edge("narrate", "finalize")
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


def run_architect(command: str, thread_id: str, job_id: str | None = None) -> str:
    """Invoke Architect with Postgres checkpointing (session-mode connection)."""
    conn = _checkpoint_conn_string()
    with PostgresSaver.from_conn_string(conn) as checkpointer:
        checkpointer.setup()
        graph = build_graph(checkpointer)
        out = graph.invoke(
            {
                "command": command or "audit current state",
                "job_id": job_id or thread_id,
            },
            config={"configurable": {"thread_id": thread_id}},
        )
    return (out.get("result") or "").strip()
