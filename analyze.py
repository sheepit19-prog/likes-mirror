# Step 3: theme share per year, actionable share, and the top themes per half-year.
# Run: python analyze.py
import json, collections

live = json.load(open('out/likes.json', encoding='utf-8'))
labels = json.load(open('out/labels.json', encoding='utf-8'))
rows = [(d, labels[tid]) for d, tid, _ in live if d and tid in labels]
print('labeled', len(rows), 'of', len(live))

tab = collections.defaultdict(collections.Counter)
act = collections.Counter()
tot = collections.Counter()
for d, (theme, actionable) in rows:
    y = d[:4]
    tab[y][theme] += 1
    tot[y] += 1
    act[y] += actionable
years = sorted(tot)
themes = sorted({t for c in tab.values() for t in c}, key=lambda t: -sum(tab[y][t] for y in years))

print('\ntheme share by year')
print('theme'.ljust(16), *[y.rjust(6) for y in years])
for t in themes:
    print(t.ljust(16), *[f'{tab[y][t] / tot[y]:>6.0%}' for y in years])
print('likes'.ljust(16), *[str(tot[y]).rjust(6) for y in years])
print('actionable'.ljust(16), *[f'{act[y] / tot[y]:>6.0%}' for y in years])

print('\ntop themes by half-year (last 2 years)')
half = collections.defaultdict(collections.Counter)
for d, (theme, _) in rows:
    if int(d[:4]) >= int(years[-1]) - 1:
        half[d[:4] + ('H1' if int(d[5:7]) <= 6 else 'H2')][theme] += 1
for k in sorted(half):
    print(k, str(sum(half[k].values())).rjust(4), half[k].most_common(4))
