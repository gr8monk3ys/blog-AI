#!/bin/bash
# PreToolUse Hook: Validate JSON syntax before writing
# Ensures JSON files have valid syntax before being written
#
# Usage: Configure in .claude/settings.json under hooks.PreToolUse
# Matcher: "Write"

set -e

# Read JSON input from stdin
INPUT=$(cat)

# Extract the file path and content
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Get file extension
EXT="${FILE_PATH##*.}"

# Only validate JSON files
case "$EXT" in
  json)
    ;;
  *)
    exit 0
    ;;
esac

# Validate JSON syntax
if ! echo "$CONTENT" | jq empty 2>/dev/null; then
  # Invalid JSON - block the write
  cat << EOF
{
  "hookSpecificOutput": {
    "permissionDecision": "deny",
    "permissionDecisionReason": "Invalid JSON syntax in '$FILE_PATH'. Please fix the JSON before writing."
  }
}
EOF
  exit 2
fi

# Valid JSON, allow the operation
exit 0
