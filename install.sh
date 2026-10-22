#!/usr/bin/env bash
# Symlink this repo's Claude Code config into ~/.claude/.
#   ./install.sh          링크 생성 (기존 실제 파일은 백업 후 교체)
#   ./install.sh --check  링크 상태만 점검 (변경 없음)
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

PATHS=(
  settings.json
  hooks/guard-dangerous-bash.sh
  hooks/guard-sensitive-files.sh
  hooks/log-test-failure.sh
  hooks/notify-stop.sh
  hooks/check-settings-drift.sh
  hud/statusline-wrapper.sh
  .omc/hud-config.json
  memory
  agents/verify-router.md
  agents/machine-verifier.md
  agents/numeric-verifier.md
  agents/source-verifier.md
  agents/independent-checker.md
  agents/designer-agent.md
)

# 내가 만든 스킬은 개수가 계속 변하므로 하드코딩하지 않고 있는 대로 집는다.
# 스킬 폴더 자체(~/.claude/skills)는 링크하지 않는다 — 그 안의 synced/ 는
# claude.ai 가 내려받아 관리하는 영역이라 저장소로 끌어오면 안 되기 때문.
for d in "$REPO"/claude/skills/*/; do
  [ -d "$d" ] || continue
  PATHS+=("skills/$(basename "$d")")
done

if [ "${1:-}" = "--check" ]; then
  rc=0
  for rel in "${PATHS[@]}"; do
    src="$REPO/claude/$rel" dst="$DEST/$rel"
    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
      echo "ok      $rel"
    elif [ -e "$dst" ]; then
      # Claude Code가 설정 파일을 통째로 다시 쓰면 심링크가 실제 파일로 대체된다.
      echo "DRIFT   $rel (심링크가 아닌 실제 파일 — 내용 확인 후 ./install.sh 재실행)"; rc=1
    else
      echo "MISSING $rel"; rc=1
    fi
  done
  exit $rc
fi

mkdir -p "$REPO/claude/memory"  # 공개 저장소엔 메모리가 없다(.gitignore) — 새 PC에선 빈 폴더로 시작
for rel in "${PATHS[@]}"; do
  src="$REPO/claude/$rel" dst="$DEST/$rel"
  mkdir -p "$(dirname "$dst")"
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    cp -pR "$dst" "$dst.bak-$(date +%Y%m%d-%H%M%S)"   # -R: memory/ 같은 디렉토리 대비
  fi
  ln -sfn "$src" "$dst"
  echo "linked  $rel"
done

# 저장소에서 스킬을 지우면 ~/.claude/skills 에 끊어진 링크가 남는다.
# 깨진 스킬 폴더는 로딩을 꼬이게 하므로 이쪽을 가리키는 죽은 링크만 걷어낸다.
for l in "$DEST"/skills/*; do
  [ -L "$l" ] || continue          # synced/ 같은 실제 폴더는 건드리지 않는다
  [ -e "$l" ] && continue          # 살아있는 링크는 둔다
  case "$(readlink "$l")" in "$REPO"/*) rm "$l"; echo "removed 끊어진 링크 skills/$(basename "$l")";; esac
done

# harness-tree 를 어디서나 실행할 수 있게 PATH 에 올린다.
mkdir -p "$HOME/.local/bin"
ln -sfn "$REPO/harness-tree.sh" "$HOME/.local/bin/harness-tree"
echo "linked  ~/.local/bin/harness-tree"
