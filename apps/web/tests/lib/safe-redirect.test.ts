import { describe, expect, it } from 'vitest'
import { safeRedirectPath } from '../../lib/safe-redirect'

describe('safeRedirectPath', () => {
  it.each(['/history', '/tools/x?y=1', '/'])('keeps the same-origin path %s', (path) => {
    expect(safeRedirectPath(path)).toBe(path)
  })

  it.each(['//evil.test', '/\\evil.test', 'https://evil.test', 'javascript:alert(1)', '', undefined, ['/a']])(
    'falls back for %j',
    (value) => {
      expect(safeRedirectPath(value)).toBe('/generate')
    }
  )
})
