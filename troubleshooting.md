# Troubleshooting

## Frontend Install or Build Fails

Reinstall dependencies and clear the Next.js build output:

```bash
rm -rf node_modules .next
bun install
bun run build
```

## Frontend Cannot Reach the Backend

Check these values in `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

Then make sure the backend is running from [backend/server.py](/Users/natalyscaturchio/code/blog-AI/backend/server.py).

## Port Already in Use

Find the conflicting process:

```bash
lsof -i :3000
lsof -i :8000
```

Stop the old process or run the service on another port.

## Clerk Sign-In Pages Show a Configuration Warning

Set these values in `.env.local`:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

## Database Features Fall Back to In-Memory Storage

Persistent features such as history, templates, and analytics require `DATABASE_URL` or `DATABASE_URL_DIRECT`. Add the connection string, then rerun:

```bash
bun run db:migrate
```

## Runtime Audit Fails

Run:

```bash
bun run audit:runtime
```

If it reports a blocking advisory, update the affected package and regenerate `bun.lock` with `bun install`.

## Backend Import or Dependency Errors

Recreate the backend virtual environment:

```bash
cd backend
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
