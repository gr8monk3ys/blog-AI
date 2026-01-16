/**
 * Types for content generation responses
 */

export interface SubTopic {
  title: string
  content: string
}

export interface BlogSection {
  title: string
  subtopics: SubTopic[]
}

export interface BlogContent {
  title: string
  description: string
  date: string
  image: string
  tags: string[]
  sections: BlogSection[]
}

export interface Topic {
  title: string
  content: string
}

export interface BookChapter {
  number: number
  title: string
  topics: Topic[]
}

export interface BookContent {
  title: string
  description: string
  date: string
  image: string
  tags: string[]
  chapters: BookChapter[]
}

export interface BlogGenerationResponse {
  success: boolean
  type: 'blog'
  content: BlogContent
  file_path?: string
  title?: string
  message?: string
  detail?: string
}

export interface BookGenerationResponse {
  success: boolean
  type: 'book'
  content: BookContent
  file_path?: string
  title?: string
  message?: string
  detail?: string
}

export type ContentGenerationResponse = BlogGenerationResponse | BookGenerationResponse
