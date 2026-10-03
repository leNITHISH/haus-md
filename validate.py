import logging

log = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when house_full fails a hard data-quality invariant."""


def check_rating_range(con):
    bad = con.sql(
        "SELECT COUNT(*) FROM house_full WHERE averageRating < 1 OR averageRating > 10"
    ).fetchone()[0]
    if bad:
        return f"{bad} row(s) have averageRating outside [1, 10]"
    return None


def check_no_duplicate_tconsts(con):
    total, distinct = con.sql(
        "SELECT COUNT(*), COUNT(DISTINCT tconst) FROM house_full"
    ).fetchone()
    if total != distinct:
        return f"house_full has {total} rows but only {distinct} distinct tconsts"
    return None


def check_positive_votes(con):
    bad = con.sql("SELECT COUNT(*) FROM house_full WHERE numVotes <= 0").fetchone()[0]
    if bad:
        return f"{bad} row(s) have non-positive numVotes"
    return None


def check_nonempty_tables(con):
    basics_count = con.sql("SELECT COUNT(*) FROM house_basics").fetchone()[0]
    if basics_count != 1:
        return f"house_basics has {basics_count} row(s), expected exactly 1"
    for table in ("house_episodes", "house_ratings", "house_full"):
        count = con.sql(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count == 0:
            return f"{table} is empty"
    return None


HARD_CHECKS = [
    check_rating_range,
    check_no_duplicate_tconsts,
    check_positive_votes,
    check_nonempty_tables,
]


def check_vote_count_outliers(con, threshold=1000):
    """Warn (don't fail) on episodes whose numVotes is suspiciously low
    relative to the rest of the series. Known to flag the series finale,
    whose vote count (239) and unusually high tconst suggest a late/
    duplicate IMDb entry splitting votes from an "original" finale row."""

    rows = con.sql(f"""
        SELECT tconst, seasonNumber, episodeNumber, numVotes
        FROM house_full
        WHERE numVotes < {threshold}
        ORDER BY numVotes ASC
    """).fetchall()
    for tconst, season, episode, votes in rows:
        log.warning(
            "vote count outlier: %s (S%sE%s) has only %s votes (threshold %s)",
            tconst, season, episode, votes, threshold,
        )
    return rows


def run_all(con):
    """Run every hard check, collecting all failures rather than failing
    fast, then run the warn-and-log check regardless of outcome."""

    failures = [msg for check in HARD_CHECKS if (msg := check(con)) is not None]
    if failures:
        raise ValidationError("; ".join(failures))
    log.info("all hard data-quality checks passed")

    check_vote_count_outliers(con)
