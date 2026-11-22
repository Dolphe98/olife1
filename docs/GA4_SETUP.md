# GA4 + Data API Setup

**Status:** GA4 is **not** installed on the live Django site as of Phase 1 audit (`templates/base.html` has no gtag). Owner confirmed analytics not configured yet.  
**Goal:** Create GA4 property, embed Measurement ID behind a feature flag, and enable GA4 Data API for the staff CRM at `/admin`.

Do **not** commit property IDs, client emails, or JSON key files. Use Railway env + placeholders in docs.

---

## Owner checklist

### A. Create GA4 property

1. Open [Google Analytics](https://analytics.google.com/) with the Google account that will own Olife.
2. **Admin → Create Property** → name `Olife` → timezone / currency as preferred → create.
3. Create a **Web** data stream → URL `https://olife1.com` → copy **Measurement ID** `G-XXXXXXXX`.
4. Store as Railway env: `GA4_MEASUREMENT_ID=G-XXXXXXXX` (staging may use a separate stream `G-YYYYYYYY`).

### B. Site tag (agent implements after APPROVE BUILD)

5. Load gtag only when `FEATURE_GA4=true` and Measurement ID is set.
6. Place in base layout once; do not duplicate per page.
7. Respect future consent banner if/when required by jurisdiction (v1: document risk; EU traffic may need CMP later).

### C. Google Cloud project for Data API (CRM)

8. Open [Google Cloud Console](https://console.cloud.google.com/) → create project `olife-crm` (name flexible).
9. Enable **Google Analytics Data API**.
10. **IAM → Service Accounts → Create** → name `olife-ga4-reader`.
11. Grant the service account **Viewer** access on the GA4 property:
    - GA Admin → Property Access Management → add service account email → role **Viewer**.
12. Create a JSON key → download once → **do not commit**.
13. On Railway, prefer storing either:
    - `GOOGLE_APPLICATION_CREDENTIALS_JSON=<minified json>` (secret), or
    - upload to a private secret store and mount path.
14. Also set `GA4_PROPERTY_ID=<numeric property id>` (Admin → Property Settings → Property ID — **not** the Measurement ID).

### D. CRM usage (Phase 4)

15. Staff `/admin` dashboard reads:
    - sessions / users / page views (28d)
    - top pages / top posts (map paths → `Post`)
    - traffic sources (high-level)
16. Cache responses (e.g. 15–60 min) to stay within API quotas.
17. Fail soft: if API errors, show “GA4 unavailable” — never block public site.

### E. Confirm

18. Realtime view shows your visit after flag ON on staging.
19. Data API `runReport` returns rows for last 7 days (may take 24–48h for fresh properties to accumulate).
20. Reply: “GA4 ready” (no IDs in chat if you prefer; or Measurement ID only).

---

## Placeholders

| Variable | Placeholder |
|----------|-------------|
| Measurement ID | `<GA4_MEASUREMENT_ID>` |
| Property ID (numeric) | `<GA4_PROPERTY_ID>` |
| Service account email | `<GA4_SERVICE_ACCOUNT_EMAIL>` |
| Credentials JSON | `<GOOGLE_APPLICATION_CREDENTIALS_JSON>` |
