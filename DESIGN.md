# Design Direction — Olife

Brand law: `docs/BRAND.md`. Motion: subtle fade/slide. No parallax. No bounce. Quiet, late-night, honest.

---

## 1. Reference sites (browsed)

### Reference A — [The Tenebrous Archive](https://thetenebrousarchive.com/)

**Why it fits:** Slow, contemplative editorial voice; philosophy + attention; resists spectacle. Dark, intimate reading feel without guru energy.  
**Steal:** Single-column essay gravity, sparse nav, copy that speaks to one reader.  
**Don’t steal:** Stationery/journaling product focus; WordPress-default rhythms if any.

### Reference B — [LYENNE](https://lyenne.com/)

**Why it fits:** Conscious living through ritual and ordinary life; editorial “house” posture; sentences that feel crafted but human.  
**Steal:** Hero as one composition (brand + one line + atmosphere); restrained CTA; quiet sections with one job each.  
**Don’t steal:** Luxury-goods gallery energy; overly precious lifestyle commerce.

### Reference C — [Metapsychosis](https://metapsychosis.com/)

**Why it fits:** Consciousness / literature / art journal; existential and inner-life essays; serious without TED-talk polish.  
**Steal:** Long-form respect, category as ideas not funnels, denser reading texture when content demands it.  
**Don’t steal:** Academic jargon walls; multi-author magazine chrome that dilutes a personal brand.

### Honorable mention (tone only)

[City of Dis](https://www.city-of-dis.org/) — intellectual honesty and anti-consolation clarity. Useful as a **tone** check for courage; **not** a visual target (too cold/cosmicist for Olife’s “being in the middle” warmth).

---

## 2. Anti-references (what we must NOT look like)

1. **Hustle-bro guru land** — neon gradients, “wake up at 4am,” countdown timers, fake scarcity, testosterone-marketing typography, testimonial carousels of Lamborghinis.  
2. **Wellness-cliché pastel spa** — soft beige + sage “self-care kits,” lotus icon grids, detox detox detox, influencer soft-glow stock smiles.

If a mockup could be mistaken for either after removing the word “Olife,” reject it.

---

## 3. Visual direction

**One sentence:** A dark sanctuary for one reader at night — teal as a single calm signal of life, not a SaaS accent.

Current live site already leans this way (near-black ground, teal CTAs, moody photography). Phase 2–3 refine tokens, type, and motion; do not flip to light mode.

---

## 4. Color tokens

```css
:root {
  /* Surfaces */
  --bg-void: #07090c;
  --bg-base: #0c1016;
  --bg-raised: #141a22;
  --bg-overlay: rgba(7, 9, 12, 0.72);

  /* Text */
  --text-primary: #e8edf2;
  --text-secondary: #9aa6b2;
  --text-muted: #6b7682;

  /* Brand signal */
  --accent: #2ec4b6;          /* teal — primary CTA / brand wordmark */
  --accent-soft: #1a8f85;
  --accent-glow: rgba(46, 196, 182, 0.18);

  /* Semantic */
  --border-subtle: rgba(232, 237, 242, 0.08);
  --danger: #d64545;
  --success: #3dba7a;

  /* Focus */
  --focus-ring: #2ec4b6;
}
```

Avoid purple-on-white SaaS gradients, cream-serif terracotta clichés, and glow-heavy “AI dark mode.”

---

## 5. Typography

**Display / brand:** **Fraunces** (soft optical axis) or **Newsreader** — human, literary, not startup.  
**Body / UI:** **Source Serif 4** for long reading **or** **IBM Plex Sans** for UI chrome if serif body feels too heavy on mobile — pick one pairing in Phase 2 and stick to it.

Proposed pairing (default):

| Role | Font | Size scale |
|------|------|------------|
| Brand wordmark | Fraunces semibold | clamp(2rem, 5vw, 3.5rem) |
| H1 | Fraunces | clamp(1.75rem, 4vw, 2.75rem) |
| H2 | Fraunces | 1.5–1.75rem |
| Body | Source Serif 4 | 1.125rem / 1.7 |
| UI / nav | IBM Plex Sans | 0.8125rem uppercase tracking |

Do **not** use Inter, Roboto, Arial, or system-ui as the brand face.

---

## 6. Spacing & layout

- Base unit: **8px**. Section padding: `64–120px` desktop, `40–64px` mobile.
- Max measure for prose: **36–40rem**.
- First viewport: **one composition** — brand, one headline, one supporting sentence, one CTA group, one dominant visual plane. No stats strips, no card grids in the hero.
- Cards: default **none**. Use cards only for interactive containers (forms, comment composer).

---

## 7. Motion

| Moment | Motion |
|--------|--------|
| Page enter | 200–320ms fade |
| Scroll reveal | fade + 8–16px translateY, once, reduced-motion safe |
| Buttons | 150ms color/opacity |
| Forbidden | parallax, bounce, elastic, infinite pulse, marquee |

`prefers-reduced-motion: reduce` → instant opacity only.

---

## 8. Component list (v1)

- Site header (logo, Fragments/Blog/About/Contact, Join CTA)
- Brand row / wordmark
- Hero (editorial)
- Fragment masonry/grid (simple, not card-chrome)
- Post list row + post article
- Quote rule / divider
- Form fields (contact, newsletter)
- Footer (privacy, copyright, social)
- Staff CRM shell (`/admin`) — dense, utilitarian, still on dark tokens
- Auth screens (allauth) — minimal, flag-gated

---

## 9. Minimal asset kit (to create in Phase 2/3)

1. **Wordmark:** “OLIFE” in Fraunces, tracking slightly open, accent color on dark void — SVG + PNG.
2. **Mark:** Optional solitary teal vertical bar or thin horizon line (Horizontal Divide nod) — not a lotus, not a rocket.
3. **Favicon:** Existing `favicon.svg` refined to match tokens.
4. **OG default image:** 1200×630 moody still + wordmark; no sticker badges.
5. **Social avatars:** square crop of wordmark on void.

No hard brand assets exist yet — Designers/agents generate these under manifesto constraints.
