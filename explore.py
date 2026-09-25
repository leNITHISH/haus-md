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


# Step 5 (currently broken, on hold — see notes/progress.md): pull in
# ratings for the show from title.ratings. The subquery below references
# `b.tconst` but house_basics is never aliased as `b` in this scope, so
# this raises "Binder Error: Referenced table 'b' not found!". Left as-is
# intentionally rather than fixed mid-exam-break.
con.sql("""
        CREATE TABLE house_ratings AS
        SELECT r.* FROM read_csv('data/title.ratings.tsv.gz', 
        nullstr='\\N', 
        sample_size=-1
    ) r   WHERE r.tconst = (
            SELECT b.tconst from house_basics where startyear=2004
    ) ;
""")


