# DuckDB notes

## querying a file
SELECT * FROM read_csv('file.tsv.gz');

### adding delim and headers (duck auto detects this but doesn't hurt to be explicit)
SELECT * FROM read_csv('file.tsv.gz', delim='\t', header=true);

## checking inferred types before loading
DESCRIBE SELECT * FROM read_csv('file.tsv.gz');

## handling IMDb's `\N` null marker + full type inference
IMDb tsv dumps use the literal string `\N` for nulls. By default DuckDB only
samples the first chunk of rows to guess column types, which can misdetect a
column (e.g. a numeric column that has `\N` early on but real numbers later).
Fix both with:

SELECT * FROM read_csv('file.tsv.gz', nullstr='\N', sample_size=-1);

- `nullstr='\N'` — treat the literal `\N` as SQL NULL instead of a string.
- `sample_size=-1` — scan the whole file for type inference instead of just
  a sample, so a column doesn't get typed wrong because of what shows up
  early in the file.

## materializing a filtered table
CREATE TABLE some_table AS
SELECT * FROM read_csv('file.tsv.gz', nullstr='\N', sample_size=-1)
WHERE some_column = 'value';

## gotcha: table aliases only apply to the FROM they're attached to
An alias given to one table in a query is not visible inside a subquery
that reads from a *different* table, even if that subquery is scoped inside
the same statement. E.g.:

```sql
SELECT r.* FROM read_csv('ratings.tsv.gz') r
WHERE r.tconst = (
    SELECT b.tconst FROM house_basics WHERE startYear = 2004
);
```

This fails with `Binder Error: Referenced table "b" not found!` — `house_basics`
was never aliased as `b`; only the outer `read_csv(...)` was aliased `r`. Each
FROM clause needs its own alias if you want to reference one, e.g.
`FROM house_basics b`.


