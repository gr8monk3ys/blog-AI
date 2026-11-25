import 'server-only'

import { betterAuth } from 'better-auth'
import { nextCookies } from 'better-auth/next-js'
import { jwt } from 'better-auth/plugins'
import { Pool } from 'pg'

import { sendAuthEmail } from './email'
import { getSignupMode } from './signup-mode'

/**
 * Better Auth server config. Tables come from db/migrations/011_better_auth.sql.
 *
 * Without DATABASE_URL (local dev only; next.config.mjs refuses a production
 * build without it) accounts live in memory and vanish on restart.
 */
const createAuth = () => {
  const databaseUrl = process.env.DATABASE_URL
  return betterAuth({
    secret: process.env.BETTER_AUTH_SECRET,
    baseURL: process.env.BETTER_AUTH_URL,
    database: databaseUrl ? new Pool({ connectionString: databaseUrl }) : undefined,
    emailAndPassword: {
      enabled: true,
      disableSignUp: getSignupMode() !== 'open',
      requireEmailVerification: true,
      revokeSessionsOnPasswordReset: true,
      sendResetPassword: async ({ user, url }) => {
        await sendAuthEmail({
          to: user.email,
          subject: 'Reset your Blog AI password',
          text: `Someone asked to reset the password for this account.\n\nSet a new password: ${url}\n\nThe link expires in one hour. If this was not you, ignore this email.`,
        })
      },
    },
    emailVerification: {
      sendOnSignUp: true,
      autoSignInAfterVerification: true,
      sendVerificationEmail: async ({ user, url }) => {
        await sendAuthEmail({
          to: user.email,
          subject: 'Confirm your Blog AI email',
          text: `Confirm your email address to finish creating your account: ${url}\n\nThe link expires in one hour.`,
        })
      },
    },
    plugins: [
      // Signs short-lived EdDSA JWTs for the FastAPI backend (GET /api/auth/token),
      // verified there against GET /api/auth/jwks. `sub` is the user id; iss and
      // aud default to BETTER_AUTH_URL. The payload carries nothing else.
      jwt({ jwt: { definePayload: () => ({}) } }),
      nextCookies(),
    ],
  })
}

let instance: ReturnType<typeof createAuth> | undefined

/** Created on first use, so importing this module (e.g. during `next build`) does no auth work. */
export function getAuth(): ReturnType<typeof createAuth> {
  instance ??= createAuth()
  return instance
}
