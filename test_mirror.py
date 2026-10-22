# Run: python test_mirror.py   (no API key needed, the model call is faked)
from types import SimpleNamespace
from stats import snowflake_date, read_likes
from label import label_all, normalize, Label

# snowflake id -> date
assert snowflake_date('20') is None
assert snowflake_date('1590000000000000000').date().isoformat() == '2022-11-08'

# sample archive: duplicates collapse
assert len(read_likes(['sample/like.js'])) == 90

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
print('ok')
