import type { Metadata } from 'next'
import AuthShell from '../../components/auth/AuthShell'
import { ForgotPasswordForm } from '../../components/auth/AuthForms'

export const metadata: Metadata = {
  title: 'Forgot Password',
  description: 'Request a link to reset your Blog AI password.',
}

export default function ForgotPasswordPage() {
  return (
    <AuthShell
      label="Password reset"
      title="Forgot your password?"
      lead="Enter your email and we will send you a link to set a new one."
    >
      <ForgotPasswordForm />
    </AuthShell>
  )
}
