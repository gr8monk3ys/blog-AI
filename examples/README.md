# Examples

This directory contains example outputs and usage demonstrations for blog-AI.

## Directory Structure

```
examples/
├── blogs/              # Example blog posts (MDX)
├── books/              # Example books (DOCX)
├── configs/            # Example configuration files
└── README.md           # This file
```

## Quick Start Examples

### Generate a Blog Post

```bash
# Simple blog post
blog-ai-blog "The Future of Artificial Intelligence"

# With custom options
blog-ai-blog "Python Best Practices" \
    --sections 5 \
    --model gpt-4 \
    --temperature 0.7 \
    --output ./my-blogs \
    --verbose
```

### Generate a Book

```bash
# Simple book
blog-ai-book "Introduction to Machine Learning"

# With custom options
blog-ai-book "Advanced Python Programming" \
    --chapters 15 \
    --model gpt-4 \
    --temperature 0.8 \
    --output ./my-books/advanced-python.docx \
    --verbose
```

## Example Outputs

### Blog Post Structure (MDX)

Generated blog posts follow this structure:

```mdx
import { BlogLayout } from '@/components/BlogLayout'

export const metadata = {
  title: 'The Future of Artificial Intelligence',
  description: 'Exploring how AI is transforming our world...',
  date: '2024-01-15',
  image: '/images/blog/ai-future.jpg',
  tags: ['ai', 'technology', 'future'],
}

export default (props) => <BlogLayout metadata={metadata} {...props} />

# Section 1: Understanding Modern AI

## Subtopic 1: Machine Learning Fundamentals
Content here...

## Subtopic 2: Deep Learning Architectures
Content here...

# Section 2: AI Applications
...
```

### Book Structure (DOCX)

Generated books include:

1. **Title Page**
   - Book title
   - Author name (optional)

2. **Chapters** (with consistent formatting)
   - Chapter number and title
   - Hierarchical headings
   - Paragraph content
   - Page breaks between chapters

3. **Professional Styling**
   - Title: 24pt, Bold
   - Chapter Headings: 18pt, Bold
   - Section Headings: 14pt, Bold
   - Body Text: 11pt
   - Proper spacing

## Configuration Examples

### Basic Configuration (.blog-ai.toml)

```toml
[general]
model = "gpt-4"
temperature = 0.9
verbose = false

[blog]
sections = 3
subtopics_per_section = 3
output_dir = "./output/blogs"
default_tags = ["AI", "technology"]

[book]
chapters = 11
output_dir = "./output/books"
```

### Advanced Configuration

```toml
[general]
model = "gpt-4"
temperature = 0.9

[blog]
sections = 5
subtopics_per_section = 4

[prompts.blog]
title_prompt = """
Generate an engaging title for: {topic}
Requirements:
- Under 60 characters
- SEO-optimized
- Includes relevant keywords
"""
```

## Real-World Use Cases

### Use Case 1: Technical Documentation

```bash
# Generate technical blog post
blog-ai-blog "RESTful API Design Best Practices" \
    --sections 4 \
    --temperature 0.7

# Expected output:
# - Introduction to REST principles
# - Resource design patterns
# - Authentication and security
# - Error handling and versioning
```

### Use Case 2: Educational Content

```bash
# Generate comprehensive book
blog-ai-book "Python for Data Science" \
    --chapters 12 \
    --temperature 0.8

# Expected chapters:
# 1. Python Basics
# 2. Data Structures
# 3. NumPy
# 4. Pandas
# ... etc.
```

### Use Case 3: Thought Leadership

```bash
# Generate opinion piece
blog-ai-blog "The Ethics of AI in Healthcare" \
    --sections 4 \
    --model gpt-4 \
    --temperature 0.9

# Expected output:
# - Current AI applications in healthcare
# - Ethical considerations
# - Privacy and security concerns
# - Future outlook
```

## Workflow Examples

### Complete Blog Workflow

```bash
# 1. Generate blog
blog-ai-blog "Kubernetes Best Practices" \
    --output ./content/blogs \
    --verbose

# 2. Review output
cat ./content/blogs/kubernetes-best-practices.mdx

# 3. Edit if needed
code ./content/blogs/kubernetes-best-practices.mdx

# 4. Publish to your site
cp ./content/blogs/kubernetes-best-practices.mdx \
   ../my-website/content/blog/
```

### Batch Generation

```bash
# Generate multiple topics
for topic in "AI Ethics" "Cloud Computing" "DevOps"; do
    blog-ai-blog "$topic" --output ./batch-blogs
done
```

### Custom Pipeline

```bash
# 1. Generate with specific model
blog-ai-blog "Topic" --model gpt-4-turbo-preview

# 2. Check quality with tests
make test

# 3. Run quality checks
make quality

# 4. Deploy
./deploy.sh ./output/blogs/
```

## Sample Topics

### Technology Blog Topics

- "The Rise of Edge Computing"
- "Microservices vs Monolithic Architecture"
- "Introduction to WebAssembly"
- "GraphQL Best Practices"
- "Serverless Architecture Patterns"

### Book Topics

- "Complete Guide to TypeScript"
- "Mastering Docker and Kubernetes"
- "Full-Stack Development with Next.js"
- "Data Science with Python"
- "Cloud-Native Applications"

## Tips for Best Results

### 1. Be Specific

```bash
# Good
blog-ai-blog "Implementing JWT Authentication in Node.js"

# Less Specific
blog-ai-blog "Authentication"
```

### 2. Adjust Temperature

```bash
# Creative content (0.9-1.2)
blog-ai-blog "The Future of Work" --temperature 1.0

# Technical content (0.5-0.8)
blog-ai-blog "Python Type Hints Guide" --temperature 0.6
```

### 3. Use Appropriate Section Count

```bash
# Quick overview (2-3 sections)
blog-ai-blog "Topic" --sections 2

# Comprehensive article (4-6 sections)
blog-ai-blog "Topic" --sections 5
```

### 4. Choose Right Model

```bash
# For technical accuracy
--model gpt-4

# For creative content
--model gpt-4 --temperature 1.0

# For faster generation
--model gpt-3.5-turbo
```

## Troubleshooting Examples

### Issue: Content Too Short

```bash
# Increase sections and subtopics
blog-ai-blog "Topic" --sections 5

# Adjust in config:
[blog]
sections = 5
subtopics_per_section = 4
```

### Issue: Content Too Technical

```bash
# Lower temperature for more focused output
blog-ai-blog "Topic" --temperature 0.6
```

### Issue: Output Not Formatted

```bash
# Check file extension
ls ./output/blogs/*.mdx

# Verify formatter working
make test-unit
```

## Performance Benchmarks

Typical generation times:

| Content Type | Sections/Chapters | Time | Cost (est.) |
|-------------|-------------------|------|-------------|
| Blog Post   | 3 sections        | 45s  | $0.10       |
| Blog Post   | 5 sections        | 75s  | $0.15       |
| Book        | 11 chapters       | 8min | $1.50       |
| Book        | 20 chapters       | 15min| $2.75       |

*Note: Times and costs are approximate and vary based on topic complexity*

## Next Steps

1. Try generating your first blog post
2. Experiment with different topics and settings
3. Review output quality
4. Adjust temperature and sections as needed
5. Create custom templates for your use case

## Resources

- Main Documentation: [README.md](../README.md)
- Contributing Guide: [CONTRIBUTING.md](../CONTRIBUTING.md)
- Template Guide: [templates/README.md](../templates/README.md)
- API Reference: [SYSTEM_DESIGN.md](../SYSTEM_DESIGN.md)

---

**Last Updated**: 2024-01-15
