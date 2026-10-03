from pathlib import Path

REPO_ROOT = Path(__file__).parent
DATA_DIR = REPO_ROOT / "data"
DB_PATH = REPO_ROOT / "haus.duckdb"
OUTPUT_DIR = REPO_ROOT / "output"

IMDB_BASE_URL = "https://datasets.imdbws.com/"
RAW_FILES = [
    "title.basics.tsv.gz",
    "title.episode.tsv.gz",
    "title.ratings.tsv.gz",
    "title.crew.tsv.gz",
    "name.basics.tsv.gz",
]

HOUSE_TCONST = "tt0412142"
HOUSE_START_YEAR = 2004
