/**
 * Types for book-related components
 */

export interface Topic {
  title: string;
  content: string;
}

export interface Chapter {
  number: number;
  title: string;
  topics: Topic[];
}

export interface Book {
  title: string;
  chapters: Chapter[];
  tags?: string[];
  date?: string;
}

export interface BookGenerationOptions {
  title: string;
  num_chapters: number;
  sections_per_chapter: number;
  keywords: string[];
  tone: 'informative' | 'conversational' | 'professional' | 'friendly' | 'authoritative' | 'technical';
  research: boolean;
  proofread: boolean;
  humanize: boolean;
}

export interface BookGenerationResponse {
  success: boolean;
  book: Book;
  file_path: string;
  message?: string;
  detail?: string;
}

export interface BookEditResponse {
  success: boolean;
  message: string;
  book?: Book;
}

export interface BookDownloadOptions {
  file_path: string;
  format: 'markdown' | 'json';
}
