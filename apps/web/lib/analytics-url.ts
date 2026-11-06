/**
 * beforeSend for Vercel Web Analytics and Speed Insights. Query strings here can
 * hold OAuth codes (/social/callback), template presets (/tools/*) and topics a
 * user typed (/bulk), none of which belongs in analytics, so only the path is sent.
 */
export function withoutQueryString<T extends { url: string }>(event: T): T {
  const url = new URL(event.url)
  url.search = ''
  url.hash = ''
  return { ...event, url: url.toString() }
}
