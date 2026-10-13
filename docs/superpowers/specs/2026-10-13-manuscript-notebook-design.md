# Blog AI design revamp: "The Manuscript"

**Date:** 2026-10-13 · **Status:** approved (owner: "same language, own ink") · **Ships as:** v0.2.0

## 1. Intent

Re-skin Blog AI from its amber-on-cream SaaS identity (amber-700 primary, cream-to-white body gradient, glass cards, glow shadows, Inter + Source Serif 4 from Google Fonts, entrance animations) to the design language shared by lscaturchio.xyz and InfiniStar — warm paper, one ink, sand hairlines, flat surfaces, a serif that speaks and a monospace that catalogues — while keeping Blog AI its own product through a different ink and its own signature objects.

What does not change: routes, data, behaviour, copy, the accessibility floors (every text token ≥ 4.5:1 in both themes, Lighthouse a11y 100, dark-mode axe 0), the Lighthouse score floors and the 72,000-byte home document budget in CI, and the rule that fonts are self-hosted with no network fetch at build time.

## 2. Creative north star

**The Manuscript.** Blog AI is a manuscript in progress: a draft on paper with the editor's marks in iron-gall ink. Every post, book and template is a sheet pasted into the notebook; every generated draft is the next page. The paper is the same stationery as the sibling sites; what tells this notebook apart is the pen — **Iron Gall**, the blue-black ink manuscripts were actually written in — and the paragraph mark the editor leaves in the margin.

What Blog AI keeps that the sibling sites do not have: the **draft sheet** (a square-cornered paper plate for a post or book preview), **hairline-divided rows** for history, templates and tools lists, and a working surface of forms and generators that the notebook language has to extend to. What it drops: the body gradient, the radial "orbs", every glass surface, every lift shadow, the sparkle pill, the hero rise and scroll-reveal animations, and raw Tailwind hues.

## 3. Tokens

### 3.1 Colour

Paper and night neutrals are **identical to lscaturchio.xyz and InfiniStar** — same stationery. Only the ink differs.

| Token                                | Light (paper)               | Dark (night)                | Role                                          |
| ------------------------------------ | --------------------------- | --------------------------- | --------------------------------------------- |
| `--background`                       | `38 25% 97%` (#f9f8f5)      | `220 15% 8%` (#111317)      | the page                                      |
| `--card` / `--popover`               | `38 25% 98%`                | `220 15% 10%`               | a surface one shade lighter than the page     |
| `--muted`                            | `38 18% 92%`                | `220 10% 16%`               | tinted paper; the draft sheet                 |
| `--accent`                           | `32 50% 92%`                | `210 16% 16%`               | sand highlight for hover fills                |
| `--foreground`                       | `210 15% 12%`               | `0 0% 98%`                  | ink (text)                                    |
| `--muted-foreground`                 | `215 10% 42%`               | `220 10% 70%`               | metadata, captions, wall labels               |
| `--border` / `--input`               | `30 18% 86%`                | `220 10% 18%`               | the sand hairline                             |
| `--primary` / `--ring`               | **`224 48% 32%`** (#2a3f79) | **`224 55% 76%`** (#a0b2e3) | **Iron Gall** — the one pen                   |
| `--primary-foreground`               | `0 0% 100%`                 | `220 15% 8%`                | text on an Iron Gall fill                     |
| `--secondary`                        | `224 35% 42%` (#465a91)     | `224 35% 36%` (#3c4d7c)     | Iron Gall Soft, the rare secondary fill       |
| `--destructive`                      | `0 72% 38%`                 | `0 70% 70%`                 | error text and destructive buttons            |
| `--success` / `--warning` / `--info` | as the sibling sites        | as the sibling sites        | status only, each with a `-muted` 10–15% tint |
| `--scrim` / `--scrim-alpha`          | `0 0% 4%` / 0.25            | same / 0.55                 | the modal scrim (ink in both themes)          |

Measured (`apps/web/tests/lib/design-tokens.test.ts`): Iron Gall on paper **9.48:1**, on tinted paper 8.53:1, white on it 10.07:1; dark Iron Gall on night **8.83:1**, on night-tinted 7.09:1, night text on it 8.83:1; Iron Gall Soft on paper 6.31:1. Everything clears the 4.5:1 body floor, so the ink may be used for small text.

**Why Iron Gall.** It is the ink manuscripts were written in, which fits a product that writes prose; at 224° it is the cool blue-black that reads as "editor's pen" against warm paper, and it sits far enough from the personal site's forest green and InfiniStar's mulberry that the three notebooks are told apart at a glance. The amber it replaces was the generic SaaS warm accent; nothing in the product's story depended on it.

### 3.2 Typography

Three voices with fixed jobs, the same three as the sibling sites: **Fraunces** (display; variable) speaks — headings, the wordmark, titles on draft sheets; **Instrument Sans** (body; variable) reads; **IBM Plex Mono** 400/500/600 catalogues — the wall label (`label-mono`): 0.72rem, 500, 0.16em tracking, uppercase, tabular numerals, Ink Muted.

Scale (fluid, `clamp()`, weights 720 → 700 → 650 → 620 → 560): Display `clamp(2.4rem, 5.2vw, 4.9rem)`; Headline `clamp(1.9rem, 3.6vw, 3.2rem)`; Title `clamp(1.55rem, 2.4vw, 2.25rem)`; Card Title 1.25rem; Subsection 1.075rem. Body 1rem / 1.65.

**Fonts are self-hosted** through `next/font/local` from `@fontsource-variable/fraunces`, `@fontsource-variable/instrument-sans` and `@fontsource/ibm-plex-mono` (`apps/web/lib/fonts.ts`): body and display preloaded with `swap` (the display face is preloaded because the home masthead is the LCP element and a late swap measured 0.117 CLS on CI); mono `display: optional, preload: false` (a swapping mono label flips metadata rows between one line and two). `tests/lib/fonts.test.ts` fails on any `next/font/google` import. The old `font-sans` / `font-serif` class names map onto the body and display voices until the page PRs rename them.

### 3.3 Shape, space, motion

- Radius: controls 14px, small controls 10px, fields 8px, Card and dialogs 18px, chips full. The scale is clamped at 18px. **Draft sheets are square** (0px).
- Borders: always 1px `--border`, often at reduced opacity.
- Elevation: **flat paper**. Exactly two shadows exist: the sticky header sheet (`0 8px 30px rgba(0,0,0,0.08)`) and the primary button's 1px ledge. Modals separate with the scrim.
- Grain: the fixed 3.5% SVG noise on `body::after`.
- Motion: content does not animate itself in. Hover/focus 150–200ms; the `ink-underline`; `animate-pulse` / `animate-spin` slow to 3s under `prefers-reduced-motion`, everything else collapses to 0.01ms.
- Focus: one `:focus-visible` outline, 2px ink at 2px offset, as a default. Selection: ink at 22%.

## 4. Components

- **Button** (`components/ui/Button.tsx`): `default` = `cta-primary` (one per view); `secondary` / `outline` = `cta-secondary`; `ghost`; `link` = `ink-underline`; `destructive` = the secondary shape with Error text. No ring stacks.
- **Input / Textarea / Select**: `input-field`, 8px, 40px tall.
- **Card**: paper card, hairline, 18px, no shadow. **Badge**: round chip, outline by default, one filled form, four status washes.
- **Plate** (`components/ui/Plate.tsx`): the draft sheet — square, hairline, tinted paper, 3:4 by default.
- **ConfirmModal / Toast**: brought onto the tokens with their props unchanged.
- **Mark** (`components/brand/Logo.tsx`): a square Iron Gall plate with a pilcrow (¶) cut out of it — the paragraph mark — as one `evenodd` path on a 24-unit grid. A pen-nib alternative was rejected because it read as a map pin. **Wordmark**: "Blog AI" in Fraunces 700 with "AI" in the ink. `scripts/generate-brand.mjs` renders the SVG lockups, favicons, app icons and the maskable icon; `app/manifest.ts` and `app/opengraph-image.tsx` use the same colours.

## 5. Engineering

- `scripts/check-design-system.mjs` (`bun run design:check`, in CI right after Lint): hard rules palette / flat-paper / no-gradient / one-glass / serif-speaks / tiny-font / no-entrance, an `ALLOWLIST` (empty: the header sheet's shadow and blur live in the `header-sheet` utility in `globals.css`) and a `LEGACY` ratchet whose counts may only fall. Baselines on 2026-10-13: palette-hue 5276, white-black 407, shadow 128, backdrop-blur 9, gradient 51, glass 17, entrance-css 14, entrance-motion 84, font-serif 26, tiny-font 1.
- `app/globals.css` keeps a transitional `@theme inline` block of the v3 palette hues the call sites still use (the a11y floors were measured against those values) and flat-paper shims for `glass-*`, `card-surface`, `page-gradient`; both leave with the page PRs.
- `DESIGN.md` is rewritten in full and `.impeccable/design.json` regenerated for the new tokens.

## 6. Delivery

Four PRs on the trunk, each green and each a conventional commit so release-please folds them into **v0.2.0**:

1. `build(tailwind): migrate to Tailwind v4` (#223) — pixel-equivalent.
2. `feat(design): Manuscript notebook tokens, fonts, primitives, brand and enforcement` — §3, §4, §5. The app is on the new stationery; pages still carry old composition.
3. `feat(design): marketing pages on the notebook` — home, pricing, blog, tools, auth; header and footer redesign; drives the ratchet down.
4. `feat(design): app pages on the notebook` — generate, history, templates, brand, bulk, settings; the ratchet to zero and the transitional palette block, shims and entrance keyframes deleted.

## 7. Out of scope

Copy and product-claim changes (Phase 3). The Clerk appearance mapping (PR 3). Renaming the `font-serif` call sites (PR 3/4).
