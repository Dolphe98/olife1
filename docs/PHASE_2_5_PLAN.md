# Phase 2.5 — Migration plan (executed)

Staging only. Ghost empty tables dropped first (0 rows), then Django models aligned to DATA_MODEL.

| # | Operation | Risk | Reversible | Data impact |
|---|-----------|------|------------|-------------|
| 1 | DROP empty ghost tables (`sitepages_post`, M2Ms, media, page, category, tag) | Low | Recreate empty via reverse SQL | **0 rows** |
| 2 | Create `Media`, `Category`, `Tag` | Low | Yes (migrate reverse) | None |
| 3 | RenameModel `BlogPost`→`Post`; add DATA_MODEL fields; keep legacy `image` CharField | Med | Rename back | **3 posts preserved** (table rename) |
| 4 | Evolve `Fragment` (slug, caption, created_at, optional Media FK); keep legacy `image` | Low | Yes | **4 fragments preserved** |
| 5 | Create `Page`, `Profile`, `Comment`, `ContentPipelineItem`, `DeployEvent` | Low | Yes | None |
| 6 | Data migration: populate unique `slug` on Post/Fragment from titles | Low | Clear slugs | No deletes |
| 7 | Code: views/admin/seed → `Post` | Low | Revert commit | None |
| 8 | Deploy staging + verify gates | — | — | — |

**Owner approval needed historically:** dropping tables with rows — N/A (all ghosts empty).
