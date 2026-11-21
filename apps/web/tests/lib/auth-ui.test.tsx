import { describe, it, expect } from 'vitest'
import { render, screen, renderHook } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { AccountMenu, SignedIn, SignedOut, useAuth } from '../../lib/auth-ui'
import { authClientMock, sessionState } from '../auth-mock'

function renderGates() {
  return render(
    <>
      <SignedIn>
        <div data-testid="signed-in" />
      </SignedIn>
      <SignedOut>
        <div data-testid="signed-out" />
      </SignedOut>
    </>
  )
}

describe('auth-ui', () => {
  it('maps a loaded session to signed in', () => {
    const { result } = renderHook(() => useAuth())
    expect(result.current).toEqual({ isLoaded: true, isSignedIn: true, userId: 'test-user' })

    renderGates()
    expect(screen.getByTestId('signed-in')).toBeInTheDocument()
    expect(screen.queryByTestId('signed-out')).not.toBeInTheDocument()
  })

  it('shows the signed-out view, never the signed-in one, while the session loads', () => {
    Object.assign(sessionState, { data: null, isPending: true })

    const { result } = renderHook(() => useAuth())
    expect(result.current).toEqual({ isLoaded: false, isSignedIn: false, userId: null })

    renderGates()
    expect(screen.queryByTestId('signed-in')).not.toBeInTheDocument()
    expect(screen.getByTestId('signed-out')).toBeInTheDocument()
  })

  it('shows the signed-out view when there is no session', () => {
    sessionState.data = null

    renderGates()
    expect(screen.queryByTestId('signed-in')).not.toBeInTheDocument()
    expect(screen.getByTestId('signed-out')).toBeInTheDocument()
  })

  it('account menu shows the email, links to settings and signs out', async () => {
    const user = userEvent.setup()
    render(<AccountMenu />)

    await user.click(screen.getByRole('button', { name: /account menu/i }))
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Settings' })).toHaveAttribute('href', '/settings/webhooks')

    await user.click(screen.getByRole('menuitem', { name: 'Sign out' }))
    expect(authClientMock.signOut).toHaveBeenCalledOnce()
  })

  it('account menu renders nothing without a session', () => {
    sessionState.data = null
    const { container } = render(<AccountMenu />)
    expect(container).toBeEmptyDOMElement()
  })
})
