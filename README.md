# Likes Mirror

Your X likes are a better record of what you actually care about than anything you'd write down.
Likes Mirror reads the `like.js` file from your X data export, labels every like with Claude, and shows
how your interests shifted year by year, how much of what you save is something you can actually use,
and, if you give it a goal, where your attention contradicts it.

Everything runs locally. Your archive, labels and report stay in `out/`, which git ignores.

## What you get

`out/report.html`, a single file with no scripts or external assets:

- **Biggest shifts:** "finance went from 22% of your likes in 2024 to 4% in 2026."
- **Theme share by year,** with the share of likes that are actionable (a technique, tool or resource you could apply).
- **Last two years by half-year,** to see what rose and what died.
- **Moves toward your goal** (optional): a short, evidence-backed read of where your feed helps or fights the goal,
  and up to 3 moves. Each one cites a number or a saved post, and comes with a "check before acting" caveat.

<!-- screenshot: add once generated from real labels -->

## Run it

1. Request your archive: X > Settings > Your account > Download an archive of your data. When it arrives, unzip it and find `data/like.js`.
2. Install and set your key:
   ```
   pip install -r requirements.txt
   export ANTHROPIC_API_KEY=...          # PowerShell: $env:ANTHROPIC_API_KEY="..."
   ```
3. Run:
   ```
   python stats.py path/to/like.js   # dedupe, date each like from its post id -> out/likes.json
   python label.py                   # Claude labels theme + actionable -> out/labels.json
   python analyze.py                 # quick look in the terminal
   python report.py --goal "get my first 10 paying customers"   # -> out/report.html
   ```

Try `python label.py --limit 100` first to see labels and cost on a small slice. `report.py` without `--goal`
makes no API call. `sample/like.js` has 30 invented posts to try the pipeline on.

## Check the labels yourself

A labeler you haven't measured is a guess. `eval.py` gives you a blind check:

```
python eval.py sample        # 50 random likes -> out/eval.csv, without the model's labels
python eval.py fill          # shows each post, you type a theme number and 1/0 (or edit the csv in a spreadsheet)
python eval.py score         # agreement %, most confused theme pairs, every disagreement
```

If agreement is low for one theme pair, the taxonomy is the problem more often than the model: sharpen the
two descriptions in `THEMES` (top of `label.py`), delete `out/labels.json`, relabel, and run `eval.py sample` again.

## How it works

- **Dates without timestamps.** The export doesn't say when you liked something. `stats.py` recovers the post's
  publish date from its id (X ids are snowflakes: the top bits are milliseconds since Nov 2010). Posts from
  deleted or suspended accounts come with no text and are dropped.
- **Structured labels.** `label.py` sends 50 posts per request to Claude Haiku 5.5 and gets back a validated
  Pydantic object (`theme`, `actionable`) via structured outputs, so there is no JSON parsing by hand. Unknown
  themes fall back to `other` and ids the model invents are dropped.
- **Pay once.** Labels are cached by post id and saved after every batch. A re-run, or a crash halfway,
  only pays for likes that aren't labeled yet. Scripts print token counts and dollar cost.
- **Moves are grounded.** `report.py --goal` makes one Claude Opus 5.5 call with your theme table and up to 120
  recent actionable likes from your top themes. The prompt forbids invented numbers and motivational filler.
  Everything the model returns is HTML-escaped before it reaches the page.
- **Your taxonomy.** Themes are a plain dict at the top of `label.py`. Edit it to match your feed.

## Tests

```
python test_mirror.py
```

No API key needed: model calls are faked. Covers id-to-date, deduping, label cleanup, the cache, the yearly math,
HTML escaping and eval scoring.
