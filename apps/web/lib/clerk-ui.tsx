import type { ReactNode } from 'react'
import {
  ClerkProvider as ClerkProviderImpl,
  SignedIn as SignedInImpl,
  SignedOut as SignedOutImpl,
  UserButton as UserButtonImpl,
  SignIn as SignInImpl,
  SignUp as SignUpImpl,
  useAuth as useAuthImpl,
} from '@clerk/nextjs'

type UseAuthResult = {
  isLoaded: boolean
  isSignedIn: boolean
  userId: string | null
}

export function isClerkConfigured(): boolean {
  return !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
}

export function ClerkProvider({
  children,
  publishableKey,
}: {
  children: ReactNode
  publishableKey: string
}): ReactNode {
  if (!isClerkConfigured()) {
    return children
  }

  return <ClerkProviderImpl publishableKey={publishableKey}>{children}</ClerkProviderImpl>
}

export function SignedIn({ children }: { children: ReactNode }): ReactNode {
  if (!isClerkConfigured()) {
    return null
  }

  return <SignedInImpl>{children}</SignedInImpl>
}

export function SignedOut({ children }: { children: ReactNode }): ReactNode {
  if (!isClerkConfigured()) {
    return children
  }

  return <SignedOutImpl>{children}</SignedOutImpl>
}

export function UserButton(props: Record<string, unknown>): ReactNode {
  if (!isClerkConfigured()) {
    return null
  }

  return <UserButtonImpl {...props} />
}

export function SignIn(props: Record<string, unknown>): ReactNode {
  if (!isClerkConfigured()) {
    return null
  }

  return <SignInImpl {...props} />
}

export function SignUp(props: Record<string, unknown>): ReactNode {
  if (!isClerkConfigured()) {
    return null
  }

  return <SignUpImpl {...props} />
}

export function useAuth(): UseAuthResult {
  let auth: ReturnType<typeof useAuthImpl> | null = null

  try {
    // This wrapper intentionally tolerates missing Clerk config and provider state.
    // eslint-disable-next-line react-hooks/rules-of-hooks
    auth = useAuthImpl()
  } catch {
    auth = null
  }

  if (!isClerkConfigured() || !auth) {
    return {
      isLoaded: true,
      isSignedIn: false,
      userId: null,
    }
  }

  return {
    isLoaded: auth.isLoaded,
    isSignedIn: !!auth.isSignedIn,
    userId: auth.userId ?? null,
  }
}
