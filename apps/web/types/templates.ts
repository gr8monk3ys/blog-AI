/**
 * Types for Templates Library feature
 */

/**
 * Template category for filtering
 */
export type TemplateCategory =
  | 'marketing'
  | 'saas'
  | 'ecommerce'
  | 'content'
  | 'social'
  | 'email'
  | 'video'
  | 'business'
  | 'other'

/**
 * Template category information for display
 */
export interface TemplateCategoryInfo {
  id: TemplateCategory
  name: string
  description: string
  color: string
  bgColor: string
  borderColor: string
}

/**
 * Template data structure
 */
export interface Template {
  id: string
  name: string
  description: string | null
  slug: string
  toolId: string
  presetInputs: Record<string, unknown>
  category: TemplateCategory
  tags: string[]
  isPublic: boolean
  useCount: number
  createdAt: string
  updatedAt: string
}

/**
 * Template creation input
 */
export interface CreateTemplateInput {
  name: string
  description?: string
  toolId: string
  presetInputs: Record<string, unknown>
  category: TemplateCategory
  tags?: string[]
  isPublic?: boolean
}

/**
 * Template update input
 */
export interface UpdateTemplateInput {
  name?: string
  description?: string
  presetInputs?: Record<string, unknown>
  category?: TemplateCategory
  tags?: string[]
  isPublic?: boolean
}

/**
 * Category information mapping
 */
export const TEMPLATE_CATEGORIES: Record<TemplateCategory, TemplateCategoryInfo> = {
  marketing: {
    id: 'marketing',
    name: 'Marketing',
    description: 'Marketing campaigns and promotional content',
    color: 'text-foreground',
    bgColor: 'bg-card',
    borderColor: 'border-border',
  },
  saas: {
    id: 'saas',
    name: 'SaaS',
    description: 'Software as a Service content',
    color: 'text-foreground',
    bgColor: 'bg-card',
    borderColor: 'border-border',
  },
  ecommerce: {
    id: 'ecommerce',
    name: 'E-commerce',
    description: 'Online store and product content',
    color: 'text-foreground',
    bgColor: 'bg-card',
    borderColor: 'border-border',
  },
  content: {
    id: 'content',
    name: 'Content',
    description: 'General content creation',
    color: 'text-foreground',
    bgColor: 'bg-card',
    borderColor: 'border-border',
  },
  social: {
    id: 'social',
    name: 'Social Media',
    description: 'Social media posts and engagement',
    color: 'text-foreground',
    bgColor: 'bg-card',
    borderColor: 'border-border',
  },
  email: {
    id: 'email',
    name: 'Email',
    description: 'Email marketing and newsletters',
    color: 'text-foreground',
    bgColor: 'bg-card',
    borderColor: 'border-border',
  },
  video: {
    id: 'video',
    name: 'Video',
    description: 'Video scripts and content',
    color: 'text-foreground',
    bgColor: 'bg-card',
    borderColor: 'border-border',
  },
  business: {
    id: 'business',
    name: 'Business',
    description: 'Professional business content',
    color: 'text-foreground',
    bgColor: 'bg-card',
    borderColor: 'border-border',
  },
  other: {
    id: 'other',
    name: 'Other',
    description: 'Miscellaneous templates',
    color: 'text-foreground',
    bgColor: 'bg-card',
    borderColor: 'border-border',
  },
}

/**
 * Sample templates for initial data
 */
export const SAMPLE_TEMPLATES: Template[] = [
  {
    id: 'tpl-1',
    name: 'SaaS Landing Page Copy',
    description: 'Create compelling copy for SaaS product landing pages with clear value propositions and CTAs.',
    slug: 'saas-landing-page-copy',
    toolId: 'blog-post-generator',
    presetInputs: {
      topic: 'SaaS product landing page',
      tone: 'professional',
      keywords: ['features', 'benefits', 'pricing', 'testimonials'],
      sections: ['hero', 'features', 'social-proof', 'pricing', 'cta'],
    },
    category: 'saas',
    tags: ['landing-page', 'conversion', 'copy'],
    isPublic: true,
    useCount: 245,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
  },
  {
    id: 'tpl-2',
    name: 'Product Launch Email',
    description: 'Announce new products with engaging email copy that drives excitement and conversions.',
    slug: 'product-launch-email',
    toolId: 'newsletter-writer',
    presetInputs: {
      topic: 'New product announcement',
      tone: 'excited',
      structure: ['teaser', 'reveal', 'features', 'early-bird-offer', 'cta'],
    },
    category: 'email',
    tags: ['product-launch', 'announcement', 'email-marketing'],
    isPublic: true,
    useCount: 189,
    createdAt: '2024-01-16T14:30:00Z',
    updatedAt: '2024-01-16T14:30:00Z',
  },
  {
    id: 'tpl-3',
    name: 'LinkedIn Thought Leadership',
    description: 'Share industry insights and establish expertise with professional LinkedIn posts.',
    slug: 'linkedin-thought-leadership',
    toolId: 'linkedin-post',
    presetInputs: {
      tone: 'professional',
      format: 'story-driven',
      includeHashtags: true,
      callToAction: 'engage',
    },
    category: 'social',
    tags: ['linkedin', 'thought-leadership', 'professional'],
    isPublic: true,
    useCount: 312,
    createdAt: '2024-01-17T09:15:00Z',
    updatedAt: '2024-01-17T09:15:00Z',
  },
  {
    id: 'tpl-4',
    name: 'YouTube Tutorial Script',
    description: 'Create structured tutorial scripts with clear instructions and engaging delivery.',
    slug: 'youtube-tutorial-script',
    toolId: 'video-script',
    presetInputs: {
      format: 'tutorial',
      structure: ['hook', 'intro', 'prerequisites', 'steps', 'recap', 'cta'],
      tone: 'friendly',
      includTimestamps: true,
    },
    category: 'video',
    tags: ['youtube', 'tutorial', 'educational'],
    isPublic: true,
    useCount: 156,
    createdAt: '2024-01-18T11:45:00Z',
    updatedAt: '2024-01-18T11:45:00Z',
  },
  {
    id: 'tpl-5',
    name: 'E-commerce Product Description',
    description: 'Write compelling product descriptions that highlight benefits and drive purchases.',
    slug: 'ecommerce-product-description',
    toolId: 'product-description',
    presetInputs: {
      format: 'benefit-focused',
      includeSEO: true,
      tone: 'persuasive',
      sections: ['headline', 'key-benefits', 'features', 'specifications'],
    },
    category: 'ecommerce',
    tags: ['product', 'ecommerce', 'sales'],
    isPublic: true,
    useCount: 278,
    createdAt: '2024-01-19T08:20:00Z',
    updatedAt: '2024-01-19T08:20:00Z',
  },
  {
    id: 'tpl-6',
    name: 'Weekly Newsletter',
    description: 'Engage subscribers with curated content, updates, and valuable insights.',
    slug: 'weekly-newsletter',
    toolId: 'newsletter-writer',
    presetInputs: {
      format: 'digest',
      sections: ['intro', 'featured', 'news', 'tips', 'community', 'cta'],
      tone: 'friendly',
    },
    category: 'email',
    tags: ['newsletter', 'weekly', 'engagement'],
    isPublic: true,
    useCount: 134,
    createdAt: '2024-01-20T16:00:00Z',
    updatedAt: '2024-01-20T16:00:00Z',
  },
]
