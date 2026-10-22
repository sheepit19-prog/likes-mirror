# Likes Mirror

Your X likes are a better record of what you actually care about than anything you'd write down.
Likes Mirror reads the `like.js` file from your X data export, labels every like with Claude, and shows
how your interests shifted year by year and how much of what you save is something you can actually use.

Everything runs locally. Your archive and the labels stay in `out/`, which git ignores.

## What you get

```
theme share by year
theme              2024   2025   2026
ai_tech             12%    31%    54%
business             6%    11%    15%
finance             22%    14%     4%
humor               19%     9%     5%
...
likes               412    388    305
actionable          21%    38%    62%
```

Read it as: "finance went from a fifth of my feed to almost nothing, and two thirds of what I like now is
something I could act on". That's the kind of thing you can't see from inside the feed.
(Numbers above are illustrative. `sample/like.js` has 90 invented posts to try the pipeline on.)

## Run it

1. Request your archive: X > Settings > Your account > Download an archive of your data. When it arrives, unzip it and find `data/like.js`.
2. Install and set your key:
   ```
   pip install -r requirements.txt
   export ANTHROPIC_API_KEY=...
   ```
3. Run the three steps:
   ```
   python stats.py path/to/like.js   # dedupe, date each like from its post id -> out/likes.json
   python label.py                   # Claude labels theme + actionable -> out/labels.json
   python analyze.py                 # tables above
   ```

Try `python label.py --limit 100` first to see the labels and cost on a small slice.

## How it works

- **Dates without timestamps.** The export doesn't say when you liked something. `stats.py` recovers the post's
  publish date from its id (X ids are snowflakes: the top bits are milliseconds since Nov 2010). Posts from
  deleted or suspended accounts come with no text and are dropped.
- **Structured labels.** `label.py` sends 50 posts per request to Claude Haiku 5.5 and gets back a validated
  Pydantic object (`theme`, `actionable`) via structured outputs, so there is no JSON parsing by hand. Unknown
  themes fall back to `other` and ids the model invents are dropped.
- **Pay once.** Labels are cached by post id and saved after every batch. A re-run, or a crash halfway,
  only pays for likes that aren't labeled yet. The script prints the token count and dollar cost at the end.
  On Haiku 5.5, a few thousand likes cost cents.
- **Your taxonomy.** Themes are a plain dict at the top of `label.py`. Edit it to match your feed.

## Tests

```
python test_mirror.py
```

No API key needed: the model call is faked, so the test covers id-to-date, deduping, label cleanup and the cache.
