#!/usr/bin/env bash

set -euo pipefail

REPO="${1:-gr8monk3ys/blog-AI}"
MILESTONE_TITLE="Competitive Parity Q2 2026"
MILESTONE_DUE_ON="2026-06-30T23:59:59Z"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

need_cmd gh
need_cmd jq

gh_retry() {
  local tries=0
  until "$@"; do
    tries=$((tries + 1))
    if [[ "$tries" -ge 5 ]]; then
      return 1
    fi
    sleep 2
  done
}

ensure_label() {
  local name="$1"
  local color="$2"
  local description="$3"

  if gh_retry gh api "repos/${REPO}/labels/${name}" >/dev/null 2>&1; then
    return 0
  fi

  gh_retry gh api "repos/${REPO}/labels" \
    -X POST \
    -f name="${name}" \
    -f color="${color}" \
    -f description="${description}" >/dev/null
}

ensure_milestone_number() {
  local number
  number="$(
    gh_retry gh api "repos/${REPO}/milestones?state=all&per_page=100" \
    | jq -r --arg t "${MILESTONE_TITLE}" '.[] | select(.title == $t) | .number' \
    | head -n1
  )"

  if [[ -n "${number}" ]]; then
    echo "${number}"
    return 0
  fi

  gh_retry gh api "repos/${REPO}/milestones" \
    -X POST \
    -f title="${MILESTONE_TITLE}" \
    -f description="Execution of parity roadmap vs Jasper and Copy.ai (workflow, team, enterprise, monetization)." \
    -f due_on="${MILESTONE_DUE_ON}" >/dev/null

  gh_retry gh api "repos/${REPO}/milestones?state=all&per_page=100" \
  | jq -r --arg t "${MILESTONE_TITLE}" '.[] | select(.title == $t) | .number' \
  | head -n1
}

find_issue_number_by_title() {
  local title="$1"
  gh_retry gh api "repos/${REPO}/issues?state=all&per_page=100" \
  | jq -r --arg t "${title}" '.[] | select((.pull_request | not) and .title == $t) | .number' \
  | head -n1
}

create_issue_if_missing() {
  local title="$1"
  local labels_csv="$2"
  local body="$3"
  local milestone_number="$4"

  local existing
  existing="$(find_issue_number_by_title "${title}")"
  if [[ -n "${existing}" ]]; then
    echo "${existing}"
    return 0
  fi

  local -a cmd
  cmd=(
    gh api "repos/${REPO}/issues"
    -X POST
    -f title="${title}"
    -f body="${body}"
    -F milestone="${milestone_number}"
  )

  IFS=',' read -r -a labels <<< "${labels_csv}"
  for label in "${labels[@]}"; do
    cmd+=( -F "labels[]=${label}" )
  done

  gh_retry "${cmd[@]}" | jq -r '.number'
}

ensure_label "parity" "1D76DB" "Competitive parity roadmap and execution"
ensure_label "p0" "B60205" "Highest priority, blocks core outcomes"
ensure_label "p1" "D93F0B" "High priority after p0 blockers"
ensure_label "sprint" "5319E7" "Sprint-scoped implementation task"

MILESTONE_NUMBER="$(ensure_milestone_number)"
if [[ -z "${MILESTONE_NUMBER}" ]]; then
  echo "Failed to resolve milestone number for ${MILESTONE_TITLE}" >&2
  exit 1
fi

EPIC_TITLE="Epic: Competitive parity execution (Q2 2026)"
EPIC_BODY="$(cat <<'EOF'
## Objective
Execute the Q2 2026 roadmap to reach sellable parity on core workflows vs Jasper and Copy.ai.

## Source Plan
- docs/COMPETITIVE-PARITY-GAP-SPRINT-BOARD.md

## Scope
1. Persistence hardening for workflow/team/auth-critical paths
2. Workflow productization in UI
3. Team + business tier monetization activation
4. SEO + citation quality gates in primary generation UX
5. Integration depth expansion
6. Enterprise readiness hardening

## Success Criteria
- All child sprint issues closed
- No in-memory-only storage in P0 critical paths
- Business tier fully sellable with seats/invites/billing
EOF
)"

EPIC_NUMBER="$(create_issue_if_missing "${EPIC_TITLE}" "enhancement,parity,p0" "${EPIC_BODY}" "${MILESTONE_NUMBER}")"

S1_TITLE="Sprint 1 (P0): Persistence hardening for workflow/social/SSO"
S1_BODY="$(cat <<EOF
## Goal
Replace in-memory stores in critical execution/auth paths with durable persistence.

## Why
Parity blockers: workflow, social campaigns/scheduler, and SSO config/session durability.

## Tasks
- Persist workflow definitions/executions (replace route-level in-memory maps)
- Persist social scheduler + campaign state
- Persist SSO runtime/admin configuration/session state
- Add reboot/recovery integration tests for workflow + SSO continuity

## Acceptance Criteria
- No P0 workflow/team auth path uses in-memory-only storage
- Restart test preserves active workflows and auth sessions
- Documentation updated with storage architecture and migration notes

## Parent
Closes as part of #${EPIC_NUMBER}
EOF
)"

S2_TITLE="Sprint 2 (P0): Workflow productization UI + execution history"
S2_BODY="$(cat <<EOF
## Goal
Ship first-class workflow product UX over existing backend capabilities.

## Tasks
- Build /workflows UI (create, execute, status, history, retry, cancel)
- Expose execution artifacts and per-step status timeline
- Add UX around webhook/polling handoff for external orchestrators

## Acceptance Criteria
- Non-technical user can run end-to-end multi-step workflow from UI
- 95%+ runs have traceable status history and execution artifacts
- Error handling + retries are visible and actionable

## Parent
Closes as part of #${EPIC_NUMBER}
EOF
)"

S3_TITLE="Sprint 3 (P0): Team + business tier activation"
S3_BODY="$(cat <<EOF
## Goal
Activate business-tier GTM path (seats/invites/roles/billing) and remove test-only upgrade behavior.

## Tasks
- Enable Business tier in pricing UI and checkout path
- Replace invite-token response shortcut with production invite delivery flow
- Remove direct test-mode tier upgrade behavior from public API paths
- Add end-to-end tests for seat invite/accept/role assignment

## Acceptance Criteria
- Business checkout + seat invite + role assignment work in production
- Tier upgrades require billing-confirmed path
- Team onboarding conversion funnel is measurable end-to-end

## Parent
Closes as part of #${EPIC_NUMBER}
EOF
)"

S4_TITLE="Sprint 4 (P1): SEO + citation quality gates in primary UX"
S4_BODY="$(cat <<EOF
## Goal
Make SEO and citation quality gates first-class in creation flows.

## Tasks
- Integrate /seo/* endpoints directly into blog/remix UX
- Require source/citation visibility for research-mode outputs
- Add score thresholds + repair loop when quality/evidence is below bar

## Acceptance Criteria
- Long-form publish flow exposes SEO + citation checkpoints
- Citation coverage and SEO score are visible in final output UX
- Threshold failures are recoverable via guided fixes

## Parent
Closes as part of #${EPIC_NUMBER}
EOF
)"

S5_TITLE="Sprint 5 (P1): Integration depth expansion + reliability"
S5_BODY="$(cat <<EOF
## Goal
Increase practical integration depth while keeping Zapier as universal fallback.

## Tasks
- Prioritize and add at least 3 high-demand native integrations
- Standardize trigger-input/API-run/webhook callback orchestration model
- Add integration reliability observability (success/failure, retries, latency)

## Acceptance Criteria
- >=3 new integrations production-usable
- Integration error budget + SLOs defined and monitored
- Clear docs for connection setup and troubleshooting

## Parent
Closes as part of #${EPIC_NUMBER}
EOF
)"

S6_TITLE="Sprint 6 (P1): Enterprise readiness hardening"
S6_BODY="$(cat <<EOF
## Goal
Close enterprise trust gaps (SSO lifecycle, governance, auditability, readiness).

## Tasks
- Finalize SSO lifecycle hardening and admin governance controls
- Ensure complete audit logs for team/workflow/admin actions
- Complete enterprise readiness checklist (security/compliance/ops)

## Acceptance Criteria
- Enterprise pilot can onboard via SSO and pass admin/audit acceptance
- Governance and audit controls are test-covered and documented
- Operational runbook exists for incident and access management

## Parent
Closes as part of #${EPIC_NUMBER}
EOF
)"

S1_NUMBER="$(create_issue_if_missing "${S1_TITLE}" "enhancement,parity,p0,sprint" "${S1_BODY}" "${MILESTONE_NUMBER}")"
S2_NUMBER="$(create_issue_if_missing "${S2_TITLE}" "enhancement,parity,p0,sprint" "${S2_BODY}" "${MILESTONE_NUMBER}")"
S3_NUMBER="$(create_issue_if_missing "${S3_TITLE}" "enhancement,parity,p0,sprint" "${S3_BODY}" "${MILESTONE_NUMBER}")"
S4_NUMBER="$(create_issue_if_missing "${S4_TITLE}" "enhancement,parity,p1,sprint" "${S4_BODY}" "${MILESTONE_NUMBER}")"
S5_NUMBER="$(create_issue_if_missing "${S5_TITLE}" "enhancement,parity,p1,sprint" "${S5_BODY}" "${MILESTONE_NUMBER}")"
S6_NUMBER="$(create_issue_if_missing "${S6_TITLE}" "enhancement,parity,p1,sprint" "${S6_BODY}" "${MILESTONE_NUMBER}")"

echo "Created/verified issues in ${REPO}:"
echo "- Epic: #${EPIC_NUMBER}"
echo "- Sprint 1: #${S1_NUMBER}"
echo "- Sprint 2: #${S2_NUMBER}"
echo "- Sprint 3: #${S3_NUMBER}"
echo "- Sprint 4: #${S4_NUMBER}"
echo "- Sprint 5: #${S5_NUMBER}"
echo "- Sprint 6: #${S6_NUMBER}"
