#!/usr/bin/env node
// Usage: node scripts/verify-summary.mjs <stage> <report-file>
// Reads a machine-readable test report (vitest/jest --json, playwright json, or JUnit XML)
// and prints ONE line: VERIFY stage=<name> tests=<total> passed=<n> failed=<n> skipped=<n>
// The line is also appended to $GITHUB_STEP_SUMMARY when set. Exits 1 if counts can't be parsed.
import { appendFileSync, readFileSync } from 'node:fs'
import { pathToFileURL } from 'node:url'

export function parseCounts(text) {
  const trimmed = text.trim()
  if (trimmed.startsWith('<')) {
    // JUnit XML: sum every <testsuite> (pytest, vitest, jest-junit all emit these).
    let tests = 0, failed = 0, skipped = 0, seen = 0
    for (const m of trimmed.matchAll(/<testsuite\b([^>]*)>/g)) {
      const attr = (name) => Number((m[1].match(new RegExp(`\\b${name}="(\\d+)"`)) || [])[1] ?? 0)
      tests += attr('tests'); failed += attr('failures') + attr('errors'); skipped += attr('skipped'); seen++
    }
    if (!seen) throw new Error('no <testsuite> elements in JUnit XML')
    return { tests, passed: tests - failed - skipped, failed, skipped }
  }
  const j = JSON.parse(trimmed)
  if (j.stats && typeof j.stats.expected === 'number') {
    // Playwright JSON reporter
    const { expected, unexpected, flaky, skipped } = j.stats
    return { tests: expected + unexpected + flaky + skipped, passed: expected + flaky, failed: unexpected, skipped }
  }
  if (typeof j.numTotalTests === 'number') {
    // Jest --json and vitest --reporter=json share this shape
    const skipped = (j.numPendingTests ?? 0) + (j.numTodoTests ?? 0)
    return { tests: j.numTotalTests, passed: j.numPassedTests, failed: j.numFailedTests, skipped }
  }
  throw new Error('unrecognised report format')
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [stage, file] = process.argv.slice(2)
  if (!stage || !file) {
    console.error('usage: verify-summary.mjs <stage> <report-file>')
    process.exit(1)
  }
  let c
  try {
    c = parseCounts(readFileSync(file, 'utf8'))
    if (![c.tests, c.passed, c.failed, c.skipped].every(Number.isInteger) || c.tests === 0) {
      throw new Error(`implausible counts ${JSON.stringify(c)}`)
    }
  } catch (err) {
    console.error(`verify-summary: cannot parse ${file}: ${err.message}`)
    process.exit(1)
  }
  const line = `VERIFY stage=${stage} tests=${c.tests} passed=${c.passed} failed=${c.failed} skipped=${c.skipped}`
  console.log(line)
  if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, `${line}\n`)
}
