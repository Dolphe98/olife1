# Multi-Agent Topology — Olife LangGraph

Self-hosted **LangGraph** (library only — not LangGraph Platform).  
Each agent is a named graph node, addressable by name.

---

## 1. Topology changes vs initial suggestion

| Suggested | Decision | Justification |
|-----------|----------|---------------|
| Orchestrator | **Keep** | Single entry + routing |
| Architect | **Keep** | Specs / ADRs before code |
| Designer | **Keep** | Tokens, templates aesthetics, asset kit |
| FrontendBuilder | **Keep** (Django templates/CSS/JS only) | Still a distinct skill from models/APIs |
| BackendBuilder | **Keep** | Models, views, auth, CRM APIs |
| ContentMigrator | **Keep** | Seed → Post/Media/redirects |
| SEOSpecialist | **Keep** | Sitemap, meta, JSON-LD, RSS |
| CRMBuilder | **Keep** | `/admin` dashboard + GA4 |
| Deployer | **Keep** | Railway + git + audit log |
| QAInspector | **Keep** | Smoke + healthz + brand voice spot-check |
| — | **Add BrandVoice** | Manifesto compliance on user-facing copy |
| — | **Add SiteAuditor** | Recurring live/repo audits (SSL, links, inventory) |

Split Frontend/Backend retained because Olife is template-rendered Django: CSS/motion vs data layer still diverge. No React agent.

---

## 2. Agent catalog

### Orchestrator
- **Purpose:** Parse intent; plan DAG; call agents; enforce HITL gates.
- **Input:** Chat/command text, task id, repo state summary.
- **Output:** Plan markdown, assigned tasks, final report.
- **Tools:** `list_agents`, `run_node`, `read_file`, `git_status`, `write_audit`.
- **Commands:** `/plan`, `/status`, `/report`, `/pause`, routes all others.
- **Failure:** Pause graph; emit `/report` with blocker; never deploy on own.

### Architect
- **Purpose:** Technical design within locked stack; update docs when architecture shifts.
- **Input:** Feature brief, constraints.
- **Output:** Spec section, file touch list, risks.
- **Tools:** `read_docs`, `search_repo`, `web_docs` (Railway/Supabase/Django).
- **Commands:** via `/plan`, `/build <architecture task>`.
- **Failure:** Return `needs_human` if stack lock would break.

### Designer
- **Purpose:** DESIGN.md tokens → template/CSS; asset kit; anti-reference checks.
- **Input:** Page brief, manifesto excerpts.
- **Output:** CSS variables, template structure notes, SVG/PNG asset paths.
- **Tools:** `read_file`, `write_file` (static/templates), image gen (optional).
- **Commands:** `/build <design…>`.
- **Failure:** Revert file writes; flag contrast/a11y issues.

### FrontendBuilder
- **Purpose:** Django templates, `static/css`, `static/js`, accessibility, motion.
- **Input:** Designer spec + routes.
- **Output:** Template/static PRs on feature branch.
- **Tools:** `write_file`, `git_commit` (feature branch), `preview_url`.
- **Commands:** `/build <ui…>`, `/preview`.
- **Failure:** Do not push `main`; open fix commit on same branch.

### BackendBuilder
- **Purpose:** Models, views, allauth flags, `/healthz`, email, Supabase wiring.
- **Input:** DATA_MODEL.md tasks.
- **Output:** Migrations, views, settings changes.
- **Tools:** `write_file`, `run_manage` (migrate/check), `git`.
- **Commands:** `/build <backend…>`.
- **Failure:** Stop before deploy; include migration risk in report.

### ContentMigrator
- **Purpose:** Execute MIGRATION_REPORT after approval; Media upload; redirects.
- **Input:** URL map, seed data.
- **Output:** DB rows, redirect table, migration notes.
- **Tools:** `manage.py` commands, Supabase storage, `write_audit`.
- **Commands:** `/build <migrate content>`.
- **Failure:** No partial prod redirects; rollback DB migration if staging fails.

### SEOSpecialist
- **Purpose:** robots, sitemap, RSS, JSON-LD, OG/Twitter, slug redirects.
- **Input:** Post/Page metadata.
- **Output:** SEO routes + per-template tags.
- **Tools:** `write_file`, link crawler, `preview`.
- **Commands:** `/build <seo…>`, contributes to `/report`.
- **Failure:** Block launch checklist item; non-fatal for staging.

### CRMBuilder
- **Purpose:** Staff `/admin` KPIs (GA4), pipeline, deploy health — read-only v1.
- **Input:** GA4 credentials presence, DeployEvent rows.
- **Output:** CRM views/templates.
- **Tools:** GA4 Data API client, Railway status read, `write_file`.
- **Commands:** `/crm`, `/build <crm…>`.
- **Failure:** Show empty states; never break public site.

### Deployer
- **Purpose:** Push allowed branches; Railway deploy staging; prod only with APPROVE DEPLOY; rollback.
- **Input:** SHA, target env, approval token in state.
- **Output:** Deployment URL, audit entry.
- **Tools:** `git_push`, Railway MCP/CLI, `write_audit`, health poll.
- **Commands:** `/preview`, `/deploy`, `APPROVE DEPLOY`, `ROLLBACK`.
- **Failure:** Auto-stop; trigger rollback on healthz fail; audit always.

### QAInspector
- **Purpose:** Smoke routes, SSL sanity, form posts, brand voice spot-check.
- **Input:** Base URL (staging/prod).
- **Output:** Pass/fail checklist.
- **Tools:** HTTP client, simple HTML asserts, BrandVoice sample.
- **Commands:** after `/preview`, before `/deploy` promote.
- **Failure:** Block APPROVE DEPLOY recommendation.

### BrandVoice
- **Purpose:** Score/rewrite user-facing copy against `docs/BRAND.md`.
- **Input:** Draft strings.
- **Output:** Pass / rewrite suggestions.
- **Tools:** LLM via adapter, read BRAND.md.
- **Commands:** hooked by Orchestrator on content tasks.
- **Failure:** Soft-fail with warnings unless copy is launch-critical.

### SiteAuditor
- **Purpose:** Recurring inventory (pages, SSL, env presence counts).
- **Input:** Live URL + repo path.
- **Output:** Audit markdown fragment for `/status` / `/report`.
- **Tools:** HTTP, DNS lookup, Railway domain-status (no secret dump).
- **Commands:** `/status`, `/report`.
- **Failure:** Report partial results.

---

## 3. Google Chat commands → agents

| Trigger | Primary agent | Notes |
|---------|---------------|-------|
| `/status` | SiteAuditor + Orchestrator | Deploy health, SSL, pipeline summary |
| `/plan` | Orchestrator + Architect | Plan only |
| `/build <task>` | Orchestrator → specialists | Staging push allowed post APPROVE BUILD |
| `/preview` | Deployer + QAInspector | Staging URL |
| `/deploy` | Deployer | Staging by default; prod needs APPROVE DEPLOY |
| `/rollback` | Deployer | Last prod deploy |
| `/report` | Orchestrator | Aggregate |
| `/crm` | CRMBuilder | KPI snapshot |
| `/pause` | Orchestrator | Interrupt graph |
| `APPROVE BUILD` | Orchestrator | Unlocks push + staging deploy autonomy |
| `APPROVE DEPLOY` | Deployer | Staging → production |
| `ROLLBACK` | Deployer | Alias of `/rollback` |

---

## 4. LangGraph diagram (text)

```text
                    ┌──────────────┐
                    │  Chat/Cmd    │
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
              ┌────►│ Orchestrator │◄──── /pause
              │     └──────┬───────┘
              │            │ route
              │            ▼
              │     ┌──────────────┐
              │     │  Architect   │──docs──┐
              │     └──────┬───────┘        │
              │            ▼                │
              │     ┌──────────────┐        │
              │     │   Designer   │        │
              │     └──────┬───────┘        │
              │            ▼                │
              │     ┌──────────────┐        │
              │     │BrandVoice    │◄───────┘
              │     └──────┬───────┘
              │            ▼
              │   ┌────────┴────────┐
              │   ▼                 ▼
              │ FrontendBuilder  BackendBuilder
              │   │                 │
              │   └────────┬────────┘
              │            ▼
              │     ContentMigrator / SEOSpecialist / CRMBuilder
              │            │
              │            ▼
              │     ┌──────────────┐
              │     │ QAInspector  │
              │     └──────┬───────┘
              │            │
              │   {smoke_ok?}────no───► Orchestrator (fix / report)
              │            │yes
              │            ▼
              │   ★ HITL: APPROVE DEPLOY? (prod only)
              │      no → stop / wait
              │      yes ▼
              │     ┌──────────────┐
              │     │   Deployer   │──audit──► logs/audit/
              │     └──────┬───────┘
              │            ▼
              │     healthz poll ─fail─► Deployer.rollback
              │            │ok
              └────────────┴──► SiteAuditor ──► /report
```

**Conditional edges:** `smoke_ok`, `approvals.build`, `approvals.deploy`, `health_ok`, `pause_requested`.  
**HITL checkpoints:** before first autonomous staging era (`APPROVE BUILD` once); before every production promote (`APPROVE DEPLOY`); before destructive schema/data ops (explicit confirm in state).

---

## 5. Google Chat feasibility (verified against Google docs)

Google’s Chat developer docs state: **“Google Chat API is only available to Google Workspace users.”** Configuring a Chat app / calling Chat API requires a **Business or Enterprise Workspace** account with Chat access. Personal Gmail can *use* some Chat apps as an end user but **cannot host/configure** the bot.

**Phase 5 gate:** Owner must confirm Workspace vs personal Gmail before build.

**Fallback (if personal only):**

1. **Preferred:** Staff **web command console** at `/admin/commands/` (same command grammar).
2. **Alternative:** Telegram bot (BotFather token in Railway env) with identical command parser.
3. Keep `chatbot/` adapters: `GoogleChatAdapter` | `TelegramAdapter` | `WebConsoleAdapter` behind one interface.

---

## 6. LLM config

- Secrets: `GEMINI_API_KEY`, optional `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` on Railway.
- Non-secrets: `config/llm.yaml` — primary `gemini-flash`, optional `gemini-pro`, fallbacks list, temperatures.
- Adapter pattern: `agents/tools/llm.py` → `complete(messages, model=None)`.
