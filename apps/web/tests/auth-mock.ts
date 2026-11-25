import { vi } from 'vitest'

type Session = { user: { id: string; email: string; name: string } }

/**
 * Stand-in for lib/auth-client's `authClient`, installed for every test by
 * tests/setup.tsx. Tests set `sessionState` to drive useSession().
 */
export const sessionState: { data: Session | null; isPending: boolean } = {
  data: null,
  isPending: false,
}

export const signedInSession: Session = {
  user: { id: 'test-user', email: 'test@example.com', name: 'Test User' },
}

/** Mirrors the JWT plugin: a session answer carries the token in `set-auth-jwt`. */
export const jwtState: { header: string | null } = { header: 'mock-token' }

export function resetSessionState(): void {
  jwtState.header = 'mock-token'
  sessionState.data = signedInSession
  sessionState.isPending = false
}

export const authClientMock = {
  useSession: () => sessionState,
  getSession: vi.fn(
    async (options: {
      fetchOptions: { onSuccess: (context: { response: Response }) => void }
    }) => {
      const headers = new Headers()
      if (jwtState.header) headers.set('set-auth-jwt', jwtState.header)
      options.fetchOptions.onSuccess({ response: new Response(null, { headers }) })
      return { data: sessionState.data, error: null }
    }
  ),
  signOut: vi.fn(async () => ({ data: { success: true }, error: null })),
  signIn: {
    email: vi.fn(
      async (_body: {
        email: string
        password: string
        callbackURL: string
      }): Promise<{ error: { code?: string; message?: string } | null }> => ({ error: null })
    ),
  },
  sendVerificationEmail: vi.fn(async (_body: { email: string; callbackURL: string }) => ({
    error: null,
  })),
}
