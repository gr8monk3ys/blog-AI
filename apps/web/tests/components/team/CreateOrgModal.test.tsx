import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

// HeadlessUI Dialog uses ResizeObserver internally
globalThis.ResizeObserver = class {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

import CreateOrgModal from '../../../components/team/CreateOrgModal'

const mockApiFetch = vi.fn()

vi.mock('../../../lib/api', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  API_ENDPOINTS: {
    organizations: {
      create: '/api/v1/organizations',
    },
  },
}))

describe('CreateOrgModal', () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    onCreated: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockApiFetch.mockResolvedValue({ success: true, data: { id: 'org_new' } })
  })

  it('renders when open', () => {
    render(<CreateOrgModal {...defaultProps} />)
    expect(screen.getByText('Create Organization')).toBeDefined()
  })

  it('does not render content when closed', () => {
    render(<CreateOrgModal {...defaultProps} open={false} />)
    expect(screen.queryByText('Create Organization')).toBeNull()
  })

  it('shows organization name input', () => {
    render(<CreateOrgModal {...defaultProps} />)
    expect(screen.getByLabelText('Organization Name')).toBeDefined()
  })

  it('shows cancel and create buttons', () => {
    render(<CreateOrgModal {...defaultProps} />)
    expect(screen.getByText('Cancel')).toBeDefined()
    expect(screen.getByText('Create')).toBeDefined()
  })

  it('disables create button when name is empty', () => {
    render(<CreateOrgModal {...defaultProps} />)
    const createBtn = screen.getByText('Create')
    expect(createBtn).toHaveProperty('disabled', true)
  })

  it('enables create button when name is filled', () => {
    render(<CreateOrgModal {...defaultProps} />)
    const input = screen.getByLabelText('Organization Name')
    fireEvent.change(input, { target: { value: 'My Team' } })
    const createBtn = screen.getByText('Create')
    expect(createBtn).toHaveProperty('disabled', false)
  })

  it('calls onClose when cancel is clicked', () => {
    render(<CreateOrgModal {...defaultProps} />)
    fireEvent.click(screen.getByText('Cancel'))
    expect(defaultProps.onClose).toHaveBeenCalled()
  })

  it('submits form and calls callbacks on success', async () => {
    render(<CreateOrgModal {...defaultProps} />)
    const input = screen.getByLabelText('Organization Name')
    fireEvent.change(input, { target: { value: 'My Team' } })
    fireEvent.click(screen.getByText('Create'))

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        '/api/v1/organizations',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ name: 'My Team' }),
        })
      )
    })

    await waitFor(() => {
      expect(defaultProps.onCreated).toHaveBeenCalled()
      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  it('shows error message on API failure', async () => {
    mockApiFetch.mockRejectedValueOnce(new Error('Name already taken'))
    render(<CreateOrgModal {...defaultProps} />)
    const input = screen.getByLabelText('Organization Name')
    fireEvent.change(input, { target: { value: 'Duplicate' } })
    fireEvent.click(screen.getByText('Create'))

    await waitFor(() => {
      expect(screen.getByText('Name already taken')).toBeDefined()
    })
  })

  it('shows loading state during submission', async () => {
    let resolveApi: (value: unknown) => void
    mockApiFetch.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveApi = resolve
      })
    )
    render(<CreateOrgModal {...defaultProps} />)
    const input = screen.getByLabelText('Organization Name')
    fireEvent.change(input, { target: { value: 'My Team' } })
    fireEvent.click(screen.getByText('Create'))

    await waitFor(() => {
      expect(screen.getByText('Creating...')).toBeDefined()
    })

    resolveApi!({ success: true })
  })
})
