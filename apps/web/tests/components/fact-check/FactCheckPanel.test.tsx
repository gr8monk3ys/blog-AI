import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FactCheckPanel from '../../../components/fact-check/FactCheckPanel'
import type { FactCheckResult } from '../../../types/factCheck'

const mockResult: FactCheckResult = {
  overall_confidence: 0.75,
  verified_count: 2,
  unverified_count: 1,
  contradicted_count: 0,
  summary: 'Checked 3 claims: 2 verified, 1 unverified, 0 contradicted.',
  claims: [
    {
      text: 'The Earth is approximately 4.5 billion years old',
      status: 'verified',
      confidence: 0.95,
      explanation: 'Confirmed by scientific literature',
      supporting_sources: ['Nature.com'],
    },
    {
      text: 'Water covers 71% of Earth surface',
      status: 'verified',
      confidence: 0.9,
      explanation: 'Well-established fact',
      supporting_sources: [],
    },
    {
      text: 'Mars has three moons',
      status: 'unverified',
      confidence: 0.4,
      explanation: 'Mars actually has two moons',
      supporting_sources: ['NASA.gov'],
    },
  ],
}

describe('FactCheckPanel', () => {
  it('renders overall confidence', () => {
    render(<FactCheckPanel result={mockResult} />)
    expect(screen.getByText('75% confident')).toBeInTheDocument()
  })

  it('renders heading', () => {
    render(<FactCheckPanel result={mockResult} />)
    expect(screen.getByText('Fact Check')).toBeInTheDocument()
  })

  it('shows verification counts', () => {
    render(<FactCheckPanel result={mockResult} />)
    expect(screen.getByText('2 verified')).toBeInTheDocument()
    expect(screen.getByText('1 unverified')).toBeInTheDocument()
    expect(screen.getByText('0 contradicted')).toBeInTheDocument()
  })

  it('renders claim text', () => {
    render(<FactCheckPanel result={mockResult} />)
    expect(screen.getByText(/4\.5 billion years/)).toBeInTheDocument()
    expect(screen.getByText(/71% of Earth/)).toBeInTheDocument()
  })

  it('shows status badges', () => {
    render(<FactCheckPanel result={mockResult} />)
    const badges = screen.getAllByText('Verified')
    expect(badges).toHaveLength(2)
    expect(screen.getByText('Unverified')).toBeInTheDocument()
  })

  it('expands claim details on click', async () => {
    const user = userEvent.setup()
    render(<FactCheckPanel result={mockResult} />)

    // The explanation shouldn't be visible initially
    expect(screen.queryByText('Confirmed by scientific literature')).not.toBeInTheDocument()

    // Click the first claim
    const firstClaim = screen.getByText(/4\.5 billion years/)
    await user.click(firstClaim)

    expect(screen.getByText('Confirmed by scientific literature')).toBeInTheDocument()
  })

  it('renders summary', () => {
    render(<FactCheckPanel result={mockResult} />)
    expect(screen.getByText(/Checked 3 claims/)).toBeInTheDocument()
  })
})
