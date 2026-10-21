# settings — Claude 환경 단일 저장소

Claude Code와 관련된 모든 것의 실체를 여기 두고, 전역 경로(`~/.claude/`)에서는
**심볼릭 링크로 접근**한다. 파일 실체가 하나뿐이므로 "저장소 내용 = 실제 동작 중인 설정"이
항상 일치한다.

## 사용법

```sh
./install.sh          # 링크 생성/복구 (새 맥북 세팅 시에도 이것만 실행)
./install.sh --check  # 링크 상태 점검, 변경 없음
harness-tree          # 지금 하네스 구조를 트리로 출력 (어느 폴더에서나)
```

## 구조

| 경로 | 심링크 | 역할 |
|------|--------|------|
| `claude/` | **O** → `~/.claude/` | 전역에서 동작해야 하는 실체 파일 |
| `harness-tree.sh` | **O** → `~/.local/bin/harness-tree` | 현재 구조를 실제 파일시스템에서 읽어 출력 |
| `cmux-mods-pane.sh` | X (cmux 레이아웃 ③이 직접 실행) | mods 허브 자리 지킴이 — 아래 mods 참고 |
| `fonts/<이름>/` | X | 직접 만든 폰트 — 각 폴더의 `README.md`에 적용 방법 |

구조 설명을 **문서로 적어두지 않는다.** 문서는 파일이 바뀌는 순간 낡지만
`harness-tree`는 매번 실제 상태를 읽으므로 틀릴 수 없다.

### `claude/` — 전역 심링크 대상

| 경로 | 역할 |
|------|------|
| `settings.json` | 훅·플러그인·statusLine·model·mods 경로 등 전역 설정 |
| `hooks/guard-dangerous-bash.sh` | 위험 명령어 차단 (PreToolUse/Bash) |
| `hooks/guard-sensitive-files.sh` | 민감 파일 접근 차단 (PreToolUse/Read\|Edit\|Write) |
| `hooks/log-test-failure.sh` | 테스트/빌드 실패 로그 축적 (PostToolUseFailure/Bash) |
| `hooks/notify-stop.sh` | 완료 시 macOS 알림 (Stop) |
| `hooks/check-settings-drift.sh` | 심링크 끊김 감지 (SessionStart) — 정상이면 침묵 |
| `hud/statusline-wrapper.sh` | ponytail 배지 + OMC HUD를 한 상태줄로 합침 |
| `.omc/hud-config.json` | HUD 표시 프리셋 |
| `agents/*.md` | verified-team 에이전트 정의 (5개) |
| `memory/` | 자동 메모리 — 모든 프로젝트가 공유하는 단일 기억 |
| `skills/<이름>/` | 내가 만든 전역 스킬 (`claude/skills/README.md` 참고) |

**스킬은 폴더 전체가 아니라 하나씩 링크한다.** `~/.claude/skills/synced/`는 claude.ai가
내려받아 관리하는 영역이라 저장소로 끌어오면 동기화와 충돌하기 때문이다.
`install.sh`는 `claude/skills/` 아래 있는 것을 **자동으로 집으므로** 스킬을 추가할 때
목록을 고칠 필요가 없고, 저장소에서 스킬을 지우면 남은 끊어진 링크도 걷어낸다.

**메모리를 한 곳으로 모은 이유**: 기본값은 작업 디렉토리마다 따로 쌓는다
(`~/.claude/projects/<경로>/memory/`). 그래서 `project_orbit.md`가 `Developer/` 밑에만 쌓여
정작 `work/orbit`에서 작업할 때는 보이지 않았다. `settings.json`의
`autoMemoryDirectory: "~/.claude/memory"` 로 통합했고, 그 경로가 이 저장소를 가리킨다.
**단 이 저장소는 공개(GitHub `Shin-junyeob/settings`, 2026-10-21~)라 `claude/memory/`는 `.gitignore`로 뺐다 —
기억은 git으로 백업되지 않는다.** 공개 전 기록(메모리 포함)은 비공개 `Shin-junyeob/my-claude-settings`와
로컬 `.git-private/`(`git --git-dir=.git-private` 로 열람)에 남아 있다. 공개 기록은 그 내용을 빼고 새로 시작했다.

에이전트는 **반드시 `~/.claude/agents/`에 있어야** 하위 저장소에서도 인식된다
(`~/Developer/CLAUDE.md`의 "확인된 사실" 참고). 그래서 실체는 여기 두고 링크로 내보낸다.

### 에이전트 5개가 하는 일

**질문마다 "무엇이 이 질문을 닫아주는가(검증기)"를 먼저 정하고, 그 증거를 만들 수 있는
전문가에게 위임하며, 증거가 없으면 답을 지어내지 않고 "미해결 + 이유"를 반환한다.**

`verify-router`가 검증 계층을 고르고 나머지 넷에 위임한다 — `machine-verifier`(pyright·실행·빌드),
`numeric-verifier`(uv+numpy/sympy를 독립 두 경로로), `source-verifier`(1차 출처 2개 교차),
`independent-checker`(로컬 ollama = 다른 가중치 모델의 동의).

규칙은 전부 각 `claude/agents/*.md` 안에 있다. 설계 의도와 v0에서 바뀐 이유는 커밋 `036ef76` 참고.

## mods와 cmux 화면

### 구성

- **mods** — `~/Developer/personal/working_place`(별도 git 저장소, GitHub `Shin-junyeob/working_place`).
  `pane-tools`(`/mods` 허브·메모·테트리스·포켓몬) + `long-run-watch`(긴 명령 예상시간·초과 알림).
  `settings.json`의 `env.CLAUDE_CODE_PLUGIN_DIRS`로 불러와서 파일을 고치면 바로 반영되고 `git push/pull`로 PC끼리 맞춘다.
  새 맥이면 그 저장소의 `bash install.sh` 한 줄로 이 설정이 만들어진다(심링크된 `settings.json`도 지원, `52e3e2a`).
- **cmux 기본 레이아웃** — `~/.config/cmux/cmux.json`의 `orbit-dev`(앱 실행·`cmd+n` 기본값, 그림은 그 파일 맨 위).
  ① `claude agents` | ② 세션 활동 피드(`feed.py`) / ③ mods 허브 | ④ Orbit(`localhost:3000`) / ⑤ 터미널.
  ②는 2026-10-21 `claude agents`에서 피드로 바꿨다 — 다른 PC(tmux)는 `/mods`가 `feedTarget` 패널에 피드를 띄우지만
  cmux에선 그 장치가 없어서 ③처럼 레이아웃 명령으로 고정한다(q로 닫으면 셸이 남으니 다시 띄우려면 명령을 다시 친다).
  ③은 **22줄**(테트리스 판 20 + 테두리 2)에 맞춰 ⑤를 줄였다 — 비율 0.763 / 0.393, 이 맥 창 크기에서 실측(② 13 · ③ 22 · ⑤ 10줄).
  패널을 직접 조절할 땐 `cmux resize-pane --pane <ref> -U|-D --amount <px>`(단위는 픽셀, 그 방향으로 경계를 민다).
  CLI의 `cmux workspace create`는 기본값을 적용하지 않으므로 지금 화면에 적용하려면 `--layout`으로 그 JSON을 넘긴다.
- **③ 허브는 ①에 열린 세션을 따라간다** — `--follow-pane cmux:0`(이 워크스페이스의 0번 패널, working_place `6361812`).
  패널은 번호로 찾는다: `surface:N`은 cmux를 켤 때마다 바뀌지만 레이아웃 순서는 그대로다.
  그래서 ①엔 레이아웃에서 이름을 붙이지 않는다 — 탭 제목이 '열린 세션 이름'이어야 ③이 읽는다.

### 동작 규칙

- ③은 `cmux-mods-pane.sh`가 지킨다: 허브를 띄우고, 닫히면 신호 파일(`~/.claude/pane-tools/mods-slot.signal`)을
  기다렸다 다시 띄운다. **`/mods`는 cmux를 건드리지 않고 신호 파일만 만든다**(`pluginConfigs."pane-tools@inline"`의
  `launcher: command`에 `touch … # {cmd}`). 새로 나누지 않으니 패널이 늘지 않고, 허브가 떠 있는 동안 들어온
  `/mods`는 버린다(안 그러면 닫자마자 다시 열림).
  **허브의 `[ 설정 ]`에서 '띄울 곳'은 바꾸지 말 것** — 거기서 고른 값(`launcher`·`command`·`followPane` 등)은
  `~/.claude/pane-tools/settings.json`에 적히고 `/mods`가 `/config`의 `pluginConfigs`보다 **먼저** 쓴다(working_place `886dc85`).
  바꾸면 위의 신호 파일 방식이 덮여 ③ 고정이 풀린다. 되돌리려면 그 파일에서 해당 키를 지운다.
- **세션 안에서 cmux를 직접 부르지 않는다.** 백그라운드 세션은 Claude 데몬 아래서 돌고, cmux 소켓 기본값 `cmuxOnly`는
  그 데몬을 띄운 패널이 살아 있을 때만 접근을 허락한다. 그 패널이 사라지면 데몬 아래 세션 **전부**의 cmux 명령이
  `Access denied - only processes started inside cmux`로 막힌다(실측). 처음엔 `/mods`가 세션에서 ③ 탭을 직접
  교체했다가 이것 때문에 지금 방식으로 바꿨다. 접근을 넓히는 `allowAll` 류 설정은 같은 사용자의 아무 프로세스나
  터미널에 키를 쳐 넣게 되므로 쓰지 않는다.
- **mods는 세션이 시작할 때만 붙는다.** `CLAUDE_CODE_PLUGIN_DIRS`와 `pluginConfigs`는 프로세스 시작 시점에만 읽히고,
  `/reload-plugins`는 마켓플레이스 플러그인만 다시 읽는다(실측: 8개만 재로드, mods 0). 설정을 바꾼 뒤엔 세션을 새로
  열어야 하고, mods가 붙기 전에 쓴 토큰은 포켓몬에 쌓이지 않는다.
- **허브는 오래 켜 두므로 코드 반영 방식이 다르다.** `hub.py`가 바뀌면 허브가 같은 인자로 스스로 다시 뜨고
  (working_place `818c2dc`), `pokemon.py`는 바뀔 때 다시 읽는다. 그 밖의 모듈(`_pokedata.py`·`memo.py` 등)만
  고쳤다면 `touch …/pane-tools/bin/hub.py`로 허브를 다시 띄울 것 — 안 그러면 옛 코드로 계속 돈다(실측).
  재시작은 파일이 **5초 동안 안 바뀐 뒤**, 새 파일에도 재시작 코드가 있을 때만 한다. working_place는 작업 트리가
  곧 실행 중인 mods라, `git switch main` → `git pull` 사이 3초 동안 옛 `hub.py`(재시작 코드 없음)로 옮겨 타
  갇힌 적이 있다(2026-10-20, 복사본에서 재현·수정 확인). 머지 뒤 받을 땐 `git fetch && git switch -C main origin/main`
  처럼 옛 커밋을 거치지 않는 쪽이 안전하다.
- **동료 그림** — 허브에 PokeAPI 도트를 3줄 크기로 띄운다. 허브가 시작할 때 터미널에 물어 방식을 고른다:
  Kitty 그래픽(cmux — 2026-10-20 질의·눈으로 확인) → Sixel(Windows Terminal·WezTerm, tmux 안에선 그 패널만 passthrough —
  다른 PC에서 추가, working_place `828bd0d`) → 둘 다 아니면 `▀▄` 칸. 컬러/회색은 PC마다
  `~/.claude/pane-tools/settings.json`의 `"sprite"`(포켓몬 모드에서 `c`) — 이 맥은 `color`, 회사 PC는 `gray`.
  그림 파일은 처음 쓸 때 `~/.claude/pane-tools/sprites/`로 받는다(저장소 밖, 런타임).
- **③에 들어오면 영문 자판, 나가면 원래 자판** — 한글 입력기는 자모 하나를 '조합 중'으로 잡아 둬서 단축키를 두 번 눌러야
  했다(프로그램 쪽에선 못 고침). 그래서 허브·포켓몬·테트리스가 터미널 포커스 신호(`ESC[?1004h` → `ESC[I`/`ESC[O`, cmux는
  패널마다 보냄 — 확인함)를 받아 `macism`으로 자판을 바꾼다. 들어오기 전 자판은 `~/.claude/pane-tools/input-source.saved`에
  두고 나갈 때·메모장을 열 때·허브를 닫을 때 되돌린다. `macism`은 `brew install laishulu/homebrew/macism`(작성자 GitHub 릴리스
  바이너리, sha256 고정 — 2026-10-21 설치). 영문 자판 id는 `com.apple.keylayout.ABC`. 한글로 되돌리는 데 0.27초, 영문 0.06초.
  허브를 두 개 띄우면 같은 저장 파일을 두고 서로 자판을 바꿔 엉킨다(시험 중 실측).
- **macOS에서 curses 화면의 반복 글자가 `�`로 깨지면** — cmux의 terminfo(`TERMINFO=/Applications/cmux.app/…`)엔
  `rep`(같은 글자 N번 반복)가 있는데, Homebrew Python이 쓰는 macOS 기본 ncurses 6.0(2015)은 `rep`로 `░` 같은
  여러 바이트 글자를 보낼 때 마지막 바이트만 보낸다(2026-10-20, `script`로 기록: `E2 96 91` → `91 ESC[6b`). 글씨체 문제가
  아니다 — `cmux read-screen`에 U+FFFD로 찍히면 이것. mods는 `memo.py`가 curses 전에 `TERMINFO`를 빼 시스템 설명(rep 없음)을
  쓰게 해 막았다(working_place `8bb3419`). 다른 curses 도구를 cmux에서 돌릴 때도 같은 함정이 있다.
- cmux 0.64의 `new-surface`엔 `--command`가 없다(모르는 옵션을 조용히 무시). GitHub 문서가 설치 버전보다 앞서 있으니
  `cmux <명령> --help`로 설치된 쪽을 확인할 것.

### 고장 시 복구 — 세션들의 cmux 접근이 끊겼을 때

cmux는 '자기 아래에서 시작된 프로세스'만 받아 준다. 원인은 두 가지고, 어느 쪽인지는 `claude daemon status`의
origin(데몬을 띄운 쪽)과 끊긴 세션의 조상(`ps -o ppid=`를 따라 올라가 cmux가 나오나)으로 가린다.

**A. 데몬 자체가 cmux 밖에 묶였다 — 모든 세션이 끊김.** 데몬은 ①의 `claude agents`가 띄워 ①에 묶여 있다.
Mac 재부팅은 데몬도 같이 죽고 ①에서 다시 뜨니 문제없고, ①을 닫거나 Mac은 켜둔 채 cmux 앱만 재시작하면 생긴다.

1. 모든 세션이 쉬는 중인지 확인하고 `claude daemon stop --any` (세션도 함께 종료, 대화는 보존)
2. 살아 있는 ①의 `claude agents`가 새 데몬을 스스로 띄운다 — 확인: `claude daemon status`의 origin
3. 데몬 밖에 고아로 남은 `claude bg-pty-host`는 `kill`
4. **데몬을 내린 뒤엔 죽은 표식을 가진 프로세스에서 `claude`를 부르지 말 것** — 데몬이 없으면 그 프로세스의 환경으로
   새 데몬이 떠서 같은 문제가 반복된다

(2026-10-19 실행·검증: 새 데몬의 부모와 cmux shim이 모두 ①이었고 세션들의 접근이 돌아왔다.)

**B. 데몬은 ①에 그대로인데 예전부터 돌던 세션만 끊김 — Claude CLI 자동 업데이트 뒤.** 업데이트되면 데몬이
`cause=upgrade`로 내려갔다 ①에서 다시 뜨는데(`~/.claude/daemon.log`), 그 전부터 돌던 세션의 `bg-pty-host`는
launchd(1) 밑 고아로 넘겨져 cmux 조상이 끊긴다. 새로 여는 세션은 정상(2026-10-20 실측: 2.1.303 → 2.1.304, 06:42).
데몬은 건드리지 말고 **그 세션만 다시 띄운다** — `claude stop <id>` 뒤 `claude --bg --resume <전체 sessionId>`(새 데몬이
① 환경으로 띄운다, 대화 보존). **`--resume`엔 `claude agents --json`의 `sessionId`(전체, 소문자)를 줄 것** — 짧은 id(`e34434d7`)를
주면 그 세션을 잇지 않고 대화 복사본을 새 id로 만든다(2026-10-20 실측, `f25b6320`이 생김). 자기 자신을 재시작할 땐 세션 안에서 바로 부르지 말고, 분리된 감시 프로세스가 턴이 끝나길
기다렸다 실행한다(로그 `~/Library/Logs/claude-restart-<id>.log`).
**자동 업데이트는 켜 둔다**(2026-10-21 결정) — 끄면 이 끊김은 사라지지만 새 버전을 늦게 받는다. 업데이트는 거의 매일 있어
(10-20 2.1.304, 10-21 2.1.306) 그때마다 B로 그 세션만 다시 띄운다.

**③ 지킴이가 꺼졌을 때**(③에 허브 대신 셸 프롬프트만 보임, 대기 중 Ctrl+C 등): ③에서
`bash ~/Developer/personal/settings/cmux-mods-pane.sh`를 다시 실행한다. 원인 모르게 두 번 꺼져서(2026-10-20·21) 지킴이가
`~/Library/Logs/cmux-mods-pane.log`에 시작·허브 종료 코드·끝난 이유(Ctrl+C / TERM·HUP)를 남긴다 — 또 꺼지면 이것부터 본다.

## 관리하지 않는 것 (의도적 제외)

- `hud/omc-hud.mjs`, `hud/lib/` — oh-my-claudecode 플러그인 정본 템플릿의 복사본.
  플러그인 업데이트마다 낡으므로 `/oh-my-claudecode:hud setup`으로 재생성한다.
- `~/.config/cmux/cmux.json` — cmux 자체 설정이라 여기 두지 않는다. 바꾸기 전엔 `.bak-<시각>` 백업을 남긴다.
- 런타임 상태·캐시·기록 — `.ponytail-active`, `daemon*`, `sessions/`, `projects/`,
  `plugins/`, `history.jsonl`, `shell-snapshots/`, `telemetry/`, `~/.claude/pane-tools/` 등 전부.

## 알아둘 것

**심링크 드리프트** — `settings.json`의 심링크가 실제 파일로 바뀌어 저장소가 낡는 것. Claude Code 자체의 쓰기
(`/model`, `/config` 등)는 **링크를 따라가서 써서 끊지 않는다**(2026-10-19 실측). 끊는 건 `os.replace`·rename으로
파일을 바꿔치기하는 외부 도구다(예: 고치기 전의 working_place `install.sh`).

`check-settings-drift.sh`(SessionStart 훅)가 세션 시작마다 자동으로 잡아낸다. 정상이면
아무 말도 하지 않고, 끊겼을 때만 경고한다.

**경고가 뜨면 `./install.sh`부터 돌리지 말 것.** 드리프트는 그 실제 파일에 저장소가 모르는
변경이 들어있다는 뜻이므로, 먼저 내용을 확인해 저장소에 반영한 뒤 재링크해야 한다.
순서를 바꾸면 그 변경이 사라진다. (자동 복구를 넣지 않은 이유가 이것이다.)

**`.claude/settings.json`에 `bgIsolation: none`을 둔 이유** — 이 저장소는 작업 트리 자체가
실제 배포 상태다(`~/.claude/`의 심링크가 이 경로를 직접 가리킨다). 백그라운드 작업을
워크트리로 격리하면 심링크가 낡은 파일을 가리켜 검증이 무의미해지므로 이 저장소에 한해 끈다.
