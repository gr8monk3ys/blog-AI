See the sd-template.md

# Requirements

## Functional Requirements (pick 2 to 3)
- As a user I should be able to generate SEO-optimized blog posts by providing a topic, keywords, and tone preferences
- As a user I should be able to generate full-length books with customizable chapters and sections
- As a user I should be able to conduct web research (SERP, Tavily, Metaphor) to enhance content accuracy and include citations

## Non-Functional Requirements (pick 2 to 3)
- The service should be **highly available** (AP in CAP) - content generation can tolerate eventual consistency
- The service should support **real-time communication** via WebSockets for conversation tracking and streaming responses
- The service should be **horizontally scalable** to handle bursts of concurrent generation requests

CAP: AP (Availability + Partition Tolerance) - We prioritize availability; temporary inconsistencies in conversation state are acceptable
Read/Write: Write-heavy (generating new content) with moderate reads (retrieving conversations, viewing content)
Bursts: Yes - expect traffic spikes during peak hours; content generation is CPU/API intensive
Security: API key protection for LLM providers, rate limiting, input sanitization to prevent prompt injection
Environment: Cloud-native (Docker containers), multi-region deployment possible

# Scale

_scale_
- Daily Active Users: Target 10K DAU initially, scaling to 100K DAU
- Requests per day: ~50K blog generations, ~5K book generations
- Data per blog post: ~50KB (JSON with sections, metadata)
- Data per book: ~500KB - 2MB (multiple chapters, full content)
- Conversation history: ~10KB per session (messages, timestamps)
- LLM API calls per blog: 5-15 calls (outline, intro, sections, conclusion, FAQs)
- LLM API calls per book: 50-200 calls (depends on chapters/sections)
- Peak concurrent users: ~1K during business hours
- Storage growth: ~5GB/day for conversation logs and generated content


# Data Model

_For each use case_

## Conversations (Real-time Chat)
* Semi-structured (JSON messages with timestamps)
* Data type: Key-Value pairs with UUID keys
* CAP: AP (availability over consistency)
* BASE preferred - conversations don't require ACID
* **Storage**: Redis (for active sessions) + MongoDB (for persistence)

## Generated Content (Blogs/Books)
* Structured hierarchical data (nested sections, chapters)
* Data type: JSON documents with rich nested structures
* CAP: AP (eventual consistency acceptable)
* BASE - content can be eventually consistent
* **Storage**: MongoDB (document store for flexible schemas)

## User Accounts & Sessions
* Structured relational data
* Data type: Users, API keys, usage quotas
* CAP: CP (consistency for billing/auth)
* ACID required for user management
* **Storage**: PostgreSQL

## Research Cache
* Semi-structured (search results, web content)
* Data type: Cached API responses with TTL
* CAP: AP (stale research data acceptable)
* BASE - caching doesn't need ACID
* **Storage**: Redis with TTL expiration

## Content Search
* Unstructured text indexing
* Data type: Full-text content for search
* **Storage**: ElasticSearch / OpenSearch

## Generated Files (PDFs, DOCX, Images)
* Unstructured binary data
* **Storage**: S3 / CDN for delivery

## Data Models

```
BlogPost {
  id: UUID
  title: string
  description: string
  date: ISO timestamp
  image: string (URL)
  tags: string[]
  sections: Section[]
}

Section {
  title: string
  subtopics: SubTopic[]
}

SubTopic {
  title: string
  content: string
}

Book {
  id: UUID
  title: string
  chapters: Chapter[]
  output_file: string
  tags: string[]
  date: ISO timestamp
}

Chapter {
  number: int
  title: string
  topics: Topic[]
}

Conversation {
  id: UUID
  messages: Message[]
  created_at: ISO timestamp
}

Message {
  role: "user" | "assistant" | "system"
  content: string
  timestamp: ISO timestamp
}
```


# Interfaces / Services / Endpoints

## REST API Endpoints

### Content Generation Service
```
POST /api/v1/generate-blog
  Request: { topic, keywords[], tone, research: bool, proofread: bool, humanize: bool, conversation_id }
  Response: { id, title, sections[], tags[], metadata }

POST /api/v1/generate-book
  Request: { title, num_chapters, sections_per_chapter, keywords[], tone, research: bool, proofread: bool, humanize: bool, conversation_id }
  Response: { id, title, chapters[], output_file, tags[] }
```

### Conversation Service
```
GET  /api/v1/conversations/{conversation_id}
  Response: { id, messages[], created_at }

DELETE /api/v1/conversations/{conversation_id}
  Response: { success: bool }
```

### Research Service
```
POST /api/v1/research
  Request: { query, sources: ["serp", "tavily", "metaphor"], max_results }
  Response: { results[], related_queries[], people_also_ask[] }
```

### Publishing Service
```
POST /api/v1/publish/wordpress
  Request: { content_id, site_url, username, password, status: "draft"|"publish" }
  Response: { post_id, url }

POST /api/v1/publish/medium
  Request: { content_id, token, publication_id }
  Response: { post_id, url }

POST /api/v1/publish/github
  Request: { content_id, repo, branch, path, token }
  Response: { commit_sha, url }
```

### Export Service
```
POST /api/v1/export/{content_id}
  Request: { format: "markdown"|"docx"|"pdf"|"html" }
  Response: { download_url }
```

## WebSocket Endpoints
```
WS /ws/conversation/{conversation_id}
  Messages: { role, content, timestamp }
  Purpose: Real-time streaming of generation progress
```

## Internal Services
- **Text Generation Service**: Provider-agnostic LLM abstraction (OpenAI, Anthropic, Gemini)
- **Research Service**: Multi-source web research aggregation
- **SEO Service**: Meta descriptions, alt text, structured data generation
- **Post-Processing Service**: Proofreading, humanization, format conversion

# High Level Diagrams

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │  Web App     │    │  Mobile App  │    │  CLI Tool    │                   │
│  │  (Next.js)   │    │  (Future)    │    │  (Future)    │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                   │
└─────────┼───────────────────┼───────────────────┼───────────────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LOAD BALANCER (nginx/ALB)                         │
│                     HTTP/HTTPS :443 | WebSocket :443/ws                     │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API GATEWAY LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Rate Limiting        • Authentication       • Request Validation         │
│  • API Key Management   • Usage Tracking       • Request Routing            │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION SERVICES                               │
├────────────────┬────────────────┬────────────────┬──────────────────────────┤
│ Content Gen    │ Research       │ Publishing     │ WebSocket                │
│ Service        │ Service        │ Service        │ Manager                  │
│ (FastAPI)      │ (FastAPI)      │ (FastAPI)      │ (FastAPI)                │
│                │                │                │                          │
│ • Blog Gen     │ • SERP API     │ • WordPress    │ • Connection Pool        │
│ • Book Gen     │ • Tavily       │ • Medium       │ • Broadcast              │
│ • Outline Gen  │ • Metaphor     │ • GitHub       │ • Session Mgmt           │
│ • Post-Process │ • Google Trends│ • Export       │                          │
└───────┬────────┴───────┬────────┴───────┬────────┴──────────┬───────────────┘
        │                │                │                   │
        ▼                ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LLM ABSTRACTION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   OpenAI     │    │  Anthropic   │    │   Google     │                   │
│  │   GPT-4      │    │  Claude 3    │    │   Gemini     │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
├────────────────┬────────────────┬────────────────┬──────────────────────────┤
│    Redis       │   MongoDB      │  PostgreSQL    │     S3 / CDN             │
│                │                │                │                          │
│ • Session Cache│ • Blog Content │ • User Accounts│ • Generated PDFs         │
│ • Research     │ • Book Content │ • API Keys     │ • DOCX Files             │
│   Cache        │ • Conversations│ • Usage Quotas │ • Static Assets          │
│ • Rate Limits  │                │ • Billing      │                          │
└────────────────┴────────────────┴────────────────┴──────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ASYNC PROCESSING (Future)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐         │
│  │   Kafka      │ ──────► │   Workers    │ ──────► │   Results    │         │
│  │   Queue      │         │   (Celery)   │         │   Storage    │         │
│  └──────────────┘         └──────────────┘         └──────────────┘         │
│                                                                              │
│  Use cases: Long book generation, batch processing, scheduled publishing    │
└─────────────────────────────────────────────────────────────────────────────┘
```

_categories_

- **UI/APP**: Next.js 14 web application (React 18 + TypeScript)
- **Load Balancer**: nginx or AWS ALB for HTTP/WebSocket traffic distribution
- **Services**: FastAPI microservices (Content Gen, Research, Publishing, WebSocket)
- **LLM Providers**: OpenAI GPT-4, Anthropic Claude 3, Google Gemini
- **Caches**: Redis (sessions, research cache, rate limiting)
- **Databases**: MongoDB (content), PostgreSQL (users/billing)
- **Storage**: S3 for generated files, CDN for static assets
- **Async Queue**: Kafka + Celery workers for long-running tasks


# Scaling / Optimizing

## Database Optimizations
* Add indexes on conversation_id, user_id, created_at for fast lookups
* Shard MongoDB by user_id for horizontal scaling
* Use read replicas for PostgreSQL to handle read-heavy user queries
* Implement TTL indexes on conversations (auto-expire after 30 days)

## Caching Strategy
* Redis cache for research results (TTL: 1 hour) - avoid redundant API calls
* Cache LLM provider responses for identical prompts (content-addressable)
* CDN for static assets (Next.js build, images, generated PDFs)
* Browser caching headers for conversation history

## Performance Optimizations
* Pagination for conversation history and content lists
* Async logging with structured JSON (ship to ELK stack)
* Payload compression (gzip/brotli) for large content responses
* WebSocket connection pooling for real-time updates
* Streaming LLM responses to reduce perceived latency

## Horizontal Scaling
* Stateless FastAPI services behind load balancer (scale pods independently)
* Redis Cluster for distributed session management
* Kafka partitioning by conversation_id for ordered message processing
* Auto-scaling based on CPU/memory metrics and request queue depth

## Cost Optimizations
* LLM provider fallback chain: Gemini (cheapest) → GPT-4 → Claude (quality)
* Batch similar research queries to reduce API costs
* Use spot instances for async workers (non-critical tasks)
* Implement usage quotas and rate limiting per user tier

## Reliability
* Circuit breakers for external API calls (LLM providers, research APIs)
* Retry with exponential backoff for transient failures
* Dead letter queue for failed generation jobs
* Health checks and graceful degradation (mock responses when APIs down)

## Monitoring & Observability
* Distributed tracing (OpenTelemetry) across services
* Metrics: latency percentiles, error rates, LLM token usage
* Alerting on SLO violations (p99 latency > 30s for blog generation)
* Cost tracking dashboard for LLM API spend

