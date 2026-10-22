# Step 3: theme share per year, actionable share, biggest shifts, and the top themes per half-year.
# Run: python analyze.py
import json, sys, collections


def load():
    live = json.load(open('out/likes.json', encoding='utf-8'))
    try:
        labels = json.load(open('out/labels.json', encoding='utf-8'))
    except FileNotFoundError:
        labels = {}
    if not any(tid in labels for _, tid, _ in live):
        sys.exit('no labels yet: run python label.py first')
    return live, labels


def compute(live, labels):
    rows = [(d, labels[tid]) for d, tid, _ in live if d and tid in labels]
    tab = collections.defaultdict(collections.Counter)
    act = collections.Counter()
    tot = collections.Counter()
    half = collections.defaultdict(collections.Counter)
    for d, (theme, actionable) in rows:
        y = d[:4]
        tab[y][theme] += 1
        tot[y] += 1
        act[y] += actionable
    years = sorted(tot)
    for d, (theme, _) in rows:
        if int(d[:4]) >= int(years[-1]) - 1:
            half[d[:4] + ('H1' if int(d[5:7]) <= 6 else 'H2')][theme] += 1
    themes = sorted({t for c in tab.values() for t in c}, key=lambda t: -sum(tab[y][t] for y in years))
    share = {t: {y: tab[y][t] / tot[y] for y in years} for t in themes}
    # ponytail: first vs last year only, a trend fit if two-point deltas turn out noisy
    first, last = years[0], years[-1]
    delta = sorted(themes, key=lambda t: share[t][last] - share[t][first])
    return {
        'labeled': len(rows), 'total': len(live), 'years': years, 'themes': themes,
        'share': share, 'counts': dict(tot), 'actionable': {y: act[y] / tot[y] for y in years},
        'half': {k: half[k].most_common(4) for k in sorted(half)},
        'riser': (delta[-1], share[delta[-1]][first], share[delta[-1]][last]),
        'faller': (delta[0], share[delta[0]][first], share[delta[0]][last]),
    }


if __name__ == '__main__':
    s = compute(*load())
    years = s['years']
    print('labeled', s['labeled'], 'of', s['total'])
    print('\ntheme share by year')
    print('theme'.ljust(16), *[y.rjust(6) for y in years])
    for t in s['themes']:
        print(t.ljust(16), *[f'{s["share"][t][y]:>6.0%}' for y in years])
    print('likes'.ljust(16), *[str(s['counts'][y]).rjust(6) for y in years])
    print('actionable'.ljust(16), *[f'{s["actionable"][y]:>6.0%}' for y in years])
    for k in ('riser', 'faller'):
        t, a, b = s[k]
        print(f'\nbiggest {k}: {t} {a:.0%} ({years[0]}) -> {b:.0%} ({years[-1]})', end='')
    print('\n\ntop themes by half-year (last 2 years)')
    for k, top in s['half'].items():
        print(k, str(sum(n for _, n in top)).rjust(4), top)
