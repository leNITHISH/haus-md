# Progress log


## Done

- `house_basics` — created, holds the single `title.basics` row for
  *House, M.D.* (`tt0412142`, `startYear = 2004`). 1 row.
- `house_episodes` — created, all 177 episodes from `title.episode` whose
  `parentTconst` matches the show.

## In progress / broken

- `house_ratings` (bottom block of `explore.py`) — **does not run yet.**
  ```
  Binder Error: Referenced table "b" not found!
  Candidate tables: "r"
  LINE 7:             SELECT b.tconst from house_basics where startyear=2004
  ```
  The subquery selects `b.tconst` but never aliases `house_basics` as `b`
  (only the outer `title.ratings` read is aliased, as `r`). Left unfixed on
  purpose per "don't touch the logic while it's on hold" — next session,
  fix the alias (or drop it and just reference `house_basics.tconst`) and
  re-run.
- Because of the above, `house_ratings` doesn't exist in `haus.duckdb` yet
  — only `house_basics` and `house_episodes` do.

## Next steps (pick up here)

1. Fix the `house_ratings` subquery alias bug above.
2. Once `house_ratings` builds, start joining `house_episodes` +
   `house_ratings` to look at per-episode ratings over time.
3. Consider whether `house_basics`/`house_episodes` should be rebuilt from
   scratch each run or persisted — right now `explore.py` is pure scratch
   (comment/uncomment blocks by hand), no idempotency or `CREATE OR REPLACE`.
