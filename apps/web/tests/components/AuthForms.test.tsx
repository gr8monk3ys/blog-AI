import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRouter } from 'next/navigation'
import { SignInForm } from '../../components/auth/AuthForms'
import { authClientMock } from '../auth-mock'

async function submitSignIn(): Promise<void> {
  const user = userEvent.setup()
  render(<SignInForm redirectTo="/history" />)
  await user.type(screen.getByLabelText('Email'), 'a@example.com')
  await user.type(screen.getByLabelText('Password'), 'correct horse')
  await user.click(screen.getByRole('button', { name: 'Sign In' }))
}

describe('SignInForm', () => {
  it('signs in with the redirect target as callback', async () => {
    await submitSignIn()
    expect(authClientMock.signIn.email).toHaveBeenLastCalledWith({
      email: 'a@example.com',
      password: 'correct horse',
      callbackURL: '/history',
    })
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('resends the confirmation and moves to /verify-email for an unverified account', async () => {
    authClientMock.signIn.email.mockResolvedValueOnce({ error: { code: 'EMAIL_NOT_VERIFIED' } })
    await submitSignIn()
    expect(authClientMock.sendVerificationEmail).toHaveBeenLastCalledWith({
      email: 'a@example.com',
      callbackURL: '/verify-email?verified=1',
    })
    expect(useRouter().push).toHaveBeenLastCalledWith('/verify-email?email=a%40example.com')
  })

  it('shows the server message for other failures', async () => {
    authClientMock.signIn.email.mockResolvedValueOnce({
      error: { code: 'INVALID_EMAIL_OR_PASSWORD', message: 'Invalid email or password' },
    })
    await submitSignIn()
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password')
  })
})
