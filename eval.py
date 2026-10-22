# How good are the labels? Label a random sample yourself, blind, then compare with the model.
# Run: python eval.py sample [--n 50]   -> out/eval.csv
#      python eval.py fill              -> label the rows in the terminal (or edit the csv in a spreadsheet)
#      python eval.py score             -> agreement and every disagreement
import argparse, csv, io, json, random, collections
from label import THEMES

CSV, IDS = 'out/eval.csv', 'out/eval_ids.json'  # ids live in a sidecar: Excel mangles 19-digit numbers
FIELDS = ['n', 'text', 'your_theme', 'your_actionable']


def read_rows():
    with open(CSV, encoding='utf-8-sig') as f:
        text = f.read()
    try:
        dialect = csv.Sniffer().sniff(text[:2048], ',;')  # Excel may save with ;
    except csv.Error:
        dialect = 'excel'
    return list(csv.DictReader(io.StringIO(text, newline=''), dialect=dialect))


def write_rows(rows):
    with open(CSV, 'w', newline='', encoding='utf-8-sig') as f:  # BOM so Excel reads non-ASCII text
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)


def sample(n):
    live = json.load(open('out/likes.json', encoding='utf-8'))
    labels = json.load(open('out/labels.json', encoding='utf-8'))
    pool = [(tid, txt) for _, tid, txt in live if tid in labels]
    picked = random.Random(42).sample(pool, min(n, len(pool)))
    json.dump([tid for tid, _ in picked], open(IDS, 'w'))
    write_rows([{'n': i, 'text': txt, 'your_theme': '', 'your_actionable': ''} for i, (_, txt) in enumerate(picked, 1)])
    print(f'wrote {CSV} with {len(picked)} rows. Next: python eval.py fill')


def fill(rows, ask, save):
    """Asks for every blank row; saves after each answer so you can stop with Ctrl+C and resume."""
    themes = list(THEMES)
    menu = '  '.join(f'{i}={t}' for i, t in enumerate(themes, 1))
    todo = [r for r in rows if not r['your_theme'].strip()]
    for k, r in enumerate(todo, 1):
        print(f'\n[{k}/{len(todo)}] {r["text"]}\n{menu}')
        while (t := ask('theme number: ').strip()) not in {str(i) for i in range(1, len(themes) + 1)}:
            pass
        while (a := ask('actionable? 1 or 0: ').strip()) not in {'0', '1'}:
            pass
        r['your_theme'], r['your_actionable'] = themes[int(t) - 1], a
        save(rows)


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
    ap.add_argument('cmd', choices=['sample', 'fill', 'score'])
    ap.add_argument('--n', type=int, default=50)
    a = ap.parse_args()
    if a.cmd == 'sample':
        sample(a.n)
    elif a.cmd == 'fill':
        rows = read_rows()
        fill(rows, input, write_rows)
        print('\nall rows done. Next: python eval.py score')
    else:
        n, t, act, conf, diffs = score(read_rows(), json.load(open(IDS)), json.load(open('out/labels.json', encoding='utf-8')))
        if not n:
            raise SystemExit('no rows filled in yet')
        print(f'{n} rows: theme agreement {t / n:.0%}, actionable agreement {act / n:.0%}')
        print('most confused (you -> model):', ', '.join(f'{a}->{b} x{c}' for (a, b), c in conf) or 'none')
        for txt, mine, model in diffs:
            print(f'  you {mine:<20} model {model:<20} {txt!r}')
