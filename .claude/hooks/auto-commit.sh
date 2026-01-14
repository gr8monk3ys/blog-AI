#!/bin/bash
# Stop Hook: Auto-commit changes after Claude finishes
# Creates a git commit with a descriptive message when Claude completes edits
#
# Usage: Configure in .claude/settings.json under hooks.Stop
# Note: Only commits if there are staged/unstaged changes

set -e

# Read JSON input from stdin (contains session info)
INPUT=$(cat)

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree &> /dev/null 2>&1; then
  exit 0
fi

# Check if there are any changes
if git diff --quiet && git diff --staged --quiet; then
  # No changes to commit
  exit 0
fi

# Get list of changed files
CHANGED_FILES=$(git diff --name-only && git diff --staged --name-only | sort -u)
FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l | tr -d ' ')

# Determine commit message based on changes
if [ "$FILE_COUNT" -eq 1 ]; then
  FILE_NAME=$(echo "$CHANGED_FILES" | head -1)
  BASE_NAME=$(basename "$FILE_NAME")

  # Determine action type based on git status
  if git diff --name-only --diff-filter=A | grep -q "$FILE_NAME"; then
    ACTION="Add"
  elif git diff --name-only --diff-filter=D | grep -q "$FILE_NAME"; then
    ACTION="Remove"
  else
    ACTION="Update"
  fi

  COMMIT_MSG="$ACTION $BASE_NAME via Claude"
else
  # Multiple files - summarize
  COMMIT_MSG="Update $FILE_COUNT files via Claude"
fi

# Add all changes
git add -A

# Create commit
git commit -m "$COMMIT_MSG

Files changed:
$(echo "$CHANGED_FILES" | head -10)
$([ "$FILE_COUNT" -gt 10 ] && echo "... and $((FILE_COUNT - 10)) more")

Co-Authored-By: Claude <noreply@anthropic.com>" 2>/dev/null || true

echo "Auto-committed: $COMMIT_MSG"
exit 0
