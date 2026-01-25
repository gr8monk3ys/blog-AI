# Blog AI API Documentation

This document provides comprehensive API documentation for external developers integrating with the Blog AI SaaS platform.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Endpoint Reference](#endpoint-reference)
   - [Health & Status](#health--status)
   - [Content Generation](#content-generation)
   - [Brand Voice](#brand-voice)
   - [Content Remix](#content-remix)
   - [Batch Processing](#batch-processing)
   - [Image Generation](#image-generation)
   - [Export](#export)
   - [Tools](#tools)
   - [Usage & Quotas](#usage--quotas)
   - [Payments](#payments)
   - [Conversations](#conversations)
6. [Webhooks](#webhooks)
7. [SDKs & Examples](#sdks--examples)

---

## Overview

Blog AI provides a RESTful API for AI-powered content generation. The API supports:

- Blog post and book generation with SEO optimization
- Brand voice training and application
- Content transformation across social media formats
- Batch processing for high-volume operations
- AI image generation
- Multi-format export (Markdown, HTML, PDF, WordPress)

### Base URLs

| Environment | URL |
|-------------|-----|
| Production | `https://api.blogai.com` |
| Development | `http://localhost:8000` |

### API Versioning

The API supports versioned endpoints:
- **Root endpoints**: `https://api.blogai.com/endpoint` (backward compatible)
- **Versioned endpoints**: `https://api.blogai.com/api/v1/endpoint` (recommended)

### OpenAPI Specification

Interactive API documentation is available at:
- Swagger UI: `{base_url}/docs`
- ReDoc: `{base_url}/redoc`
- OpenAPI JSON: `{base_url}/openapi.json`

---

## Authentication

All API endpoints (except `/health` and `/` root) require authentication via API key.

### Obtaining an API Key

API keys are generated when you create an account. Contact support or use the dashboard to manage your API keys.

### Using Your API Key

Include your API key in the `X-API-Key` header with every request:

```bash
curl -X POST "https://api.blogai.com/generate-blog" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI in Healthcare", "conversation_id": "conv-123"}'
```

### Security Best Practices

1. **Never expose API keys** in client-side code or public repositories
2. **Rotate keys regularly** using the dashboard
3. **Use environment variables** to store keys
4. **Monitor usage** to detect unauthorized access

### Authentication Errors

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | `Missing API key` | No `X-API-Key` header provided |
| 401 | `Invalid API key` | The provided key is not valid |
| 403 | `Access denied` | Key is valid but lacks permission for this resource |

---

## Rate Limiting

Rate limits protect the API from abuse and ensure fair usage across all users.

### Tier-Based Limits

| Tier | Requests/Minute | Requests/Hour |
|------|-----------------|---------------|
| Free | 10 | 100 |
| Starter | 30 | 500 |
| Pro | 60 | 2,000 |
| Business | 120 | 10,000 |

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1706140800
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in the current window |
| `X-RateLimit-Remaining` | Requests remaining before limit is reached |
| `X-RateLimit-Reset` | Unix timestamp when the limit resets |

### Rate Limit Exceeded Response

When you exceed the rate limit, you receive a `429 Too Many Requests` response:

```json
{
  "success": false,
  "error": "Rate limit exceeded. Maximum 60 requests per minute.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "limit": 60,
  "remaining": 0,
  "reset_at": 1706140800,
  "retry_after": 45,
  "window": "minute",
  "tier": "pro",
  "upgrade_url": "/pricing"
}
```

The response includes a `Retry-After` header indicating seconds to wait.

---

## Error Handling

The API uses standard HTTP status codes and returns consistent error responses.

### Error Response Format

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "detail": "Additional context when available"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created (for generation endpoints) |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid API key |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource does not exist |
| 422 | Unprocessable Entity - Validation failed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 502 | Bad Gateway - AI provider error |
| 503 | Service Unavailable - Temporary outage |

### Common Error Codes

| Code | Description |
|------|-------------|
| `RATE_LIMIT_EXCEEDED` | Request rate limit hit |
| `QUOTA_EXCEEDED` | Monthly generation quota exhausted |
| `VALIDATION_ERROR` | Input validation failed |
| `PROVIDER_ERROR` | AI provider (OpenAI/Anthropic/Gemini) error |
| `GENERATION_FAILED` | Content generation failed |
| `RESOURCE_NOT_FOUND` | Requested resource not found |

---

## Endpoint Reference

### Health & Status

#### GET /health

Check overall system health status.

**Authentication**: Not required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-24T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": {"status": "up", "latency_ms": 5.2},
    "stripe": {"status": "up", "mode": "live"},
    "sentry": {"status": "up"}
  }
}
```

#### GET /health/db

Detailed database health check.

#### GET /health/stripe

Detailed Stripe configuration status.

#### GET /health/cache

Cache statistics and performance metrics.

---

### Content Generation

#### POST /generate-blog

Generate an AI-powered blog post.

**Authentication**: Required (API key)

**Request Body**:
```json
{
  "topic": "The Future of AI in Healthcare",
  "keywords": ["artificial intelligence", "healthcare", "diagnosis"],
  "tone": "professional",
  "research": true,
  "proofread": true,
  "humanize": true,
  "conversation_id": "conv-abc123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | Yes | Blog topic (1-500 characters) |
| `keywords` | array | No | SEO keywords (max 10) |
| `tone` | string | No | Writing tone: `informative`, `professional`, `casual`, `formal`, `friendly`, `persuasive` |
| `research` | boolean | No | Enable web research for factual content |
| `proofread` | boolean | No | Run proofreading pass (default: true) |
| `humanize` | boolean | No | Apply humanization to reduce AI patterns (default: true) |
| `conversation_id` | string | Yes | Unique conversation identifier |

**Response** (201 Created):
```json
{
  "success": true,
  "type": "blog",
  "content": {
    "title": "The Future of AI in Healthcare: Transforming Patient Care",
    "description": "Explore how artificial intelligence is revolutionizing healthcare...",
    "date": "2024-01-24",
    "image": null,
    "tags": ["AI", "Healthcare", "Technology"],
    "sections": [
      {
        "title": "Introduction",
        "subtopics": [
          {
            "title": "The AI Revolution in Medicine",
            "content": "..."
          }
        ]
      }
    ]
  }
}
```

**Errors**:
- `400`: Invalid topic or parameters
- `429`: Rate limit or quota exceeded
- `502`: AI provider error

---

#### POST /generate-book

Generate a full book with multiple chapters.

**Request Body**:
```json
{
  "title": "Complete Guide to Machine Learning",
  "num_chapters": 5,
  "sections_per_chapter": 3,
  "keywords": ["machine learning", "data science"],
  "tone": "informative",
  "research": true,
  "proofread": true,
  "humanize": true,
  "conversation_id": "conv-xyz789"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Book title (1-500 characters) |
| `num_chapters` | integer | No | Number of chapters (1-20, default: 5) |
| `sections_per_chapter` | integer | No | Sections per chapter (1-10, default: 3) |
| `keywords` | array | No | Keywords for content guidance |
| `tone` | string | No | Writing tone |
| `research` | boolean | No | Enable research mode |
| `proofread` | boolean | No | Run proofreading (default: true) |
| `humanize` | boolean | No | Humanize content (default: true) |
| `conversation_id` | string | Yes | Conversation identifier |

**Response** (201 Created):
```json
{
  "success": true,
  "type": "book",
  "content": {
    "title": "Complete Guide to Machine Learning",
    "description": "A comprehensive exploration of machine learning...",
    "date": "2024-01-24",
    "tags": ["Machine Learning", "Data Science"],
    "chapters": [
      {
        "number": 1,
        "title": "Introduction to Machine Learning",
        "topics": [
          {
            "title": "What is Machine Learning?",
            "content": "..."
          }
        ]
      }
    ]
  }
}
```

---

### Brand Voice

Train custom brand voices and apply them to generated content.

#### POST /brand-voice/analyze

Analyze content to extract voice characteristics.

**Request Body**:
```json
{
  "content": "Your sample content here (minimum 50 characters)...",
  "content_type": "text",
  "provider": "openai"
}
```

**Response**:
```json
{
  "success": true,
  "analysis": {
    "vocabulary_patterns": {...},
    "sentence_structures": {...},
    "tone_distribution": {...},
    "style_metrics": {...}
  },
  "quality_score": 0.85
}
```

#### POST /brand-voice/samples

Add a voice sample to a brand profile.

**Request Body**:
```json
{
  "profile_id": "my-brand-voice",
  "content": "Sample content representing your brand voice...",
  "content_type": "text",
  "title": "Blog Post Example",
  "source_url": "https://example.com/blog/post",
  "is_primary_example": true
}
```

#### GET /brand-voice/samples/{profile_id}

List all voice samples for a brand profile.

#### DELETE /brand-voice/samples/{profile_id}/{sample_id}

Delete a voice sample.

#### POST /brand-voice/train

Train a voice fingerprint from samples.

**Request Body**:
```json
{
  "profile_id": "my-brand-voice",
  "sample_ids": ["sample-1", "sample-2"],
  "provider": "openai"
}
```

**Response**:
```json
{
  "success": true,
  "fingerprint": {...},
  "sample_count": 5,
  "training_quality": 0.92,
  "voice_summary": "Professional, authoritative tone with technical vocabulary..."
}
```

#### GET /brand-voice/fingerprint/{profile_id}

Get the trained voice fingerprint.

#### POST /brand-voice/score

Score content against a trained brand voice.

**Request Body**:
```json
{
  "profile_id": "my-brand-voice",
  "content": "Content to score for voice consistency...",
  "provider": "openai"
}
```

**Response**:
```json
{
  "success": true,
  "score": {
    "overall_score": 0.87,
    "vocabulary_match": 0.92,
    "tone_match": 0.85,
    "style_match": 0.84
  },
  "grade": "B",
  "passed": true
}
```

#### GET /brand-voice/status/{profile_id}

Get training status for a profile.

---

### Content Remix

Transform content across multiple formats.

#### GET /remix/formats

Get all available content formats.

**Response**:
```json
[
  {
    "format": "twitter_thread",
    "name": "Twitter Thread",
    "icon": "twitter",
    "description": "Multi-tweet thread format",
    "max_length": 2800,
    "platform": "twitter",
    "supports_images": true
  },
  {
    "format": "linkedin_post",
    "name": "LinkedIn Post",
    "icon": "linkedin",
    "description": "Professional LinkedIn update",
    "max_length": 3000,
    "platform": "linkedin",
    "supports_images": true
  }
]
```

#### POST /remix/transform

Transform content into multiple formats.

**Request Body**:
```json
{
  "source_content": {
    "title": "AI in Healthcare",
    "body": "Full blog post content..."
  },
  "target_formats": ["twitter_thread", "linkedin_post"],
  "preserve_voice": true,
  "brand_profile_id": "my-brand-voice",
  "conversation_id": "conv-123",
  "provider": "openai"
}
```

**Response**:
```json
{
  "success": true,
  "analysis": {...},
  "transformations": [
    {
      "format": "twitter_thread",
      "content": {
        "tweets": [
          "1/ AI is revolutionizing healthcare...",
          "2/ Here's what you need to know..."
        ]
      },
      "quality_score": 0.89
    }
  ],
  "total_formats": 2,
  "processing_time_ms": 3500
}
```

#### POST /remix/preview

Preview transformation without full generation.

---

### Batch Processing

Process multiple content items in parallel.

#### POST /batch/import/csv

Import topics from CSV and start batch generation.

**Request**: `multipart/form-data` with CSV file

**CSV Format**:
```csv
topic,keywords,tone,content_type
"AI in Healthcare","AI,healthcare,diagnosis",professional,blog
"Future of Remote Work","remote,productivity",informative,blog
```

**Query Parameters**:
- `provider_strategy`: `single`, `round_robin`, `cost_optimized`, `quality_optimized`
- `preferred_provider`: `openai`, `anthropic`, `gemini`
- `research_enabled`: boolean
- `parallel_limit`: 1-10 (default: 3)
- `conversation_id`: required

**Response** (202 Accepted):
```json
{
  "success": true,
  "job_id": "batch-abc123",
  "status": "pending",
  "total_items": 10,
  "estimated_cost_usd": 2.50,
  "cost_breakdown": {...}
}
```

#### GET /batch/template/csv

Download CSV template for batch import.

#### GET /batch/jobs

List batch jobs with optional filtering.

**Query Parameters**:
- `status`: Filter by status (`pending`, `processing`, `completed`, `failed`, `cancelled`)
- `limit`: Max results (1-100, default: 20)
- `offset`: Pagination offset

#### GET /batch/{job_id}

Get batch job status.

**Response**:
```json
{
  "job_id": "batch-abc123",
  "name": "CSV Import: topics.csv",
  "status": "processing",
  "total_items": 10,
  "completed_items": 6,
  "failed_items": 1,
  "progress_percentage": 70.0,
  "estimated_cost_usd": 2.50,
  "actual_cost_usd": 1.75,
  "providers_used": {"openai": 5, "anthropic": 2},
  "created_at": "2024-01-24T12:00:00Z"
}
```

#### GET /batch/{job_id}/results

Get completed batch results.

#### GET /batch/export/{job_id}

Export batch results.

**Query Parameters**:
- `format`: `json`, `csv`, `markdown`, `zip`

#### POST /batch/{job_id}/retry

Retry failed items in a batch job.

**Request Body**:
```json
{
  "item_indices": [3, 7],
  "change_provider": "anthropic"
}
```

#### POST /batch/{job_id}/cancel

Cancel a running batch job.

#### POST /batch/estimate

Estimate cost for a batch job before running.

---

### Image Generation

Generate AI-powered images for content.

#### POST /images/generate

Generate a single image.

**Request Body**:
```json
{
  "custom_prompt": "A futuristic healthcare facility with AI assistants",
  "image_type": "featured",
  "size": "1792x1024",
  "style": "natural",
  "quality": "hd",
  "provider": "openai"
}
```

Or generate from content:
```json
{
  "content": "Blog post content to generate image for...",
  "image_type": "featured",
  "size": "1792x1024",
  "style": "vivid",
  "provider": "openai"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "url": "https://...",
    "prompt_used": "...",
    "size": "1792x1024",
    "provider": "openai",
    "style": "natural"
  }
}
```

#### POST /images/generate-for-blog

Generate all images for a blog post.

**Request Body**:
```json
{
  "content": "Full blog post content...",
  "title": "AI in Healthcare",
  "keywords": ["AI", "healthcare"],
  "generate_featured": true,
  "generate_social": true,
  "inline_count": 2,
  "provider": "openai",
  "style": "natural",
  "quality": "hd"
}
```

#### GET /images/styles

Get available image styles and sizes.

#### GET /images/health

Check image generation service status.

---

### Export

Export content to various formats.

#### POST /export/markdown

Export as Markdown file.

**Request Body**:
```json
{
  "title": "Blog Post Title",
  "content": "Markdown content...",
  "content_type": "blog",
  "metadata": {
    "date": "2024-01-24",
    "description": "Post description",
    "tags": ["AI", "Technology"]
  }
}
```

**Response**: Downloadable `.md` file

#### POST /export/html

Export as styled HTML file.

#### POST /export/text

Export as plain text file.

#### POST /export/pdf

Export as PDF file.

#### POST /export/wordpress

Export as WordPress Gutenberg blocks.

**Response**:
```json
{
  "success": true,
  "content": "<!-- wp:heading -->...",
  "format": "wordpress"
}
```

#### POST /export/medium

Export as Medium-compatible HTML.

---

### Tools

Content generation tools and utilities.

#### GET /tools

List all available tools.

**Query Parameters**:
- `category`: Filter by category (`blog`, `email`, `social`, `seo`)
- `search`: Search term
- `tags`: Comma-separated tags
- `limit`: Max results (1-100)
- `offset`: Pagination offset

#### GET /tools/categories

List all tool categories.

#### GET /tools/{tool_id}

Get detailed tool information.

#### POST /tools/{tool_id}/execute

Execute a tool.

**Request Body**:
```json
{
  "inputs": {
    "topic": "Value for topic input",
    "tone": "professional"
  },
  "provider_type": "openai",
  "options": {
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

#### POST /tools/{tool_id}/validate

Validate inputs without executing.

#### POST /tools/{tool_id}/score

Score generated content.

#### POST /tools/{tool_id}/variations

Generate A/B test variations.

#### POST /tools/score

Score any content (not tool-specific).

---

### Usage & Quotas

Track usage and manage quotas.

#### GET /usage/stats

Get usage statistics for the authenticated user.

**Response**:
```json
{
  "user_hash": "abc123...",
  "tier": "pro",
  "daily_count": 15,
  "daily_limit": 50,
  "daily_remaining": 35,
  "monthly_count": 120,
  "monthly_limit": 200,
  "monthly_remaining": 80,
  "tokens_used_today": 45000,
  "tokens_used_month": 380000,
  "is_limit_reached": false,
  "percentage_used_daily": 30.0,
  "percentage_used_monthly": 60.0,
  "reset_daily_at": "2024-01-25T00:00:00Z",
  "reset_monthly_at": "2024-02-01T00:00:00Z"
}
```

#### GET /usage/check

Check if user has remaining quota.

#### GET /usage/tiers

Get all available subscription tiers.

#### GET /usage/tier/{tier_name}

Get details for a specific tier.

#### GET /usage/features

Get features available to the user based on their tier.

#### GET /usage/quota/stats

Get detailed quota statistics (new system).

#### GET /usage/quota/check

Check quota availability.

#### GET /usage/quota/breakdown

Get usage breakdown by operation type.

---

### Payments

Subscription and billing management.

#### GET /api/payments/pricing

Get available pricing tiers (no authentication required).

**Response**:
```json
{
  "success": true,
  "tiers": [
    {
      "id": "free",
      "name": "Free",
      "price_monthly": 0,
      "price_yearly": 0,
      "generations_per_month": 5,
      "features": [
        "5 generations per month",
        "Basic blog generation",
        "Standard support"
      ]
    },
    {
      "id": "starter",
      "name": "Starter",
      "price_monthly": 19.00,
      "price_yearly": 190.00,
      "generations_per_month": 50,
      "features": [...],
      "stripe_price_id": "price_xxx"
    }
  ]
}
```

#### POST /api/payments/create-checkout-session

Create a Stripe checkout session.

**Request Body**:
```json
{
  "price_id": "price_xxx",
  "success_url": "https://app.blogai.com/success?session_id={CHECKOUT_SESSION_ID}",
  "cancel_url": "https://app.blogai.com/pricing"
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "cs_xxx",
  "url": "https://checkout.stripe.com/..."
}
```

#### POST /api/payments/create-portal-session

Create a Stripe customer portal session.

**Request Body**:
```json
{
  "return_url": "https://app.blogai.com/settings"
}
```

**Response**:
```json
{
  "success": true,
  "url": "https://billing.stripe.com/..."
}
```

#### GET /api/payments/subscription-status

Get current subscription status.

**Response**:
```json
{
  "success": true,
  "has_subscription": true,
  "tier": "pro",
  "status": "active",
  "current_period_end": 1709251200,
  "cancel_at_period_end": false,
  "customer_id": "cus_xxx",
  "generations_limit": 200
}
```

---

### Conversations

Manage conversation history.

#### GET /conversations/{conversation_id}

Get conversation history.

**Response**:
```json
{
  "conversation": [
    {
      "role": "user",
      "content": "Generate a blog post about AI",
      "timestamp": "2024-01-24T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Generated blog post: AI in Healthcare",
      "timestamp": "2024-01-24T12:00:05Z"
    }
  ]
}
```

---

## Webhooks

Blog AI uses Stripe webhooks for subscription lifecycle events.

### Webhook Endpoint

```
POST /api/payments/webhook
```

This endpoint receives events from Stripe. It does not require API key authentication but validates requests using the Stripe webhook signature.

### Setting Up Webhooks

1. Go to Stripe Dashboard > Developers > Webhooks
2. Add endpoint: `https://api.blogai.com/api/payments/webhook`
3. Select events to listen for
4. Copy the signing secret to your environment as `STRIPE_WEBHOOK_SECRET`

### Supported Events

| Event | Description |
|-------|-------------|
| `checkout.session.completed` | User completed checkout |
| `customer.subscription.created` | New subscription created |
| `customer.subscription.updated` | Subscription modified |
| `customer.subscription.deleted` | Subscription cancelled |
| `invoice.paid` | Payment successful |
| `invoice.payment_failed` | Payment failed |

### Webhook Payload Processing

The webhook handler:
1. Validates the Stripe signature
2. Parses the event data
3. Updates user subscription tier in the database
4. Returns 200 OK on success

### Testing Webhooks

Use Stripe CLI for local testing:

```bash
stripe listen --forward-to localhost:8000/api/payments/webhook
```

---

## SDKs & Examples

### Python Example

```python
import requests

API_KEY = "your_api_key"
BASE_URL = "https://api.blogai.com"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Generate a blog post
response = requests.post(
    f"{BASE_URL}/generate-blog",
    headers=headers,
    json={
        "topic": "AI in Healthcare",
        "keywords": ["artificial intelligence", "healthcare"],
        "tone": "professional",
        "research": True,
        "conversation_id": "my-session-123"
    }
)

if response.status_code == 201:
    data = response.json()
    print(f"Generated: {data['content']['title']}")
else:
    print(f"Error: {response.json()}")
```

### JavaScript/TypeScript Example

```typescript
const API_KEY = 'your_api_key';
const BASE_URL = 'https://api.blogai.com';

async function generateBlog(topic: string): Promise<BlogResponse> {
  const response = await fetch(`${BASE_URL}/generate-blog`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      topic,
      keywords: ['AI', 'technology'],
      tone: 'professional',
      research: true,
      conversation_id: crypto.randomUUID(),
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Generation failed');
  }

  return response.json();
}

// Usage
const result = await generateBlog('The Future of AI');
console.log(result.content.title);
```

### cURL Examples

**Generate Blog Post**:
```bash
curl -X POST "https://api.blogai.com/generate-blog" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI in Healthcare",
    "keywords": ["AI", "healthcare"],
    "tone": "professional",
    "research": true,
    "conversation_id": "conv-123"
  }'
```

**Check Usage**:
```bash
curl -X GET "https://api.blogai.com/usage/stats" \
  -H "X-API-Key: your_api_key"
```

**Export to Markdown**:
```bash
curl -X POST "https://api.blogai.com/export/markdown" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Blog Post",
    "content": "# Heading\n\nContent here...",
    "content_type": "blog"
  }' \
  --output blog-post.md
```

---

## Changelog

### v1.0.0 (2024-01-24)

- Initial public API release
- Blog and book generation endpoints
- Brand voice training
- Content remix
- Batch processing
- Image generation
- Multi-format export
- Stripe integration for payments

---

## Support

- **Documentation**: https://docs.blogai.com
- **API Status**: https://status.blogai.com
- **Email**: support@blogai.com
- **Discord**: https://discord.gg/blogai
