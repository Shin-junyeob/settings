#!/bin/bash
# PreToolUse hook (matcher: Read|Edit|Write) — blocks access to sensitive files.
input=$(cat)
file_path=$(echo "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input", {}).get("file_path", ""))' 2>/dev/null)

if [ -z "$file_path" ]; then
  exit 0
fi

if echo "$file_path" | grep -qE '\.ssh/id_(ed25519|rsa|ecdsa|dsa)$'; then
  echo "차단됨: SSH 개인키 파일 접근은 허용되지 않습니다." >&2
  exit 2
fi
if echo "$file_path" | grep -qE '(^|/)\.env(\.[^/]*)?$'; then
  echo "차단됨: .env 계열 파일 접근은 허용되지 않습니다 (민감 정보 보호)." >&2
  exit 2
fi
if echo "$file_path" | grep -qiE '(credentials|secret)'; then
  echo "차단됨: credentials/secret 관련 파일 접근은 허용되지 않습니다." >&2
  exit 2
fi
if echo "$file_path" | grep -qE '\.(pem|key)$'; then
  echo "차단됨: 키/인증서 파일(.pem/.key) 접근은 허용되지 않습니다." >&2
  exit 2
fi

exit 0
