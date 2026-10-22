# How good are the labels? Label a random sample yourself, blind, then compare with the model.
# Run: python eval.py sample [--n 50]   -> out/eval.csv (fill in your_theme and your_actionable)
#      python eval.py score             -> agreement and every disagreement
import argparse, csv, io, json, random, collections
from label import THEMES

CSV, IDS = 'out/eval.csv', 'out/eval_ids.json'  # ids live in a sidecar: Excel mangles 19-digit numbers


def sample(n):
    live = json.load(open('out/likes.json', encoding='utf-8'))
    labels = json.load(open('out/labels.json', encoding='utf-8'))
    pool = [(tid, txt) for _, tid, txt in live if tid in labels]
    picked = random.Random(42).sample(pool, min(n, len(pool)))
    json.dump([tid for tid, _ in picked], open(IDS, 'w'))
    with open(CSV, 'w', newline='', encoding='utf-8-sig') as f:  # BOM so Excel reads non-ASCII text
        w = csv.writer(f)
        w.writerow(['n', 'text', 'your_theme', 'your_actionable'])
        for i, (_, txt) in enumerate(picked, 1):
            w.writerow([i, txt, '', ''])
    print(f'wrote {CSV} with {len(picked)} rows. Themes: {", ".join(THEMES)}. actionable: 1 or 0.')


def score(rows, ids, labels):
    """rows: dicts from the csv. Returns (n, theme_agree, act_agree, confusions, disagreements)."""
    n = theme_ok = act_ok = 0
    conf, diffs = collections.Counter(), []
    for r in rows:
        mine_t, mine_a = r['your_theme'].strip(), r['your_actionable'].strip()
        if not mine_t:
            continue  # row left blank
        theme, actionable = labels[ids[int(r['n']) - 1]]
        n += 1
        theme_ok += mine_t == theme
        act_ok += mine_a == str(actionable)
        if mine_t != theme:
            conf[(mine_t, theme)] += 1
        if mine_t != theme or mine_a != str(actionable):
            diffs.append((r['text'][:100], f'{mine_t}/{mine_a}', f'{theme}/{actionable}'))
    return n, theme_ok, act_ok, conf.most_common(3), diffs


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['sample', 'score'])
    ap.add_argument('--n', type=int, default=50)
    a = ap.parse_args()
    if a.cmd == 'sample':
        sample(a.n)
    else:
        with open(CSV, encoding='utf-8-sig') as f:
            text = f.read()
        try:
            dialect = csv.Sniffer().sniff(text[:2048], ',;')  # Excel may save with ;
        except csv.Error:
            dialect = 'excel'
        rows = list(csv.DictReader(io.StringIO(text, newline=''), dialect=dialect))
        n, t, act, conf, diffs = score(rows, json.load(open(IDS)), json.load(open('out/labels.json', encoding='utf-8')))
        if not n:
            raise SystemExit('no rows filled in yet')
        print(f'{n} rows: theme agreement {t / n:.0%}, actionable agreement {act / n:.0%}')
        print('most confused (you -> model):', ', '.join(f'{a}->{b} x{c}' for (a, b), c in conf) or 'none')
        for txt, mine, model in diffs:
            print(f'  you {mine:<20} model {model:<20} {txt!r}')
