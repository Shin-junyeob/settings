#!/usr/bin/env bash
# cmux 레이아웃의 ③ 패널에서 도는 mods 허브 자리. 허브를 띄우고, 닫히면 /mods 신호를 기다렸다가 다시 띄운다.
#
# /mods 는 cmux 를 직접 건드리지 않고 신호 파일만 만든다. 백그라운드 세션은 Claude 데몬의 환경을 물려받는데,
# cmux(socketControlMode=cmuxOnly)는 그 데몬이 시작된 탭이 닫히면 데몬 아래 세션 전부를 'cmux 밖'으로 보고
# 소켓 접근을 막는다(2026-10-19 실측). 그래서 cmux 일은 cmux 안에서 도는 이 스크립트가 한다.
# 허브는 ① 패널에 열린 세션을 따라간다(--follow-pane cmux:0 = 이 워크스페이스의 0번 패널).
HUB="$HOME/Developer/personal/working_place/pane-tools/bin/hub.py"
SIG="$HOME/.claude/pane-tools/mods-slot.signal"
# 이 자리가 원인 모르게 두 번 꺼졌다(2026-10-20·21, ③ 에 셸만 남음) — 다음엔 왜인지 보이게 시작·허브 종료·끝난 이유를 적는다
LOG="$HOME/Library/Logs/cmux-mods-pane.log"
log() { echo "$(date '+%F %T') [$$] $*" >> "$LOG"; }
# Ctrl+C 한 번에 이 자리가 꺼져 /mods 가 안 먹었다(2026-10-28 00:07·00:13 — 닫힌 화면의 안내 문구를 보고 누름).
# 실수로 눌러도 버티게 한 번은 무시하고 적어 두며, 3초 안에 두 번 눌러야 끝낸다
on_int() {
  local now; now=$(date +%s)
  if (( now - ${LAST_INT:-0} <= 3 )); then log "끝남 — Ctrl+C 두 번"; exit 130; fi
  LAST_INT=$now
  log "Ctrl+C 한 번 — 무시(3초 안에 한 번 더 누르면 끝)"
}
trap on_int INT
trap 'log "끝남 — 신호 TERM/HUP"; exit 143' TERM HUP
trap 'log "종료 (exit $?)"' EXIT
log "시작"
mkdir -p "$(dirname "$SIG")"
while :; do
  python3 "$HUB" --follow-pane cmux:0
  log "허브 종료 (exit $?)"
  # 허브가 떠 있는 동안 들어온 /mods 는 버린다 — 안 그러면 닫자마자 다시 열린다
  rm -f "$SIG"
  clear
  # Ctrl+C 는 안내하지 않는다 — '(Ctrl+C: 이 자리 끝내기)'를 해야 할 일로 읽고 눌러서 이 자리가 꺼졌다(2026-10-28)
  echo "mods 허브를 닫았습니다 — Claude 에서 /mods 를 입력하면 여기에 다시 뜹니다."
  until [ -e "$SIG" ]; do sleep 1; done
done
