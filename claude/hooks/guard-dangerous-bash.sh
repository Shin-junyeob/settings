#!/bin/bash
# PreToolUse hook (matcher: Bash) — blocks destructive shell commands.
input=$(cat)
command=$(echo "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))' 2>/dev/null)

if echo "$command" | grep -qE 'rm[[:space:]]+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)[[:space:]]+(/|~)([[:space:]]|$)'; then
  echo "차단됨: 홈/루트 디렉토리 대상 rm -rf 로 보입니다. 경로를 다시 확인하세요." >&2
  exit 2
fi
if echo "$command" | grep -qE 'git[[:space:]]+push.*(--force|-f)([[:space:]]|$)'; then
  echo "차단됨: git push --force 는 원격 히스토리를 덮어씁니다. 정말 필요하면 사용자가 직접 실행하세요." >&2
  exit 2
fi
if echo "$command" | grep -qE 'git[[:space:]]+reset[[:space:]]+--hard'; then
  echo "차단됨: git reset --hard 는 커밋되지 않은 변경사항을 삭제합니다." >&2
  exit 2
fi
if echo "$command" | grep -qE 'dd[[:space:]]+if=|mkfs(\.|[[:space:]])'; then
  echo "차단됨: 디스크를 직접 조작하는 명령입니다." >&2
  exit 2
fi
if echo "$command" | grep -qE 'chmod[[:space:]]+-R[[:space:]]+777[[:space:]]+/'; then
  echo "차단됨: 루트 경로에 대한 재귀적 777 권한 변경입니다." >&2
  exit 2
fi
if echo "$command" | grep -qE 'sudo[[:space:]]+rm'; then
  echo "차단됨: sudo rm 명령입니다. 필요하면 사용자가 직접 실행하세요." >&2
  exit 2
fi

exit 0
