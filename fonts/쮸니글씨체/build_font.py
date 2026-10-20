"""작성본 PDF(+overrides, +받침 조합)로 손글씨 웹 폰트를 만든다.

실행: uv run --no-project --with pymupdf --with numpy --with pillow --with scipy --with potracer \
        --with fonttools --with brotli python -I build_font.py out/template_60percent.pdf
출력: out/JjyuniHand.otf, out/JjyuniHand.woff2, out/preview.html

좌표: 한글 잉크 높이 중앙값 = HANGUL_HEIGHT units가 되도록 전체를 같은 배율로 키운다 (영문과의 크기 비율은 쓴 그대로).
- 영문·숫자·기호: 쓴 위치 그대로, 기준선 위에 쓴 글자들의 바닥 중앙값을 y=0으로
- 한글·자모: 칸 가운데를 대문자·숫자 높이의 가운데에, 칸 안에서 쓴 위치는 그대로 (손글씨의 들쭉날쭉함을 살림)
"""

import json
import sys
from pathlib import Path

import numpy as np
import potrace
import pymupdf
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont, newTable
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))  # python -I는 스크립트 폴더를 경로에서 빼므로
import compose_demo as cd  # noqa: E402
FAMILY = "쮸니글씨체"
FAMILY_EN = "Jjyuni Hand"  # 영어 환경·한글을 못 쓰는 자리(CFF 이름표)용
PS_NAME = "JjyuniHand"  # PostScript 이름·파일 이름은 규격상 ASCII만
DPI = cd.DPI
PX = DPI / 25.4  # mm → px
HANGUL_HEIGHT = 760  # 칸 한 변=1000으로 하면 글씨가 em의 40%뿐이라 너무 작게 찍힘(실측)
SIDE = 45  # 영문 글자 양옆 여백(units)
LATIN_TAIL_MM = 4  # Y·Z 꼬리가 칸 아래로 ~2.8mm 넘어감(실측). 그 아래 다음 줄 라벨(회색)은 더 밝은 기준으로 거른다
DESCENDERS = set("gjpqyJYZfz,;")


def render_pages(pdf_path, numbers):
    doc = pymupdf.open(pdf_path)
    pages = {}
    for n in numbers:
        pix = doc[n - 1].get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
        pages[n] = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
    return pages


def cut(img, c, tail_mm=0):
    """칸을 회색조로 자른다. 칸 아래 tail_mm까지 넓히되 그 부분은 진한 잉크만 남긴다."""
    x0, y0 = round(c["x"] * PX) + 3, round(c["y"] * PX) + 3
    x1, y1 = round((c["x"] + c["w"]) * PX) - 3, round((c["y"] + c["h"]) * PX) - 3
    gray = img[y0:y1, x0:x1].copy()
    gray[gray > 190] = 255  # 연한 안내선
    if tail_mm:
        extra = img[y1:y1 + round(tail_mm * PX), x0:x1].copy()
        extra[extra >= 50] = 255  # 다음 줄 라벨 글자는 회색(~77)이라 지워짐
        gray = np.vstack([gray, extra])
    return gray, y0  # y0: 잘라낸 위치(px), 칸 위쪽 기준 좌표를 맞추는 데 쓴다


def trace(gray, to_font, up=2):
    """회색조 글씨를 외곽선으로 바꿔 T2 charstring 그리기 함수(pen을 받는)로 돌려준다.

    흑백으로 먼저 나누면 픽셀 계단이 곡선에 그대로 남아 울퉁불퉁해진다(실측). 회색조를 up배로
    부드럽게 키운 뒤 나눠야 붓펜 가장자리의 중간 톤이 살아서 매끈해진다. 살짝 흐리게 해서
    잔물결도 지운다 — 안 지우면 곡선 조각이 늘어 woff2가 451KB → 1.1MB(실측).
    """
    big = np.array(Image.fromarray(gray).resize((gray.shape[1] * up, gray.shape[0] * up), Image.LANCZOS))
    big = ndimage.gaussian_filter(big.astype(float), 1.2)
    # potracer는 이미지처럼 밝은 값을 바탕으로 본다 — 잉크를 False로 넘긴다
    curves = potrace.Bitmap(big >= cd.INK).trace(turdsize=8 * up * up, alphamax=1.0, opttolerance=0.4)
    pt = lambda p: to_font(p.x / up, p.y / up)  # noqa: E731

    def draw(pen):
        for curve in curves:
            pen.moveTo(pt(curve.start_point))
            for seg in curve.segments:
                if seg.is_corner:
                    pen.lineTo(pt(seg.c))
                    pen.lineTo(pt(seg.end_point))
                else:
                    pen.curveTo(pt(seg.c1), pt(seg.c2), pt(seg.end_point))
            pen.closePath()
    return draw


def collect(pdf_path):
    """{글자: (회색조 배열, 종류, 칸 위쪽에서 배열 첫 줄까지 px)}"""
    manifest = json.loads((ROOT / "out/template.json").read_text(encoding="utf-8"))
    want = [p for p in manifest["pages"] if p["kind"] == "char" and
            (p["guide"] == "latin" or "자모" in p["section"])]
    pages = render_pages(pdf_path, [p["page"] for p in want])
    glyphs = {}
    for p in want:
        latin = p["guide"] == "latin"
        for c in p["cells"]:
            ink, y0 = cut(pages[p["page"]], c, LATIN_TAIL_MM if latin else 0)
            if (ink < cd.INK).sum() > 30:
                glyphs[c["text"]] = (ink, "latin" if latin else "hangul", y0 - c["y"] * PX)
    cells = cd.load_cells(pdf_path)  # 한글 음절 + overrides
    for ch, gray in cells.items():
        glyphs[ch] = (gray, "hangul", 3)
    splittable = [c for c, g in cells.items() if cd.parts(c, g)]
    for code in range(0xAC00, 0xD7A4):
        t = chr(code)
        if t not in cells and (pair := cd.donors(t, cells, splittable)):
            img = cd.compose(cells, *pair)
            if img is not None:
                glyphs[t] = (img, "hangul", 3)
    return glyphs


def build(glyphs, out_dir):
    box_px = 18 * PX
    glyphs = {ch: (g < cd.INK, g, kind, top) for ch, (g, kind, top) in glyphs.items()}
    hangul_h = [np.ptp(np.where(g[0].any(axis=1))[0]) for g in glyphs.values() if g[2] == "hangul"]
    UNITS = HANGUL_HEIGHT / float(np.median(hangul_h))  # px → font units
    latin = {ch: (g[0], g[2], g[3]) for ch, g in glyphs.items() if g[2] == "latin"}
    bottoms = [g[2] + np.where(g[0].any(axis=1))[0][-1] for ch, g in latin.items()
               if ch.isalnum() and ch not in DESCENDERS]
    baseline_px = float(np.median(bottoms))  # 칸 위쪽에서 기준선까지(px)
    tops = [g[2] + np.where(g[0].any(axis=1))[0][0] for ch, g in latin.items()
            if (ch.isupper() or ch.isdigit()) and ch not in DESCENDERS]
    # ponytail: 한글 가운데 = 대문자·숫자 높이의 가운데. 혼합 문장 페이지로 재면 더 정확해짐
    hangul_center = (baseline_px - float(np.median(tops))) * UNITS / 2

    hangul_w = [np.ptp(np.where(g[0].any(axis=0))[0]) for g in glyphs.values() if g[2] == "hangul"]
    hangul_adv = round(float(np.median(hangul_w)) * UNITS * 1.18)  # ponytail: 고정폭 = 중앙 잉크 폭의 118%. 혼합 문장 페이지로 재면 더 정확해짐

    order, cmap, charstrings, metrics = [".notdef", "space"], {32: "space"}, {}, {}
    empty = T2CharStringPen(500, None)
    charstrings[".notdef"] = empty.getCharString()
    space = T2CharStringPen(round(hangul_adv * 0.3), None)
    charstrings["space"] = space.getCharString()
    metrics[".notdef"], metrics["space"] = (500, 0), (round(hangul_adv * 0.3), 0)

    def visual(ink):
        ys, xs = np.where(ink.any(axis=1))[0], np.where(ink.any(axis=0))[0]
        return float(np.sqrt(np.ptp(ys) * np.ptp(xs)))
    syllables = [visual(g[0]) for ch, g in glyphs.items() if "가" <= ch <= "힣"]
    target = float(np.median(syllables))

    for ch, (ink, gray, kind, top_px) in sorted(glyphs.items()):
        xs, ys = np.where(ink.any(axis=0))[0], np.where(ink.any(axis=1))[0]
        cx, cy = (xs[0] + xs[-1]) / 2, (ys[0] + ys[-1]) / 2
        # 한글 음절은 크기 편차를 70%만 줄인다 — 직접 쓴 '얌'(89×60px)이 '체'(112×93px) 옆에서 너무 작아 보였음.
        # 다 같은 크기로 맞추면 손글씨 느낌이 사라지므로 일부만, 한 글자에 0.8~1.3배까지만
        sc = float(np.clip((target / visual(ink)) ** 0.7, 0.8, 1.3)) if "가" <= ch <= "힣" else 1.0
        if kind == "latin":
            adv = round(np.ptp(xs) * UNITS) + 2 * SIDE
            dx = SIDE - xs[0] * UNITS
            to_y = lambda y, t=top_px: (baseline_px - (t + y)) * UNITS
        else:
            # 넓은 글자(ㄸ·ㅃ 등)는 고정폭을 넘어 옆 글자를 침범하므로 그 글자만 넓힌다
            adv = max(hangul_adv, round(np.ptp(xs) * sc * UNITS) + 2 * SIDE)
            dx = adv / 2 - cx * UNITS
            to_y = lambda y, t=top_px: hangul_center + (box_px / 2 - (t + y)) * UNITS
        to_font = lambda x, y, dx=dx, to_y=to_y, u=UNITS, sc=sc, cx=cx, cy=cy: (
            round((cx + (x - cx) * sc) * u + dx), round(to_y(cy + (y - cy) * sc)))
        pen = T2CharStringPen(adv, None)
        trace(gray, to_font)(pen)
        name = f"uni{ord(ch):04X}"
        order.append(name)
        cmap[ord(ch)] = name
        charstrings[name] = pen.getCharString()
        metrics[name] = (adv, 0)

    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupCFF(PS_NAME, {"FullName": FAMILY_EN}, charstrings, {})
    # lsb는 실제 외곽선 xMin이어야 한다
    cs = fb.font["CFF "].cff.topDictIndex[0].CharStrings
    bounds = {n: cs[n].calcBounds(cs) for n in order}
    fb.setupHorizontalMetrics({n: (metrics[n][0], round(b[0]) if b else 0) for n, b in bounds.items()})
    ymax = max(b[3] for b in bounds.values() if b)
    ymin = min(b[1] for b in bounds.values() if b)
    asc, desc = round(ymax) + 20, round(ymin) - 20
    fb.setupHorizontalHeader(ascent=asc, descent=desc)
    fb.setupNameTable({"familyName": {"en": FAMILY_EN, "ko": FAMILY}, "styleName": "Regular",
                       "fullName": {"en": FAMILY_EN, "ko": FAMILY}, "psName": PS_NAME})
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=0,
                usWinAscent=asc, usWinDescent=-desc, fsType=0)
    fb.setupPost()
    # macOS는 현대 한글 11,172자를 다 갖추지 않은 글꼴을 한국어 글꼴로 안 쳐서 서체 메뉴의 '한국어'에서 빠진다
    # (실측: 코드페이지 비트·상용 2,350자 채우기로는 안 되고, 지원 언어를 meta 표에 직접 적으면 됨)
    meta = newTable("meta")
    meta.data = {"dlng": "Kore, Latn", "slng": "Kore, Latn"}
    fb.font["meta"] = meta
    otf = out_dir / f"{PS_NAME}.otf"
    fb.save(otf)
    font = TTFont(otf)
    font.flavor = "woff2"
    font.save(out_dir / f"{PS_NAME}.woff2")
    return len(order) - 2, hangul_adv, asc, desc


PREVIEW = """<!doctype html>
<meta charset="utf-8">
<title>쮸니글씨체</title>
<style>
@font-face { font-family: "쮸니글씨체"; src: url("JjyuniHand.woff2") format("woff2"); font-display: swap; }
body { font-family: "쮸니글씨체", sans-serif; font-size: 40px; line-height: 1.5; margin: 32px; }
</style>
<p>다람쥐 헌 쳇바퀴에 타고파</p>
<p>오늘은 2026년 10월 20일, Orbit을 켰다!</p>
<p>The quick brown fox jumps over the lazy dog.</p>
<p>빨갛다 닳다 짰다 찼다 큭큭 킁킁 토마토</p>
"""


def main():
    out = ROOT / "out"
    glyphs = collect(sys.argv[1])
    n, adv, asc, desc = build(glyphs, out)
    (out / "preview.html").write_text(PREVIEW, encoding="utf-8")
    kinds = {}
    for ch, g in glyphs.items():
        kinds[g[1]] = kinds.get(g[1], 0) + 1
    print(f"글리프 {n}개 {kinds}, 한글 폭 {adv}, ascent {asc}, descent {desc}")


if __name__ == "__main__":
    main()
