# Prompt Templates

This directory contains customizable prompt templates for blog-AI.

## Directory Structure

```
templates/
├── prompts/              # Prompt templates
│   ├── blog_creative.txt     # Creative writing style
│   ├── blog_technical.txt    # Technical documentation style
│   └── book_comprehensive.txt # Comprehensive book format
└── README.md            # This file
```

## Using Templates

### List Available Templates

```bash
python scripts/template-manager.py list
```

### View a Template

```bash
python scripts/template-manager.py view blog_creative
```

### Show Template Variables

```bash
python scripts/template-manager.py vars blog_creative
```

### Create New Template

```bash
python scripts/template-manager.py create
```

## Template Format

Templates use simple variable substitution with `{variable_name}` syntax.

### Common Variables

**Blog Templates:**
- `{topic}` - The main topic for the blog post
- `{num_sections}` - Number of sections to generate
- `{subtopics_per_section}` - Subtopics per section
- `{tone}` - Desired tone (professional, casual, etc.)
- `{audience_level}` - Target audience (beginner, advanced, etc.)

**Book Templates:**
- `{topic}` - The main topic for the book
- `{num_chapters}` - Number of chapters
- `{book_type}` - Type of book (tutorial, reference, etc.)
- `{audience_level}` - Target audience level
- `{tone}` - Writing tone

## Creating Custom Templates

### Example: Simple Blog Template

```
# My Custom Blog Template

You are a {tone} writer creating content about {topic}.

Generate {num_sections} sections with detailed explanations.

Include:
- Clear introduction
- Practical examples
- Actionable takeaways
```

Save this as `templates/prompts/blog_custom.txt`

### Example: Specialized Book Template

```
# Technical Tutorial Book

Topic: {topic}
Chapters: {num_chapters}
Style: Hands-on tutorial

Each chapter should:
1. Start with learning objectives
2. Include code examples
3. Provide exercises
4. Build on previous chapters

Target audience: {audience_level} developers
```

Save this as `templates/prompts/book_tutorial.txt`

## Available Templates

### Blog Templates

1. **blog_creative.txt**
   - Style: Creative and engaging
   - Best for: Thought leadership, storytelling
   - Tone: Conversational, friendly
   - Features: Analogies, real-world examples

2. **blog_technical.txt**
   - Style: Technical and precise
   - Best for: Developer documentation, tutorials
   - Tone: Professional, clear
   - Features: Code examples, troubleshooting

### Book Templates

1. **book_comprehensive.txt**
   - Style: Thorough and educational
   - Best for: Comprehensive guides, textbooks
   - Structure: Progressive difficulty
   - Features: Learning objectives, exercises

## Template Best Practices

1. **Be Specific**: Clear instructions produce better results
2. **Use Structure**: Outline the expected format
3. **Include Examples**: Show what you want
4. **Define Tone**: Specify writing style
5. **Set Constraints**: Word limits, section counts, etc.

## Integration with blog-AI

Templates can be referenced in future CLI enhancements:

```bash
# Future feature
blog-ai blog "Topic" --template blog_technical
blog-ai book "Topic" --template book_comprehensive
```

## Template Variables Reference

### Standard Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{topic}` | Main subject | "Machine Learning" |
| `{num_sections}` | Section count | 3 |
| `{num_chapters}` | Chapter count | 11 |
| `{subtopics_per_section}` | Subtopics | 3 |
| `{tone}` | Writing tone | "professional" |
| `{audience_level}` | Skill level | "intermediate" |
| `{book_type}` | Book category | "tutorial" |

### Custom Variables

You can add custom variables to your templates:

```
{company_name}
{product_name}
{industry}
{target_market}
{key_features}
```

These can be passed via configuration or CLI in future versions.

## Tips for Effective Templates

### 1. Clear Structure

```
# Good
Generate a blog post with:
- Introduction (1 paragraph)
- 3 main sections
- Conclusion with call-to-action

# Less Effective
Write about the topic
```

### 2. Specific Instructions

```
# Good
Each section should:
1. Start with a descriptive heading
2. Include 2-3 practical examples
3. End with a key takeaway

# Less Effective
Make it informative
```

### 3. Tone Guidance

```
# Good
Use a friendly, conversational tone suitable for beginners.
Explain technical concepts with everyday analogies.
Avoid jargon or define it clearly.

# Less Effective
Write well
```

## Contributing Templates

To share your templates:

1. Create template in `templates/prompts/`
2. Follow naming convention: `{type}_{style}.txt`
3. Include header comment explaining purpose
4. Test with various topics
5. Document variables used
6. Submit via pull request

## Future Enhancements

Planned template features:

- [ ] Template inheritance (extend base templates)
- [ ] Conditional sections based on parameters
- [ ] Template validation tool
- [ ] Community template repository
- [ ] Template preview before generation
- [ ] A/B testing different templates

## Support

- Report template issues: GitHub Issues
- Share template ideas: GitHub Discussions
- Template questions: See CONTRIBUTING.md

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0
