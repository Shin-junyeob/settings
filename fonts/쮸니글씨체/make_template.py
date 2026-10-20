"""손글씨 폰트 템플릿 PDF + 셀 좌표 manifest 생성.

실행: uv run --no-project --with reportlab python -I make_template.py
출력: out/template.pdf, out/template.json (좌표 단위 mm, 원점은 페이지 왼쪽 위)

template.json은 나중에 글씨를 칸별로 잘라낼 때 쓰는 유일한 좌표 기준이다.
글씨를 쓰기 시작한 뒤에는 레이아웃 상수를 바꾸지 말 것.
"""

import json
import re
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent
SLICES = ROOT / "data/gf-slices/korean_default.txt"  # googlefonts/nam-files, 웹 사용 빈도순
FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"

PAGE_W, PAGE_H = 210, 297
LEFT, TOP = 10, 24
COLS, ROWS = 10, 10
PITCH_X, PITCH_Y = 19, 26
LABEL_H, BOX = 6, 18
LINE_W = PITCH_X * (COLS - 1) + BOX
MARKER = 4  # 네 모서리 정합용 검은 사각형 (스크린샷으로 받아도 페이지를 맞출 수 있게)
MARKERS = [(4, 4), (PAGE_W - 8, 4), (4, PAGE_H - 8), (PAGE_W - 8, PAGE_H - 8)]
# 칸 높이 대비 비율(위에서부터): 대문자 높이, 소문자 높이, 기준선, 아래로 내려가는 획
LATIN_GUIDES = {"cap": 0.15, "xheight": 0.42, "baseline": 0.70, "descender": 0.92}

HINTS = {
    "`": "백틱", "'": "곧은", '"': "곧은", "‘": "여는", "’": "닫는", "“": "여는", "”": "닫는",
    "·": "가운뎃점", ".": "마침표", ",": "쉼표", "-": "하이픈", "_": "밑줄", "|": "세로선",
    "l": "소문자 엘", "I": "대문자 아이", "O": "대문자 오", "0": "숫자 영", "1": "숫자 일",
}

ENGLISH = [
    "The quick brown fox",
    "jumps over the lazy dog",
    "PACK MY BOX WITH FIVE",
    "DOZEN LIQUOR JUGS",
    "Hamburgefonstiv",
    "minimum illicit fluffy",
    "AVATAR WAVE Type Yes To",
    "rhythm quickly zebra exact",
    "Hello, world! (Orbit)",
    "2026-10-12 $1,234.50 100%",
]
KOREAN = [
    "다람쥐 헌 쳇바퀴에 타고파",
    "동해물과 백두산이 마르고",
    "빠른 갈색 여우가 뛰어넘는다",
    "안녕하세요! 반갑습니다.",
    "오늘은 2026년 10월 12일",
    "Orbit을 켰다, 잘 된다!",
]


def hangul_tiers():
    blocks = SLICES.read_text(encoding="utf-8").split("subsets {")[1:]
    slices = [[int(c) for c in re.findall(r"codepoints:\s*(\d+)", b)] for b in blocks]
    # 파일은 낮은 우선순위부터 적혀 있다 — 마지막 20개가 빈도 상위 2,000자(100자씩)
    freq = [[chr(c) for c in s if 0xAC00 <= c <= 0xD7A3] for s in reversed(slices[-20:])]
    tier1 = sum(freq[:8], [])
    tier2 = sum(freq[8:], [])
    ksx1001 = [bytes([a, b]).decode("euc_kr") for a in range(0xB0, 0xC9) for b in range(0xA1, 0xFF)]
    seen = set(tier1 + tier2)
    tier3 = [c for c in ksx1001 if c not in seen]
    assert len(ksx1001) == 2350 and set(ksx1001) <= seen | set(tier3)
    return tier1, tier2, tier3


def sections():
    upper = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    lower = [chr(c) for c in range(ord("a"), ord("z") + 1)]
    punct = [chr(c) for c in range(33, 127) if not chr(c).isalnum()]
    consonants = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
    vowels = [chr(c) for c in range(0x314F, 0x3164)]
    t1, t2, t3 = hangul_tiers()
    latin_note = "빨간 선이 기준선. 대문자는 맨 위 선까지, 소문자 몸통은 가운데 선까지, g·y 꼬리는 맨 아래 선까지."
    hangul_note = "칸 가운데에, 칸의 80% 정도 크기로. 평소 쓰는 글씨체 그대로."
    return [
        dict(title="1. 알파벳", note=latin_note, guide="latin", kind="char", groups=[upper, lower]),
        dict(title="2. 숫자·기호", note=latin_note, guide="latin", kind="char",
             groups=[list("0123456789"), punct, list("‘’“”…·")]),
        dict(title="3. 영단어", note="위에 적힌 글을 평소 속도로 한 줄에. 글자 사이 간격을 재는 데 쓴다.",
             guide="latin", kind="line", groups=[ENGLISH]),
        dict(title="4. 한글·혼합 문장", note="한글과 영문·숫자의 크기 비율과 띄어쓰기 폭을 재는 데 쓴다.",
             guide="latin", kind="line", groups=[KOREAN]),
        dict(title="5. 한글 자모", note=hangul_note, guide="hangul", kind="char", groups=[consonants, vowels]),
        dict(title="6. 한글 1단계 (필수)", note=hangul_note, guide="hangul", kind="char", groups=[t1]),
        dict(title="7. 한글 2단계 (권장)", note=hangul_note, guide="hangul", kind="char", groups=[t2]),
        dict(title="8. 한글 3단계 (선택)", note=hangul_note, guide="hangul", kind="char", groups=[t3]),
    ]


def paginate(secs):
    """각 칸을 (페이지, 좌표)에 배치한다. 그룹은 새 줄에서, 섹션은 새 페이지에서 시작."""
    pages = []
    for sec in secs:
        cols = COLS if sec["kind"] == "char" else 1
        width = BOX if sec["kind"] == "char" else LINE_W
        cells, row = [], 0
        for group in sec["groups"]:
            for i, text in enumerate(group):
                if row == ROWS:
                    pages.append((sec, cells))
                    cells, row = [], 0
                cells.append(dict(text=text, x=LEFT + PITCH_X * (i % cols), y=TOP + PITCH_Y * row + LABEL_H,
                                  w=width, h=BOX))
                if i % cols == cols - 1 or i == len(group) - 1:
                    row += 1
        pages.append((sec, cells))
    return pages


def draw(pages, path):
    pdfmetrics.registerFont(TTFont("KR", FONT_PATH))
    glyphs = pdfmetrics.getFont("KR").face.charToGlyph
    c = canvas.Canvas(str(path), pagesize=(PAGE_W * mm, PAGE_H * mm))
    c.setTitle("손글씨 폰트 템플릿")
    y_ = lambda y: (PAGE_H - y) * mm  # 위쪽 원점 mm → PDF 좌표

    def hline(x, y, w):
        c.line(x * mm, y_(y), (x + w) * mm, y_(y))

    for n, (sec, cells) in enumerate(pages, 1):
        c.setFillGray(0)
        for mx, my in MARKERS:
            c.rect(mx * mm, y_(my + MARKER), MARKER * mm, MARKER * mm, stroke=0, fill=1)
        c.setFont("KR", 13)
        c.drawString(LEFT * mm, y_(14), sec["title"])
        c.drawRightString((PAGE_W - LEFT) * mm, y_(14), f"{n} / {len(pages)}")
        c.setFillGray(0.4)
        c.setFont("KR", 7.5)
        c.drawString(LEFT * mm, y_(20), sec["note"] + "  검은색 펜으로, 칸 밖으로 나가지 않게.")
        c.setLineWidth(0.4)
        for cell in cells:
            x, y, w, h = cell["x"], cell["y"], cell["w"], cell["h"]
            assert all(ord(ch) in glyphs for ch in cell["text"] if ch != " "), cell["text"]
            c.setFillGray(0.3)
            c.setFont("KR", 10)
            c.drawString(x * mm, y_(y - 1.6), cell["text"])
            if cell["text"] in HINTS:
                c.setFont("KR", 5.5)
                c.drawString((x + 5) * mm, y_(y - 1.6), HINTS[cell["text"]])
            # 안내선은 연한 색 — 검은 글씨와 색으로도 구분되게
            c.setStrokeColorRGB(0.72, 0.82, 1.0)
            c.setDash()
            c.rect(x * mm, y_(y + h), w * mm, h * mm)
            c.setDash(1, 2)
            if sec["guide"] == "hangul":
                hline(x, y + h / 2, w)
                c.line((x + w / 2) * mm, y_(y), (x + w / 2) * mm, y_(y + h))
            else:
                for name, frac in LATIN_GUIDES.items():
                    if name == "baseline":
                        c.setStrokeColorRGB(1.0, 0.6, 0.6)
                        c.setDash()
                    hline(x, y + h * frac, w)
                    c.setStrokeColorRGB(0.72, 0.82, 1.0)
                    c.setDash(1, 2)
        c.showPage()
    c.save()


def main():
    secs = sections()
    singles = [t for s in secs if s["kind"] == "char" for g in s["groups"] for t in g]
    assert len(singles) == len(set(singles)), "같은 글자가 두 번 들어감"
    pages = paginate(secs)
    assert sum(len(cells) for _, cells in pages) == sum(len(g) for s in secs for g in s["groups"])
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    draw(pages, out / "template.pdf")
    manifest = dict(
        unit="mm", origin="top-left", page=[PAGE_W, PAGE_H], marker_size=MARKER, markers=MARKERS,
        latin_guides=LATIN_GUIDES,
        pages=[dict(page=n, section=sec["title"], kind=sec["kind"], guide=sec["guide"], cells=cells)
               for n, (sec, cells) in enumerate(pages, 1)],
    )
    (out / "template.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    for sec in secs:
        count = sum(len(g) for g in sec["groups"])
        nums = [n for n, (s, _) in enumerate(pages, 1) if s is sec]
        print(f"{sec['title']}: {count}칸, {nums[0]}~{nums[-1]}쪽")


if __name__ == "__main__":
    main()
