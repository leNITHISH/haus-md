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


def load_crew_tables(con):
    """Materialize house_directors, house_writers, house_people from
    title.crew.tsv.gz and name.basics.tsv.gz. Requires house_episodes to
    already exist (see load_raw_tables). title.crew's directors/writers
    columns are comma-separated nconst lists, one row per episode -- these
    get split into one row per (tconst, nconst) pair so they join cleanly
    against house_full later."""

    con.sql(f"""
        CREATE TABLE IF NOT EXISTS house_directors AS
        SELECT tconst, UNNEST(string_split(directors, ',')) AS nconst
        FROM read_csv('{config.DATA_DIR / "title.crew.tsv.gz"}',
            nullstr='\\N',
            sample_size=-1
        )
        WHERE tconst IN (SELECT tconst FROM house_episodes)
          AND directors IS NOT NULL;
    """)
    log.info("house_directors ready")

    con.sql(f"""
        CREATE TABLE IF NOT EXISTS house_writers AS
        SELECT tconst, UNNEST(string_split(writers, ',')) AS nconst
        FROM read_csv('{config.DATA_DIR / "title.crew.tsv.gz"}',
            nullstr='\\N',
            sample_size=-1
        )
        WHERE tconst IN (SELECT tconst FROM house_episodes)
          AND writers IS NOT NULL;
    """)
    log.info("house_writers ready")

    con.sql(f"""
        CREATE TABLE IF NOT EXISTS house_people AS
        SELECT nconst, primaryName
        FROM read_csv('{config.DATA_DIR / "name.basics.tsv.gz"}',
            nullstr='\\N',
            sample_size=-1
        )
        WHERE nconst IN (
            SELECT nconst FROM house_directors
            UNION
            SELECT nconst FROM house_writers
        );
    """)
    log.info("house_people ready")
