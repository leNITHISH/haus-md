import logging

import config

log = logging.getLogger(__name__)


def load_raw_tables(con):
    """Materialize house_basics, house_episodes, house_ratings from the raw
    IMDb .tsv.gz dumps. Idempotent: every table uses CREATE TABLE IF NOT
    EXISTS, so re-running this is a no-op once the tables exist (no
    re-scanning the large raw files)."""

    con.sql(f"""
        CREATE TABLE IF NOT EXISTS house_basics AS
        SELECT * FROM read_csv('{config.DATA_DIR / "title.basics.tsv.gz"}',
            nullstr='\\N',
            sample_size=-1
        ) WHERE tconst = '{config.HOUSE_TCONST}';
    """)
    log.info("house_basics ready")

    con.sql(f"""
        CREATE TABLE IF NOT EXISTS house_episodes AS
        SELECT * FROM read_csv('{config.DATA_DIR / "title.episode.tsv.gz"}',
            nullstr='\\N',
            sample_size=-1
        ) WHERE parentTconst = (
            SELECT tconst FROM house_basics WHERE startyear = {config.HOUSE_START_YEAR}
        );
    """)
    log.info("house_episodes ready")

    con.sql(f"""
        CREATE TABLE IF NOT EXISTS house_ratings AS
        SELECT * FROM read_csv('{config.DATA_DIR / "title.ratings.tsv.gz"}',
            nullstr='\\N',
            sample_size=-1
        ) WHERE tconst IN (SELECT tconst FROM house_episodes);
    """)
    log.info("house_ratings ready")
