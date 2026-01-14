#!/bin/bash
# PostToolUse Hook: TypeScript type-checking after edits
# Runs tsc to check for type errors in modified TypeScript files
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

# Only check TypeScript files
case "$EXT" in
  ts|tsx|mts|cts)
    ;;
  *)
    exit 0
    ;;
esac

# Find tsconfig.json
TSCONFIG=""
SEARCH_DIR=$(dirname "$FILE_PATH")
while [ "$SEARCH_DIR" != "/" ]; do
  if [ -f "$SEARCH_DIR/tsconfig.json" ]; then
    TSCONFIG="$SEARCH_DIR/tsconfig.json"
    break
  fi
  SEARCH_DIR=$(dirname "$SEARCH_DIR")
done

# Run type check
if command -v npx &> /dev/null; then
  if [ -f "node_modules/.bin/tsc" ] || npx tsc --version &> /dev/null 2>&1; then
    # Run tsc in noEmit mode to just check types
    if [ -n "$TSCONFIG" ]; then
      OUTPUT=$(npx tsc --noEmit --pretty 2>&1) || true
    else
      OUTPUT=$(npx tsc --noEmit --pretty "$FILE_PATH" 2>&1) || true
    fi

    # Filter output to only show errors related to this file
    if echo "$OUTPUT" | grep -q "error TS"; then
      # Check if any errors are in our file
      FILE_BASENAME=$(basename "$FILE_PATH")
      if echo "$OUTPUT" | grep -q "$FILE_BASENAME"; then
        echo "TypeScript errors in $FILE_PATH:"
        echo "$OUTPUT" | grep -A2 "$FILE_BASENAME" | head -20
      fi
    else
      echo "TypeScript check passed for $FILE_PATH"
    fi
  fi
fi

exit 0
