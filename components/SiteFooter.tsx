import Link from 'next/link'

export default function SiteFooter() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-500">Powered by AI · Blog AI Content Generator</p>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <Link href="/pricing" className="hover:text-amber-600 transition-colors">Pricing</Link>
            <Link href="/blog" className="hover:text-amber-600 transition-colors">Blog</Link>
            <Link href="/tools" className="hover:text-amber-600 transition-colors">Tools</Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
