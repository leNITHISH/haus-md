import pytest

import transform


def test_build_house_full_joins_correctly(clean_con):
    transform.build_house_full(clean_con)
    rows = clean_con.sql(
        "SELECT tconst, seasonNumber, episodeNumber, averageRating, numVotes FROM house_full"
    ).fetchall()

    assert len(rows) == 6
    # watch order: season then episode
    assert [r[1:3] for r in rows] == [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)]
    # spot-check one row's joined values
    first = rows[0]
    assert first[0] == "tt0001"
    assert first[3] == 8.0
    assert first[4] == 5000


def test_build_house_rolling_window(clean_con):
    transform.build_house_full(clean_con)
    transform.build_house_rolling(clean_con)
    rows = clean_con.sql(
        "SELECT rolling_avg FROM house_rolling ORDER BY seasonNumber, episodeNumber"
    ).fetchall()
    rolling = [r[0] for r in rows]

    # ratings in watch order: 8.0, 8.2, 8.4, 8.6, 8.8, 9.0
    # first row's rolling avg is just its own rating (no prior rows to average in)
    assert rolling[0] == pytest.approx(8.0)
    # once the window has 5+ rows, it's the mean of the trailing 5
    assert rolling[4] == pytest.approx((8.0 + 8.2 + 8.4 + 8.6 + 8.8) / 5)
    assert rolling[5] == pytest.approx((8.2 + 8.4 + 8.6 + 8.8 + 9.0) / 5)
