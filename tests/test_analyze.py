import pytest

import analyze
import transform


def _build(con):
    transform.build_house_full(con)
    return con


def test_season_averages(clean_con):
    _build(clean_con)
    rows = dict((season, avg) for season, avg, _ in analyze.season_averages(clean_con))
    assert rows[1] == pytest.approx(8.2)
    assert rows[2] == pytest.approx(8.8)


def test_premiere_vs_finale(clean_con):
    _build(clean_con)
    rows = {episode_type: avg for episode_type, avg, _ in analyze.premiere_vs_finale(clean_con)}
    assert rows["premiere"] == pytest.approx((8.0 + 8.6) / 2)
    assert rows["finale"] == pytest.approx((8.4 + 9.0) / 2)


def test_votes_rating_correlation_is_perfectly_linear(clean_con):
    _build(clean_con)
    # fixture ratings and vote counts both increase in lockstep
    assert analyze.votes_rating_correlation(clean_con) == pytest.approx(1.0)


def test_votes_per_season(clean_con):
    _build(clean_con)
    rows = dict((season, votes) for season, votes, _ in analyze.votes_per_season(clean_con))
    assert rows[1] == pytest.approx(5100)
    assert rows[2] == pytest.approx(5400)


def test_season_rating_outliers_top_result_is_a_season_extreme(clean_con):
    _build(clean_con)
    top = analyze.season_rating_outliers(clean_con, n=1)[0]
    _, _, _, _, z_score = top
    assert abs(z_score) == pytest.approx(1.0)


def test_director_ratings_respects_min_episodes(crew_con):
    # "Director A" (4 episodes) clears a min_episodes=3 threshold,
    # "Director B" (2 episodes) doesn't.
    names = [name for name, _, _ in analyze.director_ratings(crew_con, min_episodes=3)]
    assert names == ["Director A"]


def test_director_ratings_avg_rating(crew_con):
    rows = {name: avg for name, _, avg in analyze.director_ratings(crew_con, min_episodes=1)}
    assert rows["Director A"] == pytest.approx((8.0 + 8.2 + 8.4 + 9.0) / 4)
    assert rows["Director B"] == pytest.approx((8.6 + 8.8) / 2)


def test_writer_ratings_credited_on_every_episode(crew_con):
    rows = analyze.writer_ratings(crew_con, min_episodes=1)
    assert len(rows) == 1
    name, episode_count, avg_rating = rows[0]
    assert name == "Writer X"
    assert episode_count == 6
    assert avg_rating == pytest.approx((8.0 + 8.2 + 8.4 + 8.6 + 8.8 + 9.0) / 6)
