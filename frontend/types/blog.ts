/**
 * Types for blog-related components
 */

export interface Section {
  id: string;
  content: string;
}

export interface BlogPost {
  title: string;
  sections: Section[];
  tags?: string[];
  date?: string;
}

export interface BlogGenerationOptions {
  topic: string;
  keywords?: string[];
  tone?: 'informative' | 'conversational' | 'professional' | 'friendly' | 'authoritative' | 'technical';
  research?: boolean;
  proofread?: boolean;
  humanize?: boolean;
}

export interface BlogGenerationResponse {
  success: boolean;
  content: BlogPost;
  file_path: string;
  message?: string;
  detail?: string;
  type: 'blog';
}

export interface BlogEditResponse {
  success: boolean;
  message: string;
  section?: Section;
}

export interface SectionEditOptions {
  file_path: string;
  section_id: string;
  instructions: string;
}
