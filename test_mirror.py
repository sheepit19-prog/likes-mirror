# Run: python test_mirror.py   (no API key needed, the model call is faked)
from types import SimpleNamespace
from stats import snowflake_date, read_likes, readable
from label import label_all, normalize, Label
from analyze import compute
from report import render, recent_actionable, Moves, Move
from eval import score, fill

# snowflake id -> date
assert snowflake_date('20') is None
assert snowflake_date('1590000000000000000').date().isoformat() == '2022-11-08'

# sample archive: duplicates collapse
assert len(read_likes(['sample/like.js'])) == 33

# readable: export placeholders and link-only posts are not content
assert readable('Plan first. https://t.co/abc') and not readable('https://t.co/abc ') and not readable('')
assert not readable('This Post is from a suspended account. {learnmore}')
assert not readable('You’re unable to view this Post because this account owner limits who can view their Posts.')

# normalize: invented ids dropped, unknown theme -> other
got = normalize([Label(id='1', theme='ai_tech', actionable=True), Label(id='2', theme='cooking', actionable=False),
                 Label(id='999', theme='humor', actionable=False)], {'1', '2'})
assert got == {'1': ['ai_tech', 1], '2': ['other', 0]}

# label_all: cached likes are skipped, batches are saved as they go
calls, saves = [], []
def fake(batch):
    calls.append(len(batch))
    return {tid: ['humor', 0] for tid, _ in batch}, SimpleNamespace(input_tokens=10, output_tokens=2)
likes = [[None, str(i), 'x'] for i in range(5)]
cache = {'0': ['ai_tech', 1]}
n, tin, tout = label_all(likes, cache, fake, batch_size=2, save=lambda c: saves.append(len(c)))
assert (n, calls, saves, tin, tout) == (4, [2, 2], [3, 5], 20, 4)
assert cache['0'] == ['ai_tech', 1]

# compute: shares, actionable, shifts, half-years
live = [['2024-03-01T00:00:00', 'a', 't'], ['2024-08-01T00:00:00', 'b', 't'],
        ['2025-02-01T00:00:00', 'c', 't'], ['2025-09-01T00:00:00', 'd', '<script>alert(1)</script>'],
        [None, 'e', 'undated'], ['2025-10-01T00:00:00', 'f', 'unlabeled']]
labels = {'a': ['finance', 0], 'b': ['finance', 1], 'c': ['ai_tech', 1], 'd': ['ai_tech', 1], 'e': ['humor', 0]}
s = compute(live, labels, min_likes=1)
assert (s['labeled'], s['total'], s['years']) == (4, 6, ['2024', '2025'])
assert s['share']['finance'] == {'2024': 1.0, '2025': 0.0}
assert s['actionable'] == {'2024': 0.5, '2025': 1.0}
assert s['riser'] == ('ai_tech', 0.0, 1.0) and s['faller'] == ('finance', 1.0, 0.0)
assert s['half'] == {'2024H1': [('finance', 1)], '2024H2': [('finance', 1)], '2025H1': [('ai_tech', 1)], '2025H2': [('ai_tech', 1)]}

# min_likes: a thin year is left out of shares, shifts and half-years, and reported as left out
t = compute(live + [['2026-01-01T00:00:00', 'g', 't']], {**labels, 'g': ['humor', 0]}, min_likes=2)
assert (t['years'], t['thin'], t['last']) == (['2024', '2025'], ['2026'], '2025') and '2026H1' not in t['half']
assert 'Left out, under 30 likes: 2026.' in render(t)

# unclear: counted, kept out of shares and themes, named in the report
u = compute(live + [['2025-11-01T00:00:00', 'h', 'lol https://t.co/x']], {**labels, 'h': ['unclear', 0]}, min_likes=1)
assert u['unclear'] == 1 and u['labeled'] == 4 and 'unclear' not in u['themes'] and u['share'] == s['share']
assert '1 more could not be read from text alone' in render(u)

# recent_actionable: last 12 months, actionable, top themes only, newest first
assert [p[2] for p in recent_actionable(live, labels, {'ai_tech', 'finance'})] == ['<script>alert(1)</script>', 't']

# render: works without a goal, escapes everything from the data and the model
page = render(s)
assert 'Moves toward' not in page and '<b>ai_tech</b> went from 0% of your likes in 2024 to 100% in 2025' in page
m = Moves(mirror='<img src=x onerror=alert(1)>', moves=[Move(title='<b>t</b>', evidence='e', first_step='f', check='c')])
page = render(s, m, goal='<script>')
assert '<script>' not in page.split('</style>')[1] and '<img' not in page and '&lt;b&gt;t&lt;/b&gt;' in page

# eval score: blank rows skipped, agreement counted, ids looked up by row number
rows = [{'n': '1', 'text': 'x', 'your_theme': 'finance', 'your_actionable': '1'},
        {'n': '2', 'text': 'y', 'your_theme': 'ai_tech', 'your_actionable': '0'},
        {'n': '3', 'text': 'z', 'your_theme': '', 'your_actionable': ''}]
n, t, act, conf, diffs = score(rows, ['b', 'a', 'c'], labels)
assert (n, t, act, conf) == (2, 1, 2, [(('ai_tech', 'finance'), 1)]) and len(diffs) == 1

# eval fill: filled rows skipped, bad input asked again, saved after every row
rows = [{'n': '1', 'text': 'a', 'your_theme': 'humor', 'your_actionable': '0'},
        {'n': '2', 'text': 'b', 'your_theme': '', 'your_actionable': ''}]
answers, saved = iter(['99', 'x', '1', '7', '1']), []
fill(rows, lambda _: next(answers), lambda r: saved.append(r[1]['your_theme']))
assert rows[1]['your_theme'] == 'ai_tech' and rows[1]['your_actionable'] == '1' and saved == ['ai_tech']
print('ok')
