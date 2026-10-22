# Step 1: read one or more X archive like.js files, dedupe, date each like, write out/likes.json.
# Run: python stats.py path/to/like.js [more like.js ...]
import json, sys, os, re, datetime, collections

EPOCH_MS = 1288834974657  # X snowflake epoch (Nov 2010)
# what the export puts in place of text it can't show you
PLACEHOLDERS = ('This Post is from a suspended account', 'You’re unable to view this Post', "You're unable to view this Post",
                'Age-restricted adult content')


def snowflake_date(tweet_id):
    i = int(tweet_id)
    if i < 10**15:
        return None  # pre-snowflake (before Nov 2010), no date in the id
    return datetime.datetime.fromtimestamp(((i >> 22) + EPOCH_MS) / 1000, datetime.timezone.utc)


def read_likes(paths):
    seen = {}
    for p in paths:
        s = open(p, encoding='utf-8').read()
        for x in json.loads(s[s.index('['):]):  # strip the "window.YTD.like.part0 =" prefix
            like = x['like']
            seen.setdefault(like['tweetId'], like.get('fullText', ''))
    return seen


def readable(text):
    return bool(re.sub(r'https://t\.co/\S+', '', text).strip()) and not text.startswith(PLACEHOLDERS)


if __name__ == '__main__':
    seen = read_likes(sys.argv[1:])
    rows = [(snowflake_date(t), t, txt) for t, txt in seen.items()]
    live = [r for r in rows if readable(r[2])]  # drops deleted, suspended, locked, age-gated and link-only posts
    print('unique likes', len(rows), 'readable', len(live))
    print('by year', sorted(collections.Counter(r[0].year if r[0] else 'pre2011' for r in live).items(), key=str))
    os.makedirs('out', exist_ok=True)
    live.sort(key=lambda r: r[0] or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    json.dump([[d.isoformat() if d else None, t, txt] for d, t, txt in live],
              open('out/likes.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('wrote out/likes.json')
