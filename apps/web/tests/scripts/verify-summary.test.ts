/**
 * scripts/verify-summary.mjs turns runner reports into the VERIFY lines CI
 * publishes. If it misreads a format, the evidence lies, so pin each shape.
 */
import { describe, expect, it } from 'vitest'

// @ts-expect-error -- plain .mjs script outside the app, no type declarations
import { parseCounts, parseReport } from '../../../../scripts/verify-summary.mjs'

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

  it('lists sorted IDs of passing tests for each format', () => {
    expect(
      parseReport(
        '{"numTotalTests":2,"numPassedTests":1,"numFailedTests":1,"testResults":[{"name":"/w/a.test.ts","assertionResults":[{"status":"passed","fullName":"A b"},{"status":"failed","fullName":"A c"}]}]}',
        '/w'
      ).passedIds
    ).toEqual(['a.test.ts::A b'])
    expect(
      parseReport(
        '{"stats":{"expected":1,"unexpected":1,"flaky":0,"skipped":0},"suites":[{"title":"e.spec.ts","file":"e.spec.ts","suites":[{"title":"D","specs":[{"title":"x","file":"e.spec.ts","tests":[{"status":"expected"}]},{"title":"y","file":"e.spec.ts","tests":[{"status":"unexpected"}]}]}]}]}'
      ).passedIds
    ).toEqual(['e.spec.ts::D > x'])
    expect(
      parseReport(
        '<testsuite tests="3" failures="1" skipped="1"><testcase classname="t.m" name="ok[a&amp;b]"/><testcase classname="t.m" name="bad"><failure/></testcase><testcase classname="t.m" name="sk"><skipped/></testcase></testsuite>'
      ).passedIds
    ).toEqual(['t.m::ok[a&b]'])
  })

  it('rejects anything else', () => {
    expect(() => parseCounts('5 passed')).toThrow()
    expect(() => parseCounts('{}')).toThrow()
  })
})
