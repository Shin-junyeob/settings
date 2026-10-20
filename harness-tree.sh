#!/usr/bin/env bash
# 이 PC의 Claude 하네스 구조를 실제 파일시스템에서 읽어 그린다.
# 정적 문서가 아니라 매번 현재 상태를 읽으므로 낡지 않는다.
set -uo pipefail

# ~/.local/bin/harness-tree 심링크로 불릴 수 있으므로 실제 스크립트 위치까지 따라간다.
# (macOS 기본 readlink 에는 -f 가 없어 수동으로 푼다.)
self="$0"
while [ -L "$self" ]; do
  link="$(readlink "$self")"
  case "$link" in /*) self="$link";; *) self="$(dirname "$self")/$link";; esac
done
REPO="$(cd "$(dirname "$self")" && pwd)"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
short() { printf '%s' "${1/#$HOME/\~}"; }

# ── 1. 전역 ──────────────────────────────────────────────────────────
echo "전역  $(short "$CLAUDE_DIR")/        — 어느 폴더에서 Claude를 켜든 적용됨"
echo

echo "  [링크] 실체는 이 저장소에 있고 여기엔 이름표만 걸려 있음"
found=0
while IFS= read -r p; do
  target="$(readlink "$p")"
  case "$target" in "$REPO"/*) ;; *) continue;; esac   # 이 저장소를 가리키는 것만
  found=1
  printf '    %-32s -> %s\n' "${p#$CLAUDE_DIR/}" "$(short "$target")"
done < <(find "$CLAUDE_DIR" -maxdepth 2 -type l 2>/dev/null | sort)
[ "$found" = 0 ] && echo "    (없음 — ./install.sh 를 실행하세요)"
echo

echo "  [실물] 기기마다 달라야 해서 저장소에 넣지 않는 것들"
for d in plugins sessions projects history.jsonl daemon.log shell-snapshots telemetry; do
  [ -e "$CLAUDE_DIR/$d" ] && printf '    %s\n' "$d"
done
echo

# ── 2. Developer 트리 ────────────────────────────────────────────────
echo "작업  ~/Developer/        — 프로젝트별 규칙은 각자 폴더 안에"
echo
walk() { # $1=경로  $2=들여쓰기  $3=남은깊이
  [ "$3" -le 0 ] && return
  local entry name mark
  while IFS= read -r entry; do
    name="$(basename "$entry")"
    case "$name" in
      .git|node_modules|.venv|.next|__pycache__|.DS_Store|.omc) continue;;
      .ruff_cache|.pytest_cache|.mypy_cache|dist|build|.github) continue;;
    esac
    mark=""
    [ -d "$entry/.git" ] && mark="  [git 저장소]"
    [ "$entry" = "$REPO" ] && mark="  [git 저장소]  <<< 설정 실체가 여기"
    if [ -d "$entry" ]; then
      printf '%s%s/%s\n' "$2" "$name" "$mark"
      walk "$entry" "  $2" "$(($3 - 1))"
    else
      case "$name" in
        CLAUDE.md) printf '%s%s      <- 이 폴더 이하 전체에 적용되는 규칙\n' "$2" "$name";;
        *) printf '%s%s\n' "$2" "$name";;
      esac
    fi
  done < <(find "$1" -mindepth 1 -maxdepth 1 2>/dev/null | sort)
}
walk "$HOME/Developer" "    " 3
echo

# ── 3. 관련 홈 설정 ──────────────────────────────────────────────────
echo "기타  홈 디렉토리의 관련 설정 (Claude 하네스 밖, 참고용)"
for p in .zshrc .vimrc .local .ollama .config .ssh .env; do
  if [ -e "$HOME/$p" ]; then
    [ -d "$HOME/$p" ] && printf '    ~/%s/\n' "$p" || printf '    ~/%s\n' "$p"
  fi
done
