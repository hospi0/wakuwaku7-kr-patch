# -*- coding: utf-8 -*-
r"""경고 화면 그림 ERRC00.2D(확장 RAM 카트리지 없음) · ERBR00.2D(백업 RAM 용량 부족) — 4bpp 16색 «SEGA SATURN SCR» (2026-10-27)
  구획: 1 맵 64×64 u16(셀 번호 = 낱말 & 0xFFF, 32 B 단위) · 2 셀(4bpp 8×8) · 3 색표 16색 · 4 0 으로 찬 자리(크기 = 셀 바이트/16)
  load(이름) → (색 번호 그림 512×512, 색표) / save(이름, 그림) → 셀 다시 만들기(같은 셀 합침) + 맵 + 구획 크기 고침"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'work', 'disc0', 'WAKTRI')


def secs(d):
    out = []; i = 0x20
    while i < 0x120:
        o, s = struct.unpack_from('>II', d, i)
        if o == 0 and s == 0: break
        out.append([o, s]); i += 16
    return out


def load(name):
    d = open(os.path.join(SRC, name), 'rb').read(); (mo, ms), (co, cs), (po, ps), _ = secs(d)
    cells = d[co + 16:co + cs]
    pal = []
    for k in range(16):
        v = struct.unpack_from('>H', d, po + 16 + k * 2)[0]; pal.append(((v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3))
    img = [[0] * 512 for _ in range(512)]
    for my in range(64):
        for mx in range(64):
            n = struct.unpack_from('>H', d, mo + 16 + (my * 64 + mx) * 2)[0] & 0xFFF
            for y in range(8):
                for x in range(8):
                    b = cells[n * 32 + y * 4 + x // 2]; img[my * 8 + y][mx * 8 + x] = (b >> 4) if x % 2 == 0 else b & 15
    return img, pal


def build(name, img):
    """→ 새 파일 바이트(구획 순서·머리 그대로, 셀·맵 다시)"""
    d = open(os.path.join(SRC, name), 'rb').read(); S = secs(d)
    (mo, ms), (co, cs), (po, ps), (zo, zs) = S
    m0 = [struct.unpack_from('>H', d, mo + 16 + i * 2)[0] for i in range(4096)]
    cells = []; idx = {}; mp = []
    for my in range(64):
        for mx in range(64):
            b = bytes((img[my * 8 + y][mx * 8 + x] << 4) | img[my * 8 + y][mx * 8 + x + 1] for y in range(8) for x in range(0, 8, 2))
            if b not in idx: idx[b] = len(cells); cells.append(b)
            mp.append((m0[my * 64 + mx] & 0xF000) | idx[b])
    cb = b''.join(cells)
    if len(cb) > cs - 16: raise SystemExit('⛔%s 셀 %d 개 = %d B > 원래 %d B' % (name, len(cells), len(cb), cs - 16))
    cb += bytes(cs - 16 - len(cb))                       # 구획 위치·크기 그대로(남는 셀 자리는 0)
    hdr = d[:0x120]; body = []
    parts = [(d[mo:mo + 16], b''.join(struct.pack('>H', w) for w in mp)), (d[co:co + 16], cb),
             (d[po:po + ps], None), (d[zo:zo + zs], None)]
    out = bytearray(hdr); table = []
    for (h, b), (o, s) in zip(parts, S):
        blob = h if b is None else h + b
        table.append((len(out), len(blob))); out += blob
    for k, (o, s) in enumerate(table): struct.pack_into('>II', out, 0x20 + 16 * k, o, s)
    return bytes(out), len(cells)


if __name__ == '__main__':
    from PIL import Image
    for nm in sys.argv[1:]:
        img, pal = load(nm)
        im = Image.new('RGB', (512, 512)); px = im.load()
        for y in range(512):
            for x in range(512): px[x, y] = pal[img[y][x]]
        im.crop((0, 0, 352, 240)).save(os.path.join(ROOT, 'work', '2d', nm + '.png'))
        print(nm, [hex(v[0] >> 3 | (v[1] >> 3) << 5 | (v[2] >> 3) << 10) for v in pal])
