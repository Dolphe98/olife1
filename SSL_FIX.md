# SSL Fix — olife1.com

**Priority:** P0. Browser shows **Not secure** with `https` struck through on `https://olife1.com`.

**Date audited:** 2026-11-21  
**Production service:** Railway project hosting the Django `olife1` repo (service `web`).  
**IDs omitted from this doc by policy** — use Railway dashboard / local `.env`, not committed docs.

---

## 1. Exact certificate error observed

| Check | Result |
|-------|--------|
| Browser (owner screenshot) | Red **Not secure**; `https` struck through on `https://olife1.com` |
| Python TLS verify | `SSLCertVerificationError: Hostname mismatch, certificate is not valid for 'olife1.com'` |
| Presented cert subject (via local inspection) | `CN=*.up.railway.app` (SAN: `*.up.railway.app`, `up.railway.app`) |
| Railway domain status — **apex** `olife1.com` | Verified: yes · Certificate: **`CERTIFICATE_STATUS_TYPE_ISSUING`** |
| Railway domain status — **www** `www.olife1.com` | Verified: yes · Certificate: **`CERTIFICATE_STATUS_TYPE_VALID`** |

**Interpretation:** Traffic reaches the Django app (HTTP 200, same HTML as the Railway `*.up.railway.app` service domain), but the **custom apex certificate has never finished issuing**. TLS is falling back to the shared `*.up.railway.app` cert → browsers correctly flag a hostname mismatch → “Not secure.”

> Note: Local antivirus TLS inspection (e.g. Avast) may re-sign certificates on the owner machine. The Railway dashboard status (`ISSUING` + unset apex CNAME) is the authoritative cause; browser “Not secure” is the user-visible symptom.

---

## 2. DNS reality vs assumption

Owner believed DNS was “fully on Railway nameservers.” Live lookup on 2026-11-21 showed:

| Record | Observed |
|--------|----------|
| Apex NS | `ns1.dns-parking.com`, `ns2.dns-parking.com` (**Hostinger parking DNS** — not Railway) |
| Apex A | `olife1.com` → `153.52.255.98` |
| www CNAME | `www.olife1.com` → `jghbrc1s.up.railway.app` (**propagated**) |
| Railway-required apex CNAME | `olife1.com` → `6uu49l2o.up.railway.app` · status: **PROPAGATED / currently unset** |

**Root cause chain:**

1. Apex does **not** point at the Railway target Railway expects for certificate issuance.
2. Railway cannot complete Let’s Encrypt (or equivalent) issuance for `olife1.com` → status stays **ISSUING**.
3. Edge serves `*.up.railway.app` cert for HTTPS to the apex hostname → **hostname mismatch**.
4. `www` has a valid Railway cert, but canonical is apex — users hitting apex see the warning. Also www currently points at an older Railway hostname (`jghbrc1s…`) that may differ from the apex target Railway now shows (`6uu49l2o…`); align both to the targets shown in the Railway Domains UI **today**.

This is **not** primarily an HSTS or mixed-content bug. Mixed content was not observed as the cause of the lock icon failure. HSTS is not configured in Django settings yet.

---

## 3. Likely causes (ranked)

1. **Apex DNS CNAME/ALIAS missing or wrong** (confirmed by Railway: required CNAME unset) — primary.
2. **Nameservers still on Hostinger parking DNS** — explains why Railway-managed DNS assumption is false; records must be edited at the registrar that controls those NS, **or** NS must be moved to Railway Domains (only if the domain is in Railway Domains with Railway nameservers).
3. **www CNAME target drift** — valid cert today, but target hostname may be stale vs Railway’s current required target.
4. **Certificate stuck in ISSUING** — consequence of (1); after DNS fix, use Railway “retry certificate issuance.”
5. **Apex vs www inconsistency** — no 301 www→apex yet (to be added in app after SSL is healthy).
6. **HSTS / mixed content** — secondary; address only after green lock.

---

## 4. Concrete fix steps (owner clicks + DNS)

### Preflight (read-only)

1. Open Railway → project that serves olife1 → service **web** → **Settings → Networking / Domains**.
2. Confirm both `olife1.com` and `www.olife1.com` are listed.
3. Copy the **exact** required DNS records Railway shows for each (do not use the hostnames in this doc if the UI differs — UI wins).

### Path A — Recommended if domain stays at current registrar (parking NS)

You keep nameservers at the current DNS host and create records there.

**You click / edit:**

1. Log into the account that controls `ns1/ns2.dns-parking.com` for `olife1.com` (typically Hostinger / the domain registrar).
2. For **apex** `olife1.com`, add exactly what Railway shows. Common patterns:
   - **CNAME flattening / ALIAS / ANAME** to the Railway target (preferred for apex), **or**
   - Railway-documented **CNAME** on apex if your DNS host supports apex CNAME flattening.
   - Do **not** leave the apex on the parking A record `153.52.255.98`.
3. For **www**, set **CNAME** to the Railway target shown for `www.olife1.com` (replace `jghbrc1s.up.railway.app` if Railway now shows a different target).
4. Remove conflicting A/AAAA/CNAME records for apex/www.
5. Wait for DNS propagation (often 5–60 minutes; up to 48h at stubborn resolvers).
6. In Railway Domains UI, confirm apex required record flips from **unset** to **matched**.
7. If certificate remains **ISSUING** after DNS matches: click **Retry certificate issuance** (Railway dashboard or `railway domain` CLI retry). Docs: Railway SSL troubleshooting / domain certificate retry.
8. Verify in an **incognito** window (or phone cellular): `https://olife1.com` shows a closed lock; cert CN/SAN includes `olife1.com`.

### Path B — Railway-managed DNS (only if domain is under Railway Domains)

Railway fully manages DNS for domains purchased/hosted through Railway Domains (`railway.com/workspace/domains`). If `olife1.com` is **not** listed there, Path A applies.

**You click:**

1. Open **Workspace → Domains** in Railway.
2. If the domain is present and NS are custom/parking: either **Reset to Railway** nameservers (per Railway Domains docs) **or** stay on Path A.
3. If switching NS: at the registrar, set nameservers to the values Railway displays → wait for NS propagation → confirm Railway DNS records for the web service are present → retry certificate if needed.

### After green lock (agent will implement after APPROVE BUILD — listed here for sequencing)

9. Enforce canonical host: **www → apex 301** (`https://www.olife1.com/*` → `https://olife1.com/*`).
10. Set Django `SECURE_SSL_REDIRECT`, HSTS (start with short `max-age`, then raise), `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` for apex + staging.
11. Add `staging.olife1.com` as a custom domain on the **staging** Railway environment/service; CNAME to staging Railway target; obtain cert before smoke tests.

---

## 5. Owner checklist (copy/paste)

1. [ ] Open Railway → web service → Domains → copy required records for `olife1.com` and `www.olife1.com`.
2. [ ] Open DNS host for parking nameservers (or Railway Domains if applicable).
3. [ ] Fix **apex** to Railway target; delete parking A record.
4. [ ] Align **www** CNAME to Railway’s current www target.
5. [ ] Wait until Railway shows DNS matched for apex.
6. [ ] Retry certificate issuance if still ISSUING.
7. [ ] Confirm green lock on `https://olife1.com` (incognito).
8. [ ] Reply in chat: “SSL green” (or paste new Railway domain-status screenshot).
9. [ ] (Later) Add `staging.olife1.com` DNS when staging service exists.

---

## 6. Verification commands (agent / owner)

```powershell
nslookup -type=NS olife1.com
nslookup olife1.com
nslookup -type=CNAME www.olife1.com
```

Expect: apex no longer on parking IP; records match Railway UI; browser lock closed; Python `ssl.create_default_context()` verify succeeds for `olife1.com`.

---

## 7. Out of scope for this fix doc

- Moving app data to Supabase (see `docs/SUPABASE_SETUP.md`).
- GA4 (see `docs/GA4_SETUP.md`).
- Code changes (require **APPROVE BUILD**).
