"""BackendBuilder — first write-capable agent (Phase 3D-1).

Plans Django backend file edits via Gemini REST, validates against a hardcoded
blocklist, applies locally on agent/backend/<job_uuid>, runs manage.py check,
then pushes a single commit and opens a PR into staging. Never merges.
"""

from __future__ import annotations

import difflib
import fnmatch
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, TypedDict
from urllib.parse import quote

import certifi
import httpx
from django.conf import settings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

from agents.result_schema import dumps_backend_builder_result, empty_backend_builder_result

# Hardcoded — enforced in validate(), never trusted from the LLM alone.
BLOCKED_PATH_PATTERNS: list[str] = [
    "sitepages/migrations/**",
    "agents/migrations/**",
    "config/settings.py",
    "config/urls.py",
    ".env",
    ".env.*",
    ".env.example",
    "Procfile",
    "railway.json",
    "railway.toml",
    "Dockerfile",
    "docker-compose.*",
    "requirements.txt",
    "poetry.lock",
    "Pipfile*",
    ".github/workflows/**",
    ".git/**",
]

MAX_FILES_PER_JOB = 10
MAX_LINES_CHANGED = 500
BASE_BRANCH = "staging"
GITHUB_OWNER = "Dolphe98"
GITHUB_REPO = "olife1"
AGENT_LABEL = "agent-generated"


class BackendBuilderState(TypedDict, total=False):
    command: str
    job_id: str
    plan: dict[str, Any]
    validation: dict[str, Any]
    work_dir: str
    branch: str
    files_changed: list[str]
    django_check: dict[str, Any]
    pr_url: str
    publish: dict[str, Any]
    result: str
    error: str


def _ensure_ssl_certs() -> None:
    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception:
        ca = certifi.where()
        os.environ["SSL_CERT_FILE"] = ca
        os.environ["REQUESTS_CA_BUNDLE"] = ca


def _repo_root() -> Path:
    override = (
        getattr(settings, "ARCHITECT_REPO_PATH", None)
        or os.environ.get("ARCHITECT_REPO_PATH", "")
        or os.environ.get("BACKEND_BUILDER_REPO_PATH", "")
    ).strip()
    if override:
        return Path(override).resolve()
    # agents/graphs/backend_builder.py → repo root
    return Path(__file__).resolve().parents[2]


def _normalize_path(path: str) -> str:
    rel = path.replace("\\", "/").strip()
    while rel.startswith("./"):
        rel = rel[2:]
    return rel


def _path_is_blocked(rel: str) -> bool:
    rel = _normalize_path(rel)
    if not rel or ".." in rel.split("/"):
        return True
    if rel.startswith("/") or (len(rel) > 1 and rel[1] == ":"):
        return True
    name = Path(rel).name
    for pattern in BLOCKED_PATH_PATTERNS:
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(name, pattern):
            return True
        # Also match basename-only patterns against full relative path segments
        if "/" not in pattern.rstrip("*") and fnmatch.fnmatch(name, pattern):
            return True
    return False


def _count_changed_lines(old: str, new: str) -> int:
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    diff = list(
        difflib.unified_diff(old_lines, new_lines, lineterm="", n=0)
    )
    # Count added/removed lines (skip --- +++ @@ headers)
    return sum(
        1
        for line in diff
        if (line.startswith("+") or line.startswith("-"))
        and not line.startswith("+++")
        and not line.startswith("---")
    )


def _read_file_text(root: Path, rel: str) -> str:
    path = root / rel
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _call_gemini_rest(prompt: str, model_name: str, api_key: str) -> str:
    _ensure_ssl_certs()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={api_key}"
    )
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2},
            },
        )
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


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise RuntimeError("LLM plan did not contain JSON object")
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise RuntimeError("LLM plan JSON is not an object")
    return data


def _github_token() -> str:
    token = (os.environ.get("GITHUB_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("GITHUB_TOKEN env var NAME is missing (value not logged)")
    return token


def _github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "olife1-backend-builder",
    }


def _run_git(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    # Avoid interactive prompts; never print tokens
    full_env.setdefault("GIT_TERMINAL_PROMPT", "0")
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=full_env,
        check=False,
    )
    if check and proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[:2000]
        raise RuntimeError(f"git {' '.join(args)} failed: {err}")
    return proc


def validate_diff(
    files: list[dict[str, Any]],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """HARDCODED checks — runs AFTER plan, BEFORE any writes."""
    blocked_attempted: list[str] = []
    if not isinstance(files, list) or not files:
        return {
            "ok": False,
            "reason": "plan.files must be a non-empty list",
            "files_blocked_attempted": [],
            "lines_changed": 0,
            "files_changed": [],
        }
    if len(files) > MAX_FILES_PER_JOB:
        return {
            "ok": False,
            "reason": f"Too many files ({len(files)} > {MAX_FILES_PER_JOB})",
            "files_blocked_attempted": [],
            "lines_changed": 0,
            "files_changed": [],
        }

    total_lines = 0
    changed: list[str] = []
    for item in files:
        if not isinstance(item, dict):
            return {
                "ok": False,
                "reason": "each files[] entry must be an object",
                "files_blocked_attempted": blocked_attempted,
                "lines_changed": total_lines,
                "files_changed": changed,
            }
        rel = _normalize_path(str(item.get("path") or ""))
        action = str(item.get("action") or "").strip().lower()
        content = item.get("content")
        if content is None or not isinstance(content, str):
            return {
                "ok": False,
                "reason": f"Missing string content for {rel or '<empty>'}",
                "files_blocked_attempted": blocked_attempted,
                "lines_changed": total_lines,
                "files_changed": changed,
            }
        if action not in ("create", "modify"):
            return {
                "ok": False,
                "reason": f"Invalid action for {rel}: {action!r}",
                "files_blocked_attempted": blocked_attempted,
                "lines_changed": total_lines,
                "files_changed": changed,
            }
        if not rel or ".." in Path(rel).parts or ".." in rel:
            blocked_attempted.append(rel or "<empty>")
            return {
                "ok": False,
                "reason": f"Path traversal or empty path refused: {rel!r}",
                "files_blocked_attempted": blocked_attempted,
                "lines_changed": total_lines,
                "files_changed": changed,
            }
        # Absolute / outside repo
        try:
            resolved = (repo_root / rel).resolve()
            if not str(resolved).startswith(str(repo_root.resolve())):
                blocked_attempted.append(rel)
                return {
                    "ok": False,
                    "reason": f"Path outside repo root refused: {rel}",
                    "files_blocked_attempted": blocked_attempted,
                    "lines_changed": total_lines,
                    "files_changed": changed,
                }
        except OSError:
            blocked_attempted.append(rel)
            return {
                "ok": False,
                "reason": f"Unresolvable path refused: {rel}",
                "files_blocked_attempted": blocked_attempted,
                "lines_changed": total_lines,
                "files_changed": changed,
            }

        if _path_is_blocked(rel):
            blocked_attempted.append(rel)
            return {
                "ok": False,
                "reason": (
                    f"Blocked path refused: {rel} "
                    f"(matches BLOCKED_PATH_PATTERNS)"
                ),
                "files_blocked_attempted": blocked_attempted,
                "lines_changed": total_lines,
                "files_changed": changed,
            }

        old = _read_file_text(repo_root, rel)
        if action == "modify" and not old and not (repo_root / rel).exists():
            # Allow modify→create if file missing, but still count lines
            pass
        if action == "create" and (repo_root / rel).is_file():
            return {
                "ok": False,
                "reason": f"create requested but file exists: {rel}",
                "files_blocked_attempted": blocked_attempted,
                "lines_changed": total_lines,
                "files_changed": changed,
            }
        total_lines += _count_changed_lines(old, content)
        changed.append(rel)

    if total_lines > MAX_LINES_CHANGED:
        return {
            "ok": False,
            "reason": (
                f"Diff too large ({total_lines} lines > {MAX_LINES_CHANGED})"
            ),
            "files_blocked_attempted": blocked_attempted,
            "lines_changed": total_lines,
            "files_changed": changed,
        }

    return {
        "ok": True,
        "reason": "",
        "files_blocked_attempted": [],
        "lines_changed": total_lines,
        "files_changed": changed,
    }


def plan(state: BackendBuilderState) -> BackendBuilderState:
    """Node 1: LLM structured plan (Gemini REST / httpx only)."""
    api_key = getattr(settings, "GEMINI_API_KEY", "") or os.environ.get(
        "GEMINI_API_KEY", ""
    )
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    model_name = getattr(settings, "GEMINI_MODEL", None) or os.environ.get(
        "GEMINI_MODEL", "gemini-3.5-flash"
    )
    # Verify model by NAME only (do not log key)
    if not (model_name or "").strip():
        raise RuntimeError("GEMINI_MODEL env var NAME is missing")

    command = (state.get("command") or "").strip()
    if not command:
        raise ValueError("BackendBuilder command is empty")

    root = _repo_root()
    # Seed context for common backend files (full content so LLM can modify)
    context_files = [
        "sitepages/views.py",
        "sitepages/urls.py",
        "sitepages/models.py",
        "crm/urls.py",
    ]
    context_blobs = []
    for rel in context_files:
        text = _read_file_text(root, rel)
        if text:
            context_blobs.append(f"### {rel}\n```python\n{text}\n```")

    prompt = (
        "You are BackendBuilder for the olife1 Django monorepo.\n"
        "Produce a JSON plan ONLY (no markdown prose outside JSON) with shape:\n"
        '{"files":[{"path":"relative/path.py","action":"create|modify",'
        '"content":"<FULL file contents>"}],"summary":"<short>"}\n'
        "OR on refusal:\n"
        '{"error":"<reason>","files":[]}\n\n'
        "HARD RULES:\n"
        f"- You MUST refuse (error) if the task requires touching any of: "
        f"{json.dumps(BLOCKED_PATH_PATTERNS)}\n"
        "- Backend only: prefer sitepages/*.py, crm/*.py, agents/*.py "
        "(not templates/, static/).\n"
        "- Do NOT create migration files. If models change would need "
        "makemigrations, return error explaining that.\n"
        "- Max 10 files. Prefer minimal diffs. Provide FULL file content "
        "for every create/modify.\n"
        "- Never touch main/prod. Base branch is staging.\n\n"
        f"TASK:\n{command}\n\n"
        "CURRENT REPO CONTEXT (may be truncated elsewhere; use these):\n"
        + "\n\n".join(context_blobs)
    )
    raw = _call_gemini_rest(prompt, model_name.strip(), api_key)
    data = _extract_json(raw)
    if data.get("error"):
        return {
            "plan": {
                "files": [],
                "summary": "",
                "error": str(data["error"]),
            }
        }
    files = data.get("files") or []
    summary = str(data.get("summary") or "").strip()
    return {"plan": {"files": files, "summary": summary, "error": None}}


def validate(state: BackendBuilderState) -> BackendBuilderState:
    """Node 2: hardcoded validate_diff BEFORE any writes."""
    plan_data = state.get("plan") or {}
    if plan_data.get("error"):
        return {
            "validation": {
                "ok": False,
                "reason": f"LLM refused: {plan_data['error']}",
                "files_blocked_attempted": [],
                "lines_changed": 0,
                "files_changed": [],
            }
        }
    result = validate_diff(plan_data.get("files") or [], repo_root=_repo_root())
    return {"validation": result}


def apply(state: BackendBuilderState) -> BackendBuilderState:
    """Node 3: write files on branch agent/backend/<job_uuid> (worktree)."""
    validation = state.get("validation") or {}
    if not validation.get("ok"):
        return {}

    job_id = (state.get("job_id") or "").strip()
    if not job_id:
        raise RuntimeError("job_id required for branch name")
    branch = f"agent/backend/{job_id}"
    root = _repo_root()
    plan_data = state.get("plan") or {}
    files = plan_data.get("files") or []

    work = Path(tempfile.mkdtemp(prefix="bb-worktree-"))
    try:
        _run_git(["fetch", "origin", BASE_BRANCH], cwd=root)
        # Detached worktree from origin/staging
        _run_git(
            ["worktree", "add", "-B", branch, str(work), f"origin/{BASE_BRANCH}"],
            cwd=root,
        )
        written: list[str] = []
        for item in files:
            rel = _normalize_path(str(item["path"]))
            content = item["content"]
            if not content.endswith("\n"):
                content += "\n"
            target = work / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(rel)
        return {
            "work_dir": str(work),
            "branch": branch,
            "files_changed": written,
        }
    except Exception:
        # Cleanup partial worktree
        try:
            _run_git(["worktree", "remove", "--force", str(work)], cwd=root, check=False)
        except Exception:
            shutil.rmtree(work, ignore_errors=True)
        raise


def verify(state: BackendBuilderState) -> BackendBuilderState:
    """Node 4: python manage.py check in the worktree."""
    validation = state.get("validation") or {}
    if not validation.get("ok"):
        return {}
    work = Path(state.get("work_dir") or "")
    if not work.is_dir():
        return {
            "django_check": {"ok": False, "output": "work_dir missing"},
        }

    env = os.environ.copy()
    env.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    # Prefer sqlite for check if no DB needed — still uses project settings
    proc = subprocess.run(
        [os.environ.get("PYTHON", "python"), "manage.py", "check"],
        cwd=str(work),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    ok = proc.returncode == 0
    return {"django_check": {"ok": ok, "output": out[:8000], "returncode": proc.returncode}}


def _ensure_label(client: httpx.Client, token: str) -> None:
    base = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
    headers = _github_headers(token)
    resp = client.get(f"{base}/labels/{quote(AGENT_LABEL)}", headers=headers)
    if resp.status_code == 200:
        return
    if resp.status_code == 404:
        create = client.post(
            f"{base}/labels",
            headers=headers,
            json={
                "name": AGENT_LABEL,
                "color": "5319e7",
                "description": "Opened by an Olife agent; needs owner review",
            },
        )
        if create.status_code not in (200, 201):
            raise RuntimeError(
                f"Failed to create label {AGENT_LABEL}: "
                f"{create.status_code} {create.text[:300]}"
            )
        return
    raise RuntimeError(f"Label check failed: {resp.status_code} {resp.text[:300]}")


def publish(state: BackendBuilderState) -> BackendBuilderState:
    """Node 5: single commit, push (token in remote URL only), open PR + label."""
    validation = state.get("validation") or {}
    check = state.get("django_check") or {}
    if not validation.get("ok"):
        return {}
    if not check.get("ok"):
        return {}

    token = _github_token()  # presence of NAME; value never logged
    work = Path(state["work_dir"])
    branch = state["branch"]
    root = _repo_root()
    plan_data = state.get("plan") or {}
    summary = (plan_data.get("summary") or "backend change").strip()
    short = summary[:72].rstrip(".")
    files = state.get("files_changed") or []
    lines = int((validation.get("lines_changed") or 0))

    author_name = os.environ.get("GIT_AUTHOR_NAME", "Olife Agent")
    author_email = os.environ.get("GIT_AUTHOR_EMAIL", "agent@olife1.com")
    git_env = {
        "GIT_AUTHOR_NAME": author_name,
        "GIT_AUTHOR_EMAIL": author_email,
        "GIT_COMMITTER_NAME": author_name,
        "GIT_COMMITTER_EMAIL": author_email,
    }

    _run_git(["add", "-A"], cwd=work)
    status = _run_git(["status", "--porcelain"], cwd=work)
    if not (status.stdout or "").strip():
        raise RuntimeError("No changes to commit after apply")

    msg = f"agent/backend: {short}"
    _run_git(["commit", "-m", msg], cwd=work, env=git_env)

    # Push with token injected at push time only (not written to disk)
    remote = (
        f"https://x-access-token:{quote(token, safe='')}"
        f"@github.com/{GITHUB_OWNER}/{GITHUB_REPO}.git"
    )
    # Never force-push; never push main
    if branch == "main" or branch.startswith("main/"):
        raise RuntimeError("Refusing to push main")
    if not branch.startswith("agent/backend/"):
        raise RuntimeError(f"Refusing unexpected branch name: {branch}")
    push = subprocess.run(
        ["git", "push", "-u", remote, f"HEAD:refs/heads/{branch}"],
        cwd=str(work),
        capture_output=True,
        text=True,
        env={**os.environ, **git_env, "GIT_TERMINAL_PROMPT": "0"},
        check=False,
    )
    if push.returncode != 0:
        err = (push.stderr or push.stdout or "").strip()
        # Redact token if it somehow appears
        err = err.replace(token, "***")
        raise RuntimeError(f"git push failed: {err[:2000]}")

    diff_summary = {
        "files": files,
        "lines_changed": lines,
        "summary": summary,
    }
    body = (
        "## Agent-generated PR\n\n"
        f"{summary}\n\n"
        f"**Branch:** `{branch}`\n"
        f"**Files:** {', '.join(f'`{f}`' for f in files)}\n"
        f"**Lines changed (approx):** {lines}\n\n"
        "### Owner checklist\n"
        "- [ ] Review diff carefully (agent-generated)\n"
        "- [ ] Confirm no migrations/settings/secrets touched\n"
        "- [ ] Merge manually only when satisfied\n"
        "- [ ] Do not auto-merge\n"
    )

    _ensure_ssl_certs()
    with httpx.Client(timeout=60.0) as client:
        headers = _github_headers(token)
        _ensure_label(client, token)
        pr_resp = client.post(
            f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/pulls",
            headers=headers,
            json={
                "title": f"agent/backend: {short}",
                "head": branch,
                "base": BASE_BRANCH,
                "body": body,
            },
        )
        if pr_resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Open PR failed: {pr_resp.status_code} {pr_resp.text[:500]}"
            )
        pr = pr_resp.json()
        pr_url = pr.get("html_url") or ""
        pr_number = pr.get("number")
        if pr_number:
            lab = client.post(
                f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
                f"/issues/{pr_number}/labels",
                headers=headers,
                json={"labels": [AGENT_LABEL]},
            )
            if lab.status_code not in (200, 201):
                raise RuntimeError(
                    f"Label PR failed: {lab.status_code} {lab.text[:300]}"
                )

    # Cleanup worktree (do not delete remote branch)
    try:
        _run_git(["worktree", "remove", "--force", str(work)], cwd=root, check=False)
    except Exception:
        shutil.rmtree(work, ignore_errors=True)

    return {
        "pr_url": pr_url,
        "publish": {"ok": True, "pr_url": pr_url, "diff_summary": diff_summary},
        "work_dir": "",
    }


def finalize(state: BackendBuilderState) -> BackendBuilderState:
    """Node 6: JSON into AgentJob.result shape."""
    validation = state.get("validation") or {}
    check = state.get("django_check") or {}
    plan_data = state.get("plan") or {}
    publish_data = state.get("publish") or {}
    branch = state.get("branch") or f"agent/backend/{state.get('job_id') or 'unknown'}"

    files_changed = list(
        state.get("files_changed")
        or validation.get("files_changed")
        or []
    )
    blocked = list(validation.get("files_blocked_attempted") or [])
    lines = int(validation.get("lines_changed") or 0)
    summary = (plan_data.get("summary") or "").strip()

    ok = bool(
        validation.get("ok")
        and check.get("ok")
        and publish_data.get("ok")
        and state.get("pr_url")
    )
    reason = ""
    if not validation.get("ok"):
        reason = validation.get("reason") or "validation failed"
    elif check and not check.get("ok"):
        reason = (
            "manage.py check failed:\n" + str(check.get("output") or "")
        )[:4000]
    elif not publish_data.get("ok") and validation.get("ok") and check.get("ok"):
        reason = state.get("error") or "publish did not complete"
    elif not ok:
        reason = state.get("error") or "backend_builder incomplete"

    payload = empty_backend_builder_result(
        ok=ok,
        pr_url=state.get("pr_url"),
        branch=branch,
        diff_summary={
            "files": files_changed,
            "lines_changed": lines,
            "summary": summary,
        },
        files_changed=files_changed,
        files_blocked_attempted=blocked,
        django_check={
            "ok": bool(check.get("ok")),
            "output": str(check.get("output") or ""),
        },
        reason=reason if not ok else "",
    )
    result = dumps_backend_builder_result(payload)

    # Cleanup leftover worktree on failure paths
    work = state.get("work_dir") or ""
    if work and Path(work).is_dir():
        try:
            _run_git(
                ["worktree", "remove", "--force", work],
                cwd=_repo_root(),
                check=False,
            )
        except Exception:
            shutil.rmtree(work, ignore_errors=True)

    out: BackendBuilderState = {"result": result}
    if not ok:
        out["error"] = reason or "backend_builder failed"
    return out


def _route_after_validate(state: BackendBuilderState) -> str:
    if (state.get("validation") or {}).get("ok"):
        return "apply"
    return "finalize"


def _route_after_verify(state: BackendBuilderState) -> str:
    if (state.get("django_check") or {}).get("ok"):
        return "publish"
    return "finalize"


def build_graph(checkpointer: PostgresSaver):
    builder = StateGraph(BackendBuilderState)
    builder.add_node("plan", plan)
    builder.add_node("validate", validate)
    builder.add_node("apply", apply)
    builder.add_node("verify", verify)
    builder.add_node("publish", publish)
    builder.add_node("finalize", finalize)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "validate")
    builder.add_conditional_edges(
        "validate",
        _route_after_validate,
        {"apply": "apply", "finalize": "finalize"},
    )
    builder.add_edge("apply", "verify")
    builder.add_conditional_edges(
        "verify",
        _route_after_verify,
        {"publish": "publish", "finalize": "finalize"},
    )
    builder.add_edge("publish", "finalize")
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


def run_backend_builder(
    command: str, thread_id: str, job_id: str | None = None
) -> str:
    """Invoke BackendBuilder; returns JSON result string. Raises on failure."""
    conn = _checkpoint_conn_string()
    with PostgresSaver.from_conn_string(conn) as checkpointer:
        checkpointer.setup()
        graph = build_graph(checkpointer)
        out = graph.invoke(
            {
                "command": command,
                "job_id": job_id or thread_id,
            },
            config={"configurable": {"thread_id": thread_id}},
        )
    result = (out.get("result") or "").strip()
    if out.get("error"):
        # Attach JSON result into the exception message for the worker to store
        raise RuntimeError(result or out["error"])
    if not result:
        raise RuntimeError("BackendBuilder returned empty result")
    return result
