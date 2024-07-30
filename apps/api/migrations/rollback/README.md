# API Migration Rollback Scripts

## Overview

This directory contains rollback (DOWN) scripts for the `apps/api/migrations/`
migration files that manage the webhook system tables.

## WARNING -- DATA LOSS

Running a rollback script **permanently deletes** the data stored in the
affected tables. Always create a full database backup before executing any
rollback:

```bash
pg_dump -Fc "$DATABASE_URL" -f backup_$(date +%Y%m%d_%H%M%S).dump
```

## Execution Order

There is currently only one migration, so run:

```bash
psql "$DATABASE_URL" -f rollback/001_drop_webhook_tables.sql
```

## Script Inventory

| Rollback Script | Rolls Back | Objects Dropped |
|---|---|---|
| `001_drop_webhook_tables.sql` | `001_create_webhook_tables.sql` | `webhook_subscriptions`, `webhook_deliveries`, `webhook_recent_events` tables + 4 functions + 2 triggers + 3 RLS policies |

## Notes

- All scripts use `IF EXISTS` and `CASCADE` for safety.
- Each script is wrapped in a `BEGIN`/`COMMIT` transaction.
