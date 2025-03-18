import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import SEOScorePanel from '../../../components/seo/SEOScorePanel'
import type { SEOScore } from '../../../types/seo'

const mockScore: SEOScore = {
  overall_score: 82.5,
  topic_coverage: 78,
  term_usage: 65,
  structure_score: 70,
  readability_score: 90,
  word_count_score: 85,
  passed: true,
  passes_used: 2,
  suggestions_applied: 3,
}

describe('SEOScorePanel', () => {
  it('renders overall score', () => {
    render(<SEOScorePanel score={mockScore} />)
    expect(screen.getByText('83')).toBeInTheDocument()
  })

  it('shows passed badge when score passes', () => {
    render(<SEOScorePanel score={mockScore} />)
    expect(screen.getByText('Passed')).toBeInTheDocument()
  })

  it('shows needs improvement when score fails', () => {
    const failing: SEOScore = { ...mockScore, passed: false, overall_score: 45 }
    render(<SEOScorePanel score={failing} />)
    expect(screen.getByText('Needs Improvement')).toBeInTheDocument()
  })

  it('renders all dimension labels', () => {
    render(<SEOScorePanel score={mockScore} />)
    expect(screen.getByText('Topic Coverage')).toBeInTheDocument()
    expect(screen.getByText('Term Usage')).toBeInTheDocument()
    expect(screen.getByText('Structure')).toBeInTheDocument()
    expect(screen.getByText('Readability')).toBeInTheDocument()
    expect(screen.getByText('Word Count')).toBeInTheDocument()
  })

  it('displays passes and fixes count', () => {
    render(<SEOScorePanel score={mockScore} />)
    expect(screen.getByText(/2 passes/)).toBeInTheDocument()
    expect(screen.getByText(/3 fixes/)).toBeInTheDocument()
  })

  it('renders heading', () => {
    render(<SEOScorePanel score={mockScore} />)
    expect(screen.getByText('SEO Analysis')).toBeInTheDocument()
  })
})
