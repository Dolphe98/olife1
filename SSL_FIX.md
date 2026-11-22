# SSL Fix — olife1.com (Option A: Hostinger DNS)

**Priority:** P0 for the green lock. **Does not block Phase 2** — do DNS in parallel.  
**Strategy:** Keep current nameservers (`ns1.dns-parking.com` / `ns2.dns-parking.com`). Add Railway records manually in Hostinger. **Do not** move nameservers to Railway.

**Audited:** 2026-11-21 (WHOIS confirmed parking NS). Records re-checked via Railway Domains API.

---

## 1. Exact records Railway shows (web → Domains)

Source: Railway custom-domain status for production service `web`.  
If the Railway UI shows different targets when you open it, **the UI wins** — paste those instead.

### Apex — `olife1.com`

| Field | Value |
|-------|--------|
| Status | Verified: **yes** · Certificate: **`ISSUING`** (broken lock cause) |
| Record type | **CNAME** (not A) |
| Host / name | `olife1.com` (Hostinger: `@`) |
| Points to / target | **`6uu49l2o.up.railway.app`** |
| DNS match | **currently unset** ← fix this |
| TXT | None returned by status API for this domain (already verified). If Railway UI shows a `_railway` / ownership **TXT**, add it exactly as shown. |
| A / AAAA | **Not required by Railway** — do not invent a static A record |

### www — `www.olife1.com`

| Field | Value |
|-------|--------|
| Status | Verified: **yes** · Certificate: **`VALID`** |
| Record type | **CNAME** |
| Host / name | `www` |
| Points to / target | **`jghbrc1s.up.railway.app`** |
| DNS match | Propagated (present) |
| TXT | None in status API; add only if UI shows one |

> Railway does **not** ask for an apex **A** record. Targets are hostnames under `*.up.railway.app` (dynamic). A static Hostinger/parking IP will break SSL again when upstream IPs change.

---

## 2. Why the browser shows “Not secure”

1. Apex CNAME to `6uu49l2o.up.railway.app` is **unset**.
2. Certificate for apex stays **ISSUING**.
3. HTTPS presents `*.up.railway.app` → hostname mismatch → Chrome strikes through `https`.

`www` already has a valid cert; canonical remains apex once fixed.

---

## 3. Hostinger steps (Option A)

Panel path: [hostinger.com](https://hostinger.com) → **Domains** → **olife1.com** → **DNS / Nameservers** → **DNS Records**.

Leave nameservers as:

- `ns1.dns-parking.com`
- `ns2.dns-parking.com`

### 3a. DELETE (parking / conflicts)

Delete these if present:

1. **A** record for `@` / `olife1.com` pointing at Hostinger parking (observed earlier: `153.52.255.98`) — or any other apex A/AAAA that is not managed as part of an ALIAS flatten.
2. Any **AAAA** on `@` that conflicts.
3. Any **old www CNAME** that does **not** equal `jghbrc1s.up.railway.app` (or the www target currently shown in Railway).
4. Any second root **ALIAS/CNAME** (Hostinger allows only one apex ALIAS). If Hostinger CDN created an ALIAS, **disable CDN** first, then remove/replace that ALIAS.

Do **not** delete unrelated MX/TXT needed for email unless you know they are obsolete.

### 3b. ADD — apex (Railway CNAME via Hostinger ALIAS)

Railway requires a **CNAME** at the root. Hostinger’s editor: choose type **CNAME**, name `@` — Hostinger stores it as **CNAME ALIAS** (flattening).

| Type | Name | Points to | TTL |
|------|------|-----------|-----|
| CNAME (becomes ALIAS) | `@` | `6uu49l2o.up.railway.app` | default |

No trailing dot needed in Hostinger. Target must be a hostname, **not** an IP.

### 3c. ADD / UPDATE — www

| Type | Name | Points to | TTL |
|------|------|-----------|-----|
| CNAME | `www` | `jghbrc1s.up.railway.app` | default |

### 3d. TXT (only if Railway UI shows one)

If Domains UI lists an ownership TXT (e.g. `_railway` / verify token), add it exactly. Domains are already **Verified** in API, so you may not need a new TXT.

### 3e. Save and wait

Propagation is often **15–60 minutes** (can be longer). Then confirm in Railway (section 4).

---

## 4. Confirm in Railway UI (exact places)

1. Open project → service **web** → **Settings** → **Networking** / **Public Networking** → **Custom Domains**.
2. For **`olife1.com`**:
   - Required DNS row should show **matched** / no longer “unset”.
   - Certificate status should move **ISSUING → ACTIVE** (or equivalent “Valid” / green) within ~15–60 minutes after DNS matches.
3. If stuck on ISSUING after DNS matches: use **Retry certificate issuance** on that domain (dashboard control or Railway CLI domain retry).
4. Browser check: **Incognito** → `https://olife1.com` → closed lock; cert SAN includes `olife1.com`.
5. Reply in chat: **`SSL green`**.

---

## 5. Apex A-record / dynamic IP — do not use static A

Railway’s live docs ([Working with Domains — Adding a root domain](https://docs.railway.com/networking/domains/working-with-domains#adding-a-root-domain)):

- Root domains use **CNAME flattening** or **dynamic ALIAS**, not a fixed A IP you copy once.
- Railway’s edge IPs change; a hard-coded A record will rot.

**Correct approach:** CNAME/ALIAS to the `*.up.railway.app` target Railway shows (section 1).

---

## 6. Important caveat (live Railway docs — not a guess)

Railway’s docs **explicitly list Hostinger** among providers that **do not** support CNAME flattening / dynamic ALIAS at the root, and recommend switching nameservers to **Cloudflare** (free) when apex CNAME never resolves.

That is **not** “migrate NS to Railway.” It is a contingency if Option A fails.

**Try Option A first** (Hostinger CNAME→ALIAS as above). Then:

| After 60+ min | Action |
|---------------|--------|
| Railway shows apex DNS **matched** + cert **ACTIVE** | Done — `SSL green` |
| Apex still **unset** / public DNS still parking A | Contingency: point domain NS to **Cloudflare**, add the same CNAME `@` → `6uu49l2o.up.railway.app` + www CNAME (Cloudflare flattens apex). Still **not** Railway nameservers. |
| Need site usable during wait | `www` already has VALID cert; temporary use `https://www.olife1.com` until apex flips (canonical stays apex in app once SSL green). |

Phase 2 proceeds on Railway `*.up.railway.app` / staging hostname regardless.

---

## 7. Owner checklist (copy/paste)

1. [ ] Hostinger → Domains → olife1.com → DNS Records  
2. [ ] Delete parking apex **A** / conflicting ALIAS / bad www CNAME  
3. [ ] Add CNAME `@` → `6uu49l2o.up.railway.app`  
4. [ ] Set CNAME `www` → `jghbrc1s.up.railway.app`  
5. [ ] Add TXT only if Railway UI shows one  
6. [ ] Railway → web → Domains → apex **matched** + cert **ACTIVE**  
7. [ ] Incognito green lock on `https://olife1.com`  
8. [ ] Reply **`SSL green`**

---

## 8. Out of scope

- Supabase / GA4 setup  
- App code (www→apex 301 after SSL green, post–APPROVE BUILD)  
- Moving nameservers to Railway (explicitly out)
