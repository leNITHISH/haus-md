import duckdb

con = duckdb.connect('haus.duckdb')
con.sql("""
    DESCRIBE SELECT * FROM read_csv('data/title.basics.tsv.gz', 
        nullstr='\\N', 
        sample_size=-1
    );
""").show()
