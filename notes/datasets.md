# Dataset reference

Schema + sample rows for the five raw IMDb files in `data/`, so I stop
having to re-`DESCRIBE` them every time. All five are tab-separated,
gzipped, and use the literal string `\N` for nulls (hence `nullstr='\N'`
everywhere `read_csv` is called).

Full upstream docs: https://developer.imdb.com/non-commercial-datasets/

Join key across the title files: `tconst` (an IMDb title ID, e.g.
`tt0412142` is *House, M.D.* the series itself; each episode gets its own
`tconst` too). `title.crew` and `name.basics` add a second key, `nconst`
(a person ID), to get from an episode to the people who made it.

## title.basics.tsv.gz

One row per title (movie, series, episode, short, etc).

| column           | type    | meaning                                                      |
|------------------|---------|---------------------------------------------------------------|
| `tconst`         | VARCHAR | title ID, primary key                                        |
| `titleType`      | VARCHAR | `movie`, `tvSeries`, `tvEpisode`, `short`, etc.               |
| `primaryTitle`   | VARCHAR | the title as popularly known / promoted                      |
| `originalTitle`  | VARCHAR | original-language title                                      |
| `isAdult`        | BIGINT  | 0 = non-adult, 1 = adult title                                |
| `startYear`      | BIGINT  | release year (movies) or series start year (series)          |
| `endYear`        | BIGINT  | series end year, NULL for movies / ongoing series             |
| `runtimeMinutes` | BIGINT  | runtime in minutes                                            |
| `genres`         | VARCHAR | up to 3 comma-separated genres                                |

Sample (the House, M.D. series row itself):

```
tconst=tt0412142  titleType=tvSeries  primaryTitle=House  originalTitle=House M.D.
isAdult=0  startYear=2004  endYear=2012  runtimeMinutes=45  genres=Drama
```

Note: individual episodes are *not* in here with useful per-episode titles
tied back to the show. Episode-to-series structure lives in `title.episode`
instead (see below). `house_basics` in `haus.duckdb` is just this one row.

## title.episode.tsv.gz

One row per TV episode, linking it back to its parent series.

| column          | type    | meaning                                              |
|-----------------|---------|-------------------------------------------------------|
| `tconst`        | VARCHAR | the episode's own title ID                             |
| `parentTconst`  | VARCHAR | the series' title ID (matches `title.basics.tconst`)   |
| `seasonNumber`  | BIGINT  | season number                                          |
| `episodeNumber` | BIGINT  | episode number within the season                       |

Sample (House, M.D. S01E01–E03):

```
tconst=tt0606035  parentTconst=tt0412142  seasonNumber=1  episodeNumber=1
tconst=tt0606034  parentTconst=tt0412142  seasonNumber=1  episodeNumber=2
tconst=tt0606033  parentTconst=tt0412142  seasonNumber=1  episodeNumber=3
```

Note: this file has no title/name for the episode. To get an episode's
actual title, join its `tconst` back into `title.basics`.
`house_episodes` in `haus.duckdb` is all 177 rows where `parentTconst =
'tt0412142'`.

## title.ratings.tsv.gz

One row per title (series, movie, *or* individual episode) with its
aggregate rating.

| column          | type    | meaning                                  |
|-----------------|---------|-------------------------------------------|
| `tconst`        | VARCHAR | title ID (series, movie, or episode)      |
| `averageRating` | DOUBLE  | weighted average rating out of 10         |
| `numVotes`      | BIGINT  | number of votes behind that average       |

Sample (the House, M.D. series as a whole):

```
tconst=tt0412142  averageRating=8.7  numVotes=601153
```

Note: because episodes have their own `tconst` (from `title.episode`), you
can also look up *per-episode* ratings here by joining
`title.episode.tconst` to `title.ratings.tconst`. That's the point of
`house_ratings`.

## title.crew.tsv.gz

One row per title, listing its director(s) and writer(s) as comma-separated
`nconst` IDs (IMDb's person ID, separate from `tconst`).

| column      | type    | meaning                                      |
|-------------|---------|-----------------------------------------------|
| `tconst`    | VARCHAR | title ID                                      |
| `directors` | VARCHAR | comma-separated director `nconst`s, or NULL   |
| `writers`   | VARCHAR | comma-separated writer `nconst`s, or NULL     |

Sample (House, M.D. S01E01):

```
tconst=tt0606035  directors=nm0001741  writers=nm0794914
```

A row can list several people in one field. `house_directors` and
`house_writers` split these with `string_split()` + `UNNEST` so each
(episode, person) pair gets its own row. Most House episodes have one
credited director but several credited writers.

## name.basics.tsv.gz

One row per person IMDb has a record for (~15 million rows total): actors,
directors, writers, everyone.

| column              | type    | meaning                                |
|---------------------|---------|------------------------------------------|
| `nconst`            | VARCHAR | person ID, primary key                   |
| `primaryName`       | VARCHAR | the name they're credited under          |
| `birthYear`         | BIGINT  | birth year, NULL if unknown              |
| `deathYear`         | BIGINT  | death year, NULL if alive or unknown     |
| `primaryProfession` | VARCHAR | up to 3 comma-separated professions      |
| `knownForTitles`    | VARCHAR | up to 4 comma-separated `tconst`s        |

Sample:

```
nconst=nm0000001  primaryName=Fred Astaire  birthYear=1899  deathYear=1987
primaryProfession=actor,miscellaneous,producer
knownForTitles=tt0072308,tt0031983,tt0050419,tt0025164
```

This file is too big to filter by any House-specific key up front, so
`house_people` only keeps rows whose `nconst` shows up in `house_directors`
or `house_writers` first, about 80 people out of 15 million.
