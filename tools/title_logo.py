# -*- coding: utf-8 -*-
r"""타이틀 로고 «わくわく7» → «두근두근7» (2026-10-27 하스피 «그림 글자로, 원본 색조·그라데이션 살려서»)
  글꼴이 아니라 획 뼈대(조절점 꺾은선)를 직접 설계해 굵은 둥근 붓으로 그린다(4배로 그린 뒤 줄임).
  ① 글자 칸 = 원본 わ·く·わ·く 자리(L1~L4) · 획 = STROKES(칸 안 0~1 좌표) · 칸마다 기울기·굵기
  ② 색 = 원본 글자 그라데이션 옮기기: 새 글자 화소의 칸 안 상대 위치 → 원본 글자 같은 상대 위치의 가장 가까운 화소 색 번호
  ③ 보라 테두리 = 새 글자 둘레 R px · 글자에 붙은 2px 는 원본 글자 바로 옆 보라색(가장 흔한 색), 그 밖은 원본 보라 화소 중 가장 가까운 것
     원본 글자 자리 중 새 글자가 안 덮는 곳도 보라로(덩어리 모양 유지) · 7·WAKU WAKU SEVEN·별·배경은 그대로
  python tools/title_logo.py → work/check/title_preview.png(원본 | 새것) · --build → work/build/WAKTRI/TYTLE_00.2D"""
import math, os, sys, colorsys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import title2d as T
from PIL import Image, ImageDraw

SS = 4                                   # 그릴 때 배율
R_OUT = 5                                # 보라 테두리 굵기(px)
# 원본 글자 칸(x0, y0, x1, y1) — 하늘 わ · 주황 く · 노랑 わ · 청록/초록 く
BOX = [(58, 55, 123, 111), (98, 83, 137, 145), (132, 71, 186, 120), (176, 82, 210, 149)]
# 새 글자: (칸 번호, 글자 그릴 칸(x0,y0,x1,y1), 기울기°, 획 굵기 px, 획들[[(u,v)…]…])
DU = [[(0.10, 0.02), (0.88, 0.02)], [(0.12, 0.02), (0.12, 0.40)], [(0.12, 0.40), (0.92, 0.40)],      # ㄷ
      [(0.00, 0.68), (1.00, 0.68)], [(0.50, 0.68), (0.50, 1.00)]]                                       # ㅜ
GEUN = [[(0.08, 0.05), (0.90, 0.05), (0.88, 0.32)],                                                     # ㄱ
        [(0.00, 0.50), (1.00, 0.50)],                                                                   # ㅡ
        [(0.12, 0.66), (0.12, 0.95), (0.95, 0.95)]]                                                     # ㄴ
LETTERS = [(0, (52, 50, 110, 120), -5, 13, DU), (2, (128, 68, 186, 132), -3, 13, DU),      # 뒤: 두 두
           (1, (96, 82, 140, 154), 8, 12, GEUN), (3, (172, 80, 218, 154), 10, 12, GEUN)]    # 앞: 근 근 (원본처럼 く 가 앞)
R_SEP = 2                                # 앞 글자가 뒤 글자를 덮을 때 사이 보라 선 굵기


def fam_letter(pal):
    S = set()
    for k in range(256):
        r, g, b = pal[k]; h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255); h *= 360
        if k > 16 and k not in (50, 66, 77) and s > 0.35 and v > 0.6 and not (h >= 300 or h < 15): S.add(k)
    return S


PURPLE = set(range(1, 17)) - {13}


def comp(img, S, box):
    """칸 안에서 글자 색으로 이어진 가장 큰 덩어리(옆 글자 색이 섞이지 않게)"""
    x0, y0, x1, y1 = box; seen = set(); best = []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) in seen or img[y][x] not in S: continue
            st = [(x, y)]; seen.add((x, y)); px = []
            while st:
                a, b = st.pop(); px.append((a, b))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (a + dx, b + dy)
                    if x0 <= q[0] <= x1 and y0 <= q[1] <= y1 and q not in seen and img[q[1]][q[0]] in S: seen.add(q); st.append(q)
            if len(px) > len(best): best = px
    return best


def draw_letter(box, rot, w, strokes, grow=0):
    x0, y0, x1, y1 = box; W, H = (x1 - x0 + 1), (y1 - y0 + 1)
    pad = w + 4 + grow; im = Image.new('L', ((W + 2 * pad) * SS, (H + 2 * pad) * SS), 0); dr = ImageDraw.Draw(im)
    cx, cy = (W + 2 * pad) * SS / 2, (H + 2 * pad) * SS / 2; a = math.radians(rot)
    def P(u, v):
        x = (pad + w / 2 + u * (W - w)) * SS; y = (pad + w / 2 + v * (H - w)) * SS
        dx, dy = x - cx, y - cy
        return (cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a))
    r = (w + 2 * grow) * SS / 2
    for st in strokes:
        pts = [P(u, v) for u, v in st]
        dr.line(pts, fill=255, width=int((w + 2 * grow) * SS), joint='curve')
        for x, y in pts: dr.ellipse((x - r, y - r, x + r, y + r), fill=255)
    sm = im.resize((W + 2 * pad, H + 2 * pad), Image.BOX)
    return {(x0 - pad + x, y0 - pad + y) for y in range(sm.height) for x in range(sm.width) if sm.getpixel((x, y)) >= 128}


def nearest_map(src_pts, targets):
    """targets 마다 src_pts 중 가장 가까운 점"""
    out = {}
    for t in targets:
        out[t] = min(src_pts, key=lambda p: (p[0] - t[0]) ** 2 + (p[1] - t[1]) ** 2)
    return out


def make():
    img, pal = T.load(); new = [r[:] for r in img]
    LS = fam_letter(pal)
    olds = [comp(img, LS, b) for b in BOX]
    old_all = set(p for c in olds for p in c)
    masks = []
    for k, box, rot, w, st in LETTERS:
        m = draw_letter(box, rot, w, st); masks.append((k, box, m))
    letter_px = set(p for _, _, m in masks for p in m)
    # 보라: 원본 보라 화소(로고 둘레 범위)
    region = [(x, y) for y in range(30, 175) for x in range(40, 260)]
    purp = [(x, y) for x, y in region if img[y][x] in PURPLE]
    # 글자에 바로 붙은 원본 보라 색(가장 흔한 것)
    from collections import Counter
    edge = Counter()
    for x, y in old_all:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in old_all and img[q[1]][q[0]] in PURPLE: edge[img[q[1]][q[0]]] += 1
    dark = edge.most_common(1)[0][0]
    # 테두리(2026-10-27 «도트 덜 튀게»): 바깥선 = 획을 R_OUT 만큼 굵게 4배로 그려 줄인 매끈한 실루엣 ∪ 원본 글자 자리
    sil = set(letter_px) | set(old_all)
    for k, box, rot, w, st in LETTERS: sil |= draw_letter(box, rot, w, st, R_OUT)
    # 구멍·좁은 홈 메우기: 실루엣 밖인데 4방향 중 3곳 이상이 실루엣이면 채우기(반복) + 막힌 작은 구멍 채우기
    for _ in range(4):
        add = {(x, y) for x, y in {(a + dx, b + dy) for a, b in sil for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - sil
               if sum(((x + dx, y + dy) in sil) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 3}
        if not add: break
        sil |= add
    xs = [p[0] for p in sil]; ys = [p[1] for p in sil]; bx0, bx1, by0, by1 = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
    out = set(); st = [(bx0, by0)]
    while st:
        q = st.pop()
        if q in out or q in sil or not (bx0 <= q[0] <= bx1 and by0 <= q[1] <= by1): continue
        if img[q[1]][q[0]] in PURPLE and q not in sil: pass
        out.add(q); st += [(q[0] + 1, q[1]), (q[0] - 1, q[1]), (q[0], q[1] + 1), (q[0], q[1] - 1)]
    holes = {(x, y) for y in range(by0, by1 + 1) for x in range(bx0, bx1 + 1) if (x, y) not in sil and (x, y) not in out}
    sil |= holes
    # 글자까지 거리(최대 R_OUT+1)
    dist = {p: 0 for p in letter_px}; cur = list(letter_px)
    for d in range(1, R_OUT + 3):
        nxt = []
        for x, y in cur:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in dist: dist[q] = d; nxt.append(q)
        cur = nxt
    # 원본 보라 단계: 바깥 가장자리 색 · 가운데 색(원본 글자에서 3~5px 떨어진 보라 중 가장 흔한 것)
    outer = Counter(); mid = Counter()
    for x, y in purp:
        if any(img[y + dy][x + dx] == 77 or img[y + dy][x + dx] in (50, 66) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): outer[img[y][x]] += 1
    od = {p: 0 for p in old_all}; cur = list(old_all)
    for d in range(1, 6):
        nxt = []
        for x, y in cur:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in od: od[q] = d; nxt.append(q)
        cur = nxt
    for q, d in od.items():
        if 3 <= d <= 5 and img[q[1]][q[0]] in PURPLE: mid[img[q[1]][q[0]]] += 1
    outer_c = outer.most_common(1)[0][0]; mid_c = mid.most_common(1)[0][0]
    for p in sil - letter_px:
        x, y = p
        edge = any((x + dx, y + dy) not in sil and img[y + dy][x + dx] not in PURPLE for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if dist.get(p, 99) <= 2: new[y][x] = dark
        elif edge: new[y][x] = outer_c
        elif img[y][x] in PURPLE and p not in old_all: new[y][x] = img[y][x]
        else: new[y][x] = mid_c
    # 글자 색 = 원본 글자 그라데이션(칸 안 상대 위치) — 뒤 글자부터, 앞 글자는 둘레 R_SEP 보라 선으로 뒤 글자를 끊고 덮음
    for k, box, m in masks:
        for x, y in m:
            for dy in range(-R_SEP, R_SEP + 1):
                for dx in range(-R_SEP, R_SEP + 1):
                    q = (x + dx, y + dy)
                    if dx * dx + dy * dy <= R_SEP * R_SEP + 1 and q not in m: new[q[1]][q[0]] = dark
        ob = BOX[k]; src = olds[k]
        mx0 = min(p[0] for p in m); mx1 = max(p[0] for p in m); my0 = min(p[1] for p in m); my1 = max(p[1] for p in m)
        for x, y in m:
            t = (ob[0] + (x - mx0) / max(1, mx1 - mx0) * (ob[2] - ob[0]), ob[1] + (y - my0) / max(1, my1 - my0) * (ob[3] - ob[1]))
            q = min(src, key=lambda s: (s[0] - t[0]) ** 2 + (s[1] - t[1]) ** 2)
            new[y][x] = img[q[1]][q[0]]
    return img, new, pal


# 위 영문 «WAKU / WAKU / SEVEN» → «DUGUN / DUGUN / SEVEN»(2026-10-27 하스피) — 2px 획 도트 글자를 직접 찍음, 줄 첫 글자 빨강, 글자마다 오른쪽 위로 3px 씩
ENG_OLD = [(107, 39, 117, 47), (119, 38, 125, 45), (125, 35, 132, 42), (133, 32, 141, 40),       # 1줄 W A K U
           (121, 46, 131, 54), (133, 45, 139, 52), (139, 42, 146, 49), (147, 39, 155, 47)]       # 2줄 W A K U
GLYPH = {
    'D': ['######..', '#######.', '##...###', '##....##', '##....##', '##....##', '##...###', '#######.', '######..'],
    'U': ['##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '######', '.####.'],
    'G': ['.####.', '######', '##....', '##.###', '##.###', '##..##', '######', '.####.'],
    'N': ['##..##', '###.##', '######', '######', '##.###', '##..##', '##..##', '##..##']}
# (글자, 왼쪽 x, 아래 y, 색 번호) — 색 = 원본 같은 자리 글자 색(빨강 13, 1줄 보라 7·8, 2줄 10·11)
ENG_NEW = [('D', 107, 47, 13), ('U', 116, 45, 7), ('G', 123, 42, 7), ('U', 130, 39, 8), ('N', 137, 36, 8),
           ('D', 121, 54, 13), ('U', 130, 52, 10), ('G', 137, 49, 10), ('U', 144, 46, 11), ('N', 151, 43, 11)]
TX = set(range(1, 17))
ENG_ROT = 22                             # 원본 영문 글자 기울기(세로획 7줄에 2~3칸 = 줄 기울기 3/7 과 같음, 하스피 «왼쪽으로 기울어»)


def english(img, new):
    mask = set()
    for x0, y0, x1, y1 in ENG_OLD:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if img[y][x] in TX and new[y][x] == img[y][x]: mask.add((x, y))
    val = {}; cur = []
    for x, y in mask:                                   # 지운 자리 = 가림 밖 가장 가까운 화소(크림 바탕·초록 붓 자국)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in mask: val[(x, y)] = new[q[1]][q[0]]; cur.append((x, y)); break
    while cur:
        nxt = []
        for x, y in cur:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q in mask and q not in val: val[q] = val[(x, y)]; nxt.append(q)
        cur = nxt
    for (x, y), v in val.items(): new[y][x] = v
    for ch, x0, yb, c in ENG_NEW:                      # 원본처럼 글자마다 왼쪽으로 ENG_ROT° 기울임(8배로 돌려 줄임), 글자 가운데 기준
        g = GLYPH[ch]; h, w = len(g), len(g[0]); K = 8
        im = Image.new('L', (w * K, h * K), 0); dr = ImageDraw.Draw(im)
        for yy, row in enumerate(g):
            for xx, b in enumerate(row):
                if b == '#': dr.rectangle((xx * K, yy * K, xx * K + K - 1, yy * K + K - 1), fill=255)
        im = im.rotate(ENG_ROT, resample=Image.BICUBIC, expand=True)
        sm = im.resize((round(im.width / K), round(im.height / K)), Image.BOX)
        cx, cy = x0 + w / 2, yb - h / 2 + 0.5
        ox, oy = round(cx - sm.width / 2), round(cy - sm.height / 2)
        for yy in range(sm.height):
            for xx in range(sm.width):
                if sm.getpixel((xx, yy)) >= 110: new[oy + yy][ox + xx] = c


def preview(img, new, pal, path):
    x0, y0, x1, y1 = 30, 20, 270, 180; W = x1 - x0
    im = Image.new('RGB', (W * 2 + 6, y1 - y0), (40, 40, 40))
    for k, m in enumerate((img, new)):
        for y in range(y0, y1):
            for x in range(x0, x1): im.putpixel((k * (W + 6) + x - x0, y - y0), pal[m[y][x]])
    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(path)
    full = Image.new('RGB', (352, 240))
    for y in range(240):
        for x in range(352): full.putpixel((x, y), pal[new[y][x]])
    full.resize((704, 480), Image.NEAREST).save(path.replace('.png', '_full.png'))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    img, new, pal = make(); english(img, new)
    if '--build' in sys.argv:
        nb, n = T.build(new); o = os.path.join(ROOT, 'work', 'build', 'WAKTRI', 'TYTLE_00.2D')
        open(o, 'wb').write(nb); print('타이틀 →', o, '셀', n)
    else:
        p = os.path.join(ROOT, 'work', 'check', 'title_preview.png'); preview(img, new, pal, p); print(p)
