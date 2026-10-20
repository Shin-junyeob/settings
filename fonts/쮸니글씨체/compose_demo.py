"""작성한 글씨에서 받침을 갈아 끼워 빠진 글자를 만드는 시험용 스크립트.

실행: uv run --no-project --with pymupdf --with numpy --with pillow --with scipy python -I compose_demo.py <작성본.pdf> [글자...]
글자를 안 주면 만들 수 있는 후보를 출력하고, 주면 out/<글자>.png로 저장한다.

방식: 목표 글자 = (같은 초성+중성에 아무 받침이 있는 글자의 윗부분) + (같은 받침을 가진 글자의 아랫부분).
위/아래는 획이 하나도 지나가지 않는 빈 가로줄로 나눈다 — 그런 줄이 없는 글자는 재료로 쓰지 않는다.
ponytail: 받침 없는 글자(초성·모음 교체)는 아직 못 만든다. 획이 붙어 있어 빈 줄로 안 나뉘기 때문.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).parent
DPI = 300
INK = 128  # 이보다 어두우면 글씨. 안내선(연파랑·연빨강)과 칸 테두리는 이보다 밝다
VERTICAL = {0, 1, 2, 3, 4, 5, 6, 7, 20}  # ㅏㅐㅑㅒㅓㅔㅕㅖㅣ — 모음이 오른쪽에 서는 글자
HORIZONTAL = {8, 12, 13, 17, 18}  # ㅗㅛㅜㅠㅡ — 모음이 아래에 눕는 글자


def jamo(ch):
    code = ord(ch) - 0xAC00
    return code // 588, (code % 588) // 28, code % 28


def group(jung):
    return "v" if jung in VERTICAL else "h" if jung in HORIZONTAL else "m"


def load_cells(pdf_path):
    """작성본에서 한글 음절 칸을 잘라 {글자: 회색조 배열}로. 빈 칸은 뺀다."""
    manifest = json.loads((ROOT / "out/template.json").read_text(encoding="utf-8"))
    doc = pymupdf.open(pdf_path)
    scale = DPI / 25.4
    cells = {}
    for page in manifest["pages"]:
        if page["guide"] != "hangul":
            continue
        pix = doc[page["page"] - 1].get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY, annots=True)
        img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
        for c in page["cells"]:
            ch = c["text"]
            if not "가" <= ch <= "힣":
                continue
            x0, y0 = round(c["x"] * scale) + 3, round(c["y"] * scale) + 3
            x1, y1 = round((c["x"] + c["w"]) * scale) - 3, round((c["y"] + c["h"]) * scale) - 3
            crop = img[y0:y1, x0:x1].copy()
            crop[crop > 190] = 255  # 연파랑 안내 점선(회색조 ~207) 지우기
            if (crop < INK).sum() > 200:
                cells[ch] = crop
    for path in sorted((ROOT / "overrides").glob("*.png")):
        cells[path.stem] = load_override(path, cells)
    return cells


def load_override(path, cells):
    """나중에 따로 써서 보낸 글자(overrides/<글자>.png)를 템플릿 칸과 같은 모양으로 맞춘다.

    메모 앱 캡처는 바탕색·크기·펜 굵기가 템플릿과 달라서, 같은 모음 계열의 받침 없는
    작성 글자들의 중앙값에 맞춰 키우고 획을 두껍게 한다.
    """
    gray = np.array(Image.open(path).convert("L"))
    if gray.mean() < 128:  # 어두운 바탕에 밝은 글씨
        gray = 255 - gray
    ink = gray < INK
    ys, xs = np.where(ink)
    ink = ink[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    target = group(jamo(path.stem)[1])
    refs = [g for c, g in cells.items()
            if jamo(c)[2] == 0 and group(jamo(c)[1]) == target]
    boxes = [bbox(g) for g in refs]
    height = np.median([b[3] - b[1] for b in boxes])
    density = np.median([(g < INK).sum() / ((b[2] - b[0] + 1) * (b[3] - b[1] + 1))
                         for g, b in zip(refs, boxes)])
    scale = height / ink.shape[0]
    big = np.array(Image.fromarray(ink.astype(np.uint8) * 255).resize(
        (round(ink.shape[1] * scale), round(ink.shape[0] * scale)), Image.LANCZOS)) > 127
    # 획을 한 픽셀씩 불려 가며 잉크 밀도가 참고 글자들과 가장 가까운 굵기를 고른다
    disk = ndimage.generate_binary_structure(2, 1)
    best = min((ndimage.binary_dilation(big, disk, iterations=r) for r in range(0, 15)),
               key=lambda m: abs(m.mean() - density))
    soft = ndimage.gaussian_filter(best.astype(float), 0.8)
    glyph = (255 - soft * 255).clip(0, 255).astype(np.uint8)
    size = refs[0].shape
    canvas = np.full(size, 255, np.uint8)
    oy, ox = (size[0] - glyph.shape[0]) // 2, (size[1] - glyph.shape[1]) // 2
    canvas[oy:oy + glyph.shape[0], ox:ox + glyph.shape[1]] = glyph
    return canvas


def split(gray, lying=False):
    """빈 가로줄에서 위(초성+중성)·아래(받침)로 나눈다. 못 나누면 None.

    빈 줄은 여러 개일 수 있다(ㄴ/ㅡ/받침 사이, ㅎ 꼭지 아래). 아래쪽 빈 줄부터 올라가며
    바로 위 덩어리가 글자 폭의 절반 이상일 때만 자른다 — 넓은 덩어리는 초성+모음이거나
    누운 모음(ㅡ·ㅗ·ㅜ)이고, 좁은 덩어리(ㄴ, ㅎ 꼭지)는 그 위·아래와 한 몸이기 때문.
    lying(누운 모음이 든 글자)이면 가장 긴 가로획(=모음)보다 아래에서만 자른다 —
    폭만 보면 넓은 초성(ㄷ) 아래에서 잘려 받침 쪽에 ㅡ가 딸려 간다(등 → ㅡ+ㅇ).
    """
    ink = gray < INK
    rows = np.where(ink.any(axis=1))[0]
    top, bottom = rows[0], rows[-1]
    cols = np.where(ink.any(axis=0))[0]
    width = cols[-1] - cols[0]
    bar = int(ink.sum(axis=1).argmax())
    gaps, start = [], None  # 빈 줄 구간 (시작, 끝)
    for y in range(top, bottom + 1):
        if not ink[y].any():
            start = y if start is None else start
        elif start is not None:
            gaps.append((start, y - 1))
            start = None
    for i in range(len(gaps) - 1, -1, -1):
        lo, hi = gaps[i]
        if lo < top + 0.4 * (bottom - top) or (lying and lo <= bar):
            break
        band = ink[(gaps[i - 1][1] + 1 if i else top):lo]
        xs = np.where(band.any(axis=0))[0]
        if xs[-1] - xs[0] >= 0.5 * width:
            below = np.where(ink[hi + 1:].any(axis=0))[0]
            # 누운 모음 글자에서 아래 조각이 글자 폭만큼 넓으면 모음이 받침에 붙어 딸려 간 것(묵 → ㅁ / ㅜ+ㄱ, 실측)
            if lying and below[-1] - below[0] >= 0.8 * width:
                return None
            upper, lower = gray.copy(), gray.copy()
            upper[(lo + hi) // 2:] = 255
            lower[:(lo + hi) // 2] = 255
            return upper, lower
    return None


def check():
    """세 줄 덩어리(좁은 ㄴ / 넓은 ㅡ / 받침)와 ㅡ·받침이 붙은 경우로 split 규칙을 확인한다."""
    img = np.full((100, 100), 255, np.uint8)
    img[10:20, 40:50] = 0  # ㄴ (좁음)
    img[40:45, 10:90] = 0  # ㅡ (넓음)
    img[60:80, 30:70] = 0  # 받침
    upper, lower = split(img, lying=True)
    assert (upper[40:45] < INK).any() and not (lower[40:45] < INK).any(), "ㅡ는 윗부분에 남아야 함"
    img[45:60, 30:70] = 0  # ㅡ와 받침이 붙으면
    assert split(img) is None, "ㄴ 아래에서 자르면 안 됨"
    img[:] = 255
    img[10:31, 15:85] = 0  # 넓은 ㄷ
    img[40:45, 10:90] = 0  # ㅡ
    img[45:60, 30:70] = 0  # ㅡ에 붙은 ㅇ
    assert split(img) is not None and split(img, lying=True) is None, "누운 모음 위에서 자르면 안 됨"
    img[10:31, 10:90] = 0  # ㄷ이 ㅡ보다 넓어 가장 긴 가로획으로 잡혀도
    img[40:45, 10:90] = 255
    img[40:45, 12:88] = 0
    assert split(img, lying=True) is None, "모음이 딸린 아래 조각은 거부해야 함"
    print("check ok")


def bbox(gray):
    ys, xs = np.where(gray < INK)
    return xs.min(), ys.min(), xs.max(), ys.max()


def parts(ch, gray):
    return split(gray, lying=group(jamo(ch)[1]) != "v")


def compose(cells, a, b):
    """a의 윗부분에 b의 받침을, a에 원래 있던 받침 자리(가운데·윗선)에 붙인다."""
    u1, l1 = parts(a, cells[a])
    _, l2 = parts(b, cells[b])
    ax0, ay0, ax1, _ = bbox(l1)
    lx0, ly0, lx1, ly1 = bbox(l2)
    piece = l2[ly0:ly1 + 1, lx0:lx1 + 1]
    x = int(round((ax0 + ax1) / 2 - piece.shape[1] / 2))
    y = ay0
    out = np.full((u1.shape[0] + piece.shape[0], u1.shape[1] + piece.shape[1]), 255, np.uint8)
    pad = piece.shape[1] // 2
    out[: u1.shape[0], pad: pad + u1.shape[1]] = u1
    region = out[y: y + piece.shape[0], pad + x: pad + x + piece.shape[1]]
    np.minimum(region, piece, out=region)
    # 칸 크기로 되돌리며 글씨 전체를 가운데에 둔다
    x0, y0, x1, y1 = bbox(out)
    ink = out[y0:y1 + 1, x0:x1 + 1]
    size = max(cells[a].shape)
    canvas = np.full((size, size), 255, np.uint8)
    oy, ox = (size - ink.shape[0]) // 2, (size - ink.shape[1]) // 2
    if oy < 0 or ox < 0:
        return None
    canvas[oy: oy + ink.shape[0], ox: ox + ink.shape[1]] = ink
    return canvas


def donors(target, cells, splittable):
    cho, jung, jong = jamo(target)
    if jong == 0:
        return None
    uppers = [c for c in splittable if jamo(c)[:2] == (cho, jung)]
    # 받침은 모음이 오른쪽에 서는 글자에서만 뗀다 — 누운 모음 글자는 ㅡ가 받침에 붙어 있으면
    # 받침 조각에 모음이 딸려 온다(흥 → 짧은 ㅡ+ㅇ, 실측)
    lowers = [c for c in splittable if jamo(c)[2] == jong and group(jamo(c)[1]) == "v"]
    if not uppers or not lowers:
        return None
    # 받침 재료는 같은 모음에서 온 것을 먼저 쓴다 (받침 폭이 모음 모양을 따라가므로)
    lowers.sort(key=lambda c: jamo(c)[1] != jung)
    return uppers[0], lowers[0]


def main():
    if sys.argv[1] == "--check":
        return check()
    pdf_path, targets = sys.argv[1], sys.argv[2:]
    cells = load_cells(pdf_path)
    splittable = [c for c, g in cells.items() if jamo(c)[2] and parts(c, g)]
    print(f"작성된 음절 {len(cells)}자, 받침으로 나뉘는 글자 {len(splittable)}자")
    if not targets:
        ks = {bytes([a, b]).decode("euc_kr") for a in range(0xB0, 0xC9) for b in range(0xA1, 0xFF)}
        possible = [chr(c) for c in range(0xAC00, 0xD7A4)
                    if chr(c) not in cells and donors(chr(c), cells, splittable)]
        in_ks = [c for c in possible if c in ks]
        print(f"조합 가능 {len(possible)}자 (그중 상용 2,350자 안 {len(in_ks)}자)")
        print("상용 중 예시:", "".join(in_ks[:300]))
        return
    for t in targets:
        pair = donors(t, cells, splittable)
        img = compose(cells, *pair) if pair else None
        if img is None:
            print(f"{t}: 못 만듦")
            continue
        Image.fromarray(img).save(ROOT / f"out/{t}.png")
        print(f"{t} = {pair[0]}의 윗부분 + {pair[1]}의 받침")


if __name__ == "__main__":
    main()
