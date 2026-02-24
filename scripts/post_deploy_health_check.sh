#!/usr/bin/env bash
set -euo pipefail

APP_URL="${APP_URL:-https://blog-ai.vivancedata.com}"
ROUTES="${ROUTES:-/ /pricing /blog /tool-directory /sitemap.xml}"
LOOKBACK="${LOOKBACK:-1h}"
LOG_LIMIT="${LOG_LIMIT:-200}"
VERCEL_PROJECT="${VERCEL_PROJECT:-blog-ai}"
VERCEL_SCOPE="${VERCEL_SCOPE:-gr8monk3ys-projects}"
FAIL_ON_WARNINGS="${FAIL_ON_WARNINGS:-false}"

failures=0
tmp_response="$(mktemp)"
trap 'rm -f "$tmp_response"' EXIT

vercel_base=(vercel)
if [[ -n "${VERCEL_TOKEN:-}" ]]; then
  vercel_base+=(--token "$VERCEL_TOKEN")
fi
if [[ -n "${VERCEL_SCOPE:-}" ]]; then
  vercel_base+=(--scope "$VERCEL_SCOPE")
fi

log() {
  printf '[health-check] %s\n' "$1"
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
    log "ERROR route=${route} expected=${expected} got=${status}"
    log "response: $(head -c 300 "$tmp_response" | tr '\n' ' ' || true)"
    failures=$((failures + 1))
    return
  fi

  log "OK route=${route} status=${status}"
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
    log "ERROR unable to query vercel logs for level=${level}"
    log "$output"
    failures=$((failures + 1))
    return
  fi

  if grep -q "No logs found" <<<"$output"; then
    log "OK no ${level} logs in the last ${LOOKBACK}"
    return
  fi

  log "FOUND ${level} logs in the last ${LOOKBACK}"
  printf '%s\n' "$output"

  if [[ "$level" == "error" || "$FAIL_ON_WARNINGS" == "true" ]]; then
    failures=$((failures + 1))
  fi
}

log "Checking deployment status for ${APP_URL}"
if ! inspect_output="$("${vercel_base[@]}" inspect "$APP_URL" 2>&1)"; then
  log "ERROR vercel inspect failed"
  log "$inspect_output"
  exit 1
fi
if grep -Eq 'status[[:space:]]+● Ready' <<<"$inspect_output"; then
  log 'OK deployment status is Ready'
else
  log 'ERROR deployment is not Ready'
  printf '%s\n' "$inspect_output"
  failures=$((failures + 1))
fi

log "Checking key routes for ${APP_URL}"
for route in $ROUTES; do
  check_route "$route" 200
done

log "Scanning recent Vercel production logs"
scan_logs error
scan_logs warning

if ((failures > 0)); then
  log "FAILED with ${failures} issue(s)"
  exit 1
fi

log 'PASSED'
