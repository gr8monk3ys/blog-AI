import Link from 'next/link'
import { Logo } from './brand/Logo'

const FOOTER_LINKS = {
  Product: [
    { label: 'AI Tools', href: '/tools' },
    { label: 'Templates', href: '/templates' },
    { label: 'Pricing', href: '/pricing' },
    { label: 'Blog', href: '/blog' },
  ],
  Resources: [
    { label: 'Tool Directory', href: '/tool-directory' },
    { label: 'Brand Voice', href: '/brand' },
    { label: 'Content History', href: '/history' },
    { label: 'Analytics', href: '/analytics' },
  ],
  Legal: [
    { label: 'Privacy Policy', href: '/privacy' },
    { label: 'Terms of Service', href: '/terms' },
  ],
}

const footerLink =
  'ink-underline text-sm text-foreground/80 transition-colors hover:text-primary'

/**
 * The colophon (DESIGN.md → Components → Navigation → Footer): a 60% hairline
 * above, a `1.1fr / 2fr` editorial split, column heads as wall labels, links
 * in the body sans that take the ink underline, and a hairline before the
 * legal line. Flat paper; no fill change.
 */
export default function SiteFooter(): React.ReactElement {
  return (
    <footer className="border-t border-border/60">
      <div className="mx-auto grid max-w-7xl gap-12 px-4 py-12 sm:px-6 md:grid-cols-[1.1fr_2fr] md:gap-16 md:py-16 lg:px-8">
        <div className="max-w-sm">
          <Link href="/" className="inline-flex items-center">
            <Logo size={16} />
          </Link>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            AI-powered content generation for blogs, marketing, and more.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-10 sm:grid-cols-3">
          {Object.entries(FOOTER_LINKS).map(([heading, links]) => {
            const id = `footer-${heading.toLowerCase()}-heading`
            return (
              <nav key={heading} aria-labelledby={id}>
                <p id={id} className="label-mono">
                  {heading}
                </p>
                <ul className="mt-4 flex flex-col items-start gap-3">
                  {links.map((link) => (
                    <li key={link.href}>
                      <Link href={link.href} className={footerLink}>
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            )
          })}
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <hr className="gallery-rule" />
        <div className="flex flex-col gap-2 py-6 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
          <p>&copy; {new Date().getFullYear()} Blog AI. All rights reserved.</p>
          <p>Powered by GPT-4, Claude &amp; Gemini</p>
        </div>
      </div>
    </footer>
  )
}
