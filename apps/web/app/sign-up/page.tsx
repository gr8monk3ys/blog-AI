import type { Metadata } from 'next'
import AuthShell from '../../components/auth/AuthShell'
import { SignUpForm } from '../../components/auth/AuthForms'

export const metadata: Metadata = {
  title: 'Sign Up',
  description: 'Create your Blog AI account and start generating content with AI-powered workflows.',
}

export default function SignUpPage() {
  return (
    <AuthShell label="Sign up" title="Start your first draft." lead="Free to start. No credit card required.">
      <SignUpForm />
    </AuthShell>
  )
}
