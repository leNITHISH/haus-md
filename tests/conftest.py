import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import transform

# 2 seasons, 3 episodes each, clean data.
EPISODES = [
    ("tt0001", 1, 1),
    ("tt0002", 1, 2),
    ("tt0003", 1, 3),
    ("tt0004", 2, 1),
    ("tt0005", 2, 2),
    ("tt0006", 2, 3),
]
RATINGS = [
    ("tt0001", 8.0, 5000),
    ("tt0002", 8.2, 5100),
    ("tt0003", 8.4, 5200),
    ("tt0004", 8.6, 5300),
    ("tt0005", 8.8, 5400),
    ("tt0006", 9.0, 5500),
]


def _seed(con, episodes=EPISODES, ratings=RATINGS):
    con.sql("CREATE TABLE house_basics (tconst VARCHAR)")
    con.sql("INSERT INTO house_basics VALUES ('tt0000')")

    con.sql("""
        CREATE TABLE house_episodes (
            tconst VARCHAR, seasonNumber INTEGER, episodeNumber INTEGER
        )
    """)
    con.executemany("INSERT INTO house_episodes VALUES (?, ?, ?)", episodes)

    con.sql("""
        CREATE TABLE house_ratings (
            tconst VARCHAR, averageRating DOUBLE, numVotes INTEGER
        )
    """)
    con.executemany("INSERT INTO house_ratings VALUES (?, ?, ?)", ratings)
    return con


@pytest.fixture
def clean_con():
    return _seed(duckdb.connect(":memory:"))


@pytest.fixture
def out_of_range_rating_con():
    ratings = list(RATINGS)
    ratings[0] = ("tt0001", 11.0, 5000)
    return _seed(duckdb.connect(":memory:"), ratings=ratings)


@pytest.fixture
def duplicate_tconst_con():
    episodes = list(EPISODES)
    episodes.append(("tt0001", 1, 1))
    ratings = list(RATINGS)
    ratings.append(("tt0001", 8.0, 5000))
    return _seed(duckdb.connect(":memory:"), episodes=episodes, ratings=ratings)


@pytest.fixture
def negative_votes_con():
    ratings = list(RATINGS)
    ratings[0] = ("tt0001", 8.0, -1)
    return _seed(duckdb.connect(":memory:"), ratings=ratings)


# "Director A" directs season 1 + the last episode of season 2, "Director B"
# directs the rest of season 2. "Writer X" writes every episode.
DIRECTORS = [
    ("tt0001", "nm001"), ("tt0002", "nm001"), ("tt0003", "nm001"),
    ("tt0004", "nm002"), ("tt0005", "nm002"), ("tt0006", "nm001"),
]
WRITERS = [(tconst, "nm010") for tconst, _, _ in EPISODES]
PEOPLE = [
    ("nm001", "Director A"),
    ("nm002", "Director B"),
    ("nm010", "Writer X"),
]


def _seed_crew(con, directors=DIRECTORS, writers=WRITERS, people=PEOPLE):
    con.sql("CREATE TABLE house_directors (tconst VARCHAR, nconst VARCHAR)")
    con.executemany("INSERT INTO house_directors VALUES (?, ?)", directors)

    con.sql("CREATE TABLE house_writers (tconst VARCHAR, nconst VARCHAR)")
    con.executemany("INSERT INTO house_writers VALUES (?, ?)", writers)

    con.sql("CREATE TABLE house_people (nconst VARCHAR, primaryName VARCHAR)")
    con.executemany("INSERT INTO house_people VALUES (?, ?)", people)
    return con


@pytest.fixture
def crew_con(clean_con):
    transform.build_house_full(clean_con)
    return _seed_crew(clean_con)


@pytest.fixture
def unresolved_crew_con(clean_con):
    transform.build_house_full(clean_con)
    return _seed_crew(clean_con, people=PEOPLE[:-1])  # "Writer X" (nm010) has no matching row
