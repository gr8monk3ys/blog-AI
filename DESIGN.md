---
name: Blog AI
description: A manuscript in progress — warm paper, Iron Gall ink, and a square draft sheet for every piece of writing.
colors:
  iron-gall: "#2a3f79"
  iron-gall-dark: "#a0b2e3"
  iron-gall-soft: "#465a91"
  iron-gall-soft-dark: "#3c4d7c"
  paper: "#f9f8f5"
  paper-card: "#fbfaf9"
  paper-tinted: "#eeece7"
  paper-warm: "#f5ebe0"
  ink: "#1a1f23"
  ink-muted: "#606976"
  hairline: "#e2dbd5"
  night: "#111317"
  night-card: "#16181d"
  night-tinted: "#25272d"
  night-ink: "#fafafa"
  night-ink-muted: "#abb0ba"
  night-hairline: "#292c32"
  signal-error: "#a71b1b"
  signal-success: "#107535"
  signal-warning: "#935f06"
  signal-info: "#0950c3"
typography:
  display:
    fontFamily: "Fraunces, ui-serif, Georgia, serif"
    fontSize: "clamp(2.4rem, 5.2vw, 4.9rem)"
    fontWeight: 720
    lineHeight: 1.02
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Fraunces, ui-serif, Georgia, serif"
    fontSize: "clamp(1.9rem, 3.6vw, 3.2rem)"
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Fraunces, ui-serif, Georgia, serif"
    fontSize: "clamp(1.55rem, 2.4vw, 2.25rem)"
    fontWeight: 650
    lineHeight: 1.18
    letterSpacing: "-0.026em"
  card-title:
    fontFamily: "Fraunces, ui-serif, Georgia, serif"
    fontSize: "1.25rem"
    fontWeight: 620
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Instrument Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "normal"
  label:
    fontFamily: "IBM Plex Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "0.72rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.16em"
rounded:
  none: "0px"
  sm: "8px"
  md: "10px"
  lg: "14px"
  card: "18px"
  full: "9999px"
spacing:
  1: "4px"
  2: "8px"
  3: "12px"
  4: "16px"
  6: "24px"
  8: "32px"
  10: "40px"
  12: "48px"
  16: "64px"
  20: "80px"
  24: "96px"
components:
  button-primary:
    backgroundColor: "{colors.iron-gall}"
    textColor: "#ffffff"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "8px 16px"
    height: "40px"
  button-secondary:
    backgroundColor: "{colors.paper-card}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "8px 16px"
    height: "40px"
  badge-outline:
    backgroundColor: "{colors.paper-card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-filled:
    backgroundColor: "{colors.iron-gall}"
    textColor: "#ffffff"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  card:
    backgroundColor: "{colors.paper-card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "24px"
  input-field:
    backgroundColor: "{colors.paper-card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "8px 12px"
    height: "40px"
  wall-label:
    backgroundColor: "transparent"
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
    padding: "0"
  draft-sheet:
    backgroundColor: "{colors.paper-tinted}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0"
  brand-mark:
    backgroundColor: "{colors.iron-gall}"
    textColor: "{colors.paper}"
    rounded: "{rounded.none}"
    padding: "0"
---

# Design System: Blog AI

## Overview

**Creative North Star: "The Manuscript"**

Blog AI is a manuscript in progress. Every post, book and template is a sheet of paper pasted into a working notebook: a square draft sheet, a title in serif, a catalogue line in mono underneath (words · tone · date). Every generated draft is the next page, and the only saturated thing on any page is the ink the editor marks it with.

The notebook is the same stationery as lscaturchio.xyz and InfiniStar, by design: warm off-white paper with a near-invisible grain, structure drawn with hairlines and space rather than boxes, a serif with personality for what the site says, a plain sans for what the reader reads, and a monospace label beside every piece of metadata. What tells the three notebooks apart is the pen. The personal site writes in forest green, InfiniStar in mulberry; Blog AI writes in **Iron Gall**, the blue-black ink that manuscripts were actually written in — the editor's pen on the draft.

What Blog AI keeps that the sibling sites do not have: the **draft sheet** as the recurring unit of the work (a post preview, a book cover, a template), **hairline-divided rows** for history, templates and tools, and a working surface of forms, generators and settings that the notebook language extends to.

The system deliberately is not three things. It is not the amber-on-cream SaaS it replaced: no body gradient, no radial orbs behind the hero, no glass cards, no glow or lift shadows, no sparkle pill, no sections that fade in as you scroll. It is not landing-page chrome: no three-column feature tiles, no badge pills as decoration. And it is not a palette: every Tailwind hue that used to be reached for directly (`gray-600`, `amber-700`, `emerald-500`) is being driven to zero by a ratchet, and colour arrives through the tokens.

**Key Characteristics:**

- One paper ground, warm off-white with a fixed 3.5% noise grain; dark mode is a night variant of the same page.
- One ink, Iron Gall, spent sparingly: links, hover, selection, the focus ring, the single primary button per view.
- Hairline rules and tint shifts structure the page; there are no floating cards and no decorative shadows.
- Three type voices with fixed jobs: Fraunces speaks, Instrument Sans reads, IBM Plex Mono catalogues.
- Squareness marks the work (draft sheets); roundness marks the interface (controls, chips).
- Motion is the interface responding to the reader, never the page introducing itself.

## Colors

A warm, low-chroma paper palette with one blue-black ink and a sand-toned hairline; dark mode inverts to a cool night page with the same ink lifted for contrast. Every pair below is measured by `apps/web/tests/lib/design-tokens.test.ts` from the HSL triplets in `apps/web/app/globals.css`; the document does not get to be wrong about contrast.

### Primary

- **Iron Gall** (`224 48% 32%` #2a3f79 light / `224 55% 76%` #a0b2e3 dark; `--primary`, `--ring`): the one pen. Links, the hover colour of any interactive text, the 22% tint behind selected text, the fill of the single primary button, the focus outline, the "AI" in the wordmark, and the border that warms on a hovered surface. Measured **9.48:1 on paper** and **8.53:1 on tinted paper**; white on the light ink 10.07:1. At night **8.83:1 on night** and 7.09:1 on night-tinted; night text on the dark ink 8.83:1. Because it clears 4.5:1 at any size, there is no separate "small text" token.
- **Iron Gall Soft** (`224 35% 42%` #465a91 light, 6.31:1 on paper / `224 35% 36%` #3c4d7c dark; `--secondary`): a diluted Iron Gall for the rare secondary fill, measured against its own white foreground. It exists so a second ink never has to be invented.

Why Iron Gall: it is the historical writing ink, which fits a product that writes prose; at 224° it is the cool blue-black that reads as an editor's pen against warm paper; and it sits far from forest green (the personal site) and mulberry (InfiniStar), so the three notebooks are told apart at a glance. The amber it replaces carried no product meaning.

### Neutral

- **Paper** (`38 25% 97%` #f9f8f5; `--background`): the page. Warm off-white, hue 38, with the noise grain laid over it.
- **Paper Card** (`38 25% 98%`; `--card`, `--popover`): a surface one shade lighter than the page, used for buttons, inputs, list rows, cards and menus so they sit on the paper rather than above it.
- **Paper Tinted** (`38 18% 92%`; `--muted`): the recessed tone. The draft sheet's ground, disabled controls, the toast's hover.
- **Paper Warm** (`32 50% 92%`; `--accent`): a sand highlight for hover fills and the rare emphasised block.
- **Ink** (`210 15% 12%`; `--foreground`): body text. A cool near-black with a blue cast that keeps the warm paper from going yellow.
- **Ink Muted** (`215 10% 42%`; `--muted-foreground`): captions, wall labels, descriptions, placeholders. Everything that is metadata rather than the work.
- **Hairline** (`30 18% 86%`; `--border`, `--input`): the rule. A sand tone, never grey, drawn at 1px and often at 40–90% opacity.
- **Night** (`220 15% 8%`), **Night Card** (`220 15% 10%`), **Night Tinted** (`220 10% 16%`), **Night Ink** (`0 0% 98%`), **Night Ink Muted** (`220 10% 70%`), **Night Hairline** (`220 10% 18%`): the dark-mode counterparts, hue 220, cool rather than warm.

### Signal

- **Error** (`0 72% 38%` light / `0 70% 70%` dark; `--destructive`), **Success** (`142 76% 26%` / `142 71% 45%`), **Warning** (`38 92% 30%` / `38 92% 50%`), **Info** (`217 91% 40%` / `217 91% 65%`): status colours for form errors, toasts, badges and the fact-check verdicts only, each with a `-muted` 10–15% tinted background. They never appear as decoration, and they are reached through the tokens (`text-destructive`, `bg-success-muted`), never as `red-500`.

### Named Rules

**The One Pen Rule.** Iron Gall is the only chromatic accent on any surface, and it marks action or emphasis, never area. If a screen has the ink in more than a few places, it has too many. No gradient anywhere, on anything.

**The Sand Hairline Rule.** Dividers are 1px of Hairline, sand-toned, never neutral grey and never thicker. Depth of structure is expressed by more rules and more space, not by darker lines.

**The Tinted Paper Rule.** A "contained" surface is the same paper at a different tint (Paper Card lighter, Paper Tinted darker), bordered by a hairline. It is never a white box on a grey page — which is why `bg-white` is on the ratchet.

## Typography

**Display Font:** Fraunces, variable, optical size auto — self-hosted from `@fontsource-variable/fraunces`, preloaded (unlike the sibling sites: the home masthead is the LCP element in this face, the file is 37 KB, and a late swap measured 0.117 CLS on CI), with a metric-adjusted Times New Roman fallback.
**Body Font:** Instrument Sans, variable — self-hosted from `@fontsource-variable/instrument-sans`, preloaded.
**Label/Mono Font:** IBM Plex Mono 400/500/600 — self-hosted from `@fontsource/ibm-plex-mono`, `display: optional` (a swapping mono label flips metadata rows between one line and two; the sibling site measured 0.135 CLS from it).

No font is fetched at build time; `apps/web/lib/fonts.ts` loads them with `next/font/local` and `apps/web/tests/lib/fonts.test.ts` fails on any `next/font/google` import. The pre-notebook `font-sans` and `font-serif` class names map onto the body and display voices in `globals.css` so the pages that still use them render in the new faces; `font-serif` is on the ratchet and the notebook speaks in `font-display`.

**Character:** A high-contrast, slightly wonky serif doing the talking, a plain humanist sans doing the reading, and a monospace doing the filing. Fraunces at heavy weights and tight tracking gives headings a printed, editorial presence; Instrument Sans at 1.65 stays out of the way; Plex Mono, small, uppercase and widely tracked, is the wall label beside the work.

### Hierarchy

- **Display** (Fraunces 720, clamp 2.4–4.9rem, 1.02, −0.035em, oldstyle numerals; `text-display`): the home masthead and nothing else.
- **Headline** (Fraunces 700, clamp 1.9–3.2rem, 1.12, −0.03em; `text-page-title`): one per page.
- **Title** (Fraunces 650, clamp 1.55–2.25rem, 1.18, −0.026em; `text-section-title`): section headings.
- **Card Title** (Fraunces 620, 1.25rem, 1.2, −0.02em; `text-card-title`): a post's title on a draft sheet or row, a dialog title. A subsection step exists at 1.075rem / 560 (`text-subsection`).
- **Body** (Instrument Sans 400, 1rem, 1.65): reading text, and the text inside every control. Lead paragraphs use 1.125rem with `text-pretty`.
- **Description** (Instrument Sans 400, 0.875–1rem, Ink Muted): secondary copy under a title.
- **Label** (IBM Plex Mono 500, 0.72rem, 0.16em tracking, uppercase, tabular numerals, Ink Muted; `label-mono`): the wall label. Kickers, dates, word counts, tones, the catalogue line under a draft sheet, footer column heads, pricing figures. With `normal-case tracking-normal` it becomes the small mono link. `label-link` adds the 24px (44px on touch) tap-target floor.

### Named Rules

**The Wall Label Rule.** Every piece of metadata (a date, a count, a tone, a category) is set as a Label: mono, small, uppercase, tracked, muted. Metadata never borrows the body or heading voice. Every section, row and figure introduces itself with one before its title — the kicker _is_ the house device.

**The Serif Speaks Rule.** Fraunces appears only where the site is speaking: `h1`–`h6`, the type-scale utilities, the wordmark, titles on draft sheets, stat numerals. Never in body copy, UI controls, generated drafts or labels. `font-display` on a non-heading fails the build unless the element carries `data-voice="display"`.

**The Fluid Heading Rule.** Headings scale with `clamp()`, not breakpoints; weights step down the hierarchy (720 → 700 → 650 → 620 → 560) and tracking loosens as size falls. A `leading-*` class is honoured over a responsive `text-*` size (Tailwind v4 routes line-height through `--tw-leading`), so write the line-height you mean.

## Layout

The page is a single centred column on open paper, with three widths: narrow (42rem) for reading and for row lists, medium (56rem) for mixed content and forms, wide (72rem) for the masthead, draft-sheet galleries and index headers. Horizontal padding is 16px, rising to 24px and 32px at the sm and lg breakpoints.

Vertical rhythm is generous. Sections breathe at 64px, then 80px at sm and 96px at lg; small sections at 32/48/64px. Rows pad at 16px (24px at sm), cards at 24px (32px at sm). Between sections sits a full-width hairline (`gallery-rule`), never a background change.

Two-column compositions are asymmetric editorial splits, never equal halves: a generator is `1fr / 320px` with the settings rail at the right edge, a post page is `1fr / 300px` with the draft sheet at the right, the footer is `1.1fr / 2fr`. Lists are stacked rows separated by hairlines with the label above the title and the description below, not tiled cards. Draft sheets are the exception: galleries of previews run 2 → 4 columns with 16px gaps, because a draft is the work and the grid is how a notebook keeps sheets.

The header is sticky, 64px, 90% paper with a 12px blur and a 40% hairline beneath; every page sits under that same sheet. Breakpoints are Tailwind's defaults.

## Elevation & Depth

Flat paper, tint shifts only. Every surface sits on one plane. Hierarchy is drawn with hairlines and with the three paper tints, and a hover is a colour change (border warming to Iron Gall at 45%, background tinting to Iron Gall at 5–6%), not a lift. The noise grain over the whole page is what stops large flat areas from reading as sterile screen white.

Two exceptions exist and are structural, not decorative: the sticky header carries a wide, soft shadow (`0 8px 30px rgba(0,0,0,0.08)`) so it reads as a separate sheet when content scrolls under it, and the primary button (`cta-primary`) carries a 1px ledge (`0 1px 0` of Iron Gall at 25%) beneath its border so the one filled button feels pressed onto the page.

### Named Rules

**The Flat Paper Rule.** No shadow on any content surface, at rest or on hover. A hovered surface changes tint and border colour; it does not rise.

**The Two Sheets Rule.** The only elevated objects are the sticky header and the primary button's 1px ledge. Nothing else may add a shadow without changing this file first.

**The Scrim Rule.** A modal separates with a scrim, not a shadow. `overlay-scrim` — `hsl(var(--scrim) / var(--scrim-alpha))`, ink in both themes, 25% on paper and 55% at night — is the third sanctioned separation mechanism, and the only one available to an overlay, since the Two Sheets Rule has already spent both of its shadows. The scrim is ink rather than `--foreground` because `--foreground` inverts at night and would lay a white veil over the dark page.

**The Measure Rule.** Running text, including generated drafts, caps at 65–75 characters per line, measured in the DOM, not assumed from the unit.

## Shapes

The form language is soft-cornered paper with one square exception. Buttons and controls use 14px corners (`rounded-xl`); small buttons 10px; fields 8px; the Card component and dialogs 18px — and the radius scale is clamped there, so `rounded-3xl` and `-4xl` from the amber era resolve to 18px. Chips, badges, round avatars and the toast's dismiss button are fully round.

**Draft sheets are square.** A post or book preview is a 3:4 plate with 0px corners and a 1px hairline on tinted paper, `object-cover` for a cover image, no hover scale, no gradient scrim over the image — the work, pasted onto the page. Squareness marks the work; roundness marks the interface. A sheet with no image shows the title in Fraunces in the ink and the catalogue line in mono at the bottom edge.

Borders are always 1px Hairline, frequently at reduced opacity. The header's 90% paper with 12px blur is the one glass surface; glass is for chrome that sits over itself, never for content.

## Components

### Buttons

- **Shape:** 14px radius, 40px tall, 16px horizontal padding; small 36px / 10px radius; large 48px / 32px padding. Text is Instrument Sans 500 at 0.875rem. `components/ui/Button.tsx`.
- **Primary** (`cta-primary`, the `Button` default): Iron Gall fill, white text, a 1px border of Iron Gall at 42%, the ledge shadow. One per view. Hover brightens 8%; active presses 1px down.
- **Secondary / Outline** (`cta-secondary`): Paper Card fill, hairline, Ink text; hover tints the fill to Iron Gall at 5% and warms the border to 45% and the text to Iron Gall. **Ghost**: transparent until hovered, then Paper Card with a hairline. **Link**: Iron Gall text with `ink-underline`. **Destructive**: the secondary shape with Error text.
- **Focus:** the global `:focus-visible` outline — 2px Iron Gall at a 2px offset — on everything focusable, pre-coloured so it never interpolates. No `ring-*` stacks on any primitive.
- **Disabled:** Paper Tinted fill, Ink Muted text, hairline, no ledge, 60% opacity.

### Chips / Badges

- **Style:** fully round, 12px horizontal / 4px vertical padding, 0.75rem semibold. `components/ui/Badge.tsx`.
- **Outline / Secondary** (the house chip): Paper Card fill with a hairline, Ink text, hover text to Iron Gall.
- **Filled** (`default`): Iron Gall fill, white text. Reserve for a single status or count (the PRO tier).
- **Status** (`success`, `warning`, `info`, `destructive`): the signal colour on its `-muted` wash. A fact-check verdict, a scheduled post's state.
- **Tag lists are not chips.** They are wall-label links separated by gap, not pills.

### Cards / Rows

- **Card:** Paper Card on Paper, 1px hairline, 18px radius, 24px padding, no shadow. `components/ui/Card.tsx`; its `CardTitle` is an `h3`. Interactive cards warm the border on hover.
- **Preferred alternative:** most "cards" are not cards. Text-led lists (history, templates, tools, brand profiles, team members) are stacked rows divided by hairlines: a mono label, a semibold title that turns Iron Gall on hover, a two-line clamped description in Ink Muted. Lists cap at 42rem.

### Inputs / Fields

- **Field** (`input-field`; `components/ui/Input.tsx`, `Textarea.tsx`, `Select.tsx`): Paper Card fill, hairline, 8px radius, 40px tall, 0.875rem text, placeholder Ink Muted at 80%. Focus warms the border to Iron Gall at 50% plus the global outline. Invalid fields (`aria-invalid`) take an Error border.
- The generator's prompt is a Textarea; its settings are Selects. Nothing has a coloured ring.

### Navigation

- **Header:** sticky, 90% paper, 12px blur, 40% hairline beneath, the one structural shadow. `<Logo>` at the left (the paragraph mark beside the wordmark); nav links in body sans with `ink-underline`; theme toggle and the sign-in button at the right, the sign-in button being the header's `cta-primary`.
- **Footer:** hairline above at 60%, column heads as wall labels, links in sans that take the ink on hover, a hairline before the legal line.

### Draft Sheet (signature)

A square-cornered 3:4 plate (`plate`, or `<Plate>` from `components/ui/Plate.tsx`) with a 1px hairline on tinted paper. Below it, outside the image: the title in Fraunces at Card Title, then one mono catalogue line — `1,240 words · conversational · 13 Oct` — with tabular numerals. Hover: the title turns Iron Gall and the sheet's border warms. It is the recurring unit of the blog index, the book builder and the templates gallery.

### Wall Label (signature)

The `label-mono` utility. It is the placard beside every piece of work: the masthead kicker, the catalogue line under a draft sheet, section counts, dates on history rows, footer column names, the pricing figures. Any new section should introduce itself with one.

### Mark and Wordmark (signature)

The mark is the paragraph mark: a square plate of Iron Gall ink — square corners, because squareness marks the work — with a pilcrow (¶) cut out of it in paper, the sign an editor leaves in the margin where a new paragraph begins. It is drawn on a 24-unit grid as one `fill-rule="evenodd"` path (the plate first, then the pilcrow: a half-disc bowl on the left and two stems to the baseline), so the ¶ is a true hole and whatever the mark sits on shows through. It was rendered and checked at 16/24/32/88/160 on paper and night; a pen-nib alternative was rejected because it read as a map pin. It is flat ink: no border, no gradient, no shadow. In the app it is `<LogoMark>` (`components/brand/Logo.tsx`), filled with `hsl(var(--primary))`, so it is Iron Gall on paper by day and the lifted Iron Gall at night with no `dark:` override.

The wordmark is "Blog AI" in Fraunces 700, tight tracking, Ink, with "AI" in Iron Gall — one phrase in ink, the house device. Two lockups (`<Logo variant>`): **horizontal** is the mark, a 12px gap and the wordmark, with the mark exactly as tall as the wordmark's capitals; **stacked** is the mark above, a 12px gap and the wordmark centred beneath at half the mark's height. In the component the wordmark is live text in `font-display`; the static files have it converted to outlines and reference no font.

Clear space around any lockup is the pilcrow's bowl (0.4 of the mark's height). Minimum size: 16px for the mark alone, 96px wide for a lockup. The favicon form fills the pilcrow with paper so it reads on light and dark tab strips. Do not rotate, recolour, outline, add a shadow or a gradient, or set the wordmark in another face. Files: `apps/web/public/brand/` (`mark.svg`, `mark-dark.svg`, `mark-mono.svg`, `logo-horizontal{,-dark}.svg`, `logo-stacked{,-dark}.svg`, a `README.md`), the favicons and app icons in `apps/web/public/`, the manifest colours in `apps/web/app/manifest.ts`, the Open Graph card in `apps/web/app/opengraph-image.tsx`, and `docs/brand/lockups.png`; the static files are regenerated by `bun run brand:generate` from `scripts/generate-brand.mjs`.

### Dialogs

Opaque `--popover` inside a 1px hairline, 18px radius, 24px padding, over the scrim (`ConfirmModal`). Titles are Card Title in Fraunces. The confirm button is the dialog's one primary button, except for a destructive confirmation, which is the secondary shape with Error text. No shadow, no blur.

### Toast

A slip of Paper Card with a hairline, fixed at the top right; only the icon carries the signal colour. No shadow, no tinted fill.

## Motion

**Content does not animate itself in.** Nothing on a page mounts hidden and waits for a scroll observer or a mount transition to become readable; the failure mode is a blank page. The `hero-rise*` keyframes and `[data-reveal]` rules still exist in `globals.css` for the home and pricing pages that use them and are on the ratchet; the pages PR deletes both.

What moves is the interface responding to the reader:

- **Hover and focus** transition at 150ms (fast), 200ms (default) or 300ms (slow) with `ease`.
- **The ink underline** scores in over 240ms on `cubic-bezier(0.16, 1, 0.3, 1)`.
- **Dialog and toast** transitions are 200–300ms Headless UI / framer-motion fades, because a dialog or a notification is the interface arriving, not content.
- **Loading** is `animate-pulse` and `animate-spin`.

Under `prefers-reduced-motion` every animation and transition collapses to `0.01ms` (not 0s, which can skip `transitionend`), with one stated exception: the two loading indicators slow to 3s rather than stopping, because a frozen loader reads as broken rather than as waiting.

## Do's and Don'ts

### Do:

- **Do** introduce every section, row and figure with a wall label before its title.
- **Do** divide with 1px sand hairlines and 64–96px of vertical space; let whitespace and rules do the structuring.
- **Do** spend Iron Gall on action and emphasis only: links, hover, selection, one primary button per view.
- **Do** build text-led lists as stacked hairline-divided rows and keep previews as square draft sheets in a gallery grid.
- **Do** route every colour through the tokens; status is `text-success`, `text-warning`, `text-info`, `text-destructive` and their `-muted` washes.
- **Do** keep numerals tabular in labels and oldstyle in display, and set every date and count in mono.
- **Do** design dark mode as the same notebook at night: cool hue-220 page, the ink lifted to `224 55% 76%`, hairlines at 18% lightness.
- **Do** give an empty section an honest empty state in the same voice: a wall label, one serif line, one primary action.
- **Do** set generated drafts in the body sans at the reading measure; the serif is for what the site says, not what the model wrote.

### Don't:

- **Don't** add shadows to content surfaces at rest or on hover; the header sheet and the CTA ledge are the only elevated objects.
- **Don't** reintroduce gradients, glow, blurred blooms, orbs or glass cards; the amber era is gone.
- **Don't** build SaaS furniture: three-column feature tiles, pill badges as decoration, sparkle icons.
- **Don't** use monospace as a voice. It is the label beside the work, never headings or body copy; the site is not a terminal.
- **Don't** set Fraunces in body text, controls, drafts or labels, and don't set body copy in anything but Instrument Sans.
- **Don't** use neutral grey for rules or muted surfaces; every neutral is warm paper (hue 30–38) in light mode and cool night (hue 220) in dark.
- **Don't** introduce a second accent colour; Iron Gall Soft exists for secondary fills and the four signal colours are for status only.
- **Don't** round a draft sheet or scale it on hover; squareness marks the work.
- **Don't** define `--spacing-xs..4xl` tokens in `@theme`; in Tailwind v4 they shadow the `max-w-*` container scale and collapse layouts.
- **Don't** animate content in, and don't ship a skeleton that a reader without JavaScript would keep.

## Enforcement

Seven of the rules above are machine-checked, so breaking them fails the build the way a type error does. `scripts/check-design-system.mjs` runs in CI (`Frontend Checks` → `Design check`, right after Lint); run it locally with:

```bash
bun run design:check                         # grouped, readable report
node scripts/check-design-system.mjs --json  # machine output
```

It reads `apps/web/app/**/*.tsx`, `apps/web/components/**/*.tsx` and `apps/web/types/*.ts` (no dependencies, well under a second) and enforces:

| Rule           | What fails                                                                                                                                                                                                                                                                                                      |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `palette`      | `bg-/text-/border-/from-/…-{red,orange,amber,yellow,lime,green,emerald,slate,gray,zinc,neutral,stone,violet,purple,indigo,blue,sky,cyan,teal,fuchsia,pink,rose}-NNN`. Status goes through `text-success`, `text-warning`, `text-info`, `text-destructive` and their `-muted` washes. _Guarded by the ratchet until it reaches zero._ |
| `flat-paper`   | `shadow-{2xs…2xl}` or an arbitrary `shadow-[…]` outside the header sheet. _Guarded._                                                                                                                                                                                                                             |
| `no-gradient`  | `bg-linear-*`, `bg-radial`, `bg-conic`, or a `*-gradient(` in markup. _Guarded._                                                                                                                                                                                                                                |
| `one-glass`    | `backdrop-blur` outside the header. _Guarded._                                                                                                                                                                                                                                                                  |
| `serif-speaks` | `font-display` in a `className` on anything but `h1`–`h6`, a `*Title` primitive, or an element marked `data-voice="display"`. _Active now._                                                                                                                                                                      |
| `tiny-font`    | `text-[Npx]` below 12px. _Guarded (one site)._                                                                                                                                                                                                                                                                  |
| `no-entrance`  | A framer-motion `initial={{ opacity: 0` mount reveal. _Guarded._                                                                                                                                                                                                                                                |

A guarded rule is one whose retired usage still exists on the day this document landed. Those usages are counted by the `LEGACY` ratchet at the top of the script and the count may only fall; a PR that adds one fails. The baselines on 2026-10-13 were: raw palette hues 5276, `bg-white`/`bg-black` 407, shadows 129, `backdrop-blur` 10, gradients 51, `glass-*` 17, `hero-rise*`/`data-reveal` 14, framer `initial={{ opacity: 0` 84, `font-serif` 26, `text-[10px]` 1. Lower a baseline in the PR that removes call sites; delete the entry at zero and the hard rule in the table takes over. The notebook lands in four PRs — Tailwind v4, this foundation, the marketing pages, the app pages — and the page PRs drive every entry to zero and then delete the transitional palette block, the flat-paper shims and the entrance keyframes from `globals.css`.

What is _not_ checked is not thereby allowed — wall labels before sections, square draft sheets and the one-button-per-view rule still need a human eye.

Genuine exceptions live in one place: the `ALLOWLIST` constant at the top of the script, one entry per exception with a one-line reason. It is empty today: the header sheet's shadow and blur, the two sanctioned exceptions, live in the `header-sheet` utility in `globals.css` rather than in a class string, so no component needs an exemption. Widening the allowlist is a policy decision and should read like one in the diff; loosening a rule's regex to make a violation disappear is not.
