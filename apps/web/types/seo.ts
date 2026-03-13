/**
 * Types for SEO scoring and optimization results
 */

export interface SEOScore {
  overall_score: number
  topic_coverage: number
  term_usage: number
  structure_score: number
  readability_score: number
  word_count_score: number
  passed: boolean
  passes_used: number
  suggestions_applied: number
}

export interface SEOThresholds {
  overall_minimum?: number
  topic_coverage_minimum?: number
  term_usage_minimum?: number
  structure_minimum?: number
  readability_minimum?: number
  word_count_minimum?: number
  max_optimization_passes?: number
}

export interface SEODimension {
  label: string
  score: number
  minimum: number
  key: keyof Pick<
    SEOScore,
    'topic_coverage' | 'term_usage' | 'structure_score' | 'readability_score' | 'word_count_score'
  >
}
