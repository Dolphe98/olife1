# Agents (Phase 3A)

Minimal LangGraph runtime: `AgentJob` queue + `agent_worker` + Echo graph (Gemini proof-of-life).

- Submit: `python manage.py agent_submit echo "<command>"`
- Worker: `python manage.py agent_worker`

Hard rules for Phase 3: no media/Storage changes; no RLS; Echo only (no real agents yet).
Topology for later phases: `/AGENTS.md`.
