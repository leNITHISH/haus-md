import pytest

import transform
import validate


def _build(con):
    transform.build_house_full(con)
    transform.build_house_rolling(con)
    return con


def test_clean_data_passes_all_checks(clean_con):
    _build(clean_con)
    validate.run_all(clean_con)  # should not raise


def test_rating_range_check_raises(out_of_range_rating_con):
    _build(out_of_range_rating_con)
    with pytest.raises(validate.ValidationError, match="averageRating"):
        validate.run_all(out_of_range_rating_con)


def test_duplicate_tconst_check_raises(duplicate_tconst_con):
    _build(duplicate_tconst_con)
    with pytest.raises(validate.ValidationError, match="distinct tconsts"):
        validate.run_all(duplicate_tconst_con)


def test_negative_votes_check_raises(negative_votes_con):
    _build(negative_votes_con)
    with pytest.raises(validate.ValidationError, match="numVotes"):
        validate.run_all(negative_votes_con)


def test_vote_count_outlier_warns_without_raising(clean_con, caplog):
    _build(clean_con)
    with caplog.at_level("WARNING"):
        validate.run_all(clean_con)  # clean fixture's votes aren't below the default threshold
    # none of the clean fixture's vote counts are below the default threshold (1000)
    assert not any("vote count outlier" in r.message for r in caplog.records)

    # lower the threshold to force the warn path to fire
    with caplog.at_level("WARNING"):
        validate.check_vote_count_outliers(clean_con, threshold=6000)
    assert any("vote count outlier" in r.message for r in caplog.records)


def test_crew_checks_pass_when_all_names_resolve(crew_con):
    validate.run_crew_checks(crew_con)  # should not raise


def test_crew_checks_raise_on_unresolved_nconst(unresolved_crew_con):
    with pytest.raises(validate.ValidationError, match="house_people"):
        validate.run_crew_checks(unresolved_crew_con)
