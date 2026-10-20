#!/bin/bash
# Stop hook — macOS desktop notification when Claude finishes responding.
osascript -e 'display notification "응답이 끝났어요" with title "Claude Code"' >/dev/null 2>&1
exit 0
