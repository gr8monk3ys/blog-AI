#!/usr/bin/env node
/* global console, process */
/**
 * check-design-system.mjs — make DESIGN.md fail the build the way TypeScript does.
 *
 * DESIGN.md (The Manuscript) documents named rules: The One Pen Rule, The
 * Flat Paper Rule, The Two Sheets Rule, The Serif Speaks Rule, … Prose does
 * not fail CI, so the rules that are mechanically checkable are checked here.
 * Zero dependencies, plain Node, one pass over apps/web/{app,components}/**\/*.tsx
 * and apps/web/types/*.ts (class strings live there too).
 *
 *   node scripts/check-design-system.mjs          human-readable report
 *   node scripts/check-design-system.mjs --json   machine output
 *
 * Exit 0 when clean, 1 when any rule fires.
 *
 * Two kinds of rule live here. Hard rules fail on the first hit. The legacy
 * ratchet counts names left over from the amber-on-cream identity and fails
 * only if a count GROWS; the page PRs take each entry to zero, delete it, and
 * the matching hard rule (`then`) takes over.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const WEB = join(ROOT, 'apps', 'web')
const SCAN = [
  { dir: join(WEB, 'app'), ext: '.tsx' },
  { dir: join(WEB, 'components'), ext: '.tsx' },
  { dir: join(WEB, 'types'), ext: '.ts' },
]

/* ------------------------------------------------------------------ policy */

/**
 * Every Tailwind hue is off-system. DESIGN.md → Colors → The One Pen Rule:
 * colour goes through the tokens, and status goes through text-success /
 * text-warning / text-info / text-destructive — never `emerald-500`. Every
 * family is ratcheted below until the page PRs have moved the call sites;
 * the hard rule then runs against this list.
 */
const PALETTE_FAMILIES = [
  'red',
  'orange',
  'amber',
  'yellow',
  'lime',
  'green',
  'emerald',
  'slate',
  'gray',
  'zinc',
  'neutral',
  'stone',
  'violet',
  'purple',
  'indigo',
  'blue',
  'sky',
  'cyan',
  'teal',
  'fuchsia',
  'pink',
  'rose',
]

const PALETTE_PREFIXES =
  'bg|text|border|from|to|via|ring|shadow|placeholder|divide|outline|fill|stroke|decoration|accent|caret'

/**
 * Documented exemptions. One entry per exemption, one line saying WHY it is
 * data (or a sanctioned singleton) rather than styling. Changing what is
 * allowed is a one-line edit here — never a change to a rule's regex.
 *
 *   rule   which rule the exemption applies to
 *   file   repo-relative path, forward slashes
 *   block  optional: only inside this named declaration (`const NAME = ...`)
 *   lines  optional: only these 1-based line numbers
 *   limit  optional: exempt at most this many hits
 */
const ALLOWLIST = [
  // Empty today. The header sheet's shadow and blur — the two sanctioned
  // exceptions (DESIGN.md → Elevation → The Two Sheets Rule) — live in the
  // `header-sheet` utility in apps/web/app/globals.css, not in a class string,
  // so no .tsx file needs an exemption. The shape of an entry:
  //   { rule: 'flat-paper', file: 'apps/web/components/X.tsx', limit: 1, why: '…' }
]

/**
 * The legacy ratchet. Each pattern is a retired name; `baseline` is how many
 * times it appeared when the notebook landed. A count above baseline fails.
 * Lower the baseline in the same PR that removes call sites, and delete the
 * entry at zero — at which point the hard rule named in `then` (if any)
 * starts running. `count` is filled in at scan time.
 *
 */
const LEGACY = [
  // Baselines counted on 2026-10-13, the day the notebook tokens landed.
  {
    name: 'palette-hue',
    pattern: new RegExp(
      `\\b(?:${PALETTE_PREFIXES})-(?:${PALETTE_FAMILIES.join('|')})-[0-9]{2,3}\\b`,
      'g'
    ),
    baseline: 5276,
    then: 'palette',
  },
  {
    // `bg-white` on paper is a white box on a grey page (The Tinted Paper
    // Rule); `bg-black/25` is a scrim that is not the scrim.
    name: 'white-black',
    pattern: new RegExp(`\\b(?:${PALETTE_PREFIXES})-(?:white|black)(?![\\w-])`, 'g'),
    baseline: 407,
  },
  {
    name: 'shadow',
    pattern: /(?<![\w-])(?:[\w-]+:)*shadow-(?:2xs|xs|sm|md|lg|xl|2xl|\[)/g,
    baseline: 128,
    then: 'flat-paper',
  },
  {
    name: 'backdrop-blur',
    pattern: /(?<![\w-])(?:[\w-]+:)*backdrop-blur(?:-[\w]+)?(?![\w-])/g,
    baseline: 9,
    then: 'one-glass',
  },
  {
    name: 'gradient',
    pattern:
      /(?<![\w-])(?:[\w-]+:)*(?:bg-linear-|bg-radial|bg-conic)[\w-]*|(?:linear|radial|conic)-gradient\(/g,
    baseline: 51,
    then: 'no-gradient',
  },
  { name: 'glass', pattern: /\bglass-(?:card|surface|panel)\b/g, baseline: 17 },
  {
    name: 'entrance-css',
    pattern: /\bhero-(?:rise(?:-lcp)?|fade)\b|\bdata-reveal(?:-stagger)?\b/g,
    baseline: 14,
  },
  {
    name: 'entrance-motion',
    pattern: /initial=\{\{\s*opacity:\s*0/g,
    baseline: 84,
    then: 'no-entrance',
  },
  // The pre-notebook serif class name; the notebook speaks in `font-display`.
  { name: 'font-serif', pattern: /(?<![\w-])font-serif(?![\w-])/g, baseline: 26 },
  {
    name: 'tiny-font',
    pattern: /text-\[(?:[0-9]|1[01])(?:\.[0-9]+)?px\]/g,
    baseline: 1,
    then: 'tiny-font',
  },
]

const RULES = {
  palette: {
    title: 'Hardcoded Tailwind palette utilities',
    doc: 'DESIGN.md → Colors → The One Pen Rule. Route every colour through the tokens; status is text-success / text-warning / text-info / text-destructive.',
  },
  'flat-paper': {
    title: 'Shadow on a content surface',
    doc: "DESIGN.md → Elevation → The Flat Paper Rule and The Two Sheets Rule: only the header sheet and cta-primary's ledge cast a shadow.",
  },
  'no-gradient': {
    title: 'Gradient fill or text',
    doc: 'DESIGN.md → Colors → The One Pen Rule: ink marks action and emphasis, never area. No gradient anywhere.',
  },
  'one-glass': {
    title: 'backdrop-blur outside the header',
    doc: 'DESIGN.md → Shapes: glass is for chrome that sits over itself, not for content.',
  },
  'serif-speaks': {
    title: 'Display font outside a heading',
    doc: 'DESIGN.md → Typography → The Serif Speaks Rule: Fraunces on h1–h6, the type-scale utilities and the wordmark only. Mark a deliberate exception with data-voice="display".',
  },
  'tiny-font': {
    title: 'Literal font size below the 12px label step',
    doc: 'DESIGN.md → Typography → Label: the wall label is the only thing under 12px, and it is a utility, not a literal.',
  },
  'no-entrance': {
    title: 'Content animates itself in',
    doc: 'DESIGN.md → Motion: content does not animate itself in. Hover, focus and loading indicators move; the page does not.',
  },
  'legacy-ratchet': {
    title: 'A retired name came back',
    doc: 'scripts/check-design-system.mjs → LEGACY: counts may only fall. Remove the new use, or lower the baseline in the PR that removes others.',
  },
}

/* ------------------------------------------------------------------- files */

function walk(dir, ext, out = []) {
  let entries
  try {
    entries = readdirSync(dir)
  } catch {
    return out
  }
  for (const entry of entries) {
    if (entry === 'node_modules' || entry === '.next' || entry.startsWith('.')) continue
    const full = join(dir, entry)
    const stat = statSync(full)
    if (stat.isDirectory()) walk(full, ext, out)
    else if (entry.endsWith(ext) && !entry.endsWith('.d.ts')) out.push(full)
  }
  return out
}

const cache = new Map()
function read(absPath) {
  let hit = cache.get(absPath)
  if (!hit) {
    const text = readFileSync(absPath, 'utf8')
    hit = { text, lines: text.split('\n') }
    cache.set(absPath, hit)
  }
  return hit
}

// Forward slashes on every platform: ALLOWLIST entries are written with "/",
// and on Windows `relative()` returns "\".
const rel = (absPath) => relative(ROOT, absPath).split('\\').join('/')

/* --------------------------------------------------------------- allowlist */

/**
 * Line range [start, end] of `const NAME = ...` / `function NAME(...)`, found by
 * bracket matching. For a `const` the count starts at the `=` so a multi-line
 * type annotation does not close the block early; for a `function` it starts
 * at the declaration line, so the parameter list balances out.
 */
function blockRange(lines, name) {
  const head = new RegExp(
    `^\\s*(?:export\\s+)?(?:async\\s+)?(?:const|let|var|function)\\s+${name}\\b`
  )
  const start = lines.findIndex((line) => head.test(line))
  if (start === -1) return null
  const isBinding = /^\s*(?:export\s+)?(?:const|let|var)\b/.test(lines[start])

  let depth = 0
  let counting = !isBinding
  for (let i = start; i < lines.length; i++) {
    const line = lines[i]
    for (let c = 0; c < line.length; c++) {
      const ch = line[c]
      if (!counting) {
        if (
          ch === '=' &&
          !'=><!'.includes(line[c + 1] ?? '') &&
          !'=><!'.includes(line[c - 1] ?? '')
        )
          counting = true
        continue
      }
      if (ch === '{' || ch === '(' || ch === '[') depth++
      else if (ch === '}' || ch === ')' || ch === ']') depth--
    }
    if (counting && depth <= 0 && i > start) return [start + 1, i + 1]
    if (counting && depth <= 0 && i === start && /[)}\]]/.test(line)) return [start + 1, i + 1]
  }
  return [start + 1, lines.length]
}

const rangeCache = new Map()
const used = new Map()

function take(entry) {
  const count = (used.get(entry) ?? 0) + 1
  used.set(entry, count)
  if (entry.limit === undefined) return entry
  return count <= entry.limit ? entry : null
}

function isAllowed(rule, file, line, lines) {
  for (const entry of ALLOWLIST) {
    if (entry.rule !== rule || entry.file !== file) continue
    if (entry.lines) {
      if (entry.lines.includes(line)) return take(entry)
      continue
    }
    if (entry.block) {
      const key = `${file}::${entry.block}`
      if (!rangeCache.has(key)) rangeCache.set(key, blockRange(lines, entry.block))
      const range = rangeCache.get(key)
      if (range && line >= range[0] && line <= range[1]) return take(entry)
      continue
    }
    return take(entry)
  }
  return null
}

/* ------------------------------------------------------------------- utils */

function* matchLines(lines, regex) {
  for (let i = 0; i < lines.length; i++) {
    regex.lastIndex = 0
    let m
    while ((m = regex.exec(lines[i])) !== null) {
      yield { line: i + 1, match: m[0], text: lines[i] }
      if (m[0] === '') regex.lastIndex++
    }
  }
}

const snippet = (text) => text.trim().replace(/\s+/g, ' ').slice(0, 118)

/* ------------------------------------------------------------------- rules */

const violations = []
function report(rule, file, line, text) {
  violations.push({ rule, file, line, snippet: snippet(text) })
}

const files = SCAN.flatMap(({ dir, ext }) => walk(dir, ext))
const activeHardRules = new Set(
  Object.keys(RULES).filter(
    (rule) => !LEGACY.some((entry) => entry.then === rule && entry.baseline > 0)
  )
)

function scan(rule, re, { transform } = {}) {
  if (!activeHardRules.has(rule)) return
  for (const abs of files) {
    const file = rel(abs)
    const { lines } = read(abs)
    for (const hit of matchLines(lines, re)) {
      const keep = transform ? transform(hit) : hit.match
      if (!keep) continue
      if (isAllowed(rule, file, hit.line, lines)) continue
      report(rule, file, hit.line, `${keep}  —  ${hit.text}`)
    }
  }
}

// palette — The One Pen Rule (guarded by the palette-hue ratchet).
scan(
  'palette',
  new RegExp(`\\b(?:${PALETTE_PREFIXES})-(?:${PALETTE_FAMILIES.join('|')})-[0-9]{2,3}\\b`, 'g')
)

// flat-paper — guarded by the shadow ratchet until the amber call sites are gone.
scan('flat-paper', /(?<![\w-])(?:[\w-]+:)*shadow-(?:2xs|xs|sm|md|lg|xl|2xl|\[[^\]]*\])(?![\w-])/g)

// no-gradient — utilities and raw CSS functions in markup.
scan(
  'no-gradient',
  /(?<![\w-])(?:[\w-]+:)*(?:bg-linear-|bg-radial|bg-conic)[\w-]*|(?:linear|radial|conic)-gradient\(/g
)

// one-glass — guarded by the backdrop-blur ratchet.
scan('one-glass', /(?<![\w-])(?:[\w-]+:)*backdrop-blur(?:-[\w]+)?(?![\w-])/g)

// serif-speaks — `font-display` on anything that is not a heading. Active
// from day one: the class is new with the notebook.
scan('serif-speaks', /<([A-Za-z][\w.]*)\b[^>]*\bfont-display\b/g, {
  transform(hit) {
    const tag = hit.match.match(/^<([A-Za-z][\w.]*)/)[1]
    // h1–h6, and the *Title primitives, which render headings.
    if (/^h[1-6]$/.test(tag) || /Title$/.test(tag)) return null
    if (/data-voice=["']display["']/.test(hit.text)) return null
    return `<${tag}> font-display`
  },
})

// tiny-font — literal font sizes below the 12px label step.
scan('tiny-font', /text-\[([0-9]+(?:\.[0-9]+)?)px\]/g, {
  transform(hit) {
    return Number(hit.match.match(/([0-9.]+)px/)[1]) < 12 ? hit.match : null
  },
})

// no-entrance — framer-motion mount reveals (guarded by the entrance-motion ratchet).
scan('no-entrance', /initial=\{\{\s*opacity:\s*0/g)

// legacy-ratchet — counts may only fall.
for (const entry of LEGACY) {
  let count = 0
  for (const abs of files) {
    entry.pattern.lastIndex = 0
    count += (read(abs).text.match(entry.pattern) ?? []).length
  }
  entry.count = count
  if (count > entry.baseline) {
    report(
      'legacy-ratchet',
      'apps/web/',
      0,
      `${entry.name}: ${count} uses, baseline ${entry.baseline}`
    )
  }
}

/* ------------------------------------------------------------------ output */

const order = Object.keys(RULES)
violations.sort(
  (a, b) =>
    order.indexOf(a.rule) - order.indexOf(b.rule) || a.file.localeCompare(b.file) || a.line - b.line
)

if (process.argv.includes('--json')) {
  const byRule = Object.fromEntries(
    order.map((r) => [r, violations.filter((v) => v.rule === r).length])
  )
  process.stdout.write(
    `${JSON.stringify(
      {
        ok: violations.length === 0,
        filesScanned: files.length,
        total: violations.length,
        rules: order,
        byRule,
        violations,
        legacy: LEGACY.map(({ name, baseline, count, then }) => ({ name, baseline, count, then })),
        allowlist: ALLOWLIST.map((entry) => ({
          rule: entry.rule,
          file: entry.file,
          block: entry.block,
          lines: entry.lines,
          limit: entry.limit,
          why: entry.why,
          applied: used.get(entry) ?? 0,
        })),
      },
      null,
      2
    )}\n`
  )
  process.exit(violations.length === 0 ? 0 : 1)
}

if (violations.length === 0) {
  const ratchet = LEGACY.filter((e) => e.baseline > 0)
  console.log(`design-system: OK — ${files.length} files, 0 violations`)
  if (ratchet.length) {
    console.log(
      `   legacy ratchet: ${ratchet.map((e) => `${e.name} ${e.count}/${e.baseline}`).join(', ')}`
    )
  }
  process.exit(0)
}

console.log('')
console.log(`design-system: ${violations.length} violation(s) across ${files.length} files`)
for (const rule of order) {
  const hits = violations.filter((v) => v.rule === rule)
  if (hits.length === 0) continue
  console.log('')
  console.log(`── ${RULES[rule].title}  (${hits.length})`)
  for (const hit of hits) console.log(`   ${hit.file}:${hit.line}  ${hit.snippet}`)
  console.log(`   → ${RULES[rule].doc}`)
}
console.log('')
console.log('Summary:')
for (const rule of order) {
  const count = violations.filter((v) => v.rule === rule).length
  console.log(`   ${String(count).padStart(3)}  ${rule}`)
}
console.log(`   ${String(violations.length).padStart(3)}  total`)
console.log('')
console.log(
  `Genuine data and sanctioned singletons belong in ALLOWLIST at the top of ${rel(
    fileURLToPath(import.meta.url)
  )} — one entry, one reason. Retired names are counted in LEGACY and may only fall.`
)
process.exit(1)
