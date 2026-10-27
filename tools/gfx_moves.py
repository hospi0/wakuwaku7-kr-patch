# -*- coding: utf-8 -*-
r"""캐릭터 선택 기술표(SEL_00.CMP 프레임 14개 = 7명 × 1P·2P) 한글화 (2026-10-27)
  ① 프레임을 색 번호 그림(128×128)으로 풀고 ② 기술 이름 줄(색 2 흰색 / 10 분홍)만 지우고 갈무리7 로 같은 색·같은 가운데에 다시 씀
  ③ (--build) 바뀐 타일을 다시 셀로 나눠 넣기 — tools/cmp_pack.py
  번역 = data/번역/기술표.tsv (캐릭터 순서·줄 순서대로)
  python tools/gfx_moves.py → work/check/moves_preview.png (원본 | 새것)"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import cmp, cmp_frames as F
from bdf import Font

SRC = os.path.join(ROOT, 'work', 'disc0', 'WAKTRI', 'SEL_00.CMP')
FRAMES = [0x3592, 0x3642, 0x36F2, 0x37A2, 0x3852, 0x3902, 0x39B2]          # 1P · 2P = +0x4D0
FRAMES2 = [o + 0x4D0 for o in FRAMES]
CHARS = ['라이', '아리나', '슬래시', '댄디 J', '티세', '마루룬', '폴리탱크Ｚ']
NAME_COLORS = (2, 10)
GALMURI7 = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri7.bdf'
X0, X1 = 8, 120                         # 지우는 가로 범위(테두리 밖)


def frame_image(c, o):
    img = [[0] * 128 for _ in range(128)]
    for fl, x, y, ids, _ in F.parts(c, o):
        for k, t in enumerate(ids):
            if t <= 0: continue
            b = c.tile(t)
            for yy in range(16):
                for xx in range(16):
                    v = b[yy * 8 + xx // 2]; img[y + 64 + 16 * k + yy][x + 64 + xx] = (v >> 4) if xx % 2 == 0 else v & 15
    return img


def name_lines(img):
    """[(y0, y1, 색, x0, x1)] — 이름 색 화소가 있는 줄 묶음(가로 16~111 안)"""
    rows = [y for y in range(128) if any(img[y][x] in NAME_COLORS for x in range(16, 112))]
    out = []
    for y in rows:
        if out and y == out[-1][1] + 1: out[-1][1] = y
        else: out.append([y, y])
    res = []
    for y0, y1 in out:
        px = [(x, img[y][x]) for y in range(y0, y1 + 1) for x in range(X0, X1) if img[y][x] in NAME_COLORS]
        col = max(set(v for _, v in px), key=[v for _, v in px].count)
        res.append((y0, y1, col, min(x for x, _ in px), max(x for x, _ in px)))
    return res


def translations():
    rows = [l.split('\t') for l in open(os.path.join(ROOT, 'data', '번역', '기술표.tsv'), encoding='utf-8').read().splitlines()[1:]]
    by = {}
    for ch, ja, ko in rows: by.setdefault(ch, []).append((ja, ko))
    return [by[c] for c in CHARS]


def erase(out, img, y0, y1, xa, xb, colors):
    """글자 색 화소를 «같은 줄 좌우로 가장 가까운 바탕색»으로 메움 — 파란 바탕 위로 삐져나온 글자 자리도 제 바탕으로"""
    for y in range(y0, y1 + 1):
        for x in range(xa, xb):
            if out[y][x] not in colors: continue
            for dx in range(1, 128):
                c = [img[y][xx] for xx in (x - dx, x + dx) if 0 <= xx < 128 and img[y][xx] not in colors]
                if c: out[y][x] = c[0]; break


def command_kana(img, out, g, ko, col=11):
    """마루룬 커맨드 «レバーぐるりん+A+B» — 하늘색 줄에서 뒤 «+A+B»(마지막 잉크 덩어리 4개)만 남기고 앞을 지우고 한글"""
    rows = [y for y in range(128) if sum(1 for x in range(X0, X1) if img[y][x] == col) > 0]
    grp = []
    for y in rows:
        if grp and y == grp[-1][1] + 1: grp[-1][1] = y
        else: grp.append([y, y])
    y0, y1 = grp[-1]
    cols = [x for x in range(X0, X1) if any(img[y][x] == col for y in range(y0, y1 + 1))]
    segs = []
    for x in cols:
        if segs and x == segs[-1][1] + 1: segs[-1][1] = x
        else: segs.append([x, x])
    plus = segs[-4][0]
    erase(out, img, y0, y1, X0, plus, (col,))
    pts, w = g.draw(ko); ys = [p[1] for p in g.draw('가')[0]]
    x0 = plus - 2 - w + 1
    for x, y in pts: out[y0 + y - min(ys)][x0 + x] = col


def coverage(c, o):
    """프레임에서 타일이 있는 화소 {(x, y)} — 타일 없는 칸에 그린 화소는 넣을 때 버려진다"""
    cov = set()
    for fl, x, y, ids, _ in F.parts(c, o):
        for k, t in enumerate(ids):
            if t > 0: cov.update((x + 64 + xx, y + 64 + 16 * k + yy) for yy in range(16) for xx in range(16))
    return cov


def new_image(img, names, g, cmd=None, cov=None):
    out = [r[:] for r in img]
    lines = name_lines(img)
    assert len(lines) == len(names), (len(lines), names)
    for (y0, y1, col, xa, xb), (ja, ko) in zip(lines, names):
        erase(out, img, y0, y1, X0, X1, NAME_COLORS)
        pts, w = g.draw(ko)
        ys = [p[1] for p in g.draw('가')[0]]
        cx = (xa + xb + 1) // 2; x0 = cx - (w - 1) // 2
        if x0 < X0 or x0 + w > X1: raise SystemExit('⛔기술표 이름 폭 %d px 넘침: %s' % (w, ko))
        # 2026-10-27 실기: 첫 줄(y 15)이 타일 없는 칸에 걸려 글자 위가 잘림(라이·댄디 J·티세) → 타일 안에 다 들어갈 때까지 아래로(최대 2px)
        for dy in range(3):
            if cov is None or all((x0 + x, y0 + y - min(ys) + dy) in cov for x, y in pts): break
        else: raise SystemExit('⛔기술표 글자가 타일 밖: %s' % ko)
        for x, y in pts:
            yy = y0 + y - min(ys) + dy
            out[yy][x0 + x] = col
    if cmd: command_kana(img, out, g, cmd)
    return out


def all_images():
    c = cmp.Cmp(open(SRC, 'rb').read()); g = Font(GALMURI7); tr = translations()
    res = {}
    for i, (o1, o2) in enumerate(zip(FRAMES, FRAMES2)):
        for o in (o1, o2):
            img = frame_image(c, o); res[o] = (img, new_image(img, tr[i], g, '레버 빙글' if CHARS[i] == '마루룬' else None, coverage(c, o)))
    return c, res


def preview(res, path):
    from PIL import Image
    pal = F.palette('d1', 0x55E0)
    im = Image.new('RGB', (2 * 130 * 2, 130 * 7), (40, 40, 40))
    for i, o in enumerate(FRAMES + FRAMES2):
        a, b = res[o]
        col = (i // 7) * 2; row = i % 7
        for k, m in enumerate((a, b)):
            for y in range(128):
                for x in range(128):
                    im.putpixel(((col + k) * 130 + x, row * 130 + y), pal[m[y][x]])
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(path)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    c, res = all_images()
    p = os.path.join(ROOT, 'work', 'check', 'moves_preview.png'); preview(res, p); print('미리보기', p)


def build():
    import cmp_pack
    c, res = all_images()
    nd, st = cmp_pack.pack(c, {o: b for o, (a, b) in res.items()})
    out = os.path.join(ROOT, 'work', 'build', 'WAKTRI', 'SEL_00.CMP'); os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'wb').write(nd)
    print('기술표 → %s · 새 타일 %d(빈 번호 %d) · 줄 자료 새로 %d B(빈 자리 %d B) · 기존 줄 재사용 셀 %d · 검산 OK' % (out, st['new_tiles'], st['free_ids'], st['used'], st['hole'], st['reused']))


if __name__ == '__main__' and '--build' in sys.argv:
    build()
