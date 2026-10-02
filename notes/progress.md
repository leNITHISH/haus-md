# Progress log

## Status: active again (exams done), as of 2026-10-02

## Done

- `house_basics` — created, holds the single `title.basics` row for
  *House, M.D.* (`tt0412142`, `startYear = 2004`). 1 row.
- `house_episodes` — created, all 177 episodes from `title.episode` whose
  `parentTconst` matches the show.
- `house_ratings` — created. Was broken on an alias-scoping bug (subquery
  referenced `b.tconst` but `house_basics` was never aliased `b` — see
  `notes/duck.md`); fixed by rewriting the filter as
  `tconst IN (SELECT tconst FROM house_episodes)` instead of a scalar
  subquery against `house_basics`.

## Next steps

1. Join `house_episodes` + `house_ratings` to look at per-episode ratings
   over time (which season/episode rated best, trend across the show's
   run, etc.) — see `notes/sql.md` for join/window-function syntax.
2. Consider whether `house_basics`/`house_episodes`/`house_ratings` should
   be rebuilt from scratch each run or persisted — right now `explore.py`
   is pure scratch (comment/uncomment blocks by hand), no idempotency or
   `CREATE OR REPLACE`.
