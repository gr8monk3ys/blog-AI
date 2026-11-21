import type { Metadata } from 'next'
import Link from 'next/link'
import AuthShell from '../../components/auth/AuthShell'
import { ResetPasswordForm } from '../../components/auth/AuthForms'

export const metadata: Metadata = {
  title: 'Reset Password',
  description: 'Set a new password for your Blog AI account.',
}

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>
}) {
  const { token } = await searchParams
  return (
    <AuthShell label="Password reset" title="Set a new password." lead="Choose at least eight characters.">
      {typeof token === 'string' && token ? (
        <ResetPasswordForm token={token} />
      ) : (
        <p role="alert" className="border-y border-border py-6 text-sm text-muted-foreground">
          This reset link is invalid or has expired.{' '}
          <Link href="/forgot-password" className="ink-underline text-foreground hover:text-primary">
            Request a new one
          </Link>
          .
        </p>
      )}
    </AuthShell>
  )
}
