import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import MembersList from '../../../components/team/MembersList'

vi.mock('../../../lib/api', () => ({
  apiFetch: vi.fn().mockResolvedValue({ success: true }),
  API_ENDPOINTS: {
    organizations: {
      updateMember: (orgId: string, userId: string) =>
        `/api/v1/organizations/${orgId}/members/${userId}`,
      removeMember: (orgId: string, userId: string) =>
        `/api/v1/organizations/${orgId}/members/${userId}`,
    },
  },
}))

const mockMembers = [
  {
    user_id: 'user_1',
    email: 'alice@example.com',
    role: 'owner' as const,
    joined_at: '2025-01-01T00:00:00Z',
  },
  {
    user_id: 'user_2',
    email: 'bob@example.com',
    role: 'admin' as const,
    joined_at: '2025-02-01T00:00:00Z',
  },
  {
    user_id: 'user_3',
    email: 'carol@example.com',
    role: 'member' as const,
    joined_at: '2025-03-01T00:00:00Z',
  },
]

describe('MembersList', () => {
  const defaultProps = {
    orgId: 'org_123',
    members: mockMembers,
    currentUserId: 'user_1',
    currentUserRole: 'owner' as const,
    onMemberUpdated: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all members', () => {
    render(<MembersList {...defaultProps} />)
    expect(screen.getByText('alice@example.com')).toBeDefined()
    expect(screen.getByText('bob@example.com')).toBeDefined()
    expect(screen.getByText('carol@example.com')).toBeDefined()
  })

  it('shows role badges for each member', () => {
    render(<MembersList {...defaultProps} />)
    // Use getAllByText since role names also appear in dropdown options
    expect(screen.getAllByText('owner').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('admin').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('member').length).toBeGreaterThanOrEqual(1)
  })

  it('marks current user with (you)', () => {
    render(<MembersList {...defaultProps} />)
    expect(screen.getByText('(you)')).toBeDefined()
  })

  it('shows actions column for owners/admins', () => {
    render(<MembersList {...defaultProps} />)
    expect(screen.getByText('Actions')).toBeDefined()
  })

  it('hides actions column for viewers', () => {
    render(<MembersList {...defaultProps} currentUserRole="viewer" />)
    expect(screen.queryByText('Actions')).toBeNull()
  })

  it('does not show remove for owner or self', () => {
    render(<MembersList {...defaultProps} />)
    // There should be Remove buttons only for non-owner, non-self members
    const removeButtons = screen.getAllByText('Remove')
    // bob (admin, not self) and carol (member, not self) can be removed
    expect(removeButtons).toHaveLength(2)
  })

  it('shows role dropdown for non-owner members when user can manage', () => {
    render(<MembersList {...defaultProps} />)
    // Role selects for bob and carol (not for alice who is owner)
    const selects = screen.getAllByRole('combobox')
    expect(selects.length).toBeGreaterThanOrEqual(2)
  })

  it('renders join dates', () => {
    render(<MembersList {...defaultProps} />)
    // Dates are rendered via toLocaleDateString — at least 2 should contain year
    const dateCells = screen.getAllByText(/202[0-9]/)
    expect(dateCells.length).toBeGreaterThanOrEqual(2)
  })

  it('shows avatar initials from email', () => {
    render(<MembersList {...defaultProps} />)
    expect(screen.getByText('A')).toBeDefined() // alice
    expect(screen.getByText('B')).toBeDefined() // bob
    expect(screen.getByText('C')).toBeDefined() // carol
  })
})
