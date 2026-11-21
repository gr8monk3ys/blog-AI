import 'server-only'

import { Resend } from 'resend'

type AuthEmail = { to: string; subject: string; text: string }

/**
 * Sends the transactional auth emails (verification, password reset).
 *
 * Without RESEND_API_KEY outside production the message is printed to the
 * server console instead, so local sign-up works without a mail account.
 */
export async function sendAuthEmail({ to, subject, text }: AuthEmail): Promise<void> {
  const apiKey = process.env.RESEND_API_KEY
  if (!apiKey) {
    if (process.env.NODE_ENV === 'production') {
      throw new Error('RESEND_API_KEY is not configured; cannot send auth email')
    }
    console.info(`[email] to=${to} subject="${subject}"\n${text}`)
    return
  }

  const from = process.env.EMAIL_FROM
  if (!from) {
    throw new Error('EMAIL_FROM is not configured; cannot send auth email')
  }

  const { error } = await new Resend(apiKey).emails.send({ from, to, subject, text })
  if (error) {
    throw new Error(`Resend rejected the auth email: ${error.message}`)
  }
}
