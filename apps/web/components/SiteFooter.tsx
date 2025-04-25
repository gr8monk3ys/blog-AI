import Link from 'next/link'

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

export default function SiteFooter(): React.ReactElement {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 dark:bg-gray-900 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-2 sm:col-span-1">
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Blog AI</p>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              AI-powered content generation for blogs, marketing, and more.
            </p>
          </div>

          {/* Link columns */}
          {Object.entries(FOOTER_LINKS).map(([heading, links]) => (
            <div key={heading}>
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{heading}</p>
              <ul className="mt-3 space-y-2">
                {links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-gray-500 dark:text-gray-400 hover:text-amber-600 transition-colors"
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
        <div className="mt-10 pt-6 border-t border-gray-200 dark:border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-400 dark:text-gray-500">
            &copy; {new Date().getFullYear()} Blog AI. All rights reserved.
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500">
            Powered by GPT-4, Claude &amp; Gemini
          </p>
        </div>
      </div>
    </footer>
  )
}
