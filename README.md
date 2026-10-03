# Haus MD

A data pipeline that pulls *House, M.D.* episode, ratings, director, and
writer data out of the full IMDb public dataset dump, builds a local DuckDB
warehouse, runs a set of analyses on it, and plots the result. Built as a
hands-on way to learn DuckDB, data pipeline structure, and data quality
validation.

## Architecture

```
download.py     ingest.py           transform.py     validate.py       analyze.py           visualize.py / export.py
    │                │                    │                │                 │                        │
    ▼                ▼                    ▼                ▼                 ▼                        ▼
fetch 5 raw     load + join IMDb    join + rolling    hard-fail +       ratings, trends,         output/: PNG plot
.tsv.gz files   tables: episodes,   average table     warn checks       premieres vs. finales,   + Parquet files
                ratings, directors,                   (data quality)   director/writer rankings
                writers, names
```

All of it runs end to end through [`pipeline.py`](pipeline.py), the single
entrypoint. Every pipeline stage is idempotent: tables use
`CREATE TABLE IF NOT EXISTS`, and `download.py` skips files that already
exist, so rerunning the whole thing is cheap and safe.

## Setup

```bash
make setup   # creates venv/, installs requirements.txt
make run     # downloads raw IMDb files if missing, builds the warehouse,
             # validates it, runs the analysis, writes output/rolling_avg.png
make test    # runs the test suite against small in-memory fixtures
```

No manual download step needed. `download.py` fetches five files from
https://datasets.imdbws.com/ into `data/` on first run (`title.basics`,
`title.episode`, `title.ratings`, `title.crew`, `name.basics`, ~685 MB
total) and skips any file that's already there on later runs.

Schema and sample rows for each raw file are in
[`notes/datasets.md`](notes/datasets.md).

## Pipeline

Filtered down from the full IMDb dump to just *House, M.D.* (`tt0412142`):

1. **`house_basics`**: the show's own row from `title.basics`.
2. **`house_episodes`**: all 177 episodes whose `parentTconst` matches the
   show, from `title.episode`.
3. **`house_ratings`**: ratings for those 177 episode `tconst`s, from
   `title.ratings`.
4. **`house_directors`** / **`house_writers`**: one row per
   (episode, person) credit, from `title.crew`. Each episode's
   comma-separated director/writer list gets split into individual rows so
   it joins cleanly.
5. **`house_people`**: names for every director/writer nconst referenced
   above, from `name.basics` (filtered down from ~15 million people to the
   ~80 who actually worked on this show).
6. **`house_full`**: `house_episodes` joined with `house_ratings`, one row
   per episode, ordered by season/episode (true watch order).
7. **`house_rolling`**: `house_full` plus a 5-episode rolling average of
   `averageRating`, to smooth noise and spot rating arcs over time.

## Data quality

[`validate.py`](validate.py) runs after every build, split into two tiers:

- **Hard checks** (raise and stop the pipeline): ratings outside `[1, 10]`,
  duplicate episode `tconst`s, non-positive vote counts, any table coming
  back empty, or a director/writer nconst with no matching row in
  `house_people` (which would otherwise just silently drop that person out
  of the rankings below instead of failing loudly).
- **Warn-and-log** (don't stop the pipeline, just flag): episodes whose
  vote count is suspiciously low relative to the rest of the series. This
  general threshold rule, not a hardcoded exception, is what catches the
  finding below automatically.

## Findings

Full queries in [`analyze.py`](analyze.py).

- **Early vs. late season rating, take 1 (flawed):** a quick flat cutoff
  (`episodeNumber > 15` = "late") suggested late-season episodes rate
  noticeably higher (8.52 vs 8.27). But the split was badly uneven
  (120 early vs 57 late episodes), which hints the cutoff itself was
  biased, since seasons have different episode counts (~20–24).
- **Early vs. late season rating, take 2 (fixed):** redefined "late" as
  "past the midpoint of *that specific* season" using a window function
  (`MAX(episodeNumber) OVER (PARTITION BY seasonNumber)`). With a fair,
  even split (87 vs 90 episodes), the gap mostly disappeared (8.40 vs
  8.29). Lesson: the first result was largely a measurement artifact, not
  a real effect, and worth remembering before trusting any "obvious"
  first result.
- **Data quality quirk, caught by an automated check:** the series
  finale's `numVotes` (239) is way out of line with every other episode
  (2,700–9,000+), and its `tconst` is numerically much higher than the
  rest. That's usually a sign an IMDb entry was added long after the
  fact, likely a re-tagged or duplicate entry splitting votes from an
  "original" finale row. `validate.py`'s outlier check flags this
  automatically on every run; it's a known, documented data quality issue
  rather than one silently "fixed" by guessing at IMDb's internal state.
- **Season 4 is the high point** (8.56 average, the best of all 8
  seasons), consistent with the "Amber" arc being the show's most
  acclaimed stretch. Two of its episodes (S4E15, S4E16) are also among
  the biggest positive rating outliers relative to their own season.
- **Finales reliably outrate premieres:** averaged across all 8 seasons,
  finales score 9.04 vs. premieres' 8.64. Unsurprising for a show built
  on season-long mysteries, but nice to see it confirmed in the data
  rather than assumed.
- **Votes and rating are positively correlated (r ≈ 0.67):** episodes
  that pulled in more IMDb votes also tended to rate higher, suggesting
  the show's most-watched and most-discussed episodes were also its best
  received, not just its most divisive.
- **Engagement declined over the show's run:** average votes per season
  drop steadily from ~5,800 (season 1) to ~3,300 (season 8), even as
  quality stayed fairly stable. That's a sign of fading cultural reach,
  not fading quality. The overall rating-vs-time trend across all 177
  episodes is close to flat (r ≈ -0.08), so there's no strong evidence
  the show got meaningfully better or worse over its run, season-to-season
  swings aside.
- **Greg Yaitanes directed the most episodes** (30, more than double the
  next-most-prolific director) at a solid 8.36 average. Among directors
  with at least 3 episodes, **Katie Jacobs rates highest** at 9.18 across
  5 episodes.
- **David Shore, the show's creator, is a credited writer on 176 of 177
  episodes.** Among writers with heavier credit loads, **Russel Friend
  and Garrett Lerner rate highest**, tied at 8.87 across 18 episodes each.

![Rolling average rating](output/rolling_avg.png)

## What this demonstrates

- An idempotent, staged pipeline (download → ingest → transform →
  validate → analyze → visualize) instead of one monolithic script.
- Explicit data quality checks with a hard-fail/warn split, not just prose
  comments about what looked off.
- Reproducibility from a clean clone: no manually-downloaded files
  required.
- Tests ([`tests/`](tests/)) that exercise the transform and validation
  logic against tiny fixtures, independent of the 280 MB real dataset.
- CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) running the
  test suite on every push.
- A Parquet export ([`export.py`](export.py)) of the final tables, for
  downstream consumption by anything that reads columnar formats.
- A broader analysis toolkit beyond a single comparison: season
  aggregates, volatility, correlation, and normalized (z-score) outlier
  detection, not just raw sorts.
- A five-way join across separate IMDb source files, including a
  one-to-many split (`title.crew`'s comma-separated director/writer lists
  become individual rows via `UNNEST`) and a filter-then-join pattern that
  cuts `name.basics` from ~15 million rows down to the ~80 people this
  project actually needs before joining.

## Learnings

DuckDB-specific notes (options like `nullstr`/`sample_size`, the `\N` null
placeholder gotcha, window functions vs. `GROUP BY`, etc.) are kept in
[`notes/duck.md`](notes/duck.md) as they came up.
