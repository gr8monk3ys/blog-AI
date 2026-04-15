# Staging Checklist

Use this before treating the product as launch-ready.

## Required Infrastructure

- Vercel deployment for `apps/web`
- Railway or equivalent deployment for `apps/api`
- Neon/Postgres connected to both
- Clerk configured end to end
- Stripe test mode configured
- at least one valid LLM provider key

## Preflight

1. `bun run lint`
2. `bun run type-check`
3. `bun run test:run`
4. `bun run test:api:blocking`
5. `bun run build`
6. `bun run audit:runtime`

## Manual Smoke Test

1. Visit the public homepage.
2. Visit pricing and confirm the public plans match the checkout-ready tiers.
3. Sign up with Clerk.
4. Complete onboarding.
5. Save a brand profile successfully.
6. Land in the bulk workflow with a prefilled first batch.
7. Run one real generation with a valid provider key.
8. Verify the result is stored where the product expects.
9. Upgrade through Stripe test checkout.
10. Return from checkout and confirm limits/features update.
11. Open the billing portal and return successfully.
12. Check backend `/health` and error monitoring after the run.

## Must-Pass Product Conditions

- protected routes work with real auth
- brand profile writes persist
- bulk workflow runs against a real LLM
- pricing, checkout, and billing portal all agree
- no fake-success or sample-data behavior leaks into paid-user paths

## Launch Warning

Do not call the product production-ready if any of these are still unproven:

- real Clerk auth
- real database persistence
- real Stripe flow
- real provider-backed generation quality
