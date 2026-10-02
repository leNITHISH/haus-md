# Dataset reference

Schema + sample rows for the three raw IMDb files in `data/`, so I stop
having to re-`DESCRIBE` them every time. All three are tab-separated,
gzipped, and use the literal string `\N` for nulls (hence `nullstr='\N'`
everywhere in `explore.py`).

Full upstream docs: https://developer.imdb.com/non-commercial-datasets/

Join key across all three: `tconst` (an IMDb title ID, e.g. `tt0412142` is
*House, M.D.* the series itself; each episode gets its own `tconst` too).

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
tied back to the show — episode-to-series structure lives in `title.episode`
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

Note: this file has no title/name for the episode — to get an episode's
actual title you'd join its `tconst` back into `title.basics`.
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
`title.episode.tconst` → `title.ratings.tconst` — that's the point of the
in-progress `house_ratings` table (see `notes/progress.md`).
