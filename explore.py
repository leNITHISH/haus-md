import duckdb

con = duckdb.connect('haus.duckdb')

#con.sql("""
#    DESCRIBE SELECT * FROM read_csv('data/title.basics.tsv.gz', 
#        nullstr='\\N', 
#        sample_size=-1
#    );
#""").show()


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


#con.sql("""
#    DESCRIBE SELECT * FROM read_csv('data/title.episode.tsv.gz', 
#        nullstr='\\N', 
#        sample_size=-1
#    );
#""").show()

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



con.sql("""
        CREATE TABLE house_ratings AS
        SELECT r.* FROM read_csv('data/title.ratings.tsv.gz', 
        nullstr='\\N', 
        sample_size=-1
    ) r   WHERE r.tconst = (
            SELECT b.tconst from house_basics where startyear=2004
    ) ;
""")


