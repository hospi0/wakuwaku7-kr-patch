# -*- coding: utf-8 -*-
r"""«SEGA SATURN SCR» 그림(.2D) 읽기 (2026-10-27)
  머리 0x20~ 구획 표(오프셋 u32, 크기 u32, 0, 0) — 구획마다 앞 16 B 머리:
    1 = 맵 64×64 u16(한 낱말 패턴 이름 = 8비트 셀 번호×2, 단위 32 B) · 2 = 셀(8×8 8비트) · 3 = 색표 RGB555 · 4 = ?(미확정)
  render(path) → PIL 그림(512×512 맵 전체) · python tools/scr2d.py <파일…> → work/2d/<이름>.png"""
import os, struct, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sections(d):
    assert d[:15] == b'SEGA SATURN SCR', d[:16]
    out = []; i = 0x20
    while i < 0x120:
        o, s = struct.unpack_from('>II', d, i)
        if o == 0 and s == 0: break
        out.append((o, s)); i += 16
    return out


def render(path):
    d = open(path, 'rb').read(); sec = sections(d)
    (mo, ms), (co, cs), (po, ps) = sec[0], sec[1], sec[2]
    cells = d[co + 16:co + cs]; pal = []
    for k in range(256):
        v = struct.unpack_from('>H', d, po + 16 + k * 2)[0] if po + 16 + k * 2 + 2 <= po + ps else 0
        pal.append(((v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3))
    im = Image.new('RGB', (512, 512)); px = im.load()
    for my in range(64):
        for mx in range(64):
            n = struct.unpack_from('>H', d, mo + 16 + (my * 64 + mx) * 2)[0] & 0x7FFF
            a = n * 32
            for y in range(8):
                row = cells[a + y * 8:a + y * 8 + 8]
                for x, b in enumerate(row): px[mx * 8 + x, my * 8 + y] = pal[b]
    return im


if __name__ == '__main__':
    out = os.path.join(ROOT, 'work', '2d'); os.makedirs(out, exist_ok=True)
    for p in sys.argv[1:]:
        render(p).crop((0, 0, 352, 240)).save(os.path.join(out, os.path.basename(p) + '.png'))
