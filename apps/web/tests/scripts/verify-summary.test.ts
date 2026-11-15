/**
 * scripts/verify-summary.mjs turns runner reports into the VERIFY lines CI
 * publishes. If it misreads a format, the evidence lies, so pin each shape.
 */
import { describe, expect, it } from 'vitest'

// @ts-expect-error -- plain .mjs script outside the app, no type declarations
import { parseCounts } from '../../../../scripts/verify-summary.mjs'

describe('verify-summary parseCounts', () => {
  it('reads vitest/jest JSON', () => {
    expect(
      parseCounts(
        '{"numTotalTests":5,"numPassedTests":3,"numFailedTests":1,"numPendingTests":1,"numTodoTests":0}'
      )
    ).toEqual({ tests: 5, passed: 3, failed: 1, skipped: 1 })
  })

  it('reads Playwright JSON', () => {
    expect(
      parseCounts('{"stats":{"expected":4,"unexpected":1,"flaky":1,"skipped":2}}')
    ).toEqual({ tests: 8, passed: 5, failed: 1, skipped: 2 })
  })

  it('sums every <testsuite> in JUnit XML', () => {
    expect(
      parseCounts(
        '<?xml version="1.0"?><testsuites><testsuite tests="3" failures="1" errors="0" skipped="1"></testsuite><testsuite tests="2" errors="1"/></testsuites>'
      )
    ).toEqual({ tests: 5, passed: 2, failed: 2, skipped: 1 })
  })

  it('rejects anything else', () => {
    expect(() => parseCounts('5 passed')).toThrow()
    expect(() => parseCounts('{}')).toThrow()
  })
})
