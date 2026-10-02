# SQL refresher

General SQL (not DuckDB-specific — see `notes/duck.md` for that). Examples
use this project's own tables so they're actually useful to copy-paste:
`house_basics` (1 row, the show itself), `house_episodes` (177 rows),
`house_ratings` (ratings per episode/show).

## Order things actually run in

Written order and execution order are different — this trips people up more
than anything else in SQL:

```
FROM   → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
```

So you *can't* refer to a `SELECT`-defined alias in `WHERE` (it doesn't
exist yet at that point), but you *can* in `ORDER BY` (runs after `SELECT`).

## SELECT / WHERE / ORDER BY / LIMIT

```sql
SELECT tconst, seasonNumber, episodeNumber
FROM house_episodes
WHERE seasonNumber = 1
ORDER BY episodeNumber
LIMIT 5;
```

- `WHERE` filters rows before any grouping — no aggregates allowed here
  (`WHERE avg(x) > 5` is invalid; that's what `HAVING` is for).
- `ORDER BY` defaults ascending; `DESC` for descending.
- `LIMIT` caps rows returned, applied last.

## JOINs

Combine rows from two tables on a matching column.

```sql
SELECT e.seasonNumber, e.episodeNumber, r.averageRating, r.numVotes
FROM house_episodes e
JOIN house_ratings r ON e.tconst = r.tconst
ORDER BY e.seasonNumber, e.episodeNumber;
```

- `JOIN` (= `INNER JOIN`) — only rows with a match on both sides.
- `LEFT JOIN` — all rows from the left table, `NULL`s on the right where
  there's no match (e.g. episodes that don't have a rating yet).
- `RIGHT JOIN` — mirror of `LEFT JOIN`, rarely used in practice (just swap
  table order and use `LEFT JOIN` instead).
- `FULL OUTER JOIN` — all rows from both sides, `NULL`s wherever there's no
  match on the other side.
- Always alias your tables (`e`, `r` above) once you're joining more than
  one — keeps column references unambiguous and queries readable.

## Aggregates + GROUP BY

```sql
SELECT seasonNumber, COUNT(*) AS num_episodes
FROM house_episodes
GROUP BY seasonNumber
ORDER BY seasonNumber;
```

- Common aggregates: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`.
- Every non-aggregated column in `SELECT` must appear in `GROUP BY`.
- `HAVING` filters *after* grouping (on aggregate results); `WHERE` filters
  *before* grouping (on raw rows):

```sql
SELECT seasonNumber, AVG(r.averageRating) AS season_avg
FROM house_episodes e
JOIN house_ratings r ON e.tconst = r.tconst
GROUP BY seasonNumber
HAVING AVG(r.averageRating) > 8.5;
```

## Subqueries

A query nested inside another, usually in `WHERE`, `FROM`, or `SELECT`.

```sql
-- scalar subquery: must return exactly one value
SELECT * FROM house_basics
WHERE tconst = (SELECT tconst FROM house_basics WHERE startYear = 2004);

-- IN subquery: returns a list, checked for membership
SELECT * FROM house_ratings
WHERE tconst IN (SELECT tconst FROM house_episodes);
```

Gotcha already hit in this project: an alias from the *outer* query's
`FROM` isn't visible inside a subquery on a *different* table unless that
table is also aliased in the subquery's own `FROM`. See `notes/duck.md`.

## CTEs (`WITH`)

A subquery you name up front and reuse — same result as a subquery, but
reads top-to-bottom instead of inside-out. Prefer this once a query gets
more than one level of nesting.

```sql
WITH rated_episodes AS (
    SELECT e.seasonNumber, e.episodeNumber, r.averageRating
    FROM house_episodes e
    JOIN house_ratings r ON e.tconst = r.tconst
)
SELECT seasonNumber, AVG(averageRating) AS season_avg
FROM rated_episodes
GROUP BY seasonNumber
ORDER BY seasonNumber;
```

## Window functions

Like aggregates, but don't collapse rows — each row keeps its identity and
gets a value computed "over" a window of related rows.

```sql
SELECT
    seasonNumber,
    episodeNumber,
    averageRating,
    RANK() OVER (PARTITION BY seasonNumber ORDER BY averageRating DESC) AS rank_in_season,
    AVG(averageRating) OVER (PARTITION BY seasonNumber) AS season_avg
FROM rated_episodes;
```

- `PARTITION BY` — restart the window per group (like `GROUP BY`, but rows
  aren't collapsed).
- `ORDER BY` inside `OVER (...)` — controls ranking/running-total order
  within each partition.
- Common ones: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG()`/`LEAD()`
  (previous/next row's value), plus any aggregate used as a window function.

## Set operations

Combine results of two queries with the same column count/types:

- `UNION` — combine + de-duplicate.
- `UNION ALL` — combine, keep duplicates (cheaper, no dedup pass).
- `INTERSECT` — rows present in both.
- `EXCEPT` — rows in the first query but not the second.

## CASE expressions

Inline conditional logic, usable anywhere an expression is valid:

```sql
SELECT
    tconst,
    CASE
        WHEN averageRating >= 9 THEN 'great'
        WHEN averageRating >= 7 THEN 'good'
        ELSE 'meh'
    END AS tier
FROM house_ratings;
```

## NULL handling

- `NULL` is "unknown" — `NULL = NULL` is `NULL`, not `TRUE`. Always use
  `IS NULL` / `IS NOT NULL`, never `= NULL`.
- `COALESCE(a, b, c)` — first non-NULL value.
- Aggregates (`COUNT`, `AVG`, etc.) ignore `NULL`s by default, except
  `COUNT(*)` which counts rows regardless of `NULL`s.
