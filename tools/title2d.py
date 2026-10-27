# -*- coding: utf-8 -*-
r"""타이틀 TYTLE_00.2D(8bpp 256색 SCR) 읽기·다시 만들기 (2026-10-27)
  구획: 1 맵 64×64 u16(셀 번호 = 낱말 & 0x7FFF, 32 B 단위 → 8bpp 셀은 번호 2씩) · 2 셀(8×8 8bpp) · 3 색표 256 · 4 0
  load() → (색 번호 그림 512×512, 색표[(r,g,b)]) / build(그림) → 새 파일 바이트(같은 셀 합침, 셀 구획 원래 크기로 채움)"""
import os, struct
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'work', 'disc0', 'WAKTRI', 'TYTLE_00.2D')


def secs(d):
    out = []; i = 0x20
    while i < 0x120:
        o, s = struct.unpack_from('>II', d, i)
        if o == 0 and s == 0: break
        out.append([o, s]); i += 16
    return out


def load(src=None):
    d = open(src or SRC, 'rb').read(); (mo, ms), (co, cs), (po, ps), _ = secs(d)
    cells = d[co + 16:co + cs]
    pal = []
    for k in range(256):
        v = struct.unpack_from('>H', d, po + 16 + k * 2)[0]; pal.append(((v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3))
    img = [[0] * 512 for _ in range(512)]
    for my in range(64):
        for mx in range(64):
            n = struct.unpack_from('>H', d, mo + 16 + (my * 64 + mx) * 2)[0] & 0xFFF
            for y in range(8):
                row = cells[n * 32 + y * 8:n * 32 + y * 8 + 8]
                for x in range(8): img[my * 8 + y][mx * 8 + x] = row[x]
    return img, pal


def build(img, src=None):
    d = open(src or SRC, 'rb').read(); S = secs(d); (mo, ms), (co, cs), (po, ps), (zo, zs) = S
    m0 = [struct.unpack_from('>H', d, mo + 16 + i * 2)[0] for i in range(4096)]
    cells = []; idx = {}; mp = []
    for my in range(64):
        for mx in range(64):
            b = bytes(img[my * 8 + y][mx * 8 + x] for y in range(8) for x in range(8))
            if b not in idx: idx[b] = len(cells); cells.append(b)
            mp.append((m0[my * 64 + mx] & 0xF000) | idx[b] * 2)
    cb = b''.join(cells)
    if len(cb) > cs - 16: raise SystemExit('⛔타이틀 셀 %d 개 = %d B > 원래 %d B' % (len(cells), len(cb), cs - 16))
    cb += bytes(cs - 16 - len(cb))
    out = bytearray(d)
    out[mo + 16:mo + ms] = b''.join(struct.pack('>H', w) for w in mp)
    out[co + 16:co + cs] = cb
    return bytes(out), len(cells)


if __name__ == '__main__':
    img, pal = load(); nb, n = build(img)
    open(SRC + '.rt', 'wb').write(nb); s0 = SRC; SRC = SRC + '.rt'; img2, _ = load(); SRC = s0; os.remove(s0 + '.rt')
    print('셀', n, '크기 같음', len(nb) == len(open(SRC, 'rb').read()), '다시 풀어 그림 같음', img2 == img)
