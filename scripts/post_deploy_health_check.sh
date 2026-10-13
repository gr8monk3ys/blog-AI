#!/usr/bin/env bash
# Logging rule: this runs in a public CI log. Print status codes, route paths and
# the aggregate health fields only -- never response bodies, Vercel log lines
# verbatim, headers, or anything derived from VERCEL_TOKEN. No `set -x`.
set -euo pipefail

APP_URL="${APP_URL:-https://blog-ai.vivancedata.com}"
ROUTES="${ROUTES:-/ /pricing /blog /tool-directory /sitemap.xml}"
# The web app's own dependency report (apps/web/app/api/health/route.ts): 200
# unless a configured dependency (database, FastAPI backend, Clerk) is down,
# then 503. Set HEALTH_ROUTE= (empty) to skip it.
HEALTH_ROUTE="${HEALTH_ROUTE-/api/health}"
LOOKBACK="${LOOKBACK:-1h}"
LOG_LIMIT="${LOG_LIMIT:-200}"
VERCEL_PROJECT="${VERCEL_PROJECT:-blog-ai}"
VERCEL_SCOPE="${VERCEL_SCOPE:-}"
FAIL_ON_WARNINGS="${FAIL_ON_WARNINGS:-false}"
USE_BUNX_VERCEL="${USE_BUNX_VERCEL:-false}"
vercel_checks_enabled=false
vercel_base=()

failures=0
tmp_response="$(mktemp)"
trap 'rm -f "$tmp_response"' EXIT

if [[ "$USE_BUNX_VERCEL" == "true" && -n "${VERCEL_TOKEN:-}" ]]; then
  vercel_checks_enabled=true
  vercel_base=(bunx vercel@50.13.2)
elif command -v vercel >/dev/null 2>&1; then
  vercel_checks_enabled=true
  vercel_base=(vercel)
fi
if [[ -n "${VERCEL_TOKEN:-}" ]]; then
  vercel_base+=(--token "$VERCEL_TOKEN")
fi
if [[ -n "${VERCEL_SCOPE:-}" ]]; then
  vercel_base+=(--scope "$VERCEL_SCOPE")
fi

log() {
  printf '[health-check] %s\n' "$1"
}

warn() {
  printf '[health-check] WARNING %s\n' "$1"
}

check_route() {
  local route="$1"
  local expected="$2"
  local url="${APP_URL}${route}"
  local status

  if ! status="$(
    curl \
      --silent \
      --show-error \
      --location \
      --max-time 20 \
      --output "$tmp_response" \
      --write-out '%{http_code}' \
      "$url"
  )"; then
    log "ERROR route=${route} request failed"
    failures=$((failures + 1))
    return
  fi

  if [[ "$status" != "$expected" ]]; then
    log "ERROR route=${route} expected=${expected} got=${status} bytes=$(wc -c <"$tmp_response" | tr -d ' ')"
    failures=$((failures + 1))
    return
  fi

  log "OK route=${route} status=${status}"
}

# Pull one string field out of the /api/health JSON without jq. Only the
# aggregate fields (status words, version, commit) are ever read this way; the
# body itself is never printed. Values are reduced to a safe character set.
json_field() {
  local key="$1"
  tr -d '\n ' <"$tmp_response" \
    | grep -oE "\"${key}\":\"[^\"]*\"" | head -n1 \
    | sed -E 's/^"[^"]*":"//; s/"$//' | tr -cd 'A-Za-z0-9._-' | head -c 64 || true
}

# status word of one entry under "checks" (db / api / clerk).
check_status() {
  local name="$1"
  tr -d '\n ' <"$tmp_response" \
    | grep -oE "\"${name}\":\{\"status\":\"[a-z]+\"" | head -n1 \
    | sed -E 's/.*"status":"//; s/"$//' || true
}

check_health_endpoint() {
  local url="${APP_URL}${HEALTH_ROUTE}"
  local status

  if ! status="$(
    curl \
      --silent \
      --show-error \
      --max-time 20 \
      --header 'Accept: application/json' \
      --output "$tmp_response" \
      --write-out '%{http_code}' \
      "$url"
  )"; then
    log "ERROR route=${HEALTH_ROUTE} request failed"
    failures=$((failures + 1))
    return
  fi

  local summary
  summary="health=$(json_field status) version=$(json_field version) commit=$(json_field commit)"
  summary+=" db=$(check_status db) api=$(check_status api) clerk=$(check_status clerk)"
  if [[ "$status" != "200" ]]; then
    log "ERROR route=${HEALTH_ROUTE} expected=200 got=${status} ${summary}"
    failures=$((failures + 1))
    return
  fi

  log "OK route=${HEALTH_ROUTE} status=${status} ${summary}"
}

scan_logs() {
  local level="$1"
  local output
  local cmd=(
    "${vercel_base[@]}"
    logs
    --environment production
    --no-branch
    --since "$LOOKBACK"
    --level "$level"
    --no-follow
    --limit "$LOG_LIMIT"
  )

  if [[ -n "${VERCEL_PROJECT:-}" ]]; then
    cmd+=(--project "$VERCEL_PROJECT")
  fi

  if ! output="$("${cmd[@]}" 2>&1)"; then
    # The CLI's error text can echo its arguments; report the failure, not the text.
    log "ERROR unable to query vercel logs for level=${level} (vercel logs exited non-zero)"
    failures=$((failures + 1))
    return
  fi

  if grep -q "No logs found" <<<"$output"; then
    log "OK no ${level} logs in the last ${LOOKBACK}"
    return
  fi

  # Log lines can carry request URLs, headers and error payloads: count them
  # and point at the dashboard instead of reprinting them into a public CI log.
  local count
  count="$(grep -c . <<<"$output" || true)"
  log "FOUND ${level} logs in the last ${LOOKBACK}: ${count} line(s). Inspect with: vercel logs --environment production --level ${level} --since ${LOOKBACK} --project ${VERCEL_PROJECT}"

  if [[ "$level" == "error" || "$FAIL_ON_WARNINGS" == "true" ]]; then
    failures=$((failures + 1))
  fi
}

log "Checking deployment status for ${APP_URL}"
if [[ "$vercel_checks_enabled" == "true" ]]; then
  if ! inspect_output="$("${vercel_base[@]}" inspect "$APP_URL" 2>&1)"; then
    warn 'Skipping Vercel deployment inspection and log scans: vercel inspect failed.'
    vercel_checks_enabled=false
  elif grep -Eq 'status[[:space:]]+● Ready' <<<"$inspect_output"; then
    log 'OK deployment status is Ready'
  else
    # Print the status line only, not the whole inspect dump.
    log "ERROR deployment is not Ready: $(grep -E '^[[:space:]]*status' <<<"$inspect_output" | head -n1 | tr -s ' ' || true)"
    failures=$((failures + 1))
  fi
else
  warn 'Skipping Vercel deployment inspection and log scans: Vercel CLI is not configured for this run.'
fi

log "Checking key routes for ${APP_URL}"
for route in $ROUTES; do
  check_route "$route" 200
done

if [[ -n "$HEALTH_ROUTE" ]]; then
  log "Checking dependency health at ${APP_URL}${HEALTH_ROUTE}"
  check_health_endpoint
fi

if [[ "$vercel_checks_enabled" == "true" ]]; then
  log "Scanning recent Vercel production logs"
  scan_logs error
  scan_logs warning
fi

if ((failures > 0)); then
  log "FAILED with ${failures} issue(s)"
  exit 1
fi

log 'PASSED'
