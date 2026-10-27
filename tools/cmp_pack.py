# -*- coding: utf-8 -*-
r"""CMP 프레임 그림 바꿔 넣기 (2026-10-27) — 파일 크기·다른 타일 그대로
  pack(c, {프레임 오프셋: 128×128 색 번호 그림}) → 새 파일 바이트
  · 프레임 타일 칸마다 새 16×16 내용: 원래 번호 내용과 같으면 그대로, 다르면 «바꾸는 프레임만 쓰던 번호» 중 빈 번호를 배정(같은 내용은 한 번호)
  · 셀: 남는 타일 셀과 같으면 그 설명값 재사용, 아니면 줄 묶음(첫 줄 + 바뀌는 줄, 표시 비트)을 줄 자료(C)에서 찾아 쓰고 없으면 빈 자리(남는 타일이 안 쓰는 C·D 바이트)에 씀(긴 것부터 best-fit, 틈 앞 바이트와 겹치기)
  · 설명값 위 비트 0 = 줄 = C + (d&0xFFFFF)×4, 표시 (d>>24)&0x7F
  · 검산: 바꾼 프레임을 다시 풀어 그림과 같은지, 남는 타일 전부 원래와 같은지"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cmp, cmp_frames as F


def all_frame_tiles(c):
    """{타일 번호: {프레임 오프셋…}}"""
    use = {}
    for o in F.frame_offsets(c):
        for fl, x, y, ids, a in F.parts(c, o):
            for t in ids:
                if t > 0: use.setdefault(t, set()).add(o)
    return use


def cell_span(c, dsc):
    d = c.d; m = (dsc >> 24) & 0x7F; n = 1 + bin(m).count('1')
    if dsc >> 31:
        r = c.D + (dsc & 0x1FFFF) * 2
        base = c.C + (struct.unpack_from('>I', d, r)[0] & 0xFFFFFF) * 4
        p = base + ((dsc >> 17) & 7) * 4
        return [(p, p + 4 * n), (base, base + 32), (r, r + 4 + 2 * ((d[r + 4] >> 5) + 1))]   # 기록(D)도 덮임
    p = c.C + (dsc & 0xFFFFF) * 4
    return [(p, p + 4 * n)]


def tile_of(img, x, y):
    b = bytearray(128)
    for yy in range(16):
        for xx in range(0, 16, 2):
            b[yy * 8 + xx // 2] = img[y + yy][x + xx] << 4 | img[y + yy][x + xx + 1]
    return bytes(b)


def cells_of(tile):
    return [tuple(tile[((k >> 1) * 8 + y) * 8 + (k & 1) * 4:((k >> 1) * 8 + y) * 8 + (k & 1) * 4 + 4] for y in range(8)) for k in range(4)]


def pack(c, images):
    d = bytearray(c.d); T = c.ntiles()
    use = all_frame_tiles(c)
    changed = set(images)
    only = {t for t, fs in use.items() if fs <= changed}                 # 바꾸는 프레임만 쓰는 번호
    # 1) 칸마다 새 내용
    slots = []                                                            # (단어 위치, 원래 번호, 새 내용)
    for o, img in images.items():
        ps = F.parts(c, o); x0 = min(p[1] for p in ps); y0 = min(p[2] for p in ps)
        for fl, x, y, ids, a in ps:
            for k, t in enumerate(ids):
                if t <= 0: continue
                slots.append((a + 2 * k, t, tile_of(img, x - x0, y - y0 + 16 * k)))
    keep = {t for _, t, b in slots if c.tile(t) == b}
    free_ids = sorted(only - keep)
    newc = {}
    for _, t, b in slots:
        if t in keep and c.tile(t) == b: continue
        newc.setdefault(b, None)
    if len(newc) > len(free_ids): raise SystemExit('⛔타일 번호 모자람 %d > %d' % (len(newc), len(free_ids)))
    for b, t in zip(newc, free_ids): newc[b] = t
    for pos, t, b in slots:
        nt = t if (t in keep and c.tile(t) == b) else newc[b]
        struct.pack_into('>h', d, pos, nt)
    # 2) 남는 타일이 쓰는 C 바이트 · 남는 셀 → 설명값
    survivors = [t for t in range(1, T + 1) if t not in set(free_ids)]
    cov = bytearray(len(d)); cell_desc = {}
    for t in survivors:
        for k in range(4):
            dsc = c.desc(t, k)
            for a, b in cell_span(c, dsc):
                for i in range(a, b): cov[i] = 1
            cell_desc.setdefault(tuple(c.cell(dsc)), dsc)
    for i in range(c.D - 4, c.D): cov[i] = 1                             # D 길이 낱말
    END = c.D + c.Dn                                                      # 줄 오프셋은 C 기준이라 바로 뒤 D 의 빈 기록 자리도 쓸 수 있다
    holes = []                                                            # (시작, 끝) 4 정렬
    i = c.C
    while i < END:
        if not cov[i]:
            j = i
            while j < END and not cov[j]: j += 1
            a = (i + 3) & ~3; b = j & ~3
            if b - a >= 4: holes.append([a, b])
            i = j
        else: i += 1
    hole_bytes = sum(b - a for a, b in holes)
    # 새 셀 모으기 → 긴 줄 묶음부터 «가장 꼭 맞는 틈»(best-fit)에
    todo = {}                                                             # 셀 → (줄 묶음, 표시)
    for b_, t in newc.items():
        for cell in cells_of(b_):
            if cell in cell_desc or cell in todo: continue
            seq = [cell[0]]; m = 0
            for y in range(1, 8):
                if cell[y] != cell[y - 1]: seq.append(cell[y]); m |= 1 << (y - 1)
            todo[cell] = (b''.join(seq), m)
    Cview = bytes(d[c.C:END]); used_new = 0; reused_rows = 0
    for cell, (s_, m) in sorted(todo.items(), key=lambda kv: -len(kv[1][0])):
        p = -1; q = Cview.find(s_)
        while q >= 0:                                                     # 남는 자료·이미 쓴 새 자료 안에서 찾기(정렬 4)
            if q % 4 == 0 and all(cov[c.C + q + z] for z in range(len(s_))): p = q; break
            q = Cview.find(s_, q + 1)
        if p >= 0: reused_rows += 1
        else:
            best = None                                                   # 틈 앞 바이트와 겹치는 만큼(4 단위) 덜 씀
            for h in holes:
                ov = 0
                for k in range(len(s_) - 4, 0, -4):
                    if h[0] - k >= c.C and all(cov[h[0] - k + z] for z in range(k)) and d[h[0] - k:h[0]] == s_[:k]: ov = k; break
                need = len(s_) - ov
                if h[1] - h[0] >= need:
                    key = (-ov, h[1] - h[0])
                    if best is None or key < best[0]: best = (key, h, ov)
            if best is None: raise SystemExit('⛔줄 자료 빈 자리 모자람 (빈 자리 %d B 중 %d B 씀)' % (hole_bytes, used_new))
            _, h, ov = best
            p = h[0] - ov - c.C; d[h[0]:h[0] + len(s_) - ov] = s_[ov:]; h[0] += len(s_) - ov; used_new += len(s_) - ov
            for z in range(len(s_)): cov[c.C + p + z] = 1
            Cview = bytes(d[c.C:END])
        assert p // 4 < 0x100000
        cell_desc[cell] = (m << 24) | (p // 4)
    for b_, t in newc.items():
        for k, cell in enumerate(cells_of(b_)):
            struct.pack_into('>I', d, c.B + (t - 1) * 16 + 4 * k, cell_desc[cell])
    # 3) 검산
    n = cmp.Cmp(bytes(d))
    for t in survivors: assert n.tile(t) == c.tile(t), ('남는 타일 바뀜', t)
    for o, img in images.items():
        ps = F.parts(n, o); x0 = min(p[1] for p in ps); y0 = min(p[2] for p in ps)
        for fl, x, y, ids, a in ps:
            for k, t in enumerate(ids):
                if t > 0: assert n.tile(t) == tile_of(img, x - x0, y - y0 + 16 * k), (hex(o), t)
    assert len(d) == len(c.d)
    return bytes(d), dict(new_tiles=len(newc), free_ids=len(free_ids), hole=hole_bytes, used=used_new, reused=reused_rows)
