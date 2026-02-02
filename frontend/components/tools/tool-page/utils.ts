/**
 * Utility functions for Tool Page components
 */

import type { Tool } from '../../../types/tools'
import type { ContentScoreResult } from '../ContentScore'

/**
 * Get the input label text based on tool category
 */
export function getInputLabel(tool: Tool): string {
  const labels: Record<string, string> = {
    blog: 'What topic would you like to write about?',
    email: 'What is this email about?',
    'social-media': 'What would you like to post about?',
    business: 'Describe your business or product',
    naming: 'Describe what you need a name for',
    video: 'What is your video about?',
    seo: 'Enter your content or topic',
    rewriting: 'Enter the content to rewrite',
  }
  return labels[tool.category] || 'Enter your input'
}

/**
 * Get the input placeholder text based on tool category
 */
export function getInputPlaceholder(tool: Tool): string {
  const placeholders: Record<string, string> = {
    blog: 'e.g., The future of artificial intelligence in healthcare...',
    email: 'e.g., Following up on our meeting about the Q4 project...',
    'social-media': 'e.g., Launching our new product line for summer...',
    business: 'e.g., A SaaS platform that helps small businesses manage...',
    naming: 'e.g., A tech startup focused on sustainable energy solutions...',
    video: 'e.g., Tutorial on how to build a React application...',
    seo: 'e.g., Best practices for remote work in 2024...',
    rewriting: 'Paste the content you want to improve here...',
  }
  return placeholders[tool.category] || 'Enter your input here...'
}

/**
 * Generate mock content scores for demo purposes
 */
export function generateMockScore(content: string, keywords: string[]): ContentScoreResult {
  const wordCount = content.split(/\s+/).length
  const sentenceCount = content.split(/[.!?]+/).filter((s) => s.trim()).length
  const headingCount = (content.match(/^#{1,6}\s/gm) || []).length
  const questionCount = (content.match(/\?/g) || []).length
  const listCount = (content.match(/^[\s]*[-*+]|\d+[.)]/gm) || []).length

  // Calculate keyword density
  const contentLower = content.toLowerCase()
  const primaryKeyword = keywords[0]?.toLowerCase() || ''
  const keywordOccurrences = primaryKeyword
    ? (contentLower.match(new RegExp(primaryKeyword, 'g')) || []).length
    : 0
  const keywordDensity = wordCount > 0 ? (keywordOccurrences / wordCount) * 100 : 0

  // Random variation for mock data
  const randomOffset = (): number => Math.floor(Math.random() * 15) - 7

  const readabilityScore = Math.min(100, Math.max(40, 70 + randomOffset()))
  const seoScore = Math.min(
    100,
    Math.max(40, wordCount > 300 ? 75 + randomOffset() : 50 + randomOffset())
  )
  const engagementScore = Math.min(100, Math.max(40, 65 + randomOffset()))

  const getLevel = (score: number): 'excellent' | 'good' | 'fair' | 'poor' => {
    if (score >= 80) return 'excellent'
    if (score >= 60) return 'good'
    if (score >= 40) return 'fair'
    return 'poor'
  }

  const overallScore = Math.round(
    readabilityScore * 0.3 + seoScore * 0.4 + engagementScore * 0.3
  )

  return {
    overall_score: overallScore,
    overall_level: getLevel(overallScore),
    readability: {
      score: readabilityScore,
      level: getLevel(readabilityScore),
      flesch_kincaid_grade: 8 + Math.random() * 4,
      flesch_reading_ease: readabilityScore,
      average_sentence_length: wordCount / Math.max(1, sentenceCount),
      average_word_length: 4.5 + Math.random(),
      complex_word_percentage: 10 + Math.random() * 10,
      suggestions:
        readabilityScore < 70
          ? [
              'Consider using shorter sentences',
              'Use simpler vocabulary for broader audience',
            ]
          : ['Readability is good. Content is accessible to most readers.'],
    },
    seo: {
      score: seoScore,
      level: getLevel(seoScore),
      keyword_density: keywordDensity,
      keyword_placement: {
        in_title:
          headingCount > 0 && primaryKeyword
            ? contentLower.includes(primaryKeyword)
            : false,
        in_first_paragraph: primaryKeyword
          ? contentLower.substring(0, 500).includes(primaryKeyword)
          : false,
        in_headings: headingCount > 0,
      },
      word_count: wordCount,
      heading_count: headingCount,
      has_meta_elements: false,
      internal_link_potential: 2,
      suggestions:
        seoScore < 70
          ? [
              'Add more headings to improve structure',
              'Consider expanding content length',
            ]
          : ['SEO structure looks good. Content is well-optimized.'],
    },
    engagement: {
      score: engagementScore,
      level: getLevel(engagementScore),
      hook_strength: 60 + Math.random() * 30,
      cta_count: listCount > 0 ? 1 : 0,
      emotional_word_count: Math.floor(wordCount * 0.02),
      question_count: questionCount,
      list_count: listCount,
      storytelling_elements: 1,
      suggestions:
        engagementScore < 70
          ? ['Add a stronger opening hook', 'Include a call-to-action']
          : ['Engagement is strong. Content has good hooks and CTAs.'],
    },
    summary:
      readabilityScore >= 70 && seoScore >= 70 && engagementScore >= 70
        ? 'Good content with solid fundamentals across all dimensions.'
        : 'Content has room for improvement. Focus on the suggestions below.',
    top_improvements: [
      '[SEO] Consider adding more relevant keywords naturally',
      '[Engagement] Add questions to engage readers',
      '[Readability] Break up long paragraphs for better scanning',
    ].slice(0, 3),
  }
}

/**
 * Generate mock output content for demo purposes
 */
export function generateMockOutput(
  tool: Tool | undefined,
  input: string,
  style: string = 'standard'
): string {
  if (!tool) return ''

  // Style modifiers for variation
  const stylePrefix: Record<string, string> = {
    standard: '',
    creative: 'Imagine a world where ',
    concise: '',
  }

  const styleSuffix: Record<string, string> = {
    standard: '',
    creative: '\n\nWhat possibilities does this open up for you?',
    concise: '',
  }

  const templates: Record<string, string> = {
    blog: `# ${input}

## Introduction
In today's rapidly evolving landscape, understanding ${input.toLowerCase()} has become more crucial than ever. This comprehensive guide will explore the key aspects and provide actionable insights for your journey.

## Key Points

### 1. Understanding the Fundamentals
The foundation of ${input.toLowerCase()} lies in grasping its core principles. When we examine this topic closely, we find several interconnected elements that work together to create meaningful outcomes.

### 2. Best Practices
To excel in this area, consider implementing these proven strategies:
- Focus on continuous learning and adaptation
- Embrace innovative approaches while respecting established methods
- Build strong networks and collaborative relationships

### 3. Future Outlook
As we look ahead, ${input.toLowerCase()} will continue to evolve. Staying informed and adaptable will be key to success in this dynamic field.

## Conclusion
By understanding and applying these principles, you'll be well-positioned to navigate the complexities of ${input.toLowerCase()} and achieve your goals.`,

    email: `Subject: ${input}

Hi [Name],

I hope this email finds you well. I wanted to reach out regarding ${input.toLowerCase()}.

After careful consideration, I believe we have an excellent opportunity to move forward with this initiative. Here are the key points I'd like to discuss:

1. The current situation and its implications
2. Our proposed approach and timeline
3. Expected outcomes and success metrics

Would you be available for a brief call this week to discuss these points in more detail? I'm confident that together we can achieve great results.

Looking forward to your response.

Best regards,
[Your Name]`,

    'social-media': `${input}

Here's what you need to know:

1/ First key insight that grabs attention
2/ Supporting evidence and examples
3/ Actionable takeaway for your audience

The future is bright for those who embrace change.

What are your thoughts on this? Drop a comment below and let's discuss.

#${input.split(' ')[0]} #Innovation #Growth`,

    business: `Product/Service Description:

${input}

Our solution addresses the critical challenges facing modern businesses by providing:

* Streamlined operations and improved efficiency
* Cost-effective implementation with measurable ROI
* Scalable architecture that grows with your needs

Key Benefits:
- Reduce operational costs by up to 40%
- Increase team productivity and collaboration
- Access real-time insights for informed decision-making

Ready to transform your business? Contact us today for a personalized demo.`,

    naming: `Based on your description of "${input}", here are some creative name suggestions:

1. **Nexacore** - Combining "next" and "core" for innovative foundations
2. **Vantiq** - A blend of "vantage" and "technique" suggesting expertise
3. **Luminary Labs** - Evoking leadership and innovation
4. **Elevate Pro** - Simple, memorable, and aspirational
5. **Zenith Solutions** - Representing peak performance

Each name is designed to be:
* Easy to pronounce and remember
* Available as a domain (recommended to verify)
* Scalable for future growth`,

    video: `VIDEO SCRIPT: ${input}

[INTRO - 0:00-0:30]
Hook: Open with a compelling question or statement that grabs attention immediately.

"Have you ever wondered about ${input.toLowerCase()}? Today, we're diving deep into this fascinating topic."

[MAIN CONTENT - 0:30-4:00]
Section 1: The Basics
- Explain foundational concepts
- Use visual examples

Section 2: Key Insights
- Share surprising facts
- Include expert perspectives

Section 3: Practical Application
- Step-by-step demonstration
- Real-world examples

[OUTRO - 4:00-4:30]
Summary and call-to-action:
"If you found this valuable, don't forget to like and subscribe for more content like this!"`,

    seo: `META DESCRIPTION:
Discover everything you need to know about ${input.toLowerCase()}. Our comprehensive guide covers key strategies, best practices, and expert tips for success. Read now!

---

OPTIMIZED TITLE OPTIONS:
1. "${input}: The Ultimate Guide for 2024"
2. "How to Master ${input} - Complete Strategy Guide"
3. "${input} Explained: Tips, Tricks & Best Practices"

---

KEYWORD SUGGESTIONS:
Primary: ${input.toLowerCase()}
Secondary: ${input.toLowerCase()} guide, ${input.toLowerCase()} tips, how to ${input.toLowerCase()}
Long-tail: best practices for ${input.toLowerCase()}, ${input.toLowerCase()} for beginners`,

    rewriting: `IMPROVED VERSION:

${input
  .split('. ')
  .map((sentence) => {
    // Simple transformation for demo
    return sentence.charAt(0).toUpperCase() + sentence.slice(1)
  })
  .join('. ')}

---

CHANGES MADE:
* Improved sentence structure and flow
* Enhanced clarity and readability
* Strengthened word choices
* Maintained original meaning and intent

The revised content is now more engaging and professional while preserving your original message.`,
  }

  const baseContent = templates[tool.category] || `Generated content for: ${input}`

  // Apply style modifications
  if (style === 'creative') {
    return stylePrefix.creative + baseContent + styleSuffix.creative
  } else if (style === 'concise') {
    // Return a shorter version
    const lines = baseContent.split('\n').filter((line) => line.trim())
    return lines.slice(0, Math.ceil(lines.length * 0.7)).join('\n')
  }

  return baseContent
}

/**
 * Parse keywords string into array
 */
export function parseKeywords(keywords: string): string[] {
  return keywords
    .split(',')
    .map((k) => k.trim())
    .filter((k) => k.length > 0)
}

/**
 * Copy text to clipboard with fallback for older browsers
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      // Fallback for older browsers or non-HTTPS contexts
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-9999px'
      textArea.style.top = '-9999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
    }
    return true
  } catch (err) {
    console.error('Failed to copy to clipboard:', err)
    return false
  }
}
