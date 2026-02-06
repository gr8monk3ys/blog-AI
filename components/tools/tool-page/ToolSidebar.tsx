'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import type { Tool } from '../../../types/tools'

interface ToolSidebarProps {
  relatedTools: Tool[]
}

/**
 * Tips section with best practices for content generation
 */
function TipsCard() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">
        Tips for best results
      </h3>
      <ul className="space-y-2 text-sm text-gray-600">
        <li className="flex items-start gap-2">
          <span className="text-indigo-600 mt-0.5">*</span>
          Be specific about your topic or goal
        </li>
        <li className="flex items-start gap-2">
          <span className="text-indigo-600 mt-0.5">*</span>
          Include relevant keywords for SEO
        </li>
        <li className="flex items-start gap-2">
          <span className="text-indigo-600 mt-0.5">*</span>
          Choose a tone that matches your brand
        </li>
        <li className="flex items-start gap-2">
          <span className="text-indigo-600 mt-0.5">*</span>
          Enable research for factual content
        </li>
      </ul>
    </div>
  )
}

/**
 * Related tools section with links to similar tools
 */
function RelatedToolsCard({ tools }: { tools: Tool[] }) {
  if (tools.length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">
        Related Tools
      </h3>
      <ul className="space-y-3">
        {tools.map((relatedTool) => (
          <li key={relatedTool.id}>
            <Link href={`/tools/${relatedTool.slug}`} className="block group">
              <div className="text-sm font-medium text-gray-900 group-hover:text-indigo-600 transition-colors">
                {relatedTool.name}
              </div>
              <div className="text-xs text-gray-500 line-clamp-1">
                {relatedTool.description}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

/**
 * Sidebar component with tips and related tools
 */
export default function ToolSidebar({ relatedTools }: ToolSidebarProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className="space-y-6"
    >
      <TipsCard />
      <RelatedToolsCard tools={relatedTools} />
    </motion.div>
  )
}
