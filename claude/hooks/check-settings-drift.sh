#!/usr/bin/env bash
# SessionStart: ~/.claude 의 심링크가 실제 파일로 대체됐는지 검사한다.
# Claude Code 가 settings.json 을 통째로 다시 쓰면(/model, /config 등) 링크가 끊긴다.
# 정상이면 아무것도 출력하지 않는다 — 매 세션 노이즈를 만들지 않기 위해.
set -uo pipefail

# 이 스크립트는 ~/.claude/hooks/ 에 심링크로 걸려 있으므로 실제 위치까지 따라가
# 저장소 경로를 얻는다. (경로를 하드코딩하면 저장소를 옮길 때 조용히 죽는다.)
self="$0"
while [ -L "$self" ]; do
  link="$(readlink "$self")"
  case "$link" in /*) self="$link";; *) self="$(dirname "$self")/$link";; esac
done
REPO="$(cd "$(dirname "$self")/../.." && pwd)"

[ -x "$REPO/install.sh" ] || exit 0

drift="$("$REPO/install.sh" --check 2>/dev/null | grep -v '^ok')"
[ -z "$drift" ] && exit 0

cat <<EOF
[설정 드리프트 감지] ~/.claude 의 일부가 더 이상 settings 저장소를 가리키지 않습니다.

$drift

DRIFT   = 심링크가 실제 파일로 대체됨. 그 파일에는 저장소가 모르는 변경이 들어있습니다.
MISSING = 링크가 아직 없음.

조치: 먼저 해당 파일의 현재 내용을 확인해 저장소($REPO)에 반영한 뒤
      'cd $REPO && ./install.sh' 로 다시 링크하십시오.
      확인 없이 install.sh 를 먼저 돌리면 그 변경이 사라집니다.
EOF
