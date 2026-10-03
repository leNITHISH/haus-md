import logging

log = logging.getLogger(__name__)


def early_vs_late_v1(con):
    """Flat cutoff (episodeNumber > 15 = "late"). Flawed: doesn't account
    for seasons having different lengths (~20-24 episodes), so it mostly
    only catches the back end of the longer seasons -- the uneven split
    this produces (120 vs 57 episodes) is itself a hint something's off."""

    return con.sql("""
        SELECT
            CASE WHEN episodeNumber > 15 THEN 'late' ELSE 'early' END AS part_of_season,
            AVG(averageRating) AS avg_rating,
            COUNT(*) AS episode_count
        FROM house_full
        GROUP BY CASE WHEN episodeNumber > 15 THEN 'late' ELSE 'early' END;
    """).fetchall()


def early_vs_late_v2(con):
    """Fixed version: "late" means past the midpoint of that specific
    season (via MAX(episodeNumber) OVER (PARTITION BY seasonNumber)). With
    a fair, even split the rating gap mostly disappears -- the v1 effect
    was largely a measurement artifact from a biased cutoff."""

    return con.sql("""
        WITH episode_with_length AS (
            SELECT *,
                   MAX(episodeNumber) OVER (PARTITION BY seasonNumber) AS season_length
            FROM house_full
        )
        SELECT
            CASE WHEN episodeNumber > season_length / 2 THEN 'late' ELSE 'early' END AS part_of_season,
            AVG(averageRating) AS avg_rating,
            COUNT(*) AS episode_count
        FROM episode_with_length
        GROUP BY CASE WHEN episodeNumber > season_length / 2 THEN 'late' ELSE 'early' END;
    """).fetchall()


def lowest_vote_episodes(con, n=5):
    return con.sql(f"""
        SELECT tconst, seasonNumber, episodeNumber, averageRating, numVotes
        FROM house_full
        ORDER BY numVotes ASC
        LIMIT {n};
    """).fetchall()


def run_all(con):
    log.info("early_vs_late_v1: %s", early_vs_late_v1(con))
    log.info("early_vs_late_v2: %s", early_vs_late_v2(con))
    log.info("lowest_vote_episodes: %s", lowest_vote_episodes(con))
