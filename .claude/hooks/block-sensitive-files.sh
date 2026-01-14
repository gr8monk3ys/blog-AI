#!/bin/bash
# PreToolUse Hook: Block modifications to sensitive files
# Prevents accidental edits to .env, secrets, credentials, and other sensitive files
#
# Usage: Configure in .claude/settings.json under hooks.PreToolUse
# Matcher: "Write|Edit"

set -e

# Read JSON input from stdin
INPUT=$(cat)

# Extract the file path from the tool input
# For Write tool: input.file_path
# For Edit tool: input.file_path
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  # No file path, allow the operation
  exit 0
fi

# Sensitive file patterns to block
SENSITIVE_PATTERNS=(
  "\.env$"
  "\.env\..*"
  "secrets\."
  "credentials\."
  "\.pem$"
  "\.key$"
  "\.p12$"
  "\.pfx$"
  "id_rsa"
  "id_ed25519"
  "\.aws/credentials"
  "\.ssh/"
  "firebase.*\.json$"
  "serviceAccount.*\.json$"
  "google-credentials\.json$"
  "\.npmrc$"
  "\.pypirc$"
  "token\.json$"
)

# Check if file matches any sensitive pattern
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
  if echo "$FILE_PATH" | grep -qE "$pattern"; then
    # Output JSON decision to deny
    cat << EOF
{
  "hookSpecificOutput": {
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: '$FILE_PATH' matches sensitive file pattern '$pattern'. This file may contain secrets or credentials. Please modify it manually if needed."
  }
}
EOF
    exit 2
  fi
done

# Allow the operation
exit 0
