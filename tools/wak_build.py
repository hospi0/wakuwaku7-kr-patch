# -*- coding: utf-8 -*-
r"""와쿠와쿠 7 한글 넣기 (2026-10-27)
  ① 글꼴: 번역에 쓰는 글자를 FBIFIX.PXB 대사 글자 칸(원래 478칸 + 빈 칸 0xFEC·0xFEE)에 배정
     · 원문 글꼴에 있는 기호(！？…♥「」ＡＢ… 등)는 원래 칸·원래 그림 그대로, 한글은 갈무리14 를 색 1 로 16×16 칸 가운데에 그림
     · 띄어쓰기 = 빈 칸 0xFEC(전각 폭) · 글자가 칸보다 많으면 실패
  ② 대사: WAK.BIN 대사 구간(표 첫 글 ~ 0x6A3F0)을 번역으로 다시 쓰고 표 오프셋(묶음 첫 항목 기준) 고침
     · 줄 = 머리 (0x8000|8−n, 0)(8자면 없음) + 글자 (0x8000, 번호)… + 끝 (위 비트 원래 값|8−n, 번호), 메시지 끝 0000
     · 한 줄 8자 넘거나 빈 줄·없는 글자 → 실패 · 구간 넘치면 실패 · 다시 읽어 번역과 같은지 검산
  python tools/wak_build.py [--preview] → work/build/ AAA.BIN · WAKTRI/WAK.BIN · WAK2.BIN · FBIFIX.PXB (+ work/check/kr_preview.png · charmap.tsv) → tools/discbuild.py
  ③ WAK2.BIN 스토리·가사·소개·조작 설명·보스전(아래 build_wak2)"""
import os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import wak_text as W
from bdf import Font

DISC = os.path.join(ROOT, 'work', 'disc0', 'WAKTRI')
OUT = os.path.join(ROOT, 'work', 'build')
GALMURI = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri14.bdf'
SPACE = 0xFEC
# 엔딩 한자 칸(恋·呪·宿·秘·宝·病·妖·精·ュ — 엔딩 글에만 쓰여 번역 뒤 비는 칸, 2026-10-27 하스피 «B: 있는 음절 위주»)
END_KANJI = (0xE26, 0xE2A, 0xE2E, 0xE44, 0xE46, 0xE48, 0xE4A, 0xE4C, 0xE4E)
EXTRA = (0xFEC, 0xFEE) + END_KANJI     # 원래 빈 칸 + 엔딩 한자 칸
SYM_EXTRA = {'♪': 0xE28}              # 대응표 밖 원래 기호 칸(엔딩 주문 끝 ♪) — 그림 그대로
TEXT_END = 0x6A3F0                     # 글 뒤 바이트 표 시작(움직이면 안 됨)
NL = chr(92) + 'n'


# 문장부호 뒤 공백 1칸은 빌더에서 지운다(전 프로젝트 표준 목록 · 2칸 이상 이어진 공백은 둔다) — 2026-10-27 실기 «문장부호 뒤 띄어쓰기»
PUNCT = ',.!?:;)]}\'"~、。，．！？：；）］｝」』】〉》”’…‥・·～〜♪♥'


def squeeze(t):
    return re.sub('([' + re.escape(PUNCT) + '])[ 　](?![ 　])', r'\1', t)


def translations():
    p = os.path.join(ROOT, 'data', '번역', '대사_ko.tsv')
    tr = {}
    for l in open(p, encoding='utf-8').read().splitlines()[1:]:
        k, t = l.split('\t'); tr[int(k)] = [squeeze(x) for x in t.split(NL)]
    return tr


def cells_of(code):
    return (code, code + 1, code + 0x10, code + 0x11)


def build_font(chars, fnt):
    """→ (글자→번호, 새 FBIFIX)"""
    src = W.font_map(); inv = {}
    for c, ch in src.items(): inv.setdefault(ch, c)
    inv.update(SYM_EXTRA)
    slots = sorted(src) + list(EXTRA)
    cmap = {' ': SPACE}
    for ch in chars:                                   # 원문에 있는 기호는 원래 칸
        if ch in inv and not ('가' <= ch <= '힣'): cmap[ch] = inv[ch]
    free = [s for s in slots if s not in cmap.values()]
    hang = sorted(c for c in chars if c not in cmap)
    if len(hang) > len(free):
        raise SystemExit('⛔글자 칸 모자람: 필요 %d, 남은 칸 %d' % (len(hang), len(free)))
    for ch, s in zip(hang, free): cmap[ch] = s
    f = bytearray(fnt); g = Font(GALMURI)
    used = set(cmap.values())
    for s in slots:                                    # 안 쓰는 칸·띄어쓰기 칸은 비움, 기호 칸은 원래 그림
        if s not in used or s == SPACE:
            for c in cells_of(s): f[c * 32:c * 32 + 32] = bytes(32)
    for ch, s in cmap.items():                         # 한글 + 원래 글꼴에 없는 기호(반각 , . — 2026-10-27 실기: 안 그려서 こ·か 가 보였다)
        if ch == ' ' or (ch in inv and not ('가' <= ch <= '힣')): continue
        if ord(ch) not in g.g: raise SystemExit('⛔갈무리14 에 없는 글자: ' + ch)
        px = [[0] * 16 for _ in range(16)]
        for x, y in g.draw(ch)[0]:
            xx, yy = x + 1, y - 3
            if 0 <= xx < 16 and 0 <= yy < 16: px[yy][xx] = 1
        for k, c in enumerate(cells_of(s)):
            ox, oy = (k & 1) * 8, (k >> 1) * 8
            for y in range(8):
                for x in range(0, 8, 2):
                    f[c * 32 + y * 4 + x // 2] = px[oy + y][ox + x] << 4 | px[oy + y][ox + x + 1]
    return cmap, bytes(f)


def build_text(d, cmap, tr):
    us, end = W.units(d); assert end == TEXT_END, hex(end)
    E = W.entries(d); P = W.ptrs(d)
    start = us[0][0]; out = bytearray(); newoff = {}
    for k, (o, lines, fin) in enumerate(us, 1):
        assert fin, ('표가 메시지 가운데를 가리킴', hex(o))
        up = {cs[-1][0] & 0xF8 for _, h, cs in lines}; assert len(up) == 1, hex(o); up = up.pop()
        newoff[o] = start + len(out)
        for ln in tr[k]:
            n = len(ln)
            if not 1 <= n <= 8: raise SystemExit('⛔%04d 줄 길이 %d: %s' % (k, n, ln))
            if n < 8: out += struct.pack('>HH', 0x8000 | (8 - n), 0)
            for i, ch in enumerate(ln):
                if ch not in cmap: raise SystemExit('⛔%04d 없는 글자 %r' % (k, ch))
                out += struct.pack('>HH', (0x8000 | up | (8 - n)) if i == n - 1 else 0x8000, cmap[ch])
        out += b'\0\0'
    if start + len(out) > TEXT_END:
        raise SystemExit('⛔대사 구간 넘침 %d B' % (start + len(out) - TEXT_END))
    nd = bytearray(d)
    nd[start:TEXT_END] = bytes(out) + bytes(TEXT_END - start - len(out))
    for i in range(len(E)):
        off = newoff[P[i]] - W.base(i); assert 0 <= off < 0x10000
        struct.pack_into('>H', nd, W.TABLE + i * 8 + 2, off)
    # 검산: 다시 읽어 번역과 같은지 + 구간 밖 바이트 그대로
    inv = {v: c for c, v in cmap.items()}
    for i in range(len(E)):
        a = W.base(i) + struct.unpack_from('>H', nd, W.TABLE + i * 8 + 2)[0]
        lines, _ = W.parse_msg(bytes(nd), a)
        k = [kk for kk, u in enumerate(us, 1) if u[0] == P[i]][0]
        got = [''.join(inv[c] for _, c in cs) for _, h, cs in lines]
        assert got == tr[k], (i, got, tr[k])
    diff = [j for j in range(len(d)) if d[j] != nd[j] and not (start <= j < TEXT_END or W.TABLE <= j < W.TABLE + 8 * len(E))]
    assert not diff, ('구간 밖 바뀜', diff[:5])
    return bytes(nd), len(out), TEXT_END - start


def preview(fnt, cmap, tr, ks, path):
    from PIL import Image
    sys.path.insert(0, HERE)
    def glyph(f, c):
        im = Image.new('L', (16, 16))
        for k, cc in enumerate(cells_of(c)):
            for y in range(8):
                for x in range(8):
                    b = f[cc * 32 + y * 4 + x // 2]; v = (b >> 4) if x % 2 == 0 else b & 15
                    if v: im.putpixel(((k & 1) * 8 + x, (k >> 1) * 8 + y), 255)
        return im
    rows = []                                          # 게임처럼 들여쓰기 (8−n)×8px · 줄 간격 24px(맵 3행)
    for k in ks:
        rows += tr[k]; rows.append('')
    im = Image.new('RGB', (16 * 8 + 16, 24 * len(rows) + 16), (248, 248, 232))
    for r, ln in enumerate(rows):
        x0 = 8 + (8 - len(ln)) * 8
        for i, ch in enumerate(ln):
            if ch == ' ': continue
            m = glyph(fnt, cmap[ch])
            im.paste((0, 0, 0), (x0 + i * 16, 8 + r * 24), m)
    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(path)


# ── WAK2.BIN (오버레이, 저속 RAM 0x00200000 에 통째) ─────────────────────────────
# 글은 포인터 없이 앞 표(시간·위치)를 따라 메시지를 차례로 읽는다 → 메시지 수·메시지별 줄 수를 지키고 구간 안에서 제자리 다시 쓰기
#   머리 있는 줄: 머리 = K − n, 끝 = T − n (K·T 는 원래 줄에서 셈 — 스토리·가사 K 19 · 조작 설명 말풍선 K 8)
#   머리 없는 줄: 끝 = C − 2n (소개·보스전 C 0x50 · 조작 설명 C 0x78)
#   가사 두 번째 벌: 글자마다 속성 위 바이트 = 0x80 + 박자 → 원래 줄 박자 합을 새 글자 수로 나눔(ＷＡＫＵＷＡＫＵ 앞머리는 원래 값, 띄어쓰기 0, 끝 글자 원래 값)
W2_REGIONS = (('스토리·가사·소개', 0x5C00), ('조작 설명', 0x20F04), ('거대 보스전', 0x23BCC), ('엔딩', 0x1C7D2))
# 엔딩(2026-10-27 실기 «엔딩 미번역»): 0x1C7D2~0x1DB9E 앞뒤가 코드 → 늘릴 수 없음 · 글자 번호 위 4비트 = 팔레트(줄마다 원래 값 유지)
#   메시지는 장면 기록 표(8 B = 시간, 일 오프셋|깃발 비트0, 영, 서 · 0xFFFF 끝, 오프셋 = 표 시작 기준)로 찾는다 — 8개, 같은 메시지 여러 번 가리키기도 함
W2_END_TABLES = (0x17CA2, 0x185DC, 0x18BE4, 0x19948, 0x1A2C8, 0x1AD56, 0x1B6B0, 0x1BD30)
W2_END_FM = {c: '?' for c in END_KANJI + (0xE28,)}
# 2026-10-27 하스피 «스페인어까지 써»: 첫 구간은 뒤 영어·스페인어 글(0x67DE~0x7506)까지 덮어 씀 → 옵션 LANGUAGE ENGLISH/SPANISH 의 스토리·소개는 깨짐(감수)
W2_LIMIT = {0x5C00: 0x7506}
W2_MAXW = 18                            # 머리 없는 줄 최대 글자 = 원문 최대 18 (2026-10-27 실기: 소개 20자 줄이 화면 밖으로 넘어 다음 줄 왼쪽에 찍힘)
# 2026-10-27 실기 크래시(스토리 3번째 메시지 = 원문 위치 0x5C8E 를 읽다 홀수 주소 쓰기) → 메시지 시작은 표의 u16 오프셋으로 찾는다
#   (표 범위, 기준 주소, 부호): 스토리 0x5B9E · 가사 두 벌 0x5BC2 · 소개 0x7508(부호, 일·영·서 3칸 중 일) · 조작 설명 0x20EB4 · 보스전 0x23B70
#   원문 값이 «기준+값 = 원래 메시지 시작»인 낱말을 찾아 새 시작으로 고친다(메시지마다 정확히 한 번씩 걸려야 함)
W2_TABLES = ((0x5B80, 0x5C00, 0x5B9E, False), (0x5B80, 0x5C00, 0x5BC2, False), (0x7506, 0x7536, 0x7508, True),
             (0x20EA0, 0x20F04, 0x20EB4, False), (0x23B60, 0x23BCC, 0x23B70, False))
WAKU = 'ＷＡＫＵＷＡＫＵ'


def w2_parse(d, a, fm):
    """→ (메시지[[(머리|None, [(속성, 번호)…])…]…], 끝 오프셋) — 글이 아닌 낱말을 만나면 멈춤"""
    msgs, cur = [], []
    while True:
        h, z = struct.unpack_from('>HH', d, a)
        if h == 0 and cur:
            msgs.append(cur); cur = []; a += 2; continue
        if h & 0xFF00 == 0x8000 and z == 0: hd = h & 0xFF; b = a + 4
        elif h >> 15 and (z & 0xFFF) in fm: hd = None; b = a
        else: break
        cs = []
        while True:
            at, c = struct.unpack_from('>HH', d, b); b += 4
            assert (c & 0xFFF) in fm, (hex(b), hex(at), hex(c)); cs.append((at, c))
            if at & 0xFF: break
        cur.append((hd, cs)); a = b
    assert not cur, hex(a)
    return msgs, a


def w2_translations():
    secs, cur = [], None
    for l in open(os.path.join(ROOT, 'data', '번역', 'wak2_ko.txt'), encoding='utf-8').read().splitlines():
        if l.startswith('#'): continue
        if l.startswith('['): cur = {'name': l, 'msgs': [[]]}; secs.append(cur); continue
        if not l:
            if cur and cur['msgs'][-1]: cur['msgs'].append([])
            continue
        cur['msgs'][-1].append(squeeze(l))
    for s in secs:
        if not s['msgs'][-1]: s['msgs'].pop()
    return secs


def w2_ending():
    """data/번역/엔딩_ko.txt — 줄마다 «번호	번역», « / » = 줄바꿈"""
    out = []
    for l in open(os.path.join(ROOT, 'data', '번역', '엔딩_ko.txt'), encoding='utf-8').read().splitlines():
        if not l or l.startswith('#'): continue
        k, t = l.split('	'); assert int(k) == len(out), k
        out.append([squeeze(x) for x in t.split(' / ')])
    return out


def w2_line(orig, ko, cmap):
    hd, cs = orig; n0, n = len(cs), len(ko)
    pal = cs[0][1] & 0xF000; assert all(c & 0xF000 == pal for _, c in cs)   # 엔딩 글자 색(줄마다 하나)
    tail0 = cs[-1][0] & 0xFF
    kara = any(at >> 8 != 0x80 for at, _ in cs)
    if hd is not None:
        K, T = hd + n0, tail0 + n0
        if not 1 <= n < K: raise SystemExit('⛔WAK2 줄 길이 %d (최대 %d): %s' % (n, K - 1, ko))
        out = struct.pack('>HH', 0x8000 | (K - n), 0); tail = T - n
    else:
        C = tail0 + 2 * n0
        if not 1 <= n <= W2_MAXW or C - 2 * n < 1: raise SystemExit('⛔WAK2 줄 길이 %d: %s' % (n, ko))
        out = b''; tail = C - 2 * n
    his = [0x80] * n
    if kara:
        pre = 0
        if ko.startswith(WAKU) and ''.join(W.font_map()[c] for _, c in cs[:8]) == WAKU:
            pre = 8; his[:8] = [at >> 8 for at, _ in cs[:8]]
        tot = sum((at >> 8) - 0x80 for at, _ in cs[pre:-1])
        idx = [i for i in range(pre, n - 1) if ko[i] != ' ']
        for k, i in enumerate(idx): his[i] = 0x80 + tot // len(idx) + (1 if k < tot % len(idx) else 0)
        his[-1] = cs[-1][0] >> 8
        assert all(0x80 <= h <= 0xFF for h in his), his
    for i, ch in enumerate(ko):
        if ch not in cmap: raise SystemExit('⛔WAK2 없는 글자 %r' % ch)
        out += struct.pack('>HH', (his[i] << 8) | (tail if i == n - 1 else 0), pal | cmap[ch])
    return out


def build_wak2(d2, cmap):
    fm = W.font_map(); secs = w2_translations()
    # 원문 메시지 순서: 스토리 6 · 가사 8 · 소개 7 · 가사(박자) 8 | 조작 설명 10 | 보스 5
    by = {s['name']: s['msgs'] for s in secs}
    lyr = by['[가사 — 두 벌 같은 글]']
    plan = [by['[스토리]'] + lyr + [m for k in ('[라이]', '[아리나]', '[스래시]', '[댄디 J]', '[티세]', '[마루룬]', '[폴리탱크Ｚ]') for m in by[k]] + lyr,
            by['[조작 설명]'], by['[거대 보스전]'], w2_ending()]
    nd = bytearray(d2); total = []
    starts = {}                                              # 원래 메시지 시작 → 새 시작
    fm_end = dict(fm); fm_end.update(W2_END_FM)
    for (name, a0), kos in zip(W2_REGIONS, plan):
        msgs, end = w2_parse(d2, a0, fm_end if name == '엔딩' else fm)
        if name == '엔딩': end_starts = set()
        a = a0
        for m in msgs:
            starts[a] = None
            if name == '엔딩': end_starts.add(a)
            a += sum((4 if hd is not None else 0) + 4 * len(cs) for hd, cs in m) + 2
        flat = [l for m in kos for l in m]                   # 번역 줄을 원래 메시지별 줄 수대로 나눔
        if len(flat) != sum(len(m) for m in msgs):
            raise SystemExit('⛔WAK2 %s 줄 수 %d ≠ 번역 %d' % (name, sum(len(m) for m in msgs), len(flat)))
        kos = []
        for m in msgs: kos.append(flat[:len(m)]); flat = flat[len(m):]
        out = b''; a = a0
        for m, ko in zip(msgs, kos):
            if len(m) != len(ko): raise SystemExit('⛔WAK2 %s 줄 수 %d ≠ %d: %s' % (name, len(m), len(ko), ko))
            starts[a] = a0 + len(out)
            a += sum((4 if hd is not None else 0) + 4 * len(cs) for hd, cs in m) + 2
            for ln, k in zip(m, ko): out += w2_line(ln, k, cmap)
            out += b'\0\0'
        lim = max(end, W2_LIMIT.get(a0, end))
        if len(out) > lim - a0: raise SystemExit('⛔WAK2 %s 구간 넘침 %d > %d' % (name, len(out), lim - a0))
        if a0 + len(out) > end: end = lim                  # 영어·스페인어 자리까지 쓰면 그 끝까지 0 으로
        nd[a0:end] = out + bytes(end - a0 - len(out))
        # 검산: 다시 읽어 번역과 같은지
        inv = {v: c for c, v in cmap.items()}
        got, _ = w2_parse(bytes(nd), a0, {v: 1 for v in cmap.values()})
        assert [[''.join(inv[c & 0xFFF] for _, c in cs) for _, cs in m] for m in got] == kos, name
        total.append('%s %d/%d B' % (name, len(out), end - a0))
    # 메시지 시작 오프셋 표 고치기
    hit = {}
    for t0, t1, base, sg in W2_TABLES:
        f = '>h' if sg else '>H'
        for p in range(t0, t1, 2):
            s = base + struct.unpack_from(f, d2, p)[0]
            if s in starts:
                hit[s] = hit.get(s, 0) + 1
                struct.pack_into(f, nd, p, starts[s] - base)
    want = set(starts) - end_starts
    if sorted(hit) != sorted(want) or set(hit.values()) != {1}:
        raise SystemExit('⛔WAK2 오프셋 표: 메시지 %d 중 %d 개만(중복 %s)' % (len(want), len(hit), [hex(s) for s, n in hit.items() if n > 1]))
    ehit = set(); nrec = 0
    for B in W2_END_TABLES:
        q = B
        while struct.unpack_from('>H', d2, q)[0] != 0xFFFF:
            w = struct.unpack_from('>H', d2, q + 2)[0]; s = B + (w & ~1)
            if s not in end_starts: raise SystemExit('⛔엔딩 기록 표 0x%X: 메시지 시작이 아님 0x%X' % (q, s))
            struct.pack_into('>H', nd, q + 2, (starts[s] - B) | (w & 1)); ehit.add(s); nrec += 1; q += 8
    if ehit != end_starts: raise SystemExit('⛔엔딩 기록 표가 안 가리키는 메시지 %d 개' % len(end_starts - ehit))
    total.append('오프셋 표 %d 곳 + 엔딩 기록 %d 개' % (len(hit), nrec))
    return bytes(nd), total


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    d = open(os.path.join(DISC, 'WAK.BIN'), 'rb').read()
    d2 = open(os.path.join(DISC, 'WAK2.BIN'), 'rb').read()
    fnt = open(os.path.join(DISC, 'FBIFIX.PXB'), 'rb').read()
    tr = translations()
    chars = set(''.join(''.join(v) for v in tr.values()))
    chars |= set(''.join(l for s in w2_translations() for m in s['msgs'] for l in m))
    chars |= set(''.join(l for m in w2_ending() for l in m))
    cmap, nf = build_font(chars, fnt)
    nd, n, cap = build_text(d, cmap, tr)
    nd2, w2s = build_wak2(d2, cmap)
    print('WAK2:', ' · '.join(w2s))
    os.makedirs(os.path.join(OUT, 'WAKTRI'), exist_ok=True)
    for rel, b in (('AAA.BIN', nd), ('WAKTRI/WAK.BIN', nd), ('WAKTRI/WAK2.BIN', nd2), ('WAKTRI/FBIFIX.PXB', nf)):
        open(os.path.join(OUT, rel), 'wb').write(b)               # AAA.BIN = 부팅 파일(WAK.BIN 과 같은 내용, 따로 있는 사본)
    open(os.path.join(ROOT, 'work', 'check', 'charmap.tsv'), 'w', encoding='utf-8').write(
        ''.join('%03X\t%s\n' % (c, ch) for ch, c in sorted(cmap.items(), key=lambda x: x[1])))
    print('글자 %d종(칸 %d) · 대사 %d B / %d B · 검산 OK → work/build/WAK.BIN, FBIFIX.PXB' % (len(cmap), len(W.font_map()) + len(EXTRA), n, cap))
    if '--preview' in sys.argv:
        p = os.path.join(ROOT, 'work', 'check', 'kr_preview.png')
        preview(nf, cmap, tr, [1, 3, 5, 29, 48, 117, 134, 246], p); print('미리보기', p)


if __name__ == '__main__':
    main()
