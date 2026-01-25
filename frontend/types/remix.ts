/**
 * Types for the Content Remix Engine
 */

// Content format identifiers
export type ContentFormatId =
  | 'blog'
  | 'article'
  | 'twitter_thread'
  | 'linkedin_post'
  | 'email_newsletter'
  | 'youtube_script'
  | 'instagram_carousel'
  | 'podcast_notes'
  | 'facebook_post'
  | 'tiktok_script'
  | 'medium_article'
  | 'press_release'
  | 'executive_summary'
  | 'slide_deck_outline'

// Format metadata
export interface ContentFormatInfo {
  format: ContentFormatId
  name: string
  icon: string
  description: string
  max_length: number
  platform: string
  supports_images: boolean
  slide_count?: { min: number; max: number }
}

// Quality scoring
export interface QualityScore {
  overall: number
  format_fit: number
  voice_match: number
  completeness: number
  engagement: number
  platform_optimization: number
}

// Content chunk for analysis
export interface ContentChunk {
  id: string
  type: 'heading' | 'paragraph' | 'list' | 'quote' | 'key_point' | 'section'
  content: string
  importance: number
  word_count: number
  source_section?: string
}

// Content analysis result
export interface ContentAnalysis {
  title: string
  summary: string
  key_points: string[]
  main_argument: string
  target_audience: string
  tone: string
  word_count: number
  chunks: ContentChunk[]
  keywords: string[]
  suggested_formats: ContentFormatId[]
}

// Twitter thread format
export interface TwitterThread {
  hook: string
  tweets: string[]
  cta: string
  hashtags: string[]
}

// LinkedIn post format
export interface LinkedInPost {
  hook: string
  body: string
  cta: string
  hashtags: string[]
}

// Email newsletter format
export interface EmailNewsletter {
  subject_line: string
  preview_text: string
  greeting: string
  intro: string
  sections: { title: string; content: string }[]
  cta: string
  signoff: string
}

// YouTube script format
export interface YouTubeScript {
  title: string
  hook: string
  intro: string
  sections: { title: string; content: string; duration: string }[]
  outro: string
  cta: string
  estimated_duration: string
}

// Instagram carousel format
export interface InstagramCarousel {
  caption: string
  slides: { title: string; content: string; image_prompt: string }[]
  hashtags: string[]
  cta: string
}

// Podcast notes format
export interface PodcastNotes {
  episode_title: string
  summary: string
  key_takeaways: string[]
  timestamps: { time: string; topic: string }[]
  resources: { title: string; url: string }[]
  transcript_excerpt: string
}

// Union of all format content types
export type FormatContent =
  | TwitterThread
  | LinkedInPost
  | EmailNewsletter
  | YouTubeScript
  | InstagramCarousel
  | PodcastNotes
  | Record<string, unknown>

// Remixed content item
export interface RemixedContent {
  format: ContentFormatId
  content: FormatContent
  quality_score: QualityScore
  word_count: number
  character_count: number
  generation_time_ms: number
  provider_used?: string
}

// Remix request
export interface RemixRequest {
  source_content: Record<string, unknown>
  target_formats: ContentFormatId[]
  preserve_voice?: boolean
  brand_profile_id?: string
  tone_override?: string
  conversation_id: string
  provider?: string
}

// Remix response
export interface RemixResponse {
  success: boolean
  source_analysis: ContentAnalysis
  remixed_content: RemixedContent[]
  total_generation_time_ms: number
  average_quality_score: number
  message?: string
}

// Preview request
export interface RemixPreviewRequest {
  source_content: Record<string, unknown>
  target_format: ContentFormatId
}

// Preview response
export interface RemixPreviewResponse {
  format: ContentFormatId
  estimated_length: number
  key_elements: string[]
  sample_hook: string
  confidence: number
}

// Analyze request
export interface AnalyzeRequest {
  source_content: Record<string, unknown>
  provider?: string
}

// Analyze response
export interface AnalyzeResponse {
  success: boolean
  analysis: ContentAnalysis
  suggested_formats: ContentFormatInfo[]
}

// Format selection state
export interface FormatSelectionState {
  selected: ContentFormatId[]
  previews: Map<ContentFormatId, RemixPreviewResponse>
}
