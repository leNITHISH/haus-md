# DuckDB notes

## querying a file
SELECT * FROM read_csv('file.tsv.gz');

### adding delim and headers (duck auto detects this but doesn't hurt to be explicit)
SELECT * FROM read_csv('file.tsv.gz', delim='\t', header=true);


