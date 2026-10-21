/**
 * The support address, in one place.
 *
 * The repo used to name `support@blogai.com`, `support@blog-ai.com`,
 * `legal@blogai.com` and `privacy@blogai.com` -- all on domains this project
 * does not own, so mail to them went nowhere. The only inbox on a domain the
 * owner controls and reads is on `lscaturchio.xyz` (SECURITY.md already uses
 * `security@lscaturchio.xyz`), so that is the default here.
 *
 * Server- and client-safe: `NEXT_PUBLIC_*` is inlined at build time, so the
 * value must be set for the build, not only for `start`.
 */

export const DEFAULT_SUPPORT_EMAIL = 'support@lscaturchio.xyz'

const configured = process.env.NEXT_PUBLIC_SUPPORT_EMAIL?.trim()

export const SUPPORT_EMAIL: string = configured || DEFAULT_SUPPORT_EMAIL

/** `mailto:` link for the support address, with an optional subject. */
export function supportMailto(subject?: string): string {
  const base = `mailto:${SUPPORT_EMAIL}`
  return subject ? `${base}?subject=${encodeURIComponent(subject)}` : base
}
