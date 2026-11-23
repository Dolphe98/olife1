# Data Model — Olife v1

Django + Supabase Postgres. English only. Extend existing `sitepages` app; do not greenfield.

---

## Entity relationship (text)

```
User (Django auth)
  └── Profile (1:1)
Comment (N) ──► Post
Comment.author ──► User
Post ◄──► Category (M2M)
Post ◄──► Tag (M2M)
Post.cover ──► Media (FK, nullable)
Fragment.image ──► Media (FK)
Page.og_image ──► Media (FK, nullable)
Subscriber (email unique)
ContactMessage (admin inbox)
NewsletterExportMeta (optional JSON on Subscriber for future Beehiiv/Mailchimp)
DeployEvent / ContentPipelineItem (CRM read models; may be DB or derived)
```

---

## Models

### `Profile` (User extension)

| Field | Type | Notes |
|-------|------|-------|
| user | OneToOne → User | |
| display_name | CharField(120), blank | |
| bio | TextField, blank | |
| avatar | FK → Media, null | |
| created_at / updated_at | DateTime | |

### `Category`

| Field | Type | Notes |
|-------|------|-------|
| name | CharField(80) unique | |
| slug | SlugField unique | |
| description | TextField blank | |

### `Tag`

| Field | Type | Notes |
|-------|------|-------|
| name | CharField(60) unique | |
| slug | SlugField unique | |

### `Media`

| Field | Type | Notes |
|-------|------|-------|
| title | CharField(255) | |
| alt_text | CharField(255) | a11y required for public images |
| storage_path | CharField(512) | Supabase Storage path |
| public_url | URLField | cached CDN/public URL |
| content_type | CharField(100) | |
| width / height | PositiveInteger null | |
| bytes | PositiveInteger null | |
| source | CharField | `upload` / `migrated-static` |
| created_at | DateTime | |

### `Post` (evolves today’s `BlogPost`)

| Field | Type | Notes |
|-------|------|-------|
| title | CharField(255) | |
| slug | SlugField unique | SEO URLs |
| episode | CharField(32) blank | e.g. S1E2 |
| excerpt | TextField | |
| content_html | TextField | v1; Markdown optional later |
| cover | FK → Media null | |
| categories | M2M Category | |
| tags | M2M Tag | |
| seo_title | CharField(255) blank | |
| seo_description | TextField blank | |
| seo_keywords | CharField(512) blank | legacy; prefer tags |
| og_title / og_description | blank | fallback to seo_* |
| twitter_card | CharField default `summary_large_image` | |
| is_published | Boolean | |
| published_at | DateTime null | real datetime (replace `date_display`) |
| date_display | CharField blank | temporary during migration |
| sort_order | PositiveInteger | |
| created_at / updated_at | DateTime | |

### `Fragment`

| Field | Type | Notes |
|-------|------|-------|
| title | CharField(255) | |
| slug | SlugField unique | |
| alt_text | CharField(255) | |
| image | FK → Media | |
| caption | TextField blank | |
| sort_order | PositiveInteger | |
| is_published | Boolean | |
| created_at | DateTime | |

### `Page`

| Field | Type | Notes |
|-------|------|-------|
| title | CharField | |
| slug | SlugField unique | `about`, `privacy`, … |
| content_html | TextField | |
| seo_* / og_* | as Post | |
| is_published | Boolean | |
| updated_at | DateTime | |

### `Comment`

| Field | Type | Notes |
|-------|------|-------|
| post | FK → Post | |
| author | FK → User | registered-only |
| body | TextField | |
| status | CharField | `pending` / `approved` / `rejected` / `flagged` |
| is_flagged | Boolean | agent-assisted queue |
| moderated_by | FK User null | |
| moderated_at | DateTime null | |
| created_at | DateTime | |

### `Subscriber`

| Field | Type | Notes |
|-------|------|-------|
| email | EmailField unique | |
| status | CharField | `active` / `unsubscribed` |
| source | CharField | `web` / `admin` / … |
| sync_provider | CharField blank | future: `beehiiv` / `mailchimp` |
| sync_external_id | CharField blank | bolt-on without migration |
| sync_payload | JSONField default dict | provider-specific metadata |
| synced_at | DateTime null | |
| created_at | DateTime | |

> Beehiiv/Mailchimp: use `sync_*` fields — no schema change required to attach a provider later.

### `ContactMessage`

| Field | Type | Notes |
|-------|------|-------|
| first_name / last_name | CharField | |
| email | EmailField | |
| subject | CharField | |
| body | TextField | |
| phone | CharField blank | optional; **not** WhatsApp CTA |
| status | CharField | `new` / `read` / `archived` |
| created_at | DateTime | |

Email notification to owner on create (server-side).

### CRM helpers (v1, minimal)

**`ContentPipelineItem`**

| Field | Type | Notes |
|-------|------|-------|
| title | CharField | |
| kind | CharField | `post` / `fragment` / `page` / `other` |
| status | CharField | `idea` / `draft` / `review` / `scheduled` / `published` |
| linked_post | FK Post null | |
| notes | TextField blank | |
| updated_at | DateTime | |

**`DeployEvent`** (also mirrored under `logs/audit/`)

| Field | Type | Notes |
|-------|------|-------|
| environment | CharField | `staging` / `production` |
| action | CharField | `deploy` / `rollback` / `migrate` |
| git_sha | CharField | |
| status | CharField | `success` / `failed` / `rolled_back` |
| actor | CharField | `agent:<name>` / `human` |
| meta | JSONField | |
| created_at | DateTime | |

---

## Feature flags (settings / env, not necessarily DB)

| Flag | Default at launch | Purpose |
|------|-------------------|---------|
| `FEATURE_GOOGLE_LOGIN` | `false` | allauth Google — plumbing shipped, OFF |
| `FEATURE_COMMENTS` | `true` or staged | registered-only comments |
| `FEATURE_GA4` | `false` until Measurement ID live | gtag + CRM charts |
| `FEATURE_STORE` | `true` (stub) | stub page |
| `FEATURE_NEWSLETTER` | `true` | DB signup |

---

## Auth

- `django.contrib.auth.User` + `Profile`
- `django-allauth` + Google provider behind `FEATURE_GOOGLE_LOGIN`
- Comments require authenticated user
- Staff CRM `/admin` requires `is_staff`
- Django admin at `/django-admin/`

---

## Migration from current tables

| Current | Target |
|---------|--------|
| `sitepages_blogpost` | `Post` (+ slug, published_at, Media FK) |
| `sitepages_fragment` | `Fragment` (+ slug, Media FK) |
| static filenames | `Media` rows + Supabase upload |
| Formspree contact/newsletter | `ContactMessage` / `Subscriber` |
