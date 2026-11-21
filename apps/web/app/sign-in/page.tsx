import type { Metadata } from 'next'
import AuthShell from '../../components/auth/AuthShell'
import { SignInForm } from '../../components/auth/AuthForms'
import { safeRedirectPath } from '../../lib/safe-redirect'

export const metadata: Metadata = {
  title: 'Sign In',
  description: 'Sign in to your Blog AI account to access content generation tools and workspace data.',
}

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>
}) {
  const params = await searchParams
  return (
    <AuthShell label="Sign in" title="Welcome back." lead="Pick up where your last draft left off.">
      <SignInForm
        redirectTo={safeRedirectPath(params.redirect)}
        notice={params.reset ? 'Password updated. Sign in with the new one.' : undefined}
      />
    </AuthShell>
  )
}
