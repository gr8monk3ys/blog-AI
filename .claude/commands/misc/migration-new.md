---
description: Create database migration files for schema changes
model: claude-opus-4-5
---

Generate a database migration for the specified schema change.

## Migration Specification

$ARGUMENTS

## Options (if not specified above, ask or use defaults)

| Option | Choices | Default |
|--------|---------|---------|
| **ORM/Tool** | Prisma, Drizzle, Supabase, Knex, Raw SQL | Auto-detect from project |
| **Database** | PostgreSQL, MySQL, SQLite | PostgreSQL |
| **Include RLS** | Yes (Supabase), No | Yes for Supabase |
| **Include Indexes** | Yes, No | Yes for foreign keys |
| **Include Rollback** | Yes, No | Yes |

If the ORM is unclear, ask: "Which database tool are you using: Prisma, Drizzle, Supabase, or Knex?"

## Migration Framework Detection

Auto-detect or specify the migration tool:
- **Prisma** - Modern ORM with migrations
- **Drizzle** - TypeScript-first ORM
- **Supabase** - PostgreSQL migrations
- **Knex** - SQL query builder migrations
- **Raw SQL** - Direct SQL migrations

## Migration Structure

### Prisma Migration

```prisma
// prisma/migrations/YYYYMMDDHHMMSS_description/migration.sql

-- Create new table
CREATE TABLE "User" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "email" TEXT NOT NULL UNIQUE,
    "name" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL
);

-- Add index
CREATE INDEX "User_email_idx" ON "User"("email");

-- Add foreign key
ALTER TABLE "Post" ADD CONSTRAINT "Post_authorId_fkey"
  FOREIGN KEY ("authorId") REFERENCES "User"("id") ON DELETE CASCADE;
```

### Drizzle Migration

```typescript
import { sql } from 'drizzle-orm'
import { pgTable, text, timestamp } from 'drizzle-orm/pg-core'

export const users = pgTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull()
})

// Migration file
export async function up(db) {
  await db.execute(sql`
    CREATE TABLE users (
      id TEXT PRIMARY KEY,
      email TEXT NOT NULL UNIQUE,
      name TEXT,
      created_at TIMESTAMP DEFAULT NOW() NOT NULL,
      updated_at TIMESTAMP DEFAULT NOW() NOT NULL
    )
  `)
}

export async function down(db) {
  await db.execute(sql`DROP TABLE users`)
}
```

### Supabase Migration

```sql
-- supabase/migrations/YYYYMMDDHHMMSS_description.sql

-- Create table with RLS
CREATE TABLE public.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL UNIQUE,
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can read own data"
  ON public.users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own data"
  ON public.users FOR UPDATE
  USING (auth.uid() = id);

-- Create indexes
CREATE INDEX users_email_idx ON public.users(email);

-- Add trigger for updated_at
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
```

### Knex Migration

```typescript
import type { Knex } from 'knex'

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('users', (table) => {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'))
    table.string('email').notNullable().unique()
    table.string('name')
    table.timestamps(true, true)
  })

  await knex.schema.table('users', (table) => {
    table.index('email')
  })
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTable('users')
}
```

## Migration Best Practices

### Safety Guidelines

**✅ DO:**
- Write reversible migrations (up and down)
- Test migrations on staging first
- Use transactions for multiple operations
- Add indexes for frequently queried columns
- Include default values for NOT NULL columns
- Document complex migrations
- Version control all migrations
- Run migrations in CI/CD pipeline

**❌ DON'T:**
- Delete columns with data without backup
- Change column types without data migration
- Skip migration testing
- Modify existing migrations (create new ones)
- Use database-specific syntax unless necessary
- Assume data integrity (validate first)

### Column Operations

**Adding Columns**
```sql
-- Safe: Add nullable column
ALTER TABLE users ADD COLUMN bio TEXT;

-- Safe: Add with default
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user' NOT NULL;

-- Risky: Add NOT NULL without default (existing rows fail)
-- ALTER TABLE users ADD COLUMN age INTEGER NOT NULL; -- DON'T DO THIS
```

**Modifying Columns**
```sql
-- Safe: Relaxing constraint
ALTER TABLE users ALTER COLUMN email DROP NOT NULL;

-- Risky: Tightening constraint
ALTER TABLE users ALTER COLUMN email SET NOT NULL; -- Check data first

-- Safe: Type widening
ALTER TABLE users ALTER COLUMN name TYPE VARCHAR(500);

-- Risky: Type narrowing
-- ALTER TABLE users ALTER COLUMN name TYPE VARCHAR(50); -- May truncate data
```

**Removing Columns**
```sql
-- Safe: Remove unused column
ALTER TABLE users DROP COLUMN deprecated_field;

-- Risky: Remove column with data
-- Ensure data is backed up or migrated first
```

### Data Migrations

```sql
-- Migrate data alongside schema changes
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN full_name TEXT;

-- Step 2: Migrate data
UPDATE users SET full_name = CONCAT(first_name, ' ', last_name);

-- Step 3: Make required (in next migration)
-- ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;

-- Step 4: Drop old columns (in another migration)
-- ALTER TABLE users DROP COLUMN first_name, DROP COLUMN last_name;
```

### Indexing Strategy

```sql
-- Single column index
CREATE INDEX users_email_idx ON users(email);

-- Composite index (order matters!)
CREATE INDEX posts_user_created_idx ON posts(user_id, created_at DESC);

-- Unique index
CREATE UNIQUE INDEX users_email_unique_idx ON users(email);

-- Partial index (PostgreSQL)
CREATE INDEX active_users_idx ON users(email) WHERE active = true;

-- Concurrent index (PostgreSQL, doesn't lock table)
CREATE INDEX CONCURRENTLY users_email_idx ON users(email);
```

### Foreign Keys and Constraints

```sql
-- Add foreign key with cascading delete
ALTER TABLE posts
  ADD CONSTRAINT posts_user_id_fkey
  FOREIGN KEY (user_id)
  REFERENCES users(id)
  ON DELETE CASCADE;

-- Add check constraint
ALTER TABLE users
  ADD CONSTRAINT users_email_check
  CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$');

-- Add unique constraint
ALTER TABLE users
  ADD CONSTRAINT users_email_unique
  UNIQUE (email);
```

## Migration Workflow

### Development
```bash
# Create new migration
prisma migrate dev --name add_user_bio

# Apply migrations
drizzle-kit push:pg

# Supabase
supabase migration new add_user_bio
supabase db push
```

### Production
```bash
# Review migration
prisma migrate diff

# Apply to production
prisma migrate deploy

# Rollback if needed
prisma migrate resolve --rolled-back MIGRATION_NAME
```

## Common Migration Patterns

### Adding a New Table
```sql
CREATE TABLE posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT,
  author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  published BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX posts_author_id_idx ON posts(author_id);
CREATE INDEX posts_published_created_idx ON posts(published, created_at DESC);
```

### Renaming Column (Safe)
```sql
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN full_name TEXT;

-- Step 2: Copy data
UPDATE users SET full_name = name;

-- Step 3: Drop old column (in separate migration)
-- ALTER TABLE users DROP COLUMN name;
```

### Adding Enum Type
```sql
-- PostgreSQL
CREATE TYPE user_role AS ENUM ('admin', 'user', 'guest');
ALTER TABLE users ADD COLUMN role user_role DEFAULT 'user' NOT NULL;

-- Or use check constraint
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user' NOT NULL;
ALTER TABLE users ADD CONSTRAINT users_role_check
  CHECK (role IN ('admin', 'user', 'guest'));
```

## Output Format

Generate:
1. **Migration File** - Complete migration with up/down
2. **Schema Changes** - Clear SQL/code for changes
3. **Indexes** - Appropriate indexes for performance
4. **Constraints** - Foreign keys, checks, uniqueness
5. **Rollback** - Down migration to reverse changes
6. **Comments** - Document non-obvious decisions

## File Naming

Format: `YYYYMMDDHHMMSS_descriptive_name.sql` or `.ts`
Example: `20250112_add_user_profile_fields.sql`

Generate safe, reversible, production-ready migrations that maintain data integrity and follow best practices.
