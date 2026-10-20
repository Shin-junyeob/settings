#!/bin/bash
# PostToolUseFailure hook (matcher: Bash) — when a failed Bash command looks like a
# test/build/lint invocation, save the command + combined stdout/stderr to a
# project-specific log dir so a later auto-mode session can resume with grounding.
# Note: PostToolUseFailure gives a single combined `error` field ("Exit code N\n<output>"),
# not separate stdout/stderr/exit_code fields.
input=$(cat)
command=$(echo "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))' 2>/dev/null)
error=$(echo "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("error", ""))' 2>/dev/null)
cwd=$(echo "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("cwd", ""))' 2>/dev/null)

[ -z "$command" ] && exit 0

if ! echo "$command" | grep -qEi '\b(npm|yarn|pnpm|bun)[[:space:]]+(run[[:space:]]+)?(test|build|lint)\b|\bpytest\b|\bpython[0-9]?[[:space:]]+-m[[:space:]]+pytest\b|\bgo[[:space:]]+(test|build|vet)\b|\bcargo[[:space:]]+(test|build|check)\b|\bmake([[:space:]]+(test|build|check))?\b|\b(mvn|mvnw)\b.*(test|package|install|verify|compile)\b|\b(gradle|gradlew)\b.*(test|build|check)\b|\bjest\b|\bvitest\b|\bmocha\b|\brspec\b|\bdotnet[[:space:]]+(test|build)\b|\btox\b|\brake[[:space:]]+test\b|\bctest\b|\bphpunit\b'; then
  exit 0
fi

sanitized=$(echo "$cwd" | sed 's/\//-/g')
log_dir="$HOME/.claude/projects/${sanitized}/logs/test-failures"
mkdir -p "$log_dir" 2>/dev/null || exit 0

timestamp=$(date "+%Y%m%d-%H%M%S")
log_file="$log_dir/${timestamp}.log"

{
  echo "timestamp: $(date -Iseconds)"
  echo "cwd: $cwd"
  echo "command: $command"
  echo "---"
  echo "$error"
} > "$log_file" 2>/dev/null

exit 0
