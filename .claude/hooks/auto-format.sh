#!/bin/bash
# PostToolUse Hook: Auto-format files after edits
# Runs prettier/eslint on modified files to maintain code style
#
# Usage: Configure in .claude/settings.json under hooks.PostToolUse
# Matcher: "Write|Edit"

set -e

# Read JSON input from stdin
INPUT=$(cat)

# Extract the file path from the tool input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

# Get file extension
EXT="${FILE_PATH##*.}"

# Define which extensions to format
case "$EXT" in
  js|jsx|ts|tsx|mjs|cjs)
    FORMAT_TYPE="javascript"
    ;;
  json)
    FORMAT_TYPE="json"
    ;;
  css|scss|less)
    FORMAT_TYPE="css"
    ;;
  md|mdx)
    FORMAT_TYPE="markdown"
    ;;
  html|htm)
    FORMAT_TYPE="html"
    ;;
  yml|yaml)
    FORMAT_TYPE="yaml"
    ;;
  *)
    # Unknown extension, skip formatting
    exit 0
    ;;
esac

# Find and run formatter
# Priority: prettier > eslint --fix > biome

# Check for prettier
if command -v npx &> /dev/null; then
  # Check if prettier is available in the project
  if [ -f "node_modules/.bin/prettier" ] || npx prettier --version &> /dev/null 2>&1; then
    npx prettier --write "$FILE_PATH" 2>/dev/null || true
    echo "Formatted $FILE_PATH with prettier"
    exit 0
  fi

  # Check for biome
  if [ -f "node_modules/.bin/biome" ] || npx @biomejs/biome --version &> /dev/null 2>&1; then
    npx @biomejs/biome format --write "$FILE_PATH" 2>/dev/null || true
    echo "Formatted $FILE_PATH with biome"
    exit 0
  fi

  # Check for eslint (JS/TS only)
  if [ "$FORMAT_TYPE" = "javascript" ]; then
    if [ -f "node_modules/.bin/eslint" ] || npx eslint --version &> /dev/null 2>&1; then
      npx eslint --fix "$FILE_PATH" 2>/dev/null || true
      echo "Fixed $FILE_PATH with eslint"
      exit 0
    fi
  fi
fi

# No formatter found, that's okay
exit 0
