import logging

log = logging.getLogger(__name__)


def build_house_full(con):
    """Join house_episodes with house_ratings into one row per episode,
    ordered by season/episode (watch order). Works against any connection
    that already has house_episodes/house_ratings populated, real or
    fixture."""

    con.sql("""
        CREATE TABLE IF NOT EXISTS house_full AS
        SELECT e.tconst, e.seasonNumber, e.episodeNumber,
               r.averageRating, r.numVotes
        FROM house_episodes e
        JOIN house_ratings r ON r.tconst = e.tconst
        ORDER BY seasonNumber, episodeNumber;
    """)
    log.info("house_full built")


def build_house_rolling(con):
    """house_full plus a 5-episode rolling average of averageRating, in
    watch order, to smooth noise and spot rating arcs over time."""

    con.sql("""
        CREATE TABLE IF NOT EXISTS house_rolling AS
        SELECT seasonNumber, episodeNumber, averageRating,
               AVG(averageRating) OVER (
                   ORDER BY seasonNumber, episodeNumber
                   ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
               ) AS rolling_avg
        FROM house_full;
    """)
    log.info("house_rolling built")
