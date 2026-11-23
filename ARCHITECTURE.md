# Architecture — Olife Platform

**Phase:** 1 (plan only)  
**Repo:** extend `Dolphe98/olife1` (Django) — not a greenfield rewrite.  
**Canonical site:** `https://olife1.com` (www → apex 301)

---

## 1. Target repository tree

```text
olife1/
├── .cursor/
│   └── rules/                    # project conventions (alwaysApply)
├── .github/
│   └── workflows/                # CI: lint/migrate-check (optional); no required tests
├── agents/                       # LangGraph multi-agent (plain library, self-hosted)
│   ├── graph.py                  # StateGraph wiring
│   ├── state.py
│   ├── nodes/                    # one module per agent
│   ├── tools/                    # gh, railway, supabase, seo, ga4 helpers
│   └── prompts/
├── chatbot/                      # Phase 5: Telegram + /admin/commands/ (one router)
│   ├── router.py                 # shared CommandRouter (plain text)
│   ├── telegram_adapter.py
│   ├── web_console_adapter.py
│   └── commands/
├── config/                       # Django project package (exists)
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── llm.yaml                  # non-secret model routing (Gemini Flash default)
├── sitepages/                    # primary Django app (exists; evolve)
├── crm/                          # staff dashboard app → mounts at /admin
├── accounts/                     # allauth adapters / Profile
├── templates/
├── static/
├── logs/
│   └── audit/                    # YYYY-MM-DD.md deploy/schema/destructive entries
├── docs/                         # BRAND, SUPABASE_SETUP, GA4_SETUP
├── ARCHITECTURE.md               # this file (Phase 1 plans at repo root)
├── scripts/                      # migrate_media, smoke_staging, seed helpers
├── manage.py
├── Procfile                      # web
│   # future: Procfile.worker or Railway startCommand for worker
├── requirements.txt
├── railway.toml                  # healthcheckPath=/healthz (add in Phase 2)
├── .env.example
└── README.md
```

No Next.js/React frontend. Django templates only.

---

## 2. Services on Railway

| Service | Env | Role |
|---------|-----|------|
| `web` | production | Gunicorn Django; public site + `/admin` CRM + `/healthz` |
| `worker` | production | LangGraph jobs / long agent runs / newsletter fanout later |
| `web` (or `web-staging`) | staging | Same image; `staging.olife1.com` |
| `worker` | staging | Optional; can share low-cost single worker initially |

**Database:** Supabase Postgres via `DATABASE_URL` only.  
**Media:** Supabase Storage.  
**Do not** attach Railway Postgres for app data unless a documented blocker appears.

### Staging vs production

| | Staging | Production |
|--|---------|------------|
| Branch auto-deploy | `staging` | `main` |
| Domain | `staging.olife1.com` | `olife1.com` |
| Agent deploy | autonomous after APPROVE BUILD | requires **APPROVE DEPLOY** |
| DB | Supabase staging project **or** separate Supabase branch/DB | Supabase prod |
| Seeds | allowed | never auto-seed destructive data |

### Health & rollback

- Every service: `GET /healthz` → 200 JSON `{ "status": "ok" }`.
- Railway healthcheck + restart/rollback on failed checks (configure in `railway.toml` / service settings).
- App-level rollback: redeploy previous successful deployment; agent writes `logs/audit/{date}.md`.

---

## 3. Supabase connection strategy

1. `dj-database-url` parses `DATABASE_URL` (already in settings).
2. Prefer **pooler** URI on Railway web/worker (`sslmode=require`).
3. Migrations run on deploy start (Procfile) **or** release-phase command — pick one in Phase 2; avoid double-migrate races.
4. Media via Storage API + service role on server; public URLs for published assets.
5. Never commit service role key.

---

## 4. LangGraph runtime model

- Library: `langgraph` in-process on the **worker** (and optionally short graphs on web for `/admin` “run agent” later).
- **Not** LangGraph Platform.
- Graph: named nodes (agents) + shared `AgentState` (task, approvals, artifacts, errors).
- Checkpoints: memory/SQLite/Postgres checkpointer for interrupt-before-deploy.
- LLM: Google **Gemini Flash** default; Pro via env; thin `LLMAdapter` with Anthropic/OpenAI fallback (`config/llm.yaml` + secrets in env).

Control plane (Phase 5): **Telegram** (primary) + staff **`/admin/commands/`** (backup) → shared `CommandRouter` → enqueue graph on worker. Plain text only — no Google Chat (personal Gmail / no Workspace). See `AGENTS.md`.

---

## 5. Deployment flow

```text
feature/* ──PR──► staging ──agent smoke──► merge main ──APPROVE DEPLOY──► production
                 ▲
                 └── agents may push + deploy staging after APPROVE BUILD
```

1. Feature branch → PR into `staging`.
2. Merge to `staging` → Railway staging auto-deploy → agent smoke (`/healthz`, critical routes).
3. PR/merge `staging` → `main` only after smoke green.
4. Production promote requires human **APPROVE DEPLOY** (Telegram or `/admin/commands/`).
5. **ROLLBACK** → previous prod deployment + audit log.

Secrets: Railway variables per environment. Commit only `.env.example`.

---

## 6. Secrets model

| Location | Contents |
|----------|----------|
| Railway env (staging/prod) | real secrets |
| Local `.env` | gitignored developer secrets |
| `.env.example` | names + placeholders only |
| `config/llm.yaml` | model names, temperature, fallbacks — **no API keys** |
| `logs/audit/` | actions, not secrets |

---

## 7. URL / app architecture

| Path | App |
|------|-----|
| `/` … public pages | `sitepages` |
| `/accounts/` | allauth (flagged) |
| `/admin/` | **custom CRM** (`crm`) staff-only |
| `/django-admin/` | Django admin escape hatch |
| `/healthz` | shared health view |
| `/sitemap.xml`, `/robots.txt`, `/feed.xml` | SEO |

---

## 8. Current production snapshot (audit)

- Django 5.2 + gunicorn + WhiteNoise + sqlite-or-DATABASE_URL.
- Procfile seeds on every boot (`seed_content`) — **must change** before prod CMS (idempotent OK short-term; remove auto-seed for prod in Phase 2/6).
- Custom domains attached; **apex SSL broken** — see `SSL_FIX.md`.
- No `railway.toml` / `/healthz` yet.
- Contact via Formspree; WhatsApp CTAs present (to remove).

---

## 9. Observability (v1)

- Railway logs + `/healthz`.
- Audit markdown under `logs/audit/`.
- GA4 (after setup) for CRM KPIs.
- Drains optional later; not required for Hobby-scale launch.
