#!/bin/bash
# PreToolUse hook (matcher: Bash) — blocks destructive shell commands.
input=$(cat)
command=$(echo "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))' 2>/dev/null)

if echo "$command" | grep -qE 'rm[[:space:]]+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)[[:space:]]+(/|~)([[:space:]]|$)'; then
  echo "차단됨: 홈/루트 디렉토리 대상 rm -rf 로 보입니다. 경로를 다시 확인하세요." >&2
  exit 2
fi
# 강제 push 는 셸처럼 토큰으로 나눠 '그 git push 명령' 안에서만 본다(2026-11-05). 정규식 '.*' 는 뒤에 이어 붙인
# 'pgrep -f' 까지 막았고, '[^;&|]*' 로 좁히자 '2>&1' 의 & 에서 멈춰 'git push 2>&1 --force' 가 빠져나갔다(보안 검토).
# 그래서 진짜 제어 연산자(; && || | &)에서만 끊고, --force · --force-with-lease · f 가 든 짧은 옵션 · +refspec 을 막는다.
# 따옴표가 안 맞아 나눌 수 없으면 예전처럼 넓게 막는다.
force_push=$(printf '%s' "$command" | python3 -c '
import re, shlex, sys
cmd = sys.stdin.read().replace("\\\n", "")  # 줄 끝 \ 이어 쓰기는 한 줄로(보안 검토 2)
BROAD = re.compile(r"push.*(--force|--mirror|\s-[a-zA-Z]*f|\s\+\S)", re.S)  # 문자열 안 명령·나눌 수 없을 때 쓰는 넓은 검사
try:
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace = " \t\r"  # 줄바꿈은 명령 구분으로 남긴다
    lex.commenters = ""  # # 를 주석으로 보면 뒤의 --force 를 놓친다(보안 검토 1)
    lex.wordchars += "+:@%^,{}"  # +main:main 같은 refspec 을 한 낱말로
    toks = list(lex)
except ValueError:
    print("1" if re.search(r"git\s+" + BROAD.pattern, cmd, re.S) else "0")
    sys.exit()
segs, cur = [], []
for t in toks:
    if t in (";", "&&", "||", "|", "&", "|&", "\n", ";;"):
        segs.append(cur); cur = []
    else:
        cur.append(t)
segs.append(cur)
DANGER_LONG = ("--force", "--force-with-lease", "--force-if-includes", "--mirror")
def flag_forced(a):
    long_ = a.split("=", 1)[0]
    # git 은 긴 옵션을 앞부분만 써도 받는다(--mirr = --mirror) — 위험한 긴 옵션의 앞부분이면 막는다(보안 검토)
    if long_.startswith("--") and len(long_) > 3 and any(d.startswith(long_) or long_.startswith(d) for d in DANGER_LONG):
        return True
    return bool(re.fullmatch(r"-[a-zA-Z]+", a) and "f" in a) or (a.startswith("+") and len(a) > 1)
CONFIG_PUSH = re.compile(r"remote\.[^\s=]*\.(push|mirror)|GIT_CONFIG_(COUNT|KEY|VALUE|PARAMETERS)|--config-env", re.I)
def forced(seg):
    names = [t.rsplit("/", 1)[-1] for t in seg]
    # 어느 자리든 git 이 든 문자열이 강제 push 꼴이면 막는다(eval · bash -c · xargs 안 · 따옴표 안 — 보안 검토)
    if any("git" in t and " " in t and BROAD.search(t) for t in seg):
        return True
    # 원격의 push·mirror 설정을 바꾸는 것(git config · -c · --config-env · GIT_CONFIG_*)도 강제 push 로 본다
    if any(CONFIG_PUSH.search(t) for t in seg) and ("git" in names or any(t.startswith("GIT_CONFIG") for t in seg)):
        return True
    gi = next((k for k, n in enumerate(names) if n == "git" or "$" in seg[k] or "`" in seg[k]), None)
    if gi is None:
        return False
    rest = seg[gi + 1:]
    if "push" in rest:
        return any(flag_forced(a) for a in rest[rest.index("push") + 1:] if a != "--")
    # 하위 명령을 변수·치환으로 감추면($cmd · `…`) push 가 안 보여도 강제 옵션만으로 막는다
    if any("$" in t or "`" in t for t in seg[gi:]):
        return any(flag_forced(a) for a in rest if a != "--")
    return False
print("1" if any(forced(s) for s in segs) else "0")
' 2>/dev/null)
if [ "$force_push" = "1" ]; then
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
