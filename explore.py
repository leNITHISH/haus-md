# Scratch space for learning DuckDB by building up a local warehouse of
# House, M.D. data pulled from the full IMDb dataset dump (see data/).
#
# Workflow so far: uncomment one block at a time, run, check the result,
# comment it back out before moving to the next. Blocks below are in the
# order they were originally run (oldest at top). See notes/progress.md
# for what's done, what's broken, and what's next.
import duckdb

con = duckdb.connect('haus.duckdb')

# Step 1: check how DuckDB infers the schema of the raw title.basics dump
# before creating anything from it.
#con.sql("""
#    DESCRIBE SELECT * FROM read_csv('data/title.basics.tsv.gz', 
#        nullstr='\\N', 
#        sample_size=-1
#    );
#""").show()


# Step 2: materialize the single House, M.D. row (tt0412142, 2004) from
# title.basics into its own table.
#con.sql("""
#    CREATE TABLE house_basics AS
#    SELECT * FROM read_csv('data/title.basics.tsv.gz', 
#        nullstr='\\N', 
#        sample_size=-1
#    )WHERE tconst='tt0412142';
#""").show()
#con.sql("""
#        SELECT * FROM house_basics;
#        """).show()


# Step 3: same as step 1, but for title.episode, before pulling in episodes.
#con.sql("""
#    DESCRIBE SELECT * FROM read_csv('data/title.episode.tsv.gz',
#        nullstr='\\N', 
#        sample_size=-1
#    );
#""").show()

# Step 4: materialize all episodes belonging to the show (parentTconst
# matches whatever house_basics resolved to) into house_episodes.
#con.sql("""
#        CREATE TABLE house_episodes AS
#        SELECT * FROM read_csv('data/title.episode.tsv.gz',
#            nullstr='\\N',
#            sample_size=-1
#        ) WHERE parenttconst=(
#            SELECT tconst from house_basics where startyear=2004
#        );
#        """)


#con.sql("""
#        SELECT * FROM house_episodes;
#        """).show()


# Step 5: pull in ratings for the show's episodes from title.ratings,
# keyed off the tconsts already collected in house_episodes. (Originally
# broken — see notes/progress.md and notes/duck.md for the alias-scoping
# bug that was here before the `tconst IN (...)` rewrite.)
#con.sql("""
#        CREATE TABLE house_ratings AS
#        SELECT * FROM read_csv('data/title.ratings.tsv.gz',
#        nullstr='\\N',
#        sample_size=-1
#    ) WHERE tconst IN (SELECT tconst FROM house_episodes) ;
#""")


# Step 6: check what's in house_ratings now that it's built.
#con.sql("""
#        SELECT * FROM house_ratings;
#        """).show();


#con.sql("""
#       CREATE TABLE house_full AS select e.tconst, e.seasonNumber, e.episodeNumber, r.averageRating, r.numVotes from house_episodes e join house_ratings r on r.tconst=e.tconst order by seasonNumber, episodeNumber;""")

con.sql("""
        SELECT * from house_full;
        """).show()
