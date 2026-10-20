# 내가 만든 스킬

여기 있는 각 폴더가 스킬 하나이고, `install.sh`가 `~/.claude/skills/<이름>`으로 링크한다.
전역이므로 어느 프로젝트에서 세션을 열든 `/<이름>`으로 부를 수 있다.

## 새 스킬 추가

```sh
mkdir -p claude/skills/my-skill
# SKILL.md 작성 (아래 형식)
./install.sh          # 목록을 하드코딩하지 않으므로 이것만 돌리면 잡힌다
```

`SKILL.md` 최소 형식:

```markdown
---
name: my-skill
description: 언제 이 스킬을 써야 하는지. 모델이 이 문장만 보고 발동을 결정한다.
---

실제 지시문.
```

## 주의

`~/.claude/skills/synced/` 는 건드리지 않는다. claude.ai 에서 내려받아 관리하는 영역이라
(morning·docs·pdf·xlsx·pptx·docx·skill-creator·import-memory) 저장소로 끌어오면 동기화와 충돌한다.
그래서 `skills/` 폴더 전체가 아니라 **스킬 폴더를 하나씩** 링크한다.

## 플러그인 스킬을 가져오고 싶을 때

oh-my-claudecode 등의 스킬은 버전 고정 캐시(`plugins/cache/.../<버전>/skills/`)에 있고
업데이트마다 갈아치워진다. 여기로 복사하면 내 것이 되는 대신 **업스트림 개선이 끊긴다.**
그러므로 통째로 옮기지 말고, 매일 쓰게 되어 직접 고쳐야 할 스킬이 생겼을 때 그것만 갈라친다.
