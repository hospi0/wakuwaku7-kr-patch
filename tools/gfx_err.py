# -*- coding: utf-8 -*-
r"""경고 화면 그림 한글화(ERRC00.2D 확장 RAM · ERBR00.2D 백업 RAM) 2026-10-27
  ① 로고 아래 글 줄 띠마다 글자 색(흰·회색 번짐)만 지우고 같은 줄 좌우 가장 가까운 바탕색으로 메움
  ② 갈무리11 을 흰색(15)으로 원래 줄 가운데에 씀 · 번역 = data/번역/경고화면.txt
  python tools/gfx_err.py → work/check/err_preview.png(원본 | 새것) · --build → work/build/WAKTRI/*.2D"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import err2d as E
from bdf import Font
GAL = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri11.bdf'
TEXT = {'ERRC00.2D': {9, 10, 13, 14, 15}, 'ERBR00.2D': {9, 12, 13, 15}}
Y0 = {'ERRC00.2D': 55, 'ERBR00.2D': 37}       # 로고(WARNING!!·CAUTION!!) 아래부터
W, H = 352, 240


def texts():
    out, cur = {}, None
    for l in open(os.path.join(ROOT, 'data', '번역', '경고화면.txt'), encoding='utf-8').read().splitlines():
        if not l or l.startswith('#'): continue
        if l.startswith('['): cur = l[1:-1]; out[cur] = []; continue
        out[cur].append(l)
    return out


def bands(img, T, y0):
    rows = [y for y in range(y0, H) if sum(1 for x in range(W) if img[y][x] in T) >= 3]
    out = []
    for y in rows:
        if out and y <= out[-1][1] + 2: out[-1][1] = y
        else: out.append([y, y])
    res = []
    for a, b in out:
        xs = [x for y in range(a, b + 1) for x in range(W) if img[y][x] in T]
        res.append((a, b, min(xs), max(xs)))
    return res


def new_image(nm, img, lines, g):
    T = TEXT[nm]; out = [r[:] for r in img]; bs = bands(img, T, Y0[nm])
    assert len(bs) == len(lines), (nm, len(bs), len(lines), bs)
    # 지우기: 글자 색 화소 + 둘레 1px(어두운 그림자·번짐) = 가림 → 가림 밖 가장 가까운 바탕 화소로(너비 우선 채우기)
    mask = set()
    for a, b, xa, xb in bs:
        for y in range(a, b + 1):
            for x in range(W):
                if img[y][x] in T:
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if 0 <= x + dx < W and Y0[nm] <= y + dy < H: mask.add((x + dx, y + dy))
    front = [(x, y) for (x, y) in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, y + dy) not in mask and 0 <= x + dx < W and 0 <= y + dy < H]
    val = {}
    for x, y in front:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in mask and 0 <= q[0] < W and 0 <= q[1] < H: val[(x, y)] = img[q[1]][q[0]]; break
    cur = list(val)
    while cur:
        nxt = []
        for x, y in cur:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q in mask and q not in val: val[q] = val[(x, y)]; nxt.append(q)
        cur = nxt
    for (x, y), v in val.items(): out[y][x] = v
    for (a, b, xa, xb), ko in zip(bs, lines):
        pts, w = g.draw(ko); ys = [p[1] for p in g.draw('가')[0]]
        x0 = (xa + xb + 1) // 2 - w // 2; yt = (a + b) // 2 - (max(ys) - min(ys)) // 2
        if w > W - 4: raise SystemExit('⛔경고 화면 줄 폭 %d px: %s' % (w, ko))
        x0 = max(2, min(x0, W - 2 - w))                 # 넓은 줄은 화면 안으로 밀기
        ink = {(x0 + x, yt + y - min(ys)) for x, y in pts}
        for x, y in ink:                                # 원래 글처럼 오른쪽 아래 1px 그림자(검정)
            if (x + 1, y + 1) not in ink: out[y + 1][x + 1] = 0
        for x, y in ink: out[y][x] = 15
    return out


def all_images():
    g = Font(GAL); tx = texts(); res = {}
    for nm in TEXT:
        img, pal = E.load(nm); res[nm] = (img, new_image(nm, img, tx[nm], g), pal)
    return res


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    res = all_images()
    if '--build' in sys.argv:
        for nm, (a, b, pal) in res.items():
            nb, n = E.build(nm, b); o = os.path.join(ROOT, 'work', 'build', 'WAKTRI', nm)
            old = len(open(os.path.join(E.SRC, nm), 'rb').read())
            print(nm, '셀', n, '크기', len(nb), '/ 원래', old)
            assert E.load.__name__ and len(nb) <= ((old + 2047) // 2048) * 2048, '⛔섹터 넘침'
            open(o, 'wb').write(nb)
    else:
        from PIL import Image
        im = Image.new('RGB', (W * 2 + 8, H * 2 + 8)); px = im.load()
        for r, (nm, (a, b, pal)) in enumerate(res.items()):
            for k, m in enumerate((a, b)):
                for y in range(H):
                    for x in range(W): px[k * (W + 8) + x, r * (H + 8) + y] = pal[m[y][x]]
        p = os.path.join(ROOT, 'work', 'check', 'err_preview.png'); im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(p); print(p)
