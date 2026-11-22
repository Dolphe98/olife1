# Migration Report — URL map & content inventory

**Status:** Inventory + redirect plan only. **Not executed.**  
**Rule:** Do not apply redirects or content moves until after **APPROVE BUILD** and Phase 6.

---

## 1. Sources audited

| Source | What it contains | Richness |
|--------|------------------|----------|
| Live site `https://olife1.com` | Running Django app; same routes/content as repo | Live truth for URLs |
| Repo `seed_content.py` | 3 `BlogPost` + 4 `Fragment` with full HTML bodies | **Richest structured content source** |
| Repo `static/images/` | 16 image assets (posts, fragments, hero, about, contact, logo, favicons) | Richest media source |
| Local `db.sqlite3` | Dev DB (gitignored); may mirror seed | Secondary |
| Older React / `olife_with_python` | **Ignored per owner** (dead) | N/A |

**Richest source decision:** Treat `sitepages/management/commands/seed_content.py` + `static/images/` as the migration corpus. Live site matches this content. No separate Markdown/CMS export found.

---

## 2. Content counts (Phase 1 audit)

| Type | Count | Notes |
|------|-------|-------|
| Blog posts | **3** | IDs 1–3; episodes S1E1 / S1E1 / S1E2 (two share S1E1 label — clean up in model migration) |
| Fragments | **4** | Keep as first-class section |
| Static images (repo) | **16** | See asset list below |
| Podcast / video URLs in seed | **0** | Podcast/Video page will be embeds-only when URLs are provided |
| Newsletter / Store / Podcast routes | **0 live** | 404 today — net-new in v1 |
| GA4 tag in templates | **0** | Not installed (owner confirmed) |
| Contact integration | Formspree + reCAPTCHA + WhatsApp links | Replace with `ContactMessage` + email; remove WhatsApp per product decision |

### Blog posts

| ID | Title | Current URL |
|----|-------|-------------|
| 1 | The Separation of the Only One | `/blog/1/` |
| 2 | The Infinite Waters | `/blog/2/` |
| 3 | What If the Sky is a Vault? | `/blog/3/` |

### Fragments

| ID | Title | Image file |
|----|-------|------------|
| 1 | Don't Ever Forget | `DONTEVERFORGETfragments1.png` |
| 2 | Light and Dark Duality | `light-and-dark-duality-olife-fragments2.png` |
| 3 | No Witness Dark Side | `no-witness-dark-side-olife-fragments3.png` |
| 4 | The Dust of Existence | `dust-combination-everything-exist-olife-fragment4.png` |

### Static image inventory (`static/images/`)

- `olife1logo.png`, `favicon.png`, `favicon.svg`
- `D.Rodolphe2026good.png`
- `olife1.comsection1image1.jpg`, `olife1.comsection1image2.jpg`
- `Olife1.comBlogposts1e1.png`, `Olife1.comBlogposts1e2.png`, `Olife1.comBlogpostsarticles3s1e2.png`
- Fragment PNGs (4 files above)
- `olifeabout2.jpg`, `olifeabout3.jpg`, `olifecontact1.jpg`

---

## 3. Live URL catalog (2026-11-21)

| URL | Status | Role |
|-----|--------|------|
| `/` | 200 | Home |
| `/fragments/` | 200 | Fragments gallery |
| `/blog/` | 200 | Blog index |
| `/blog/<int:pk>/` | 200 | Blog post (pk today) |
| `/about/` | 200 | About |
| `/contact/` | 200 | Contact + newsletter (Formspree) |
| `/privacy/` | 200 | Privacy |
| `/copyright/` | 200 | Copyright |
| `/admin/` | 200 → login | **Django admin today** (will move) |
| `/newsletter/` | 404 | Planned |
| `/store/` | 404 | Planned stub |
| `/podcast/` | 404 | Planned embeds |
| `/django-admin/` | 404 | Planned escape hatch |
| `/robots.txt` | 404 | Planned |
| `/sitemap.xml` | 404 | Planned |
| `/healthz` | 404 | Planned (required) |
| `/rss/` or `/feed/` | 404 | Planned |

**Structure:** Server-rendered Django templates + WhiteNoise static. Not a separate SPA. Procfile runs migrate → seed_content → collectstatic → gunicorn.

---

## 4. Target URL map & 301 redirects

Canonical host: **`https://olife1.com`**. `https://www.olife1.com/*` → 301 → apex.

### Keep (200, possibly enhanced)

| From | To | Notes |
|------|----|-------|
| `/` | `/` | Home |
| `/fragments/` | `/fragments/` | Keep name |
| `/blog/` | `/blog/` | Index |
| `/about/` | `/about/` | |
| `/contact/` | `/contact/` | Drop WhatsApp UI |
| `/privacy/` | `/privacy/` | |
| `/copyright/` | `/copyright/` | |

### Change with 301

| From | To | Why |
|------|----|-----|
| `/blog/1/` | `/blog/the-separation-of-the-only-one/` | Slug URLs for SEO |
| `/blog/2/` | `/blog/the-infinite-waters/` | Slug URLs |
| `/blog/3/` | `/blog/what-if-the-sky-is-a-vault/` | Slug URLs |
| `/admin/` (Django admin bookmarks) | `/django-admin/` | Free `/admin/` for CRM |
| `https://www.olife1.com/<path>` | `https://olife1.com/<path>` | Canonical apex |

> Implementation note: keep numeric `/blog/<pk>/` as permanent 301 aliases so old shares do not die.

### Net-new (no redirect)

| URL | Purpose |
|-----|---------|
| `/admin/` | Staff CRM dashboard (read-only KPIs v1) |
| `/django-admin/` | Django admin escape hatch |
| `/newsletter/` | Newsletter landing (DB signup) |
| `/podcast/` | YouTube/Spotify embeds |
| `/store/` | Stub product grid → `STORE_URL` placeholder |
| `/accounts/...` | django-allauth (feature-flagged OFF at launch) |
| `/robots.txt`, `/sitemap.xml`, `/feed.xml` | SEO |
| `/healthz` | Railway healthcheck |

---

## 5. Data model migration notes (execute later)

- Rename/evolve `BlogPost` → `Post` (or keep label with `db_table` stability).
- Add `slug`, real `published_at`, `Category` M2M/`Tag` M2M, OpenGraph fields.
- Move image filenames → `Media` rows in Supabase Storage.
- Introduce `Page` for About/Privacy/Copyright (optional: keep template-only pages initially).
- `Fragment` remains its own model (not a Post subtype) unless editorial argues otherwise — **default: keep**.

---

## 6. Open content questions (non-blocking)

- Provide shop URL for `STORE_URL`.
- Provide YouTube/Spotify embed URLs for `/podcast/`.
- Confirm final slugs if titles change.
- Episode labels: posts 1 and 2 both say `S1E1` in seed — fix during migration.
