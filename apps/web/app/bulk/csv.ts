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

// Parse a single CSV line into its fields, honoring double-quoted cells so that
// commas inside quotes (e.g. a quoted keywords list) are not treated as field
// separators. Escaped quotes ("") inside a quoted field collapse to a single ".
export function parseCSVLine(line: string): string[] {
  const fields: string[] = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i++) {
    const char = line[i]

    if (inQuotes) {
      if (char === '"') {
        if (line[i + 1] === '"') {
          current += '"'
          i++ // skip the escaped quote
        } else {
          inQuotes = false
        }
      } else {
        current += char
      }
    } else if (char === '"') {
      inQuotes = true
    } else if (char === ',') {
      fields.push(current)
      current = ''
    } else {
      current += char
    }
  }

  fields.push(current)
  return fields.map((f) => f.trim())
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
  const headers = parseCSVLine(headerLine).map((h) => h.toLowerCase())

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

    // Quote-aware parsing so commas inside a quoted keywords cell survive.
    const values = parseCSVLine(line)

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
