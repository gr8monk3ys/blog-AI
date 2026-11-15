#!/usr/bin/env node
// Usage: node scripts/verify-summary.mjs <stage> <report-file>
// Reads a machine-readable test report (vitest/jest --json, playwright json, or JUnit XML)
// and prints ONE line: VERIFY stage=<name> tests=<total> passed=<n> failed=<n> skipped=<n>
// The line is also appended to $GITHUB_STEP_SUMMARY when set. Exits 1 if counts can't be parsed.
// When $VERIFY_STAGE_DIR is set, the counts and passed test IDs are also written to
// $VERIFY_STAGE_DIR/<stage>.json for the verify-report artifact.
import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { relative } from 'node:path'
import { pathToFileURL } from 'node:url'

const unxml = (v) =>
  v.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&')

// Counts plus the sorted, de-duplicated stable IDs of the tests that passed.
export function parseReport(text, cwd = process.cwd()) {
  const trimmed = text.trim()
  const ids = new Set()
  let counts
  if (trimmed.startsWith('<')) {
    // JUnit XML: sum every <testsuite> (pytest, vitest, jest-junit all emit these).
    let tests = 0, failed = 0, skipped = 0, seen = 0
    for (const m of trimmed.matchAll(/<testsuite\b([^>]*)>/g)) {
      const attr = (name) => Number((m[1].match(new RegExp(`\\b${name}="(\\d+)"`)) || [])[1] ?? 0)
      tests += attr('tests'); failed += attr('failures') + attr('errors'); skipped += attr('skipped'); seen++
    }
    if (!seen) throw new Error('no <testsuite> elements in JUnit XML')
    counts = { tests, passed: tests - failed - skipped, failed, skipped }
    // ID: <classname>::<name>
    for (const m of trimmed.matchAll(/<testcase\b([^>]*?)(?:\/>|>([\s\S]*?)<\/testcase>)/g)) {
      if (/<(failure|error|skipped)\b/.test(m[2] ?? '')) continue
      const attr = (name) => unxml((m[1].match(new RegExp(`\\b${name}="([^"]*)"`)) || [])[1] ?? '')
      ids.add(`${attr('classname')}::${attr('name')}`)
    }
    return { counts, passedIds: [...ids].sort() }
  }
  const j = JSON.parse(trimmed)
  if (j.stats && typeof j.stats.expected === 'number') {
    // Playwright JSON reporter. ID: <file>::<describe titles > test title>
    const { expected, unexpected, flaky, skipped } = j.stats
    counts = { tests: expected + unexpected + flaky + skipped, passed: expected + flaky, failed: unexpected, skipped }
    const walk = (suite, path) => {
      for (const spec of suite.specs ?? []) {
        if ((spec.tests ?? []).some((t) => t.status === 'expected' || t.status === 'flaky')) {
          ids.add(`${spec.file}::${[...path, spec.title].join(' > ')}`)
        }
      }
      for (const child of suite.suites ?? []) walk(child, [...path, child.title])
    }
    for (const fileSuite of j.suites ?? []) walk(fileSuite, []) // top-level suite title is the file itself
    return { counts, passedIds: [...ids].sort() }
  }
  if (typeof j.numTotalTests === 'number') {
    // Jest --json and vitest --reporter=json share this shape. ID: <file relative to cwd>::<fullName>
    const skipped = (j.numPendingTests ?? 0) + (j.numTodoTests ?? 0)
    counts = { tests: j.numTotalTests, passed: j.numPassedTests, failed: j.numFailedTests, skipped }
    for (const file of j.testResults ?? []) {
      const rel = relative(cwd, file.name ?? file.testFilePath ?? '')
      for (const a of file.assertionResults ?? []) {
        if (a.status === 'passed') ids.add(`${rel}::${a.fullName ?? [...(a.ancestorTitles ?? []), a.title].join(' ')}`)
      }
    }
    return { counts, passedIds: [...ids].sort() }
  }
  throw new Error('unrecognised report format')
}

export const parseCounts = (text) => parseReport(text).counts

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [stage, file] = process.argv.slice(2)
  if (!stage || !file) {
    console.error('usage: verify-summary.mjs <stage> <report-file>')
    process.exit(1)
  }
  let c, passedIds
  try {
    ;({ counts: c, passedIds } = parseReport(readFileSync(file, 'utf8')))
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
  const dir = process.env.VERIFY_STAGE_DIR
  if (dir) {
    mkdirSync(dir, { recursive: true })
    writeFileSync(`${dir}/${stage}.json`, `${JSON.stringify({ stage, ...c, passed_ids: passedIds })}\n`)
  }
}
