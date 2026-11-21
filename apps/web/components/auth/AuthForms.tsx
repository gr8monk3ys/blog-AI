'use client'

import { useState, type FormEvent, type ReactNode } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { authClient } from '../../lib/auth-client'

const VERIFIED_CALLBACK = '/verify-email?verified=1'

type Status = { kind: 'idle' } | { kind: 'busy' } | { kind: 'error'; message: string }

function Field({
  id,
  label,
  ...props
}: { id: string; label: string } & React.InputHTMLAttributes<HTMLInputElement>): ReactNode {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-foreground">
        {label}
      </label>
      <Input id={id} name={id} required {...props} />
    </div>
  )
}

function FormError({ status }: { status: Status }): ReactNode {
  return status.kind === 'error' ? (
    <p role="alert" className="text-sm text-destructive">
      {status.message}
    </p>
  ) : null
}

function field(form: FormData, name: string): string {
  return String(form.get(name) ?? '')
}

const errorMessage = (error: { message?: string; statusText?: string }): string =>
  error.message || error.statusText || 'Something went wrong. Try again.'

export function SignInForm({ redirectTo, notice }: { redirectTo: string; notice?: string }): ReactNode {
  const router = useRouter()
  const [status, setStatus] = useState<Status>({ kind: 'idle' })

  const onSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const email = field(form, 'email')
    setStatus({ kind: 'busy' })
    // On success the client follows callbackURL with a full navigation.
    const { error } = await authClient.signIn.email({
      email,
      password: field(form, 'password'),
      callbackURL: redirectTo,
    })
    if (!error) return
    if (error.code === 'EMAIL_NOT_VERIFIED') {
      await authClient.sendVerificationEmail({ email, callbackURL: VERIFIED_CALLBACK })
      router.push(`/verify-email?email=${encodeURIComponent(email)}`)
      return
    }
    setStatus({ kind: 'error', message: errorMessage(error) })
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      {notice ? <p className="text-sm text-success">{notice}</p> : null}
      <Field id="email" label="Email" type="email" autoComplete="email" />
      <Field id="password" label="Password" type="password" autoComplete="current-password" />
      <FormError status={status} />
      <Button type="submit" className="w-full" disabled={status.kind === 'busy'}>
        Sign In
      </Button>
      <div className="flex justify-between text-sm text-muted-foreground">
        <Link href="/forgot-password" className="ink-underline hover:text-primary">
          Forgot password?
        </Link>
        <Link href="/sign-up" className="ink-underline hover:text-primary">
          Create an account
        </Link>
      </div>
    </form>
  )
}

export function SignUpForm(): ReactNode {
  const router = useRouter()
  const [status, setStatus] = useState<Status>({ kind: 'idle' })

  const onSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const email = field(form, 'email')
    setStatus({ kind: 'busy' })
    const { error } = await authClient.signUp.email({
      name: field(form, 'name'),
      email,
      password: field(form, 'password'),
      callbackURL: VERIFIED_CALLBACK,
    })
    if (error) {
      setStatus({ kind: 'error', message: errorMessage(error) })
      return
    }
    router.push(`/verify-email?email=${encodeURIComponent(email)}`)
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <Field id="name" label="Name" autoComplete="name" />
      <Field id="email" label="Email" type="email" autoComplete="email" />
      <Field id="password" label="Password" type="password" autoComplete="new-password" minLength={8} />
      <FormError status={status} />
      <Button type="submit" className="w-full" disabled={status.kind === 'busy'}>
        Create Account
      </Button>
      <p className="text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link href="/sign-in" className="ink-underline hover:text-primary">
          Sign in
        </Link>
      </p>
    </form>
  )
}

export function ForgotPasswordForm(): ReactNode {
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const [sent, setSent] = useState(false)

  const onSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault()
    setStatus({ kind: 'busy' })
    const { error } = await authClient.requestPasswordReset({
      email: field(new FormData(event.currentTarget), 'email'),
      redirectTo: '/reset-password',
    })
    if (error) {
      setStatus({ kind: 'error', message: errorMessage(error) })
      return
    }
    setSent(true)
  }

  if (sent) {
    return (
      <p role="status" className="border-y border-border py-6 text-sm text-muted-foreground">
        If an account uses that address, a reset link is on its way. It expires in one hour.
      </p>
    )
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <Field id="email" label="Email" type="email" autoComplete="email" />
      <FormError status={status} />
      <Button type="submit" className="w-full" disabled={status.kind === 'busy'}>
        Send Reset Link
      </Button>
    </form>
  )
}

export function ResetPasswordForm({ token }: { token: string }): ReactNode {
  const router = useRouter()
  const [status, setStatus] = useState<Status>({ kind: 'idle' })

  const onSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault()
    setStatus({ kind: 'busy' })
    const { error } = await authClient.resetPassword({
      newPassword: field(new FormData(event.currentTarget), 'password'),
      token,
    })
    if (error) {
      setStatus({ kind: 'error', message: errorMessage(error) })
      return
    }
    router.push('/sign-in?reset=1')
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <Field id="password" label="New password" type="password" autoComplete="new-password" minLength={8} />
      <FormError status={status} />
      <Button type="submit" className="w-full" disabled={status.kind === 'busy'}>
        Set Password
      </Button>
    </form>
  )
}

export function ResendVerificationForm({ email }: { email: string }): ReactNode {
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const [sent, setSent] = useState(false)

  const onSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault()
    setStatus({ kind: 'busy' })
    const { error } = await authClient.sendVerificationEmail({
      email: field(new FormData(event.currentTarget), 'email'),
      callbackURL: VERIFIED_CALLBACK,
    })
    if (error) {
      setStatus({ kind: 'error', message: errorMessage(error) })
      return
    }
    setSent(true)
    setStatus({ kind: 'idle' })
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <Field id="email" label="Email" type="email" autoComplete="email" defaultValue={email} />
      <FormError status={status} />
      {sent ? (
        <p role="status" className="text-sm text-success">
          Sent. Check your inbox.
        </p>
      ) : null}
      <Button type="submit" variant="secondary" className="w-full" disabled={status.kind === 'busy'}>
        Resend Confirmation Email
      </Button>
    </form>
  )
}
