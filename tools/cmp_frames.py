# -*- coding: utf-8 -*-
r"""CMP 프레임(타일 배치) 읽기·그리기 (2026-10-27)
  애니 표: 머리 표 u32[i] → (u16 프레임 오프셋, u16 ?) 목록 · 프레임 = 0x300(S+12) + 오프셋 · 부분 = u16 (깃발<<8|개수), s16 x, s16 y, s16 타일×개수(세로로 16px 씩, 0 이하는 빈칸)
  python tools/cmp_frames.py <CMP> <스테이트이름> <colr16진> <첫오프셋16진,…> → work/check/frame_<오프셋>.png"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import cmp
FB = 0x300


def frame_offsets(c):
    d = c.d; offs = set()
    for i in range(1, len(c.frames)):
        a = c.frames[i]
        if a == 0: continue
        b = min([x for x in c.frames if x > a] + [FB])
        offs.update(struct.unpack_from('>H', d, p)[0] for p in range(a, b, 4))
    return sorted(offs)


def parts(c, o):
    offs = frame_offsets(c); i = offs.index(o)
    e = FB + (offs[i + 1] if i + 1 < len(offs) else c.B - 4 - FB)
    a = FB + o; out = []
    while a < e:
        w, x, y = struct.unpack_from('>Hhh', c.d, a); n = w & 0xFF; a += 6
        out.append((w >> 8, x, y, list(struct.unpack_from('>%dh' % n, c.d, a)), a)); a += 2 * n
    return out


def render(c, o, pal):
    from PIL import Image
    ps = parts(c, o)
    x0 = min(p[1] for p in ps); y0 = min(p[2] for p in ps)
    W = max(p[1] for p in ps) - x0 + 16; H = max(p[2] + 16 * len(p[3]) for p in ps) - y0
    im = Image.new('RGB', (W, H), (60, 60, 60))
    for fl, x, y, ids, _ in ps:
        for k, t in enumerate(ids):
            if t <= 0: continue
            b = c.tile(t)
            for yy in range(16):
                for xx in range(16):
                    v = b[yy * 8 + xx // 2]; p = (v >> 4) if xx % 2 == 0 else v & 15
                    im.putpixel((x - x0 + xx, y - y0 + 16 * k + yy), pal[p])
    return im


def palette(state, colr):
    cram = open(os.path.join(ROOT, 'work', 'mem', state, 'CRAM.bin'), 'rb').read()
    u = [struct.unpack_from('>H', cram, (((colr & ~15) + i) % 2048) * 2)[0] for i in range(16)]
    return [((x & 31) << 3, (x >> 5 & 31) << 3, (x >> 10 & 31) << 3) for x in u]


if __name__ == '__main__':
    c = cmp.Cmp(open(sys.argv[1], 'rb').read()); pal = palette(sys.argv[2], int(sys.argv[3], 16))
    for o in sys.argv[4].split(','):
        render(c, int(o, 16), pal).save(os.path.join(ROOT, 'work', 'check', 'frame_%s.png' % o))
