---
name: Blog AI
description: Amber-on-cream editorial SaaS; Inter for the interface, Source Serif 4 for the claims.
colors:
  primary: "#b45309"
  primary-hover: "#92400e"
  primary-fill: "#d97706"
  primary-dark: "#fbbf24"
  primary-soft: "#fef3c7"
  primary-wash: "#fffbeb"
  primary-ink: "#78350f"
  success: "#059669"
  danger: "#dc2626"
  tier-pro: "#4338ca"
  tier-pro-soft: "#e0e7ff"
  canvas: "#fff8e6"
  surface: "#ffffff"
  surface-alt: "#f9fafb"
  ink: "#111827"
  body: "#4b5563"
  muted: "#6b7280"
  border: "#e5e7eb"
  border-strong: "#d1d5db"
  dark-canvas: "#0f0f0f"
  dark-surface: "#111827"
  dark-border: "#1f2937"
  dark-ink: "#f3f4f6"
  dark-body: "#9ca3af"
typography:
  display:
    fontFamily: "Source Serif 4, Iowan Old Style, Times New Roman, serif"
    fontSize: "clamp(2.25rem, 5vw, 3.75rem)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Source Serif 4, Iowan Old Style, Times New Roman, serif"
    fontSize: "clamp(1.875rem, 3vw, 2.25rem)"
    fontWeight: 600
    lineHeight: 1.2
  title:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.5
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.625
  body-sm:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.625
  label:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    letterSpacing: "0.05em"
rounded:
  md: "6px"
  lg: "8px"
  xl: "12px"
  2xl: "16px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  section: "80px"
  section-lg: "112px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "8px 16px"
    typography: "{typography.body-sm}"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-hero:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.xl}"
    padding: "14px 28px"
    typography: "{typography.body}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.body}"
    rounded: "{rounded.xl}"
    padding: "14px 28px"
  button-neutral:
    backgroundColor: "{colors.surface-alt}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
  chip:
    backgroundColor: "{colors.surface-alt}"
    textColor: "{colors.body}"
    rounded: "{rounded.full}"
    padding: "6px 12px"
    typography: "{typography.label}"
  badge-primary:
    backgroundColor: "{colors.primary-soft}"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
    typography: "{typography.label}"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.xl}"
    padding: "24px"
  card-glass:
    rounded: "{rounded.2xl}"
    padding: "32px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "8px 12px"
  banner:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    padding: "48px 16px"
---

# Design System: Blog AI

## Overview

**Creative North Star: "The Warm Press"**

Blog AI looks like a small, well-run publishing house that happens to be software. The
canvas is a faint cream that drifts to white, the accent is a single burnt amber, and
every claim on the marketing surfaces is set in a serif while every control is set in
Inter. The tone is confident and unhurried: generous section padding, one accent, no
decoration that does not carry meaning.

The system is one hue deep. Amber does all the work: dark amber for text and filled
actions, mid amber for switches and progress, pale amber for icon tiles, badges and hover
washes. Green and red appear only as status. The Pro tier borrows indigo for its badge
and nothing else. The dark theme swaps the cream for near-black and the amber steps two
shades lighter; it is a re-lit version of the same room, not a second brand.

**Key Characteristics:**
- Serif display over sans interface, both at semibold, never bold-on-bold.
- One accent hue, four jobs (text, fill, tile, wash), tinted rather than grayed.
- Cream canvas with translucent "glass" cards that let the gradient breathe through.
- Hairline borders (1px) carry structure; shadows are quiet and reserved for hover.
- Motion is a single fade-and-rise per section, then stillness.

## Colors

One warm accent on a cream-to-white ground, with a neutral gray ramp for text and lines.

### Primary
- **Burnt Amber** (`{colors.primary}`, Tailwind amber-700): text links, filled primary
  buttons, the amber band behind page banners, icons on white. 5.0:1 on white and 4.8:1
  on the amber wash, so it is safe for small text everywhere. Hover darkens to
  **Toasted Amber** (`{colors.primary-hover}`, amber-800).
- **Live Amber** (`{colors.primary-fill}`, amber-600): non-text fills where 3:1 is the bar:
  toggle switches, progress bars, the sliding filter indicator, spinner heads, the
  `--accent-rgb` CSS variable. Never under white text.
- **Lamp Amber** (`{colors.primary-dark}`, amber-400): the accent for text and icons on
  the dark theme, paired with `amber-300` on hover.
- **Amber Tile** (`{colors.primary-soft}`, amber-100) and **Amber Wash**
  (`{colors.primary-wash}`, amber-50): icon tiles, tier badges, selected list rows and
  hover washes on chips. Text on these is Burnt Amber or **Amber Ink**
  (`{colors.primary-ink}`, amber-900), never gray.

### Secondary
- **Pro Indigo** (`{colors.tier-pro}` on `{colors.tier-pro-soft}`): the Pro-tier badge
  only. It marks a plan, not an action.

### Tertiary
- **Status Green** (`{colors.success}`, emerald-600) and **Status Red**
  (`{colors.danger}`, red-600): connected/active, destructive/error. Both come with their
  own 50/100 washes for chips and icon-button hovers.

### Neutral
- **Cream Canvas** (`{colors.canvas}` to `{colors.surface}`): the body is a 120deg
  gradient from cream at the top-left to white by 70%. Marketing sections alternate
  between this canvas and a translucent glass band.
- **Surface** (`{colors.surface}`) and **Surface Alt** (`{colors.surface-alt}`, gray-50):
  cards and inputs on the former; the footer, neutral chips and secondary buttons on the
  latter.
- **Ink** (`{colors.ink}`, gray-900): headings and primary text.
- **Body** (`{colors.body}`, gray-600): paragraphs and descriptions.
- **Muted** (`{colors.muted}`, gray-500): captions, timestamps, icon buttons at rest,
  legal text. This is the lightest gray allowed on any light surface (4.6:1 on gray-50).
- **Line** (`{colors.border}`, gray-200) and **Line Strong** (`{colors.border-strong}`,
  gray-300, inputs): every structural border.
- **Dark theme**: canvas `{colors.dark-canvas}` to `#171717`, surfaces
  `{colors.dark-surface}`, lines `{colors.dark-border}`, ink `{colors.dark-ink}`, body
  `{colors.dark-body}`. Muted text on dark is gray-400, never gray-500.

### Named Rules
**The One Hue Rule.** Amber is the only color with a voice. Green and red state a status;
indigo names a plan; nothing else gets a hue.

**The Tint-Not-Gray Rule.** Text that sits on a colored surface is a darker shade of that
surface's hue (amber-700/900 on amber-50, emerald-700 on emerald-50). Gray text on color
is a defect.

**The Contrast Floor Rule.** Small text is at least 4.5:1, icons and fills at least 3:1,
in both themes. The gray-400 step is a placeholder and disabled color, not a text color.

## Typography

**Display Font:** Source Serif 4 (with Iowan Old Style, Times New Roman, serif)
**Body Font:** Inter (with ui-sans-serif, system-ui, sans-serif)

**Character:** A bookish serif for what the product claims, a neutral grotesque for what
the product does. Both are loaded through `next/font` with `display: swap` and exposed as
`--font-serif` / `--font-sans`. Neither ever exceeds semibold on marketing pages; `bold`
appears only inside product pages for stat values.

### Hierarchy
- **Display** (600, `{typography.display.fontSize}`, 1.1): the home hero only. Tight
  tracking (-0.025em). One amber phrase is allowed inside it.
- **Headline** (600, 1.875 to 2.25rem, 1.2): section headings on marketing surfaces, page
  banner titles, all in the serif.
- **Title** (600, 1.125 to 1.25rem, 1.5): card and feature titles, in Inter.
- **Body** (400, 1rem, 1.625): descriptions; marketing lead paragraphs step up to
  1.125 to 1.25rem. Measure is held at `max-w-2xl` (about 65ch).
- **Body Small** (400, 0.875rem, 1.625): the default size inside product UI, feature
  bullets, footer links.
- **Label** (500, 0.75rem, 0.05em tracking): badges, chips, step markers (upper-case
  with `tracking-wider`), and the copyright line.

### Named Rules
**The Serif Speaks Rule.** The serif is reserved for h1 and h2 on marketing and banner
surfaces. Product UI headings stay in Inter so the workspace reads as a tool.

## Layout

Content sits in a `max-w-7xl` (80rem) container with 16 / 24 / 32px side padding at the
`sm` / `lg` breakpoints (Tailwind defaults: 640, 768, 1024, 1280px). Marketing sections
use 80px vertical padding, rising to 112px from `sm`; product pages use 32 to 48px.
Reading columns cap at `max-w-2xl` (42rem) and `max-w-3xl` for the hero.

Grids are 1 column, 2 from `sm`, and 3 or 4 from `md`, with 24 to 32px gaps. The header
is a sticky 64px white bar with a hairline bottom border; the primary navigation collapses
under `md` into a stacked list. Spacing follows the Tailwind 4px scale; within a card,
icon tile, title and body are separated by 20 / 8px, and groups by 24 / 32px.

## Elevation & Depth

Depth is mostly tonal. Cards are white on the cream canvas with a 1px gray-200 border,
and the marketing surfaces use a translucent glass card (55% white, 1px 35% white border,
18px backdrop blur) that lets the gradient show through. Shadows are small at rest and
grow on hover; the only colored shadow is the amber-tinted glass shadow.

### Shadow Vocabulary
- **Rest** (`box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05)`, `shadow-sm`): buttons, cards,
  selected chips. The default and by far the most common.
- **Lift** (`shadow-md` / `shadow-lg`): hover on cards and tool pills, the highlighted
  pricing tier (`shadow-lg` with a 10% amber tint).
- **Glass** (`0 20px 60px rgba(217, 119, 6, 0.12)`; dark: `rgba(245, 158, 11, 0.08)`):
  the `.glass-card` ambient shadow.

### Named Rules
**The Quiet Rest Rule.** Nothing floats at rest beyond `shadow-sm`. Elevation is a
response to hover or to being the highlighted option.

## Shapes

Corners are soft and consistent: 8px (`rounded-lg`) is the default for buttons, inputs,
chips with text and list rows; 12px (`rounded-xl`) for icon tiles, hero buttons and
product cards; 16px (`rounded-2xl`) for marketing cards and step tiles; full pills for
badges, category chips and loading dots. Borders are 1px hairlines in gray-200 (gray-800
on dark). Accent borders are full-perimeter (`border-amber-400` for a highlighted row,
`border-2 border-amber-500/60` for the featured plan); there are no side tabs, and
blockquotes use a 1px amber rule. Spinners are a 2px amber-200 track with an amber-600
head.

## Components

### Buttons
- **Shape:** 8px radius in product UI, 12px for the two hero actions.
- **Primary:** Burnt Amber fill, white text, 500 weight; `px-4 py-2 text-sm` in UI,
  `px-7 py-3.5 text-base` in the hero. Hover: Toasted Amber. Focus: 2px amber-500 ring
  with 2px offset (`focus-visible:ring-2 focus-visible:ring-amber-500`).
- **Primary gradient:** long-form generate/submit buttons use a left-to-right
  amber-700 to amber-800 gradient, hover amber-800 to amber-900, `shadow-sm`.
- **Secondary:** 70% white fill, 8% black hairline, backdrop blur, gray-700 text;
  hover firms the border to 12% and the fill to 90%.
- **Neutral:** gray-100 fill, gray-900 text, hover gray-200 (unfeatured plan CTAs).
- **On amber band:** white fill with amber-700 text (hover amber-50), or white text with a
  30% white border (hover 10% white fill). Focus ring is white with an amber-700 offset.
- **Disabled:** 50% opacity, or gray-400 fill for gradient buttons.

### Chips
- **Style:** full pill, gray-100 fill, gray-700 12px text; hover amber-50 fill with
  amber-700 text. Tool-category pills use each category's own 50/700 pair with a matching
  200 border and lift to `shadow-md` on hover.
- **State:** selected filters switch to Burnt Amber fill with white text and `shadow-sm`;
  a framer-motion `layoutId` indicator slides behind the selected item.

### Badges
- **Style:** full pill, amber-100 fill, amber-700 text, 12px 500 weight (`px-2 py-0.5`);
  Pro tier uses indigo-100 / indigo-700. "Most Popular" inverts to Burnt Amber fill with
  white text.

### Cards / Containers
- **Corner Style:** 12px in product UI, 16px on marketing.
- **Background:** white with 1px gray-200 border (`card-surface`), or `.glass-card`.
- **Shadow Strategy:** `shadow-sm` at rest, `shadow-lg` on hover for feature cards.
- **Internal Padding:** 24px (`p-6`), 32px (`p-8`) on marketing.
- **Icon tile:** 44px square, 12px radius, amber-100/80 fill, amber-700 icon at 20px.

### Inputs / Fields
- **Style:** white fill, 1px gray-300 border, 8px radius, gray-900 text, gray-400
  placeholder; dark: gray-800 fill, gray-700 border, gray-100 text.
- **Focus:** `focus:ring-2 focus:ring-amber-500` with `focus:border-amber-500`.
- **Error / Disabled:** red-500 border and red-600 helper text; disabled at 50% opacity.
- **Switches:** 44x24 pill, Live Amber when on, gray-200 when off, white knob.

### Navigation
- Sticky white header, 64px, hairline bottom border; wordmark is the sparkles icon in
  Burnt Amber beside "Blog AI" at 600. Links are 14px gray-700 with amber-700 hover
  (amber-400 on dark). The theme toggle cycles light / dark / system. Mobile: a bordered
  panel of 14px rows with gray-50 hover.
- Footer: gray-50 with hairline top border, four columns of 14px links in Muted with
  amber hover; a 12px Muted bottom bar.

### Page Banner
Product pages open with a full-width amber band (gradient amber-700 to amber-800) carrying
a white serif h1 and an amber-100 lead paragraph, 48 to 64px of vertical padding, sometimes
with quick stats. It is the only place the accent covers a large area.

### Loading
Three 10px amber dots (400 / 500 / 600) pulsing with 0 / 150 / 300ms delays for auth and
typing indicators; a 2px track-and-head spinner for panels; `app/loading.tsx` adds a
"still loading?" recovery card after 8 seconds.

## Do's and Don'ts

### Do:
- **Do** put small text in gray-500 or darker on light surfaces and gray-400 or lighter on
  dark surfaces; both clear 4.5:1.
- **Do** use amber-700 for any amber that carries text or sits under white text, and keep
  amber-600 for fills that only need 3:1.
- **Do** tint text on a colored wash from that wash's hue (amber-900 on amber-50,
  red-600 on red-50).
- **Do** keep the serif for marketing and banner headings, at semibold, with tight tracking
  only on the display size.
- **Do** reveal sections once with the shared `FADE_UP` variant (24px rise, 0.5s ease-out,
  0.12s stagger, `useInView` once) and leave everything else still.
- **Do** use full-perimeter hairline borders and `shadow-sm` for structure; lift to
  `shadow-lg` only on hover or for the featured option.

### Don't:
- **Don't** set white text on amber-600 or lighter; it fails AA.
- **Don't** use gray-400 for anything but placeholders and disabled states on a light
  surface.
- **Don't** add a colored left or right border thicker than 1px to a card, list row, quote
  or callout; highlight with a full amber border or a wash instead.
- **Don't** use bounce or elastic motion; loading states pulse or spin.
- **Don't** introduce a second accent hue. Indigo exists for the Pro badge only; purple,
  blue and violet gradients are out.
- **Don't** put a kicker or eyebrow label above a heading; the serif heading carries the
  section. (The numbered "Step 01" markers are the one legacy exception and carry
  sequence information.)
