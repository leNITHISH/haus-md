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


def season_averages(con):
    """Average rating per season -- which season was actually best/worst,
    not just early-vs-late within one."""

    return con.sql("""
        SELECT seasonNumber, AVG(averageRating) AS avg_rating, COUNT(*) AS episode_count
        FROM house_full
        GROUP BY seasonNumber
        ORDER BY seasonNumber;
    """).fetchall()


def season_volatility(con):
    """Rating standard deviation per season, most volatile first -- which
    season was most inconsistent episode-to-episode vs. steady."""

    return con.sql("""
        SELECT seasonNumber, STDDEV_SAMP(averageRating) AS rating_stddev, COUNT(*) AS episode_count
        FROM house_full
        GROUP BY seasonNumber
        ORDER BY rating_stddev DESC;
    """).fetchall()


def votes_rating_correlation(con):
    """Pearson correlation between numVotes and averageRating -- do
    more-voted-on episodes tend to rate higher or lower?"""

    return con.sql("SELECT CORR(numVotes, averageRating) FROM house_full;").fetchone()[0]


def premiere_vs_finale(con):
    """Average rating of season premieres vs. season finales, across all
    seasons -- do finales reliably outperform premieres?"""

    return con.sql("""
        WITH season_bounds AS (
            SELECT *,
                   MIN(episodeNumber) OVER (PARTITION BY seasonNumber) AS first_ep,
                   MAX(episodeNumber) OVER (PARTITION BY seasonNumber) AS last_ep
            FROM house_full
        )
        SELECT
            CASE WHEN episodeNumber = first_ep THEN 'premiere' ELSE 'finale' END AS episode_type,
            AVG(averageRating) AS avg_rating,
            COUNT(*) AS episode_count
        FROM season_bounds
        WHERE episodeNumber = first_ep OR episodeNumber = last_ep
        GROUP BY CASE WHEN episodeNumber = first_ep THEN 'premiere' ELSE 'finale' END;
    """).fetchall()


def season_rating_outliers(con, n=5):
    """Episodes that deviate most from their own season's average, in
    standard deviations (z-score) -- a properly normalized alternative to
    just sorting by raw rating, so a wild episode in a tightly-clustered
    season counts as much as one in a volatile season."""

    return con.sql(f"""
        WITH season_stats AS (
            SELECT *,
                   AVG(averageRating) OVER (PARTITION BY seasonNumber) AS season_avg,
                   STDDEV_SAMP(averageRating) OVER (PARTITION BY seasonNumber) AS season_stddev
            FROM house_full
        ),
        zscored AS (
            SELECT tconst, seasonNumber, episodeNumber, averageRating,
                   (averageRating - season_avg) / NULLIF(season_stddev, 0) AS z_score
            FROM season_stats
        )
        SELECT tconst, seasonNumber, episodeNumber, averageRating, z_score
        FROM zscored
        ORDER BY ABS(z_score) DESC
        LIMIT {n};
    """).fetchall()


def overall_trend(con):
    """Correlation between watch order (episode index across the whole
    series) and rating -- a crude signal of whether the show trended
    better or worse over its run, independent of season boundaries."""

    return con.sql("""
        WITH ordered AS (
            SELECT *, ROW_NUMBER() OVER (ORDER BY seasonNumber, episodeNumber) AS watch_order
            FROM house_full
        )
        SELECT CORR(watch_order, averageRating) FROM ordered;
    """).fetchone()[0]


def votes_per_season(con):
    """Average vote count per season -- a proxy for how much lasting fan
    engagement each season attracted, independent of how it was rated."""

    return con.sql("""
        SELECT seasonNumber, AVG(numVotes) AS avg_votes, COUNT(*) AS episode_count
        FROM house_full
        GROUP BY seasonNumber
        ORDER BY seasonNumber;
    """).fetchall()


def _person_ratings(con, role_table, min_episodes):
    """Shared query behind director_ratings/writer_ratings: average rating
    per person credited in role_table (house_directors or house_writers),
    restricted to people with at least min_episodes credits so a single
    guest-directed episode can't top the list."""

    return con.sql(f"""
        SELECT p.primaryName, COUNT(*) AS episode_count, AVG(f.averageRating) AS avg_rating
        FROM {role_table} r
        JOIN house_full f ON f.tconst = r.tconst
        JOIN house_people p ON p.nconst = r.nconst
        GROUP BY p.primaryName
        HAVING COUNT(*) >= {min_episodes}
        ORDER BY avg_rating DESC;
    """).fetchall()


def director_ratings(con, min_episodes=3):
    """Average episode rating per director, directors with 3+ episodes
    only -- "best director of House" by the numbers."""

    return _person_ratings(con, "house_directors", min_episodes)


def writer_ratings(con, min_episodes=3):
    """Same as director_ratings, for writers. Most episodes have multiple
    credited writers, so a writer's count here is "episodes they were one
    of the credited writers on", not sole authorship."""

    return _person_ratings(con, "house_writers", min_episodes)


def run_all(con):
    log.info("early_vs_late_v1: %s", early_vs_late_v1(con))
    log.info("early_vs_late_v2: %s", early_vs_late_v2(con))
    log.info("lowest_vote_episodes: %s", lowest_vote_episodes(con))
    log.info("season_averages: %s", season_averages(con))
    log.info("season_volatility: %s", season_volatility(con))
    log.info("votes_rating_correlation: %s", votes_rating_correlation(con))
    log.info("premiere_vs_finale: %s", premiere_vs_finale(con))
    log.info("season_rating_outliers: %s", season_rating_outliers(con))
    log.info("overall_trend: %s", overall_trend(con))
    log.info("votes_per_season: %s", votes_per_season(con))
    log.info("director_ratings: %s", director_ratings(con))
    log.info("writer_ratings: %s", writer_ratings(con))
