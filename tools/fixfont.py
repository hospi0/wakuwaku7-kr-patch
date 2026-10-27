# -*- coding: utf-8 -*-
r"""글꼴 FBIFIX.PXB(8×8 4bpp 셀, 무압축 131,072 B → VDP2 VRAM 0x20000) — 16×16 글자 = 셀 c, c+1(위) · c+0x10, c+0x11(아래) — 스테이트 NBG3 맵 0x24000 으로 확정(2026-10-27)  (2026-10-27)
  글 = (속성 u16 0x80xx, 글자 번호 u16 짝수) 쌍 열(본체 WAK.BIN · WAK2.BIN)
  glyph(c) → 16×16 L 그림 · python tools/fixfont.py → work/check/text_<파일>.png(글 덩어리 앞부분 미리보기)"""
import os, struct, sys
from PIL import Image, ImageOps
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = open(os.path.join(ROOT, 'work', 'disc0', 'WAKTRI', 'FBIFIX.PXB'), 'rb').read()


def cell(c):
    im = Image.new('L', (8, 8)); px = im.load()
    for y in range(8):
        for x in range(8):
            b = F[c * 32 + y * 4 + x // 2]; px[x, y] = ((b >> 4) if x % 2 == 0 else b & 15) * 17
    return im


def glyph(c):
    im = Image.new('L', (16, 16))
    for dx, dy, cc in ((0, 0, c), (8, 0, c + 1), (0, 8, c + 0x10), (8, 8, c + 0x11)): im.paste(cell(cc), (dx, dy))
    return im


def runs(d):
    def ok(i):
        a, b = struct.unpack_from('>HH', d, i)
        return (a >> 8) in range(0x80, 0xE0) and 0x0700 <= b < 0x1000 and b % 2 == 0
    out = []; i = 0
    while i < len(d) - 4:
        if ok(i):
            s = i
            while i < len(d) - 4 and ok(i): i += 4
            if i - s >= 12: out.append((s, [struct.unpack_from('>H', d, k + 2)[0] for k in range(s, i, 4)]))
        else:
            i += 2
    return out


if __name__ == '__main__':
    for fn in ('WAK.BIN', 'WAK2.BIN'):
        d = open(os.path.join(ROOT, 'work', 'disc0', 'WAKTRI', fn), 'rb').read()
        rs = runs(d)[:40]
        W = max(len(c) for _, c in rs)
        im = Image.new('L', (W * 16, len(rs) * 18))
        for r, (s, cs) in enumerate(rs):
            for k, c in enumerate(cs): im.paste(glyph(c), (k * 16, r * 18))
        ImageOps.autocontrast(im).save(os.path.join(ROOT, 'work', 'check', 'text_%s.png' % fn))
        print(fn, '덩어리', len(runs(d)))
