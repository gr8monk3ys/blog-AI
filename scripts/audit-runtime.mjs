#!/usr/bin/env bun

import { spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'

const BLOCKING_SEVERITIES = new Set(['high', 'critical'])
const ALLOWED_ADVISORY_IDS = new Set([
  'GHSA-3PPC-4F35-3M26',
  // picomatch ReDoS via extglob quantifiers. Reachable only through build/dev
  // tooling globs (tailwindcss -> chokidar/micromatch, fast-glob); no production
  // runtime exposure. The patched 2.3.2 is within the parents' ^2 range but
  // can't be forced without clashing with the ^4.x consumers (bun lacks scoped
  // overrides). Accepted dev-only risk; revisit when micromatch moves off
  // picomatch 2.x. See docs/REMEDIATION_PLAN.md (Phase 0.3).
  'GHSA-C2C7-RCM5-VVQJ',
])

function extractAdvisoryId(value) {
  if (!value || typeof value !== 'string') return null
  const match = value.match(/GHSA-[\w-]+/i)
  return match ? match[0].toUpperCase() : null
}

function parseAuditOutput(stdout) {
  const raw = String(stdout || '')
  const jsonStart = raw.indexOf('{')
  if (jsonStart === -1) {
    throw new Error('bun audit did not return JSON output.')
  }

  return JSON.parse(raw.slice(jsonStart))
}

function collectBlockingIssues(report) {
  const issues = []

  for (const [name, advisories] of Object.entries(report)) {
    if (!Array.isArray(advisories)) continue

    for (const advisory of advisories) {
      const severity = String(advisory?.severity || '').toLowerCase()
      if (!BLOCKING_SEVERITIES.has(severity)) continue

      const advisoryId =
        extractAdvisoryId(advisory?.url) ??
        extractAdvisoryId(advisory?.title) ??
        (typeof advisory?.id === 'number' ? `audit:${advisory.id}` : null)

      if (advisoryId && ALLOWED_ADVISORY_IDS.has(advisoryId)) {
        continue
      }

      issues.push({
        advisoryId,
        name,
        severity,
        title: advisory?.title ?? 'Untitled advisory',
      })
    }
  }

  return issues
}

let report
try {
  if (process.env.BUN_AUDIT_JSON_PATH) {
    report = JSON.parse(readFileSync(process.env.BUN_AUDIT_JSON_PATH, 'utf8'))
  } else {
    const audit = spawnSync('bun', ['audit', '--audit-level=high', '--json'], {
      encoding: 'utf8',
    })
    report = parseAuditOutput(audit.stdout)
  }
} catch (error) {
  console.error('Unable to parse bun audit output.')
  console.error(error instanceof Error ? error.message : String(error))
  process.exit(1)
}

const blocking = collectBlockingIssues(report)

if (blocking.length > 0) {
  console.error('Blocking Bun audit findings detected:')
  for (const issue of blocking) {
    const advisoryLabel = issue.advisoryId ? ` ${issue.advisoryId}` : ''
    console.error(`- ${issue.name} (${issue.severity})${advisoryLabel}: ${issue.title}`)
  }
  process.exit(1)
}

console.log('Runtime dependency audit passed policy checks.')
