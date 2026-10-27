# -*- coding: utf-8 -*-
r"""글자 칸 예산 검사 (2026-10-27) — 번역(대사_ko.tsv + wak2_ko.txt)에 쓰인 글자 종류 수 vs 칸 480
  data/번역/글자줄이기.tsv(번호 · 바꿀 말 · 새 말 · 이유)를 적용한 결과도 셈 — 번호 «W2» = wak2_ko.txt
  python tools/glyph_budget.py [--apply 없이 셈만] → 글자 종류, 한 번만 쓰인 글자와 쓰인 곳"""
import collections, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = 480
NL = chr(92) + 'n'


def load():
    tr = dict(l.split('\t') for l in open(os.path.join(ROOT, 'data', '번역', '대사_ko.tsv'), encoding='utf-8').read().splitlines()[1:])
    w2 = [l for l in open(os.path.join(ROOT, 'data', '번역', 'wak2_ko.txt'), encoding='utf-8').read().splitlines()
          if l and not l.startswith(('#', '['))]
    tr['W2'] = NL.join(w2)
    return tr


def subs():
    p = os.path.join(ROOT, 'data', '번역', '글자줄이기.tsv')
    if not os.path.exists(p): return []
    return [l.split('\t') for l in open(p, encoding='utf-8').read().splitlines()[1:] if l.strip()]


def apply(tr, ss):
    tr = dict(tr); bad = []
    for k, a, b, *_ in ss:
        if a not in tr[k]: bad.append((k, a)); continue
        tr[k] = tr[k].replace(a, b)
    return tr, bad


def count(tr):
    return collections.Counter(c for t in tr.values() for c in t.replace(NL, '') if c != ' ')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    tr0 = load(); c0 = count(tr0)
    tr, bad = apply(tr0, subs()); c = count(tr)
    print('글자 종류 %d → %d (칸 %d, %s)' % (len(c0), len(c), CAP, '들어감' if len(c) <= CAP else '%d 넘침' % (len(c) - CAP)))
    if bad: print('못 찾은 바꿀 말:', bad)
    print('새로 생긴 글자:', ''.join(sorted(set(c) - set(c0))))
    if '-v' in sys.argv:
        for ch, n in sorted(c.items(), key=lambda x: x[1]):
            if n > 2: break
            ks = [k for k, t in tr.items() if ch in t]
            print(n, ch, ' | '.join('%s %s' % (k, tr[k].replace(NL, '/')[:60]) for k in ks[:2]))
