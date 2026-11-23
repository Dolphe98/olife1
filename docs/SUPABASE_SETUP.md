# Supabase Setup (create from scratch)

**Goal:** Supabase Postgres = sole app database · Supabase Storage = media.  
**Railway Postgres:** not used for app data unless a hard technical blocker appears (none identified in Phase 1).

Do **not** commit project refs, URLs, or service-role keys. Store them only in Railway env / local `.env`.

---

## Owner checklist

### A. Create project

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard) and sign in (GitHub or email).
2. **New project** → Organization: create `Olife` (or personal).
3. Project name: `olife1` (or similar). Region: prefer same metro as Railway web region (**iad** / US East if available).
4. Generate a strong DB password → store in a password manager. You will not see it again easily.
5. Wait until project status is **Healthy**.

### B. Connection string for Django

6. Project **Settings → Database**.
7. Copy the **URI** connection string (Transaction / Session pooler recommended for Railway dynos; Direct is fine for one-off migrations from a laptop).
8. Format for Django / `dj-database-url`:

   ```text
   DATABASE_URL=postgres://postgres.<SUPABASE_PROJECT_REF>:<PASSWORD>@<POOLER_HOST>:6543/postgres?sslmode=require
   ```

9. Paste into Railway **staging** and **production** variables (never commit). Also local `.env` (gitignored).

### C. Network / SSL

10. Confirm `sslmode=require` (Supabase requires TLS).
11. If Railway cannot connect: check Supabase **Database → Network** restrictions; allow Railway egress or use pooler + no IP allowlist initially, then tighten.

### D. Storage bucket for media

12. **Storage → New bucket** → name: `media` (public read for published assets, or signed URLs if you prefer private — v1 recommendation: **public** bucket for post/fragment images only; private later for drafts).
13. Policies (SQL editor or UI): allow public `SELECT` on `media` for published paths; allow authenticated/service role `INSERT/UPDATE/DELETE`.
14. Copy:

    - `SUPABASE_URL=https://<SUPABASE_PROJECT_REF>.supabase.co`
    - `SUPABASE_ANON_KEY=<anon public key>` (client-safe if RLS is correct)
    - `SUPABASE_SERVICE_ROLE_KEY=<service role>` (**server only**, Railway secret)

### E. Django wiring (after APPROVE BUILD — do not do in Phase 1 code)

15. Keep using `dj-database-url` + `psycopg2-binary` (already in `requirements.txt`).
16. Add storage backend (e.g. `django-storages` + S3-compatible endpoint Supabase exposes, or supabase-py upload helpers). Exact package choice locked in Phase 2 scaffold.
17. Run `migrate` against Supabase from staging first; never point local DEBUG experiments at production DB.

### F. Confirm

18. From laptop (with `.env`): `python manage.py dbshell` or a trivial `migrate --plan`.
19. Upload a test object to `media/` and fetch its public URL.
20. Reply in chat: “Supabase ready” with **no secrets** (only “staging connected / prod connected”).

---

## Placeholders for docs / `.env.example`

| Variable | Placeholder |
|----------|-------------|
| Project ref | `<SUPABASE_PROJECT_REF>` |
| Database URL | `<DATABASE_URL>` |
| API URL | `<SUPABASE_URL>` |
| Anon key | `<SUPABASE_ANON_KEY>` |
| Service role | `<SUPABASE_SERVICE_ROLE_KEY>` |
| Storage bucket | `media` |
