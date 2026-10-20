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

// The colophon: a hairline above, column heads as wall labels, links in the
// body sans that take the ink on hover. Flat paper, no fill change.
export default function SiteFooter(): React.ReactElement {
  return (
    <footer className="border-t border-border bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-2 sm:col-span-1">
            <Logo size={16} />
            <p className="mt-3 text-sm text-muted-foreground">
              AI-powered content generation for blogs, marketing, and more.
            </p>
          </div>

          {/* Link columns */}
          {Object.entries(FOOTER_LINKS).map(([heading, links]) => (
            <div key={heading}>
              <p className="label-mono">{heading}</p>
              <ul className="mt-3 space-y-2">
                {links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted-foreground hover:text-primary transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-10 pt-6 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} Blog AI. All rights reserved.
          </p>
          <p className="text-xs text-muted-foreground">
            Powered by GPT-4, Claude &amp; Gemini
          </p>
        </div>
      </div>
    </footer>
  )
}
