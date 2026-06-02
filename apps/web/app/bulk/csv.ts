// CSV parsing and draft-item helpers for the bulk generation page.
// Pure functions extracted from BulkGenerationPageClient.tsx so they can be
// unit-tested in isolation.

import { v4 as uuidv4 } from 'uuid'
import type {
  BulkGenerationItem,
  CSVRow,
  ParsedCSVData,
} from '../../types/bulk'

export interface BulkDraftItem extends BulkGenerationItem {
  localId: string
}

export function createDraftItem(
  topic = '',
  keywords: string[] = [],
  tone = 'informative'
): BulkDraftItem {
  return {
    localId: uuidv4(),
    topic,
    keywords,
    tone,
  }
}

export function parseCSV(csvText: string): ParsedCSVData {
  const lines = csvText.trim().split('\n')
  const errors: string[] = []
  const rows: CSVRow[] = []

  if (lines.length === 0) {
    return { rows: [], errors: ['Empty CSV file'], headers: [] }
  }

  // Parse header
  const headerLine = lines[0]
  if (!headerLine) {
    return { rows: [], errors: ['Empty CSV file'], headers: [] }
  }
  const headers = headerLine.split(',').map((h) => h.trim().toLowerCase())

  const topicIndex = headers.indexOf('topic')
  const keywordsIndex = headers.indexOf('keywords')
  const toneIndex = headers.indexOf('tone')

  if (topicIndex === -1) {
    errors.push('CSV must have a "topic" column')
    return { rows: [], errors, headers }
  }

  // Parse data rows
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i]
    if (!line || !line.trim()) continue

    // Simple CSV parsing (doesn't handle quoted commas)
    const values = line.split(',').map((v) => v.trim())

    const topic = values[topicIndex]
    if (!topic) {
      errors.push(`Row ${i + 1}: Missing topic`)
      continue
    }

    rows.push({
      topic,
      keywords: keywordsIndex !== -1 ? values[keywordsIndex] : undefined,
      tone: toneIndex !== -1 ? values[toneIndex] : undefined,
    })
  }

  return { rows, errors, headers }
}
