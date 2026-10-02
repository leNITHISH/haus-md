# Analysis queries + findings, run against the tables built by explore.py.
# Run explore.py first (or at least once) so house_full exists in haus.duckdb.
import duckdb

con = duckdb.connect('haus.duckdb')


# --- Finding 1: early vs late season rating, v1 (flawed) -------------------
# First attempt used a flat cutoff (episodeNumber > 15) to mean "late season".
# Result: early=8.27 (120 eps) vs late=8.52 (57 eps) -- looked like a solid
# effect, but the split was badly uneven (120 vs 57), which was a hint
# something was off: a flat cutoff doesn't account for seasons having
# different episode counts (~20-24 eps), so it mostly only caught the back
# end of the *longer* seasons.
con.sql("""
    SELECT
        CASE WHEN episodeNumber > 15 THEN 'late' ELSE 'early' END AS part_of_season,
        AVG(averageRating) AS avg_rating,
        COUNT(*) AS episode_count
    FROM house_full
    GROUP BY CASE WHEN episodeNumber > 15 THEN 'late' ELSE 'early' END;
""").show()


# --- Finding 2: early vs late season rating, v2 (fixed methodology) --------
# Fixed version: compute each season's actual length via a window function
# (MAX(episodeNumber) OVER (PARTITION BY seasonNumber)), then use "past the
# midpoint of THIS season" as the cutoff instead of a flat number.
# Result: early=8.29 (87 eps) vs late=8.40 (90 eps) -- split is now nearly
# even (as it should be), and the rating gap shrank a lot. Lesson: the v1
# "late episodes rate higher" effect was partly a measurement artifact from
# a biased cutoff, not a clean season-position effect. The real effect (if
# any) is much smaller than it first looked.
con.sql("""
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
""").show()


# --- Finding 3: data quality quirk on the series finale ---------------------
# house_episodes/house_ratings matching found 177 rows (8 seasons), all
# clean -- except the finale (tt39387148) has a suspiciously low numVotes
# (239) compared to every other episode (2,700-9,000+). Its tconst is also
# numerically way higher than every other episode's tconst, which on IMDb
# usually means the entry was added to their database much more recently
# than 2012 (when the finale actually aired). Likely explanation: IMDb at
# some point re-added/re-tagged the finale under a new tconst, splitting
# its votes from whatever the "original" finale entry might still be.
# Flagged here as a known data quality issue, not fixed/merged -- worth
# digging into further if this project gets revisited.
con.sql("""
    SELECT tconst, seasonNumber, episodeNumber, averageRating, numVotes
    FROM house_full
    ORDER BY numVotes ASC
    LIMIT 5;
""").show()


# --- Rolling average (5-episode window) -------------------------------------
# Built to visually spot rating arcs across the whole series (e.g. the
# season 4 finale / "Amber" arc). Currently just computed/stored in
# house_rolling (see explore.py) -- not plotted yet. Next step: pull this
# into matplotlib, rolling_avg on the y-axis, watch order on the x-axis,
# and actually look for the dip/spike around S4E15-16.
con.sql("SELECT * FROM house_rolling;").show()
