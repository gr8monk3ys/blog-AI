/**
 * Types for fact-checking results
 */

export type VerificationStatus = 'verified' | 'unverified' | 'contradicted'

export interface ClaimVerification {
  text: string
  status: VerificationStatus
  confidence: number
  explanation: string
  supporting_sources: string[]
}

export interface FactCheckResult {
  overall_confidence: number
  verified_count: number
  unverified_count: number
  contradicted_count: number
  summary: string
  claims: ClaimVerification[]
}
