/**
 * Types for tool discovery UI
 */

export type ToolCategory =
  | 'blog'
  | 'email'
  | 'social-media'
  | 'business'
  | 'naming'
  | 'video'
  | 'seo'
  | 'rewriting'

export interface Tool {
  id: string
  slug: string
  name: string
  description: string
  category: ToolCategory
  isFree: boolean
  icon?: string
  isNew?: boolean
  isPopular?: boolean
}

export interface ToolCategoryInfo {
  id: ToolCategory
  name: string
  description: string
  color: string
  bgColor: string
  borderColor: string
}

export const TOOL_CATEGORIES: Record<ToolCategory, ToolCategoryInfo> = {
  blog: {
    id: 'blog',
    name: 'Blog',
    description: 'Create engaging blog content',
    color: 'text-indigo-700',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200',
  },
  email: {
    id: 'email',
    name: 'Email',
    description: 'Write compelling emails',
    color: 'text-emerald-700',
    bgColor: 'bg-emerald-100',
    borderColor: 'border-emerald-200',
  },
  'social-media': {
    id: 'social-media',
    name: 'Social Media',
    description: 'Create social media content',
    color: 'text-pink-700',
    bgColor: 'bg-pink-100',
    borderColor: 'border-pink-200',
  },
  business: {
    id: 'business',
    name: 'Business',
    description: 'Professional business content',
    color: 'text-slate-700',
    bgColor: 'bg-slate-100',
    borderColor: 'border-slate-200',
  },
  naming: {
    id: 'naming',
    name: 'Naming',
    description: 'Generate creative names',
    color: 'text-amber-700',
    bgColor: 'bg-amber-100',
    borderColor: 'border-amber-200',
  },
  video: {
    id: 'video',
    name: 'Video',
    description: 'Video scripts and content',
    color: 'text-red-700',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-200',
  },
  seo: {
    id: 'seo',
    name: 'SEO',
    description: 'Search engine optimization',
    color: 'text-cyan-700',
    bgColor: 'bg-cyan-100',
    borderColor: 'border-cyan-200',
  },
  rewriting: {
    id: 'rewriting',
    name: 'Rewriting',
    description: 'Improve existing content',
    color: 'text-violet-700',
    bgColor: 'bg-violet-100',
    borderColor: 'border-violet-200',
  },
}

// Sample tools data - in production this would come from an API
export const SAMPLE_TOOLS: Tool[] = [
  // Blog Tools
  {
    id: '1',
    slug: 'blog-post-generator',
    name: 'Blog Post Generator',
    description: 'Generate complete, SEO-optimized blog posts on any topic with customizable tone and structure.',
    category: 'blog',
    isFree: true,
    isPopular: true,
  },
  {
    id: '2',
    slug: 'blog-outline',
    name: 'Blog Outline Creator',
    description: 'Create structured outlines for your blog posts with main points and subheadings.',
    category: 'blog',
    isFree: true,
  },
  {
    id: '3',
    slug: 'blog-intro-generator',
    name: 'Blog Intro Generator',
    description: 'Write captivating introductions that hook readers from the first sentence.',
    category: 'blog',
    isFree: true,
  },
  {
    id: '4',
    slug: 'blog-conclusion',
    name: 'Blog Conclusion Writer',
    description: 'Create compelling conclusions that summarize key points and include calls to action.',
    category: 'blog',
    isFree: false,
  },

  // Email Tools
  {
    id: '5',
    slug: 'email-subject-lines',
    name: 'Email Subject Lines',
    description: 'Generate attention-grabbing email subject lines that increase open rates.',
    category: 'email',
    isFree: true,
    isPopular: true,
  },
  {
    id: '6',
    slug: 'cold-email-generator',
    name: 'Cold Email Generator',
    description: 'Create personalized cold emails that get responses and drive conversions.',
    category: 'email',
    isFree: false,
  },
  {
    id: '7',
    slug: 'newsletter-writer',
    name: 'Newsletter Writer',
    description: 'Write engaging newsletter content that keeps subscribers coming back.',
    category: 'email',
    isFree: true,
  },
  {
    id: '8',
    slug: 'follow-up-email',
    name: 'Follow-up Email',
    description: 'Craft effective follow-up emails for sales, networking, and customer service.',
    category: 'email',
    isFree: true,
  },

  // Social Media Tools
  {
    id: '9',
    slug: 'instagram-caption',
    name: 'Instagram Caption Generator',
    description: 'Create engaging Instagram captions with relevant hashtags and emojis.',
    category: 'social-media',
    isFree: true,
    isPopular: true,
  },
  {
    id: '10',
    slug: 'twitter-thread',
    name: 'Twitter Thread Generator',
    description: 'Transform ideas into viral Twitter threads that drive engagement.',
    category: 'social-media',
    isFree: true,
  },
  {
    id: '11',
    slug: 'linkedin-post',
    name: 'LinkedIn Post Creator',
    description: 'Write professional LinkedIn posts that establish thought leadership.',
    category: 'social-media',
    isFree: true,
  },
  {
    id: '12',
    slug: 'facebook-ad-copy',
    name: 'Facebook Ad Copy',
    description: 'Generate high-converting Facebook ad copy for your campaigns.',
    category: 'social-media',
    isFree: false,
    isNew: true,
  },

  // Business Tools
  {
    id: '13',
    slug: 'business-plan',
    name: 'Business Plan Generator',
    description: 'Create comprehensive business plans with executive summaries and financial projections.',
    category: 'business',
    isFree: false,
  },
  {
    id: '14',
    slug: 'product-description',
    name: 'Product Description Writer',
    description: 'Write compelling product descriptions that highlight benefits and drive sales.',
    category: 'business',
    isFree: true,
    isPopular: true,
  },
  {
    id: '15',
    slug: 'press-release',
    name: 'Press Release Generator',
    description: 'Create professional press releases for announcements and news.',
    category: 'business',
    isFree: false,
  },
  {
    id: '16',
    slug: 'proposal-writer',
    name: 'Business Proposal Writer',
    description: 'Generate persuasive business proposals that win clients.',
    category: 'business',
    isFree: false,
  },

  // Naming Tools
  {
    id: '17',
    slug: 'brand-name-generator',
    name: 'Brand Name Generator',
    description: 'Generate unique and memorable brand names for your business or product.',
    category: 'naming',
    isFree: true,
    isPopular: true,
  },
  {
    id: '18',
    slug: 'tagline-generator',
    name: 'Tagline Generator',
    description: 'Create catchy taglines and slogans that capture your brand essence.',
    category: 'naming',
    isFree: true,
  },
  {
    id: '19',
    slug: 'domain-name-ideas',
    name: 'Domain Name Ideas',
    description: 'Find available and creative domain names for your website.',
    category: 'naming',
    isFree: true,
    isNew: true,
  },

  // Video Tools
  {
    id: '20',
    slug: 'youtube-title',
    name: 'YouTube Title Generator',
    description: 'Create click-worthy YouTube titles that boost views and engagement.',
    category: 'video',
    isFree: true,
    isPopular: true,
  },
  {
    id: '21',
    slug: 'video-script',
    name: 'Video Script Writer',
    description: 'Write engaging video scripts for YouTube, TikTok, and other platforms.',
    category: 'video',
    isFree: false,
  },
  {
    id: '22',
    slug: 'youtube-description',
    name: 'YouTube Description',
    description: 'Generate optimized YouTube descriptions with timestamps and links.',
    category: 'video',
    isFree: true,
  },

  // SEO Tools
  {
    id: '23',
    slug: 'meta-description',
    name: 'Meta Description Generator',
    description: 'Write SEO-optimized meta descriptions that improve click-through rates.',
    category: 'seo',
    isFree: true,
    isPopular: true,
  },
  {
    id: '24',
    slug: 'keyword-research',
    name: 'Keyword Research Assistant',
    description: 'Discover high-value keywords and content opportunities for your niche.',
    category: 'seo',
    isFree: false,
  },
  {
    id: '25',
    slug: 'seo-title',
    name: 'SEO Title Generator',
    description: 'Create compelling page titles optimized for search engines.',
    category: 'seo',
    isFree: true,
  },

  // Rewriting Tools
  {
    id: '26',
    slug: 'content-rewriter',
    name: 'Content Rewriter',
    description: 'Rewrite and improve existing content while maintaining the original meaning.',
    category: 'rewriting',
    isFree: true,
    isPopular: true,
  },
  {
    id: '27',
    slug: 'sentence-rewriter',
    name: 'Sentence Rewriter',
    description: 'Rewrite individual sentences for clarity, engagement, or different tones.',
    category: 'rewriting',
    isFree: true,
  },
  {
    id: '28',
    slug: 'tone-changer',
    name: 'Tone Changer',
    description: 'Convert content between different tones like formal, casual, or persuasive.',
    category: 'rewriting',
    isFree: true,
    isNew: true,
  },
  {
    id: '29',
    slug: 'grammar-improver',
    name: 'Grammar Improver',
    description: 'Fix grammar, spelling, and punctuation errors in your content.',
    category: 'rewriting',
    isFree: true,
  },
]
