# Roadmap — Phased delivery

Phase 1 = this branch (`phase-1-plan`): docs only.  
No production code until owner replies **`APPROVE BUILD`**.

---

## Phase 1 — Audit + Spec + Plan _(current)_

**Deliverables:** `docs/*` plans, `.cursor/rules`, `.env.example`, branch `phase-1-plan` (not merged).

**Acceptance criteria**

- [x] Live site + repo audited; SSL diagnosed
- [x] Architecture, agents, data model, design, migration URL map written
- [x] Setup checklists for Supabase + GA4
- [x] Brand manifesto in `docs/BRAND.md`
- [ ] Owner reviews docs
- [ ] Owner executes SSL DNS checklist (`SSL_FIX.md`)
- [ ] Owner replies **APPROVE BUILD** to unlock Phase 2+

---

## Phase 2 — Scaffold (extend Django)

**Work**

- Add `/healthz`; `railway.toml` healthcheck; staging service + `staging.olife1.com`
- Supabase `DATABASE_URL`; stop relying on sqlite in prod; harden Procfile (no dangerous prod re-seed)
- Move Django admin → `/django-admin/`; reserve `/admin/` for CRM shell stub
- Feature flags module; allauth Google plumbing **OFF**
- `ContactMessage` + email; remove WhatsApp CTAs; newsletter → `Subscriber`
- `config/llm.yaml` + empty `agents/` package skeleton (no full graph yet)
- Audit log writer helper; `.github/workflows` optional check

**Acceptance**

- [ ] Staging deploys from `staging` branch; `/healthz` 200
- [ ] Prod still stable; SSL green on apex
- [ ] Supabase migrations apply on staging
- [ ] Contact/newsletter persist in DB
- [ ] No secrets committed

---

## Phase 3 — Agents (LangGraph)

**Work**

- Implement graph + agents per `AGENTS.md`
- Worker service on Railway
- Commands parser (web console stub OK before Chat)
- Staging autonomy after APPROVE BUILD; prod gated

**Acceptance**

- [ ] `/plan` and `/build` produce real PRs to `staging`
- [ ] `/preview` returns staging URL; QAInspector smoke passes
- [ ] Audit entries written for deploys
- [ ] LLM adapter works with Gemini Flash + one fallback provider configured

---

## Phase 4 — CRM (`/admin`)

**Work**

- Read-only KPI dashboard: GA4 traffic, top posts, pipeline status, deploy health
- Comment moderation queue (flagged first)
- Contact inbox UI

**Acceptance**

- [ ] Staff user sees GA4 widgets (or clear empty state)
- [ ] Pipeline + last deploy visible
- [ ] `/django-admin/` still available
- [ ] Public site unaffected if GA4 fails

---

## Phase 5 — Command control surface (Telegram + admin console)

**Locked:** Personal Gmail only — **no Google Chat**. Plain text commands only (no cards/buttons).

**Work**

- Shared `CommandRouter` with the `/slash` grammar from `AGENTS.md`
- **Primary transport:** Telegram bot
- **Backup transport:** staff-only `/admin/commands/` web console (POST same command strings)
- Wire `APPROVE DEPLOY` / `ROLLBACK` / `/pause` through both transports

**Acceptance**

- [ ] Every command in `AGENTS.md` works on Telegram **and** `/admin/commands/`
- [ ] Prod deploy impossible without `APPROVE DEPLOY`
- [ ] `/pause` interrupts in-flight graph
- [ ] No Google Chat code paths or Chat-only UI primitives

---

## Phase 6 — Migration + launch

**Work**

- Execute `MIGRATION_REPORT.md` (slugs, Media→Storage, 301s)
- SEO suite live; Podcast/Store stubs; design polish per `DESIGN.md`
- Remove Formspree; enable flags intentionally
- Prod promote with APPROVE DEPLOY; post-launch `/report`

**Acceptance**

- [ ] All old `/blog/<id>/` URLs 301 to slugs
- [ ] www→apex 301; SSL valid
- [ ] Content counts match report; images on Supabase
- [ ] Launch checklist signed in audit log

---

## Cross-phase invariants

- `main` = production; `staging` = staging
- Secrets only on Railway / local `.env`
- Every deploy/rollback/schema/destructive action → `logs/audit/YYYY-MM-DD.md`
- Brand voice: `docs/BRAND.md`
- No Next.js / no separate SPA
