# -*- coding: utf-8 -*-
r"""와쿠와쿠 7 대사 읽기·추출 (2026-10-27)
  글자 번호 = FBIFIX.PXB 셀 번호(16×16 = c,c+1 / c+0x10,c+0x11), 대응 = data/font_map_src.txt
  WAK.BIN 대사 표 0x63490(8 B × 286: u8,u8, u16 글 오프셋, u16,u16) — 묶음 8개(63·63·63·36·36·9·9·7 항목)
    오프셋 셋 다 «그 묶음 첫 항목 주소» 기준 · u16 둘은 글 뒤 바이트 표(0x6A3F0~)를 가리킴 → 글은 원래 구간 안에서만 다시 쓴다
  메시지 = 줄 반복 [머리 (0x8000|들여쓰기, 0)(8자 줄은 머리 없음) · 글자 (0x8000, 번호)… · 끝 글자 (0x8000|꼬리, 번호)] + 끝 0x0000
    들여쓰기 = 8 − 글자수(8px 셀 단위 → 가운데 맞춤, 한 줄 최대 8자) · 꼬리 하위 3비트도 같은 값, 위 비트(0x90·0x68…)는 미확정 → 보존
  python tools/wak_text.py → work/text/wak_src.tsv"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE, N_ENT = 0x63490, 286
GROUPS = (0, 63, 126, 189, 225, 261, 270, 279)   # 묶음 첫 항목 번호


def font_map():
    m = {}
    for ln in open(os.path.join(ROOT, 'data', 'font_map_src.txt'), encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln or ln.startswith('#'): continue
        a, s = ln.split(' ', 1); c = int(a, 16)
        for ch in s:
            if c & 0x10: c += 0x10
            assert c not in m, hex(c); m[c] = ch; c += 2
    return m


def entries(d):
    return [struct.unpack_from('>BBHHH', d, TABLE + i * 8) for i in range(N_ENT)]


def base(i):
    return TABLE + 8 * max(g for g in GROUPS if g <= i)


def ptrs(d):
    """항목별 글 주소(파일 오프셋)"""
    return [base(i) + e[2] for i, e in enumerate(entries(d))]


def parse_msg(d, a):
    """a = 파일 오프셋 → (줄 목록[(시작 오프셋, 머리, [(속성, 번호)…])], 끝 오프셋)"""
    lines = []
    while True:
        h, z = struct.unpack_from('>HH', d, a); st = a
        if h == 0: return lines, a + 2
        assert h & 0xFFF8 == 0x8000, (hex(a), hex(h), hex(z))
        if z == 0: a += 4          # 머리 — 8자 줄(들여쓰기 0)은 머리 없이 바로 글자
        else: h = 0x8000
        cs = []
        while True:
            at, c = struct.unpack_from('>HH', d, a); a += 4
            assert at & 0xFF00 == 0x8000 and 0x700 <= c < 0x1000, (hex(a), hex(at), hex(c))
            cs.append((at, c))
            if at != 0x8000: break
        lines.append((st, h, cs))


def units(d):
    """메시지를 빈틈없이 훑고 «표가 가리키는 줄»마다 끊은 단위 목록 [(시작, [줄…], 끝0000 여부)]
    — 표 항목이 메시지 가운데 줄을 가리키기도 한다(뒷줄 공유)"""
    ptr = set(ptrs(d))
    a = min(ptr); out = []; starts = set()
    while struct.unpack_from('>H', d, a)[0] & 0xFFF8 == 0x8000:
        lines, b = parse_msg(d, a)
        cur = []
        for ln in lines:
            starts.add(ln[0])
            if ln[0] in ptr and cur: out.append((cur[0][0], cur, False)); cur = []
            cur.append(ln)
        out.append((cur[0][0], cur, True)); a = b
    assert ptr <= starts, sorted(map(hex, ptr - starts))
    return out, a


def main():
    d = open(os.path.join(ROOT, 'work', 'disc0', 'WAKTRI', 'WAK.BIN'), 'rb').read()
    fm = font_map(); E = entries(d)
    us, end = units(d)
    refs = {}
    for i, p in enumerate(ptrs(d)): refs.setdefault(p, []).append(i)
    print('단위', len(us), '표 항목', len(E), '안 가리킨 단위', sum(1 for u in us if u[0] not in refs), '글 끝', hex(end))
    out = os.path.join(ROOT, 'work', 'text'); os.makedirs(out, exist_ok=True)
    rows = ['번호\t종류\t최대\t원문\t번역\t메모\t곳']
    unk = set(); nch = 0
    for k, (o, lines, fin) in enumerate(us):
        txt = []
        for _, h, cs in lines:
            assert (h & 7) == 8 - len(cs) and (cs[-1][0] & 7) == 8 - len(cs), (hex(o), hex(h))
            for _, c in cs:
                if c not in fm: unk.add(c)
            txt.append(''.join(fm.get(c, '〓') for _, c in cs)); nch += len(cs)
        memo = '' if fin else '뒤 단위로 이어짐'
        rows.append('%04d\t대사\t8자/줄\t%s\t\t%s\tWAK.BIN@%05X 표%s' % (k + 1, '\\n'.join(txt), memo, o, ','.join(map(str, refs.get(o, [])))))
    open(os.path.join(out, 'wak_src.tsv'), 'w', encoding='utf-8-sig').write('\n'.join(rows) + '\n')
    print('글자', nch, '미등록 글자', sorted(map(hex, unk)))


if __name__ == '__main__':
    main()
