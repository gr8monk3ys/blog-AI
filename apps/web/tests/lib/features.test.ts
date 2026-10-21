import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { FEATURE_FLAG_ENV, features, parseFlag, type FeatureName } from '../../lib/features'
import { DEFAULT_SIGNUP_MODE, getSignupMode, parseSignupMode } from '../../lib/signup-mode'

const ALL_FLAG_VARS = [...Object.values(FEATURE_FLAG_ENV), 'NEXT_PUBLIC_SIGNUP_MODE']

beforeEach(() => {
  for (const key of ALL_FLAG_VARS) vi.stubEnv(key, '')
})

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('parseFlag', () => {
  it.each(['1', 'true', 'TRUE', ' on ', 'yes'])('treats %j as on', (value) => {
    expect(parseFlag(value)).toBe(true)
  })

  it.each(['0', 'false', 'off', 'no'])('treats %j as off even with an on default', (value) => {
    expect(parseFlag(value, true)).toBe(false)
  })

  it('returns the fallback for unset or empty values', () => {
    expect(parseFlag(undefined)).toBe(false)
    expect(parseFlag('', true)).toBe(true)
  })

  it('treats a typo as off so a misspelling never turns a promise on', () => {
    expect(parseFlag('ture', true)).toBe(false)
  })
})

describe('features defaults (mirror the live deployment)', () => {
  const offByDefault: FeatureName[] = [
    'knowledgeBase',
    'gemini',
    'webResearch',
    'imageGeneration',
    'plagiarismCheck',
    'socialPosting',
    'teams',
  ]

  it.each(offByDefault)('%s is off until its flag is set', (name) => {
    expect(features[name]).toBe(false)
  })

  it('billing is on by default because Stripe is live', () => {
    expect(features.billing).toBe(true)
  })

  it('billing can be switched off explicitly', () => {
    vi.stubEnv('NEXT_PUBLIC_FEATURE_BILLING', 'false')
    expect(features.billing).toBe(false)
  })

  it.each(Object.entries(FEATURE_FLAG_ENV) as [FeatureName, string][])(
    '%s re-reads %s on every access',
    (name, envVar) => {
      vi.stubEnv(envVar, 'true')
      expect(features[name]).toBe(true)
      vi.stubEnv(envVar, 'false')
      expect(features[name]).toBe(false)
    }
  )

  it('exposes the sign-up mode alongside the booleans', () => {
    vi.stubEnv('NEXT_PUBLIC_SIGNUP_MODE', 'waitlist')
    expect(features.signupMode).toBe('waitlist')
  })
})

describe('signup mode', () => {
  it('defaults to open', () => {
    expect(DEFAULT_SIGNUP_MODE).toBe('open')
    expect(getSignupMode()).toBe('open')
  })

  it.each(['open', 'waitlist', 'invite'])('accepts %s', (mode) => {
    vi.stubEnv('NEXT_PUBLIC_SIGNUP_MODE', mode)
    expect(getSignupMode()).toBe(mode)
  })

  it('normalises case and whitespace', () => {
    expect(parseSignupMode('  Invite ')).toBe('invite')
  })

  it('falls back to open for unknown values', () => {
    expect(parseSignupMode('closed')).toBe('open')
    expect(parseSignupMode(null)).toBe('open')
  })
})
