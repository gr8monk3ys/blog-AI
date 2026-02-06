'use client'

import { motion } from 'framer-motion'
import { TemplateCategory, TEMPLATE_CATEGORIES } from '../../types/templates'

interface TemplateCategoryFilterProps {
  selectedCategory: TemplateCategory | 'all'
  onCategoryChange: (category: TemplateCategory | 'all') => void
  templateCounts: Record<TemplateCategory | 'all', number>
}

export default function TemplateCategoryFilter({
  selectedCategory,
  onCategoryChange,
  templateCounts,
}: TemplateCategoryFilterProps) {
  const categories: (TemplateCategory | 'all')[] = [
    'all',
    ...Object.keys(TEMPLATE_CATEGORIES) as TemplateCategory[],
  ]

  return (
    <div className="flex flex-wrap gap-2">
      {categories.map((category) => {
        const isSelected = selectedCategory === category
        const count = templateCounts[category] || 0
        const categoryInfo = category === 'all' ? null : TEMPLATE_CATEGORIES[category]

        return (
          <motion.button
            key={category}
            type="button"
            onClick={() => onCategoryChange(category)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className={`
              inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium
              transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
              ${
                isSelected
                  ? category === 'all'
                    ? 'bg-indigo-600 text-white'
                    : `${categoryInfo?.bgColor} ${categoryInfo?.color} border ${categoryInfo?.borderColor}`
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }
            `}
            aria-pressed={isSelected}
          >
            <span>{category === 'all' ? 'All' : categoryInfo?.name}</span>
            <span
              className={`
                inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-xs
                ${
                  isSelected
                    ? category === 'all'
                      ? 'bg-indigo-500 text-white'
                      : 'bg-white/50 text-current'
                    : 'bg-gray-100 text-gray-500'
                }
              `}
            >
              {count}
            </span>
          </motion.button>
        )
      })}
    </div>
  )
}
