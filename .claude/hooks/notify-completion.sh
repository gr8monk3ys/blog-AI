#!/bin/bash
# Stop Hook: Send notification when Claude finishes
# Sends a desktop notification when Claude completes a task
#
# Usage: Configure in .claude/settings.json under hooks.Stop

set -e

# Read JSON input from stdin
INPUT=$(cat)

# Extract session info
STOP_REASON=$(echo "$INPUT" | jq -r '.stop_hook_data.stop_reason // "completed"')

# Compose notification message
TITLE="Claude Code"
case "$STOP_REASON" in
  "end_turn")
    MESSAGE="Task completed successfully"
    ;;
  "max_tokens")
    MESSAGE="Reached token limit"
    ;;
  "stop_sequence")
    MESSAGE="Stopped at sequence"
    ;;
  *)
    MESSAGE="Task finished: $STOP_REASON"
    ;;
esac

# Send notification based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  osascript -e "display notification \"$MESSAGE\" with title \"$TITLE\"" 2>/dev/null || true
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # Linux
  if command -v notify-send &> /dev/null; then
    notify-send "$TITLE" "$MESSAGE" 2>/dev/null || true
  fi
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
  # Windows (Git Bash/Cygwin)
  if command -v powershell.exe &> /dev/null; then
    powershell.exe -Command "[System.Windows.Forms.MessageBox]::Show('$MESSAGE','$TITLE')" 2>/dev/null || true
  fi
fi

exit 0
