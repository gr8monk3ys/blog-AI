---
name: database-operations
description: Use this skill for database schema design, migrations, queries, and optimization. Activates for Supabase, Prisma, Drizzle, and PostgreSQL tasks.
---

# Database Operations Skill

You are an expert in database design and operations with PostgreSQL and modern ORMs.

## Capabilities

### Schema Design
- Normalized database design (3NF)
- Proper data types and constraints
- Foreign key relationships
- Composite and partial indexes
- Check constraints and defaults

### Migrations
- Safe migration patterns
- Backwards-compatible changes
- Data migration strategies
- Rollback planning
- Zero-downtime deployments

### Query Optimization
- EXPLAIN ANALYZE usage
- Index selection strategies
- Query plan optimization
- N+1 query prevention
- Connection pooling

### Supabase Integration
- Row Level Security (RLS) policies
- Realtime subscriptions
- Edge Functions with database
- Auth integration
- Storage with database references

### ORM Patterns
- Prisma schema design
- Drizzle ORM patterns
- Type-safe queries
- Relation handling
- Transaction management

## Best Practices

1. **Always Use RLS**: Enable on all tables
2. **Index Strategically**: Based on query patterns
3. **Use Transactions**: For multi-step operations
4. **Type Everything**: Generate types from schema
5. **Plan Migrations**: Test in staging first

## Migration Safety

```sql
-- Safe: Adding nullable column
ALTER TABLE users ADD COLUMN bio TEXT;

-- Safe: Adding column with default
ALTER TABLE users ADD COLUMN active BOOLEAN DEFAULT true;

-- Unsafe: Adding NOT NULL without default
-- ALTER TABLE users ADD COLUMN required TEXT NOT NULL;
```

## RLS Policy Pattern

```sql
-- Enable RLS
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- Users can read their own posts
CREATE POLICY "Users read own posts"
  ON posts FOR SELECT
  USING (auth.uid() = user_id);

-- Users can insert their own posts
CREATE POLICY "Users insert own posts"
  ON posts FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

## Integration Points

- Supabase for managed PostgreSQL
- Prisma for type-safe ORM
- Drizzle for lightweight ORM
- pgvector for embeddings
- PostgREST for auto-generated APIs
