import type { Metadata } from 'next'
import Link from 'next/link'
import AuthShell from '../../components/auth/AuthShell'
import { ResendVerificationForm } from '../../components/auth/AuthForms'
import { buttonVariants } from '../../components/ui/Button'

export const metadata: Metadata = {
  title: 'Confirm Your Email',
  description: 'Confirm the email address for your Blog AI account.',
}

export default async function VerifyEmailPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>
}) {
  const { verified, error, email } = await searchParams

  if (verified && !error) {
    return (
      <AuthShell label="Email confirmed" title="You are in." lead="Your email is confirmed and you are signed in.">
        <Link href="/generate" className={buttonVariants({ size: 'lg' })}>
          Open the Workspace
        </Link>
      </AuthShell>
    )
  }

  return (
    <AuthShell
      label="Confirm your email"
      title={error ? 'That link did not work.' : 'Check your inbox.'}
      lead={
        error
          ? 'The confirmation link is invalid or has expired. Send yourself a new one.'
          : 'We sent a confirmation link. Open it to finish creating your account.'
      }
    >
      <ResendVerificationForm email={typeof email === 'string' ? email : ''} />
    </AuthShell>
  )
}
