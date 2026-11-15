#!/usr/bin/env bash
# Backend test stages, shared by `bun run verify:api` / `verify:api:db` and the CI backend jobs,
# so local runs and CI execute the same pytest invocations. Each stage writes a JUnit report
# and prints one VERIFY line via scripts/verify-summary.mjs.
# Usage: scripts/verify-api.sh <stage>...   stages: smoke routes full db
set -euo pipefail
cd "$(dirname "$0")/../apps/api"
mkdir -p reports

run() {
  local name=$1
  shift
  pytest "$@" -q --junitxml="reports/$name.xml"
  node ../../scripts/verify-summary.mjs "$name" "reports/$name.xml"
}

for stage in "$@"; do
  case $stage in
    smoke)
      DEV_MODE=true OPENAI_API_KEY=test run api-smoke \
        tests/test_feature_smoke.py tests/test_routes_health.py
      ;;
    routes)
      (
        export DEV_MODE=true DEV_API_KEY=test-key ENVIRONMENT=development \
          SENTRY_ENVIRONMENT=development RATE_LIMIT_ENABLED=false OPENAI_API_KEY=test
        run api-routes \
          tests/test_routes_blog.py tests/test_routes_book.py tests/test_routes_webhooks.py \
          tests/test_routes_payments.py tests/test_routes_usage.py \
          --cov=app.routes.blog --cov=app.routes.book --cov=app.routes.webhooks \
          --cov=app.routes.payments --cov=app.routes.usage \
          --cov-fail-under=85 --cov-report=xml --cov-report=term-missing
        # Ratchet floor for routes not yet at 85%. Only ever raise it.
        run api-routes-ratchet \
          tests/test_routes_organizations.py tests/test_routes_sso.py \
          tests/test_routes_export.py tests/test_routes_research.py \
          --cov=app.routes.organizations --cov=app.routes.sso \
          --cov=app.routes.export --cov=app.routes.research \
          --cov-fail-under=50 --cov-report=term-missing
      )
      ;;
    full)
      DEV_MODE=true OPENAI_API_KEY=test run api-full
      ;;
    db)
      # Needs a migrated Postgres; CI provides one (see the backend-db-tests job).
      : "${DATABASE_URL:?verify-api.sh db needs DATABASE_URL pointing at a migrated Postgres}"
      DEV_MODE=true OPENAI_API_KEY=test run api-db \
        tests/test_version_service.py tests/test_knowledge_metadata.py \
        tests/test_analytics_neon.py tests/test_quota_usage_db.py
      ;;
    *)
      echo "verify-api.sh: unknown stage '$stage' (smoke|routes|full|db)" >&2
      exit 1
      ;;
  esac
done
