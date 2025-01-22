/**
 * Types for AI image generation.
 *
 * Mirrors backend responses from:
 * - POST /api/v1/images/generate
 * - POST /api/v1/images/generate-for-blog
 * - GET  /api/v1/images/styles
 */

export type ImageProvider = 'openai' | 'stability'

export type ImageSize =
  | '1024x1024'
  | '1792x1024'
  | '1024x1792'
  | '512x512'
  | '256x256'

export type ImageStyle = 'natural' | 'vivid'

export type ImageQuality = 'standard' | 'hd'

export type ImageType = 'featured' | 'social' | 'inline' | 'thumbnail' | 'hero'

export interface ImageResult {
  url: string
  prompt_used: string
  provider: ImageProvider
  size: ImageSize
  style: ImageStyle
  quality: ImageQuality
  created_at: string
  revised_prompt?: string | null
  metadata?: Record<string, unknown>
}

export interface BlogImagesResult {
  featured_image?: ImageResult | null
  social_image?: ImageResult | null
  inline_images: ImageResult[]
  total_generated: number
  provider_used: ImageProvider
}

export interface ImageStyleOption {
  name: string
  value: string
  description?: string
}

export interface ImageStylesResponse {
  styles: ImageStyleOption[]
  sizes: Record<string, ImageSize[]>
  providers: ImageProvider[]
  qualities: ImageQuality[]
}
