import { describe, expect, it } from 'vitest'
import { withoutQueryString } from '../../lib/analytics-url'

describe('withoutQueryString', () => {
  it('removes OAuth values from the callback URL', () => {
    const event = withoutQueryString({
      type: 'pageview',
      url: 'https://blog-ai.vivancedata.com/social/callback?code=secret&state=twitter:abc',
    })

    expect(event.url).toBe('https://blog-ai.vivancedata.com/social/callback')
    expect(event.type).toBe('pageview')
  })

  it('removes the fragment and leaves a plain path alone', () => {
    expect(withoutQueryString({ url: 'https://example.com/a?b=c#d' }).url).toBe('https://example.com/a')
    expect(withoutQueryString({ url: 'https://example.com/a' }).url).toBe('https://example.com/a')
  })
})
