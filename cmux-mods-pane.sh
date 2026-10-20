#!/usr/bin/env bash
# cmux 레이아웃의 ③ 패널에서 도는 mods 허브 자리. 허브를 띄우고, 닫히면 /mods 신호를 기다렸다가 다시 띄운다.
#
# /mods 는 cmux 를 직접 건드리지 않고 신호 파일만 만든다. 백그라운드 세션은 Claude 데몬의 환경을 물려받는데,
# cmux(socketControlMode=cmuxOnly)는 그 데몬이 시작된 탭이 닫히면 데몬 아래 세션 전부를 'cmux 밖'으로 보고
# 소켓 접근을 막는다(2026-10-19 실측). 그래서 cmux 일은 cmux 안에서 도는 이 스크립트가 한다.
# 허브는 ① 패널에 열린 세션을 따라간다(--follow-pane cmux:0 = 이 워크스페이스의 0번 패널).
HUB="$HOME/Developer/personal/working_place/pane-tools/bin/hub.py"
SIG="$HOME/.claude/pane-tools/mods-slot.signal"
mkdir -p "$(dirname "$SIG")"
while :; do
  python3 "$HUB" --follow-pane cmux:0
  # 허브가 떠 있는 동안 들어온 /mods 는 버린다 — 안 그러면 닫자마자 다시 열린다
  rm -f "$SIG"
  clear
  echo "mods 허브를 닫았습니다 — Claude 에서 /mods 를 입력하면 여기에 다시 뜹니다. (Ctrl+C: 이 자리 끝내기)"
  until [ -e "$SIG" ]; do sleep 1; done
done
