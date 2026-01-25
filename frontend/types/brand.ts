/**
 * Types for Brand Voice Profile feature
 */

/**
 * Writing style options
 */
export type WritingStyle =
  | 'formal'
  | 'professional'
  | 'conversational'
  | 'casual'
  | 'friendly'
  | 'technical'
  | 'academic'
  | 'creative'
  | 'balanced'

/**
 * Tone keyword presets
 */
export type ToneKeyword =
  | 'professional'
  | 'friendly'
  | 'casual'
  | 'authoritative'
  | 'empathetic'
  | 'enthusiastic'
  | 'confident'
  | 'approachable'
  | 'innovative'
  | 'trustworthy'
  | 'playful'
  | 'serious'
  | 'warm'
  | 'bold'
  | 'humble'

/**
 * Industry options for context
 */
export type Industry =
  | 'technology'
  | 'healthcare'
  | 'finance'
  | 'education'
  | 'ecommerce'
  | 'marketing'
  | 'real-estate'
  | 'hospitality'
  | 'manufacturing'
  | 'consulting'
  | 'legal'
  | 'nonprofit'
  | 'entertainment'
  | 'other'

/**
 * Brand profile data structure
 */
export interface BrandProfile {
  id: string
  name: string
  slug: string
  toneKeywords: ToneKeyword[]
  writingStyle: WritingStyle
  exampleContent: string | null
  industry: Industry | null
  targetAudience: string | null
  preferredWords: string[]
  avoidWords: string[]
  brandValues: string[]
  contentThemes: string[]
  isActive: boolean
  isDefault: boolean
  createdAt: string
  updatedAt: string
}

/**
 * Brand profile creation input
 */
export interface CreateBrandProfileInput {
  name: string
  toneKeywords: ToneKeyword[]
  writingStyle: WritingStyle
  exampleContent?: string
  industry?: Industry
  targetAudience?: string
  preferredWords?: string[]
  avoidWords?: string[]
  brandValues?: string[]
  contentThemes?: string[]
}

/**
 * Brand profile update input
 */
export interface UpdateBrandProfileInput {
  name?: string
  toneKeywords?: ToneKeyword[]
  writingStyle?: WritingStyle
  exampleContent?: string
  industry?: Industry
  targetAudience?: string
  preferredWords?: string[]
  avoidWords?: string[]
  brandValues?: string[]
  contentThemes?: string[]
  isActive?: boolean
  isDefault?: boolean
}

/**
 * Writing style options for UI
 */
export const WRITING_STYLES: { value: WritingStyle; label: string; description: string }[] = [
  { value: 'formal', label: 'Formal', description: 'Traditional, structured, and polished' },
  { value: 'professional', label: 'Professional', description: 'Business-appropriate and clear' },
  { value: 'conversational', label: 'Conversational', description: 'Natural, engaging dialogue style' },
  { value: 'casual', label: 'Casual', description: 'Relaxed and informal' },
  { value: 'friendly', label: 'Friendly', description: 'Warm and approachable' },
  { value: 'technical', label: 'Technical', description: 'Precise and detail-oriented' },
  { value: 'academic', label: 'Academic', description: 'Scholarly and research-focused' },
  { value: 'creative', label: 'Creative', description: 'Imaginative and expressive' },
  { value: 'balanced', label: 'Balanced', description: 'Mix of professional and friendly' },
]

/**
 * Tone keywords for selection UI
 */
export const TONE_KEYWORDS: { value: ToneKeyword; label: string }[] = [
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'casual', label: 'Casual' },
  { value: 'authoritative', label: 'Authoritative' },
  { value: 'empathetic', label: 'Empathetic' },
  { value: 'enthusiastic', label: 'Enthusiastic' },
  { value: 'confident', label: 'Confident' },
  { value: 'approachable', label: 'Approachable' },
  { value: 'innovative', label: 'Innovative' },
  { value: 'trustworthy', label: 'Trustworthy' },
  { value: 'playful', label: 'Playful' },
  { value: 'serious', label: 'Serious' },
  { value: 'warm', label: 'Warm' },
  { value: 'bold', label: 'Bold' },
  { value: 'humble', label: 'Humble' },
]

/**
 * Industry options for UI
 */
export const INDUSTRIES: { value: Industry; label: string }[] = [
  { value: 'technology', label: 'Technology' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'finance', label: 'Finance' },
  { value: 'education', label: 'Education' },
  { value: 'ecommerce', label: 'E-commerce' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'real-estate', label: 'Real Estate' },
  { value: 'hospitality', label: 'Hospitality' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'consulting', label: 'Consulting' },
  { value: 'legal', label: 'Legal' },
  { value: 'nonprofit', label: 'Non-profit' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'other', label: 'Other' },
]

/**
 * Sample brand profiles for demonstration
 */
export const SAMPLE_BRAND_PROFILES: BrandProfile[] = [
  {
    id: 'bp-1',
    name: 'Tech Startup Voice',
    slug: 'tech-startup-voice',
    toneKeywords: ['innovative', 'confident', 'approachable'],
    writingStyle: 'conversational',
    exampleContent: 'We are building the future of work. Our platform empowers teams to collaborate seamlessly, breaking down barriers and unlocking unprecedented productivity. Join thousands of forward-thinking companies already transforming how they work.',
    industry: 'technology',
    targetAudience: 'Tech-savvy professionals aged 25-45 at growing startups and mid-size companies',
    preferredWords: ['innovative', 'seamless', 'empower', 'transform', 'unlock'],
    avoidWords: ['old-fashioned', 'complicated', 'difficult', 'impossible'],
    brandValues: ['Innovation', 'Transparency', 'Customer Success'],
    contentThemes: ['Future of work', 'Team collaboration', 'Productivity'],
    isActive: true,
    isDefault: true,
    createdAt: '2024-01-10T08:00:00Z',
    updatedAt: '2024-01-10T08:00:00Z',
  },
  {
    id: 'bp-2',
    name: 'Professional Services',
    slug: 'professional-services',
    toneKeywords: ['professional', 'trustworthy', 'authoritative'],
    writingStyle: 'formal',
    exampleContent: 'Our team of experienced professionals is dedicated to delivering exceptional results. With over two decades of industry expertise, we provide strategic guidance and tailored solutions that address your unique business challenges.',
    industry: 'consulting',
    targetAudience: 'C-suite executives and senior decision-makers at enterprise organizations',
    preferredWords: ['strategic', 'expertise', 'tailored', 'comprehensive', 'proven'],
    avoidWords: ['cheap', 'basic', 'simple', 'quick fix'],
    brandValues: ['Excellence', 'Integrity', 'Partnership'],
    contentThemes: ['Business strategy', 'Industry insights', 'Best practices'],
    isActive: true,
    isDefault: false,
    createdAt: '2024-01-11T10:30:00Z',
    updatedAt: '2024-01-11T10:30:00Z',
  },
  {
    id: 'bp-3',
    name: 'Lifestyle Brand',
    slug: 'lifestyle-brand',
    toneKeywords: ['friendly', 'warm', 'enthusiastic'],
    writingStyle: 'casual',
    exampleContent: 'Hey there! Ready to add some joy to your everyday? We create products that make life a little brighter, a little easier, and a lot more fun. Because you deserve to love the little things.',
    industry: 'ecommerce',
    targetAudience: 'Young adults aged 20-35 who value quality and self-expression',
    preferredWords: ['love', 'joy', 'easy', 'fun', 'beautiful', 'everyday'],
    avoidWords: ['corporate', 'traditional', 'boring', 'standard'],
    brandValues: ['Joy', 'Authenticity', 'Quality'],
    contentThemes: ['Lifestyle inspiration', 'Self-care', 'Daily moments'],
    isActive: true,
    isDefault: false,
    createdAt: '2024-01-12T14:15:00Z',
    updatedAt: '2024-01-12T14:15:00Z',
  },
]

/**
 * Generate brand voice context for AI prompts
 */
export function generateBrandVoiceContext(profile: BrandProfile): string {
  const parts: string[] = []

  parts.push(`Brand Voice: ${profile.name}`)
  parts.push(`Writing Style: ${profile.writingStyle}`)
  parts.push(`Tone: ${profile.toneKeywords.join(', ')}`)

  if (profile.industry) {
    parts.push(`Industry: ${profile.industry}`)
  }

  if (profile.targetAudience) {
    parts.push(`Target Audience: ${profile.targetAudience}`)
  }

  if (profile.brandValues.length > 0) {
    parts.push(`Core Values: ${profile.brandValues.join(', ')}`)
  }

  if (profile.preferredWords.length > 0) {
    parts.push(`Preferred Words/Phrases: ${profile.preferredWords.join(', ')}`)
  }

  if (profile.avoidWords.length > 0) {
    parts.push(`Avoid: ${profile.avoidWords.join(', ')}`)
  }

  if (profile.exampleContent) {
    parts.push(`Example Content: "${profile.exampleContent}"`)
  }

  return parts.join('\n')
}

// ============================================================================
// Voice Training Types (Enhanced Tier 1)
// ============================================================================

export type ContentType = 'text' | 'blog' | 'email' | 'social' | 'website' | 'article'

export type TrainingStatus = 'untrained' | 'analyzing' | 'training' | 'trained' | 'failed'

export interface VocabularyProfile {
  common_words: string[]
  unique_phrases: string[]
  avg_word_length: number
  vocabulary_richness: number
  formality_indicators: string[]
  casual_indicators: string[]
}

export interface SentencePatterns {
  avg_sentence_length: number
  sentence_length_variance: number
  question_frequency: number
  exclamation_frequency: number
  complex_sentence_ratio: number
  opening_patterns: string[]
  transition_words: string[]
}

export interface ToneDistribution {
  professional: number
  friendly: number
  casual: number
  authoritative: number
  empathetic: number
  enthusiastic: number
  confident: number
  approachable: number
  innovative: number
  trustworthy: number
  playful: number
  serious: number
}

export interface StyleMetrics {
  formality_score: number
  complexity_score: number
  engagement_score: number
  personality_score: number
  consistency_score: number
}

export interface SampleAnalysis {
  vocabulary: VocabularyProfile
  sentences: SentencePatterns
  tone: ToneDistribution
  style: StyleMetrics
  key_characteristics: string[]
  quality_score: number
}

export interface VoiceSample {
  id: string
  profile_id: string
  title?: string
  content: string
  content_type: ContentType
  word_count: number
  source_url?: string
  source_platform?: string
  is_analyzed: boolean
  analysis_result?: SampleAnalysis
  quality_score: number
  is_primary_example: boolean
}

export interface VoiceFingerprint {
  id: string
  profile_id: string
  vocabulary_profile: VocabularyProfile
  sentence_patterns: SentencePatterns
  tone_distribution: ToneDistribution
  style_metrics: StyleMetrics
  voice_summary: string
  sample_count: number
  training_quality: number
  last_trained_at?: string
}

export interface VoiceScore {
  overall_score: number
  tone_match: number
  vocabulary_match: number
  style_match: number
  feedback: Record<string, unknown>
  deviations: string[]
  suggestions: string[]
}

export interface AnalyzeSampleRequest {
  content: string
  content_type: ContentType
  provider?: string
}

export interface AddSampleRequest {
  profile_id: string
  content: string
  content_type: ContentType
  title?: string
  source_url?: string
  source_platform?: string
  is_primary_example?: boolean
}

export interface TrainVoiceRequest {
  profile_id: string
  sample_ids?: string[]
  provider?: string
}

export interface ScoreContentRequest {
  profile_id: string
  content: string
  content_type: ContentType
  provider?: string
}

export interface TrainingStatusResponse {
  profile_id: string
  status: TrainingStatus
  sample_count: number
  training_quality: number
  has_fingerprint: boolean
  voice_summary?: string
}
