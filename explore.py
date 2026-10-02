# Builds a local warehouse of House, M.D. data from the full IMDb dataset
# dump (see data/). Safe to rerun top to bottom: every table uses
# CREATE TABLE IF NOT EXISTS, so re-running this script is a no-op for
# any table that's already built (no wasted re-scans of the big .tsv.gz
# files, no "table already exists" errors either).
#
# Only the final query's result is printed via .show(); everything above
# it just builds the pipeline silently.
import duckdb

con = duckdb.connect('haus.duckdb')

# Step 1: materialize the single House, M.D. row (tt0412142, 2004) from
# title.basics into its own table.
con.sql("""
    CREATE TABLE IF NOT EXISTS house_basics AS
    SELECT * FROM read_csv('data/title.basics.tsv.gz',
        nullstr='\\N',
        sample_size=-1
    ) WHERE tconst='tt0412142';
""")

# Step 2: materialize all episodes belonging to the show (parentTconst
# matches house_basics's tconst) into house_episodes.
con.sql("""
    CREATE TABLE IF NOT EXISTS house_episodes AS
    SELECT * FROM read_csv('data/title.episode.tsv.gz',
        nullstr='\\N',
        sample_size=-1
    ) WHERE parentTconst = (
        SELECT tconst FROM house_basics WHERE startyear = 2004
    );
""")

# Step 3: pull in ratings for the show's episodes from title.ratings,
# keyed off the tconsts already collected in house_episodes.
con.sql("""
    CREATE TABLE IF NOT EXISTS house_ratings AS
    SELECT * FROM read_csv('data/title.ratings.tsv.gz',
        nullstr='\\N',
        sample_size=-1
    ) WHERE tconst IN (SELECT tconst FROM house_episodes);
""")

# Step 4: join episodes with ratings into one clean, watch-order table.
con.sql("""
    CREATE TABLE IF NOT EXISTS house_full AS
    SELECT e.tconst, e.seasonNumber, e.episodeNumber,
           r.averageRating, r.numVotes
    FROM house_episodes e
    JOIN house_ratings r ON r.tconst = e.tconst
    ORDER BY seasonNumber, episodeNumber;
""")

# Step 5: 5-episode rolling average of rating, in watch order.
con.sql("""
    CREATE TABLE IF NOT EXISTS house_rolling AS
    SELECT seasonNumber, episodeNumber, averageRating,
           AVG(averageRating) OVER (
               ORDER BY seasonNumber, episodeNumber
               ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
           ) AS rolling_avg
    FROM house_full;
""")

# Only the latest/final result gets printed when you run this script.
con.sql("SELECT * FROM house_rolling;").show()
