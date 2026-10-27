# -*- coding: utf-8 -*-
r"""*.CMP 스프라이트 묶음 읽기 (2026-10-27, AAA.BIN 0x06019DD8~ · 셀 해제 0x06018AEE · 바이트 고치기 0x06018B10 에서 풀어냄)
  파일 = u32 프레임 수×4 … 구획 넷(각 구획 앞 u32 = 길이):
    F 프레임 오프셋 표(0x4~) · 프레임(타일 배치: u16 (깃발<<8|개수), x, y, 타일 번호…)
    B 타일 설명값 — 타일(1부터)마다 u32 ×4 = 셀 UL·UR·LL·LR
    C 줄 자료 — 4 B(8px 4bpp) 줄
    D 기록 — (u32 줄 위치/4 (아래 24비트)) + 고치기 목록(첫 바이트 위 3비트 n → 쌍 n+1 개, 쌍 = (줄 자료 기준 바이트 0~31, 값))
  셀 설명값 d: 표시 m = (d>>24)&0x7F (비트 k = k+1 번째 줄 새로 읽기, 0 = 앞 줄 반복, 0 번째 줄은 늘 새로)
    d 위 비트 0: 줄 = C + (d & 0xFFFFF)×4
    d 위 비트 1: 기록 r = D + (d & 0x1FFFF)×2 → 바탕 = C + (u32(r)&0xFFFFFF)×4, 바탕에 고치기 목록 적용, 줄 = 바탕 + ((d>>17)&7)×4
  python tools/cmp.py <CMP> → 구획 정보"""
import os, struct, sys


class Cmp:
    def __init__(self, data):
        self.d = d = data
        nf = struct.unpack_from('>I', d, 0)[0] // 4
        self.frames = [struct.unpack_from('>I', d, 4 * i)[0] for i in range(nf)]
        a = self.frames[-1]                      # 프레임 끝
        while True:                              # 프레임 구획 뒤 첫 «길이» 를 찾기: 구획 셋이 파일 끝에 정확히 닿는 자리
            ok = self._try(a)
            if ok: break
            a += 2
            assert a < len(d), '구획 못 찾음'
        self.B, self.Bn, self.C, self.Cn, self.D, self.Dn = ok

    def _try(self, a):
        d = self.d; r = []; p = a
        for _ in range(3):
            if p + 4 > len(d): return None
            n = struct.unpack_from('>I', d, p)[0]
            if n == 0 or p + 4 + n > len(d): return None
            r += [p + 4, n]; p += 4 + n
        return r if p == len(d) else None

    def ntiles(self): return self.Bn // 16

    def desc(self, t, k): return struct.unpack_from('>I', self.d, self.B + (t - 1) * 16 + 4 * k)[0]

    def cell(self, dsc):
        d = self.d; m = (dsc >> 24) & 0x7F
        if dsc >> 31:
            r = self.D + (dsc & 0x1FFFF) * 2
            base = self.C + (struct.unpack_from('>I', d, r)[0] & 0xFFFFFF) * 4
            buf = bytearray(d[base:base + 64])
            n = d[r + 4] >> 5
            for i in range(n + 1):                                # 0x06018B10: r5 ≤ 끝 까지 → 쌍 n+1 개
                o, v = d[r + 4 + 2 * i] & 31, d[r + 5 + 2 * i]
                buf[o] = v
            src = bytes(buf); p = ((dsc >> 17) & 7) * 4
        else:
            src = d; p = self.C + (dsc & 0xFFFFF) * 4
        rows = [src[p:p + 4]]; p += 4
        for k in range(7):
            if m >> k & 1: rows.append(src[p:p + 4]); p += 4
            else: rows.append(rows[-1])
        return rows

    def tile(self, t):
        """16×16 4bpp(줄 8 B) 128 B"""
        out = bytearray(128)
        for k in range(4):
            rows = self.cell(self.desc(t, k))
            for y in range(8):
                o = ((k >> 1) * 8 + y) * 8 + (k & 1) * 4
                out[o:o + 4] = rows[y]
        return bytes(out)


if __name__ == '__main__':
    c = Cmp(open(sys.argv[1], 'rb').read())
    print('프레임 %d · 타일 설명 0x%X(%d) · 줄 0x%X(%d) · 기록 0x%X(%d) · 타일 %d' % (len(c.frames), c.B, c.Bn, c.C, c.Cn, c.D, c.Dn, c.ntiles()))
