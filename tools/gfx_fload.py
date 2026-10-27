# -*- coding: utf-8 -*-
r"""로딩 화면 FLOAD_00.2D «WELCOME TO THE / WAKUWAKU / WORLD» → «DUGUNDUGUN» (2026-10-27 하스피 «폰트·색 똑같이»)
  같은 글꼴 글자를 화면에서 떼어 씀: D = WORLD 의 D · U = WAKU 의 U · G·N = 노란 NOW LOADING 의 G·N
  (노란 글자는 줄마다 하늘색 그라데이션 색으로 다시 칠함: 채움 = 기준 U 의 같은 줄 색, 테두리 65 → 113, 그림자 255 그대로)
  WAKUWAKU 줄 글자 화소(채움·테두리·그림자)를 지우고 둘레 바탕으로 메운 뒤, 오른쪽 끝(원래 U 끝)에 맞춰 찍음
  python tools/gfx_fload.py → work/check/fload_preview.png(원본 | 새것) · --build → work/build/WAKTRI/FLOAD_00.2D"""
import os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import title2d as T
SRC = os.path.join(ROOT, 'work', 'disc0', 'WAKTRI', 'FLOAD_00.2D')
CF = set(range(250, 255)); YF = set(range(245, 250)); OUT_C, OUT_Y, SHADOW = 113, 65, 255
LINE = (150, 34, 314, 72)                 # WAKUWAKU 줄(지우는 범위)
# 글자 원본: (채움 칸 x0, y0, x1, y1, 노란색인가)
SRCBOX = {'D': (293, 76, 307, 96, False), 'U': (219, 44, 234, 64, False), 'N': (246, 188, 259, 209, True), 'G': (262, 188, 277, 208, True)}
WORD = 'DUGUNDUGUN'
TOP, RIGHT, GAP, WGAP = 44, 306, 2, 4      # 채움 위 y · 오른쪽 끝 · 글자 사이 · 낱말 사이


def glyph(img, ch):
    x0, y0, x1, y1, yel = SRCBOX[ch]; F = YF if yel else CF; O = OUT_Y if yel else OUT_C
    out = {}
    for y in range(y0 - 3, y1 + 4):
        for x in range(x0 - 3, x1 + 4):
            v = img[y][x]
            if v in F and x0 <= x <= x1: out[(x - x0, y - y0)] = ('f', v)
            elif v in (O, SHADOW): out[(x - x0, y - y0)] = ('o' if v == O else 's', v)
    # 테두리·그림자는 채움 가까이(2px) 것만 — 옆 글자 것 빼기
    fill = {p for p, (t, _) in out.items() if t == 'f'}
    keep = {}
    for p, tv in out.items():
        if tv[0] == 'f' or any((p[0] + dx, p[1] + dy) in fill for dx in range(-3, 4) for dy in range(-3, 4)): keep[p] = tv
    return keep, x1 - x0 + 1


def make():
    img, pal = T.load(SRC); new = [r[:] for r in img]
    # 기준 U 의 줄별 채움 색
    ux0, uy0, ux1, uy1, _ = SRCBOX['U']
    rowc = {}
    for y in range(uy0, uy1 + 1):
        c = Counter(img[y][x] for x in range(ux0, ux1 + 1) if img[y][x] in CF)
        if c: rowc[y - uy0] = c.most_common(1)[0][0]
    # 지우기
    x0, y0, x1, y1 = LINE
    mask = {(x, y) for y in range(y0, y1) for x in range(x0, x1) if img[y][x] in CF | {OUT_C, SHADOW}}
    val = {}; cur = []
    for x, y in mask:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in mask: val[(x, y)] = img[q[1]][q[0]]; cur.append((x, y)); break
    while cur:
        nxt = []
        for x, y in cur:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q in mask and q not in val: val[q] = val[(x, y)]; nxt.append(q)
        cur = nxt
    for (x, y), v in val.items(): new[y][x] = v
    # 글자 배치(오른쪽 끝 맞춤)
    gs = [glyph(img, ch) for ch in WORD]
    widths = [w for _, w in gs]
    total = sum(widths) + GAP * (len(WORD) - 1) + (WGAP - GAP)
    x = RIGHT - total + 1
    for i, (g, w) in enumerate(gs):
        yel = SRCBOX[WORD[i]][4]
        for (dx, dy), (t, v) in sorted(g.items(), key=lambda kv: {'s': 0, 'o': 1, 'f': 2}[kv[1][0]]):
            if t == 'f' and yel: v = rowc.get(min(max(dy, 0), max(rowc)), v)
            elif t == 'o': v = OUT_C
            new[TOP + dy][x + dx] = v
        x += w + (WGAP if i == 4 else GAP)
    # 찌꺼기: 사방이 글자 화소인데 글자 색이 아닌 점(딸려 온 그림자·글자 속 바탕) → 테두리 색
    for y in range(y0, y1):
        for x in range(x0 - 30, x1):
            if new[y][x] not in CF | {OUT_C} and all(new[y + dy][x + dx] in CF | {OUT_C} for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): new[y][x] = OUT_C
    merge_cells(new, pal, LIMIT_CELLS, (y0 // 8 - 1, y1 // 8 + 1))
    return img, new, pal


LIMIT_CELLS = 1097                        # 원본 셀 수(셀 구획 크기 그대로)


def merge_cells(new, pal, limit, keep_rows):
    """셀이 원본보다 많으면 바탕(글자 줄 밖)에서 색 차이가 가장 작은 셀 쌍부터 하나로 합침 — 잡티 많은 주황 질감이라 눈에 안 띔"""
    import numpy as np
    P = np.array(pal, dtype=np.int32)
    def cellmap():
        d = {}
        for my in range(64):
            for mx in range(64):
                d.setdefault(tuple(new[my * 8 + y][mx * 8 + x] for y in range(8) for x in range(8)), []).append((mx, my))
        return d
    d = cellmap(); extra = len(d) - limit
    if extra <= 0: return 0
    keys = [k for k, pos in d.items() if all(not (keep_rows[0] <= my <= keep_rows[1]) for mx, my in pos)]
    A = P[np.array(keys)].reshape(len(keys), -1)
    pairs = []
    for i in range(len(keys)):
        dist = np.abs(A[i + 1:] - A[i]).sum(1)
        if len(dist): j = int(dist.argmin()); pairs.append((int(dist[j]), i, i + 1 + j))
    pairs.sort(); used = set(); n = 0
    for dist, i, j in pairs:
        if n >= extra: break
        if i in used or j in used: continue
        used |= {i, j}; n += 1
        for mx, my in d[keys[j]]:
            for k, v in enumerate(keys[i]): new[my * 8 + k // 8][mx * 8 + k % 8] = v
    if n < extra: raise SystemExit('⛔로딩 화면 셀 줄이기 모자람')
    return n


def preview(img, new, pal, path):
    from PIL import Image
    im = Image.new('RGB', (352 * 2 + 6, 240), (40, 40, 40))
    for k, m in enumerate((img, new)):
        for y in range(240):
            for x in range(352): im.putpixel((k * 358 + x, y), pal[m[y][x]])
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(path)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    img, new, pal = make()
    if '--build' in sys.argv:
        nb, n = T.build(new, SRC); o = os.path.join(ROOT, 'work', 'build', 'WAKTRI', 'FLOAD_00.2D')
        open(o, 'wb').write(nb); print('로딩 화면 →', o, '셀', n)
    else:
        p = os.path.join(ROOT, 'work', 'check', 'fload_preview.png'); preview(img, new, pal, p); print(p)
