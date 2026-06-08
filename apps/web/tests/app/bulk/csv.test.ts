import { describe, it, expect } from 'vitest'
import { parseCSV, createDraftItem } from '@/app/bulk/csv'

describe('parseCSV', () => {
  it('parses a well-formed CSV with topic, keywords, and tone', () => {
    const result = parseCSV('topic,keywords,tone\nAI safety,llm;risk,professional')
    expect(result.errors).toEqual([])
    expect(result.headers).toEqual(['topic', 'keywords', 'tone'])
    expect(result.rows).toEqual([
      { topic: 'AI safety', keywords: 'llm;risk', tone: 'professional' },
    ])
  })

  it('requires a topic column', () => {
    const result = parseCSV('title,keywords\nfoo,bar')
    expect(result.rows).toEqual([])
    expect(result.errors).toContain('CSV must have a "topic" column')
  })

  it('treats an empty string as an empty file', () => {
    const result = parseCSV('')
    expect(result.rows).toEqual([])
    expect(result.errors).toContain('Empty CSV file')
  })

  it('skips blank lines and records missing-topic rows as errors', () => {
    const result = parseCSV('topic,tone\nGood topic,casual\n\n,casual')
    expect(result.rows).toEqual([{ topic: 'Good topic', keywords: undefined, tone: 'casual' }])
    expect(result.errors.some((e) => e.includes('Missing topic'))).toBe(true)
  })

  it('leaves optional columns undefined when absent', () => {
    const result = parseCSV('topic\nOnly a topic')
    expect(result.rows).toEqual([{ topic: 'Only a topic', keywords: undefined, tone: undefined }])
  })
})

describe('createDraftItem', () => {
  it('produces a unique localId and applies defaults', () => {
    const a = createDraftItem()
    const b = createDraftItem()
    expect(a.localId).not.toEqual(b.localId)
    expect(a.tone).toBe('informative')
    expect(a.keywords).toEqual([])
  })

  it('carries through provided values', () => {
    const item = createDraftItem('Topic X', ['k1', 'k2'], 'technical')
    expect(item.topic).toBe('Topic X')
    expect(item.keywords).toEqual(['k1', 'k2'])
    expect(item.tone).toBe('technical')
  })
})
